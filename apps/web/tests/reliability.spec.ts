import {test,expect,type Page} from '@playwright/test';
import {resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
const origin='http://127.0.0.1:3000';
async function identity(page:Page,label:string){await page.goto('/');expect((await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label}})).status()).toBe(200);}

test('configured oversize batch is rejected before any upload session is created',async({page})=>{
 await identity(page,'Synthetic finance workspace');let creates=0;
 await page.route('**/api/documents/intake-capabilities',route=>route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({malware_required:false,malware_scanner:'NOT_CONFIGURED',maximum_bytes:10,maximum_pages:2})}));
 await page.route('**/api/uploads',async route=>{creates++;await route.continue()});await page.goto('/documents');await expect(page.getByText('PDF, PNG or JPEG. Up to 0 MiB and 2 pages.',{exact:true})).toBeVisible();await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page.locator('.error[role="alert"]')).toContainText('10 byte limit');expect(creates).toBe(0);
});

test('actual repeated pages remain visible with a correction instruction and separate rows',async({page})=>{
 await identity(page,'Synthetic finance workspace');await page.goto('/documents');await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');await page.getByLabel('Document files').setInputFiles(resolve('../../data/kivo_reliability/d02.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);await expect(page.locator('.page-title')).toContainText('Needs your confirmation',{timeout:30000});const id=page.url().split('/').at(-1)!;
 await expect(page.getByText('Check repeated source pages',{exact:true})).toBeVisible();await expect(page.getByText(/Pages 1 and 2 have identical rendered content/)).toContainText('upload a corrected file');await expect(page.getByRole('combobox',{name:'Source page',exact:true}).locator('option')).toHaveCount(2);
 const actual=await(await page.request.get('/api/documents/'+id)).json();expect(new Set(actual.observations.filter((o:{field_path:string})=>o.field_path.startsWith('lines.')).map((o:{field_path:string})=>o.field_path.split('.')[1])).size).toBe(4);expect(actual.finance_decision).toBeNull();expect(actual.state).toBe('NEEDS_INPUT');expect(actual.draft.findings.some((f:{code:string})=>f.code==='LINE_UNRESOLVED')).toBe(true);
});

test('lost source confirmation reply replays the same case across reload',async({page})=>{
 test.setTimeout(90000);await identity(page,'Synthetic finance workspace');await page.goto('/documents');
 await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});
 const sourceUrl=page.url();const ids:string[]=[];const keys:string[]=[];const bodies:string[]=[];
 await page.route('**/api/documents/*/commit',async route=>{keys.push(route.request().headers()['idempotency-key']);bodies.push(route.request().postData()!);const response=await route.fetch();const result=await response.json();expect(response.status(),result.error?.code||'Actual committed response').toBe(201);ids.push(result.id);if(ids.length===1)await route.abort('failed');else await route.fulfill({response});});
 async function confirm(){await page.getByLabel('Verification / correction reason').fill('Source independently reviewed for interrupted confirmation replay');await page.getByText('I reviewed the source pages and confirm the observable facts.').click();await page.getByRole('button',{name:'Verify facts and evaluate'}).click();}
 await confirm();await expect(page.locator('.error[role="alert"]')).toContainText(/fetch|network/i,{timeout:45000});await page.reload();await expect(page.locator('.page-title')).toContainText('Ready to verify');await confirm();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/,{timeout:45000});
 expect(page.url()).not.toBe(sourceUrl);expect(bodies[1]).toBe(bodies[0]);expect(keys[1]).toBe(keys[0]);expect(ids[1]).toBe(ids[0]);
 const storage=await page.evaluate(()=>Object.entries(sessionStorage));expect(storage.length).toBeGreaterThan(0);expect(storage.every(([key,value])=>/^kivo:mutation:v1:[a-f0-9]{64}$/.test(key)&&/^[a-f0-9-]{36}$/.test(value))).toBe(true);
 await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:30000});const record=await(await page.request.get('/api/transactions/'+ids[0])).json();expect(record.version).toBe(1);expect(record.versions).toHaveLength(1);
});

test('budget retry records one actual event and new selection starts an empty form',async({page})=>{
 test.setTimeout(90000);await identity(page,'Synthetic finance reviewer');
 const records=(await(await page.request.get('/api/admin/catalog')).json()).items;const base=records.find((r:{kind:string})=>r.kind==='budgets').payload;
 const first=randomUUID(),second=randomUUID();
 async function post(path:string,data:unknown){const response=await page.request.post('/api/'+path,{headers:{Origin:origin,'Idempotency-Key':randomUUID()},data});expect(response.ok(),await response.text()).toBe(true);return response.json();}
 const batch=await post('reference-imports',{source_system:'SYNTHETIC_RELIABILITY',source_version:randomUUID(),reason:'Isolated fictional replay acceptance budgets',records:[first,second].map(id=>({kind:'budgets',payload:{...base,id,version:1,source_system:'SYNTHETIC_RELIABILITY',source_record_id:id,source_version:'1',ledger:[{id:randomUUID(),version:1,entry_type:'ALLOCATION',amount:'1000.00',currency:base.currency}]}}))});
 expect((await post('reference-imports/'+batch.id+'/validate',{})).state).toBe('VALID');await post('reference-imports/'+batch.id+'/activate',{reason:'Activate isolated fictional replay budgets'});
 await page.goto('/admin');await page.getByLabel('Configuration record').selectOption(first);await page.getByLabel('Budget adjustment amount').fill('7.25');await page.getByLabel('Budget adjustment reason').fill('Single fictional event after interrupted reply');
 const keys:string[]=[],ids:string[]=[];await page.route('**/api/budgets/'+first+'/adjustments',async route=>{keys.push(route.request().headers()['idempotency-key']);const response=await route.fetch();expect(response.status()).toBe(201);ids.push((await response.json()).id);if(ids.length===1)await route.abort('failed');else await route.fulfill({response});});
 await page.getByRole('button',{name:'Add audited adjustment'}).click();await expect(page.locator('.error[role="alert"]')).toContainText(/fetch|network/i);await page.reload();await page.getByLabel('Configuration record').selectOption(first);await page.getByLabel('Budget adjustment amount').fill('7.25');await page.getByLabel('Budget adjustment reason').fill('Single fictional event after interrupted reply');await page.getByRole('button',{name:'Add audited adjustment'}).click();
 await expect(page.getByText('Budget adjustment recorded.',{exact:true})).toBeVisible();expect(keys[1]).toBe(keys[0]);expect(ids[1]).toBe(ids[0]);
 const ledger=await(await page.request.get('/api/budgets/'+first+'/ledger')).json();expect(ledger.events.filter((e:{reason:string})=>e.reason==='Single fictional event after interrupted reply')).toHaveLength(1);expect(ledger.balance.available).toBe('1007.250000');
 await expect(page.getByLabel('Budget adjustment amount')).toHaveValue('');await expect(page.getByRole('button',{name:'Add audited adjustment'})).toBeDisabled();await page.getByLabel('Budget adjustment amount').fill('99.00');await page.getByLabel('Budget adjustment reason').fill('Unsubmitted values must stay with the first budget');await page.getByLabel('Configuration record').selectOption(second);await expect(page.getByLabel('Budget adjustment amount')).toHaveValue('');await expect(page.getByLabel('Budget adjustment reason')).toHaveValue('');
});

test('client navigation to another source clears confirmation and corrections',async({page})=>{
 test.setTimeout(90000);await identity(page,'Synthetic finance workspace');const urls:string[]=[];
 for(let i=0;i<2;i++){await page.goto('/documents');await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});urls.push(page.url());}
 await page.getByLabel('Verification / correction reason').fill('This source only');await page.getByText('I reviewed the source pages and confirm the observable facts.').click();await page.getByText('Review all extracted facts and correct values',{exact:true}).click();await page.locator('input[data-field-path="invoice_date"]').fill('2026-10-01');
 // Trigger Next's actual client router through the existing workspace navigation.
 await page.getByRole('link',{name:'Upload & documents',exact:true}).click();const targetId=urls[0].split('/').at(-1)!;await page.locator('a[href="/documents/'+targetId+'"]').first().click();await expect(page).toHaveURL(urls[0]);
 await expect(page.getByLabel('Verification / correction reason')).toHaveValue('');await expect(page.getByRole('checkbox')).not.toBeChecked();await page.getByText('Review all extracted facts and correct values',{exact:true}).click();await expect(page.locator('input[data-field-path="invoice_date"]')).toHaveValue('');
});

test('new multi-line source drafts receive distinct server-assigned row identities',async({page})=>{
 test.setTimeout(90000);await identity(page,'Synthetic finance workspace');await page.goto('/documents');await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_multipage.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});
 await page.getByLabel('Verification / correction reason').fill('Review the two original source rows with distinct financial identities');await page.getByRole('checkbox').check();const completed=page.waitForResponse(r=>r.url().endsWith('/commit')&&r.request().method()==='POST');await page.getByRole('button',{name:'Verify facts and evaluate'}).click();const response=await completed;expect(response.status()).toBe(201);const result=await response.json();await expect(page).toHaveURL('/cases/'+result.id);
 const record=await(await page.request.get('/api/transactions/'+result.id)).json();expect(record.version).toBe(1);expect(record.versions).toHaveLength(1);const lines=record.versions[0].payload.lines;expect(lines).toHaveLength(2);expect(new Set(lines.map((line:{id:string})=>line.id)).size).toBe(2);for(const line of lines){expect(line.id).toMatch(/^[a-f0-9-]{36}$/);expect(typeof line.net_amount).toBe('string');expect(line.currency).toBe('INR');}
});

test('changed policy values discard an earlier in-flight validated draft',async({page})=>{
 await identity(page,'Synthetic policy administrator');await page.goto('/admin');const records=(await(await page.request.get('/api/admin/catalog')).json()).items;const hotel=records.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL'&&(r.payload as {policy_code?:string}).policy_code==='DEMO-EXP-HOTEL');await page.getByLabel('Configuration record').selectOption(hotel.id);
 let release!:()=>void;const wait=new Promise<void>(r=>release=r);let captured!:()=>void;const received=new Promise<void>(r=>captured=r);
 await page.route('**/api/admin/records/*/drafts',async route=>{const response=await route.fetch();expect(response.status()).toBe(201);captured();await wait;await route.fulfill({response});});
 await page.getByLabel('New allowance',{exact:true}).fill('9050.00');await page.getByLabel('Configuration change reason').fill('Fictional validation race only, do not activate');await page.getByRole('button',{name:'Validate and save draft',exact:true}).click();await received;await page.getByLabel('New allowance',{exact:true}).fill('9100.00');release();await expect(page.getByRole('button',{name:'Validate and save draft',exact:true})).toBeEnabled();await expect(page.getByRole('button',{name:'Activate new version',exact:true})).toHaveCount(0);await expect(page.getByLabel('New allowance',{exact:true})).toHaveValue('9100.00');
 const current=(await(await page.request.get('/api/admin/catalog')).json()).items.find((r:{id:string})=>r.id===hotel.id);expect(current.version).toBe(hotel.version);expect(current.payload.allowance_amount).toBe(hotel.payload.allowance_amount);
});

test('late policy history stays bound to the selected record',async({page})=>{
 await identity(page,'Synthetic policy administrator');await page.goto('/admin');const records=(await(await page.request.get('/api/admin/catalog')).json()).items;const hotel=records.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL'&&(r.payload as {policy_code?:string}).policy_code==='DEMO-EXP-HOTEL');const second=records.find((r:{id:string;kind:string})=>r.kind==='expense_policies'&&r.id!==hotel.id);expect(second).toBeTruthy();
 let release!:()=>void;const wait=new Promise<void>(r=>release=r);let captured!:()=>void;const received=new Promise<void>(r=>captured=r);await page.route('**/api/admin/records/'+hotel.id+'/versions',async route=>{const response=await route.fetch();captured();await wait;await route.fulfill({response});});
 await page.getByLabel('Configuration record').selectOption(hotel.id);await received;await page.getByLabel('Configuration record').selectOption(second.id);const actual=await(await page.request.get('/api/admin/records/'+second.id+'/versions')).json();release();await page.getByText('Policy versions and audit metadata',{exact:true}).click();await page.getByText('Full audit record and identifiers',{exact:true}).click();await expect.poll(async()=>JSON.parse(await page.locator('.policy-history pre').innerText())).toEqual(actual.items);
});
