import {test, expect, type Page} from '@playwright/test';
import {readFileSync, mkdirSync, writeFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomUUID, createHash} from 'node:crypto';

test.skip(process.env.AP_RUN_PANEL_REHEARSAL !== '1', 'Explicit local fictional panel rehearsal required');
const origin = 'http://127.0.0.1:3000';
const privateOutput = resolve('../../runtime/kivo-panel');
function save(name:string, value:unknown) {
 mkdirSync(privateOutput, {recursive:true, mode:0o700});
 writeFileSync(resolve(privateOutput, name), JSON.stringify(value, null, 2)+'\n', {mode:0o600});
}
async function get(page:Page, path:string) {
 const r=await page.request.get('/api/'+path);expect(r.status()).toBe(200);return r.json();
}
async function identity(page:Page, label:string) {
 const r=await page.request.post('/api/development/session', {headers:{Origin:origin},data:{label}});expect(r.status()).toBe(200);
}
async function post(page:Page, path:string, data:unknown) {
 const r=await page.request.post('/api/'+path, {headers:{Origin:origin,'Idempotency-Key':randomUUID()},data});
 expect(r.ok(),path+' '+r.status()).toBe(true);return r.json();
}
function catalogHash(items:{id:string}[]) {
 return createHash('sha256').update(JSON.stringify([...items].sort((a,b)=>a.id.localeCompare(b.id)))).digest('hex');
}
async function screenshotBoth(page:Page, name:string) {
 await page.setViewportSize({width:1366,height:900});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/panel-'+name+'-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/panel-'+name+'-phone.png',fullPage:true});
}

test('first-time Finance entry processes unfamiliar source and retains a page-two human correction', async({page})=>{
 test.setTimeout(120000);
 await page.goto('/welcome');await page.getByRole('link',{name:'Get started',exact:true}).click();
 await page.getByRole('button',{name:'Finance workspace Upload, source review and finance exceptions',exact:true}).click();
 await page.getByRole('link',{name:'Upload & documents',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Upload a document',exact:true})).toBeVisible();
 await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');
 await page.getByLabel('Document files').setInputFiles(resolve('../../data/kivo_panel/d01.pdf'));
 const started=Date.now();await page.getByRole('button',{name:'Upload and process',exact:true}).click();
 await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);
 await expect(page.getByLabel('Document progress')).toBeVisible();
 await expect(page.locator('.page-title')).toContainText('Needs your confirmation',{timeout:45000});
 const intakeSeconds=(Date.now()-started)/1000;const sourceUrl=page.url();const sourceId=sourceUrl.split('/').at(-1)!;
 const original=await get(page,'documents/'+sourceId);
 expect(original.state).toBe('NEEDS_INPUT');expect(original.finance_decision).toBeNull();
 expect(original.draft.candidate.invoice_date).toBeNull();expect(original.pages).toHaveLength(2);
 expect(original.observations.find((o:{field_path:string})=>o.field_path==='invoice_date').raw_value).toBe('10/02/2026');
 await page.getByRole('combobox',{name:'Source page',exact:true}).selectOption('2');
 await expect(page.getByRole('img',{name:/d01\.pdf, page 2/i})).toBeVisible();
 await screenshotBoth(page,'source-clarification');await page.setViewportSize({width:1366,height:900});
 await page.getByText('Review all extracted facts and correct values',{exact:true}).click();
 const input=page.locator('input[data-field-path="invoice_date"]');await input.fill('2026-10-02');
 await input.locator('xpath=..').getByLabel('Correction source page').selectOption('2');
 const reason='Page 2 supplier clarification explicitly states 2 October 2026 and ISO date 2026-10-02.';
 await page.getByText('Match supplier, budget and business references',{exact:true}).click();
 await expect(page.getByLabel('Submission date',{exact:true})).toBeEditable();
 await page.getByLabel('Submission date',{exact:true}).fill('2026-10-05');
 await page.getByLabel('Verification / correction reason').fill(reason);await page.getByRole('checkbox').check();
 const completed=page.waitForResponse(r=>r.url().endsWith('/commit')&&r.request().method()==='POST');
 await page.getByRole('button',{name:'Verify facts and evaluate',exact:true}).click();
 const response=await completed;expect(response.status()).toBe(201);const created=await response.json();
 await expect(page).toHaveURL('/cases/'+created.id);
 await expect(page.locator('.result-summary h2')).toHaveText(/On hold|Needs review/,{timeout:45000});
 const record=await get(page,'transactions/'+created.id);expect(record.eligible).toBe(false);
 expect(record.versions.at(-1).payload.invoice_date).toBe('2026-10-02');
 expect(record.versions.at(-1).payload.submission_date).toBe('2026-10-05');
 const evaluation=await get(page,'evaluations/'+record.latest_evaluation_id);
 expect(evaluation.rules.find((r:{rule_id:string})=>r.rule_id==='VAL-002').status).toBe('PASS');
 expect(evaluation.rules.find((r:{rule_id:string})=>r.rule_id==='APR-001').status).toBe('FAIL');
 const sources=await get(page,'transactions/'+created.id+'/sources');expect(sources.documents.some((d:{verified:boolean})=>d.verified)).toBe(true);
 const after=await get(page,'documents/'+sourceId);
 expect(after.extraction_runs).toEqual(original.extraction_runs);expect(after.observations).toEqual(original.observations);
 expect(after.draft.candidate.invoice_date).toBeNull();
 await screenshotBoth(page,'new-case');await page.reload();await expect(page.locator('.result-summary h2')).toHaveText(/On hold|Needs review/);
 expect((await get(page,'transactions/'+created.id)).version).toBe(record.version);
 expect((await get(page,'transactions/'+created.id)).latest_evaluation_id).toBe(record.latest_evaluation_id);
 expect((await page.request.get('/api/admin/catalog')).status()).toBe(403);
 save('presentation-source.json',{sourceUrl,caseUrl:'/cases/'+created.id,intakeSeconds,reason,sourceId,record,sources,original,after});
});

test('isolated fictional hotel policy edits dates amount and audit without changing established records', async({page})=>{
 test.setTimeout(120000);await page.goto('/login');await identity(page,'Synthetic finance reviewer');
 const before=await get(page,'admin/catalog');
 const baseline=catalogHash(before.items);
 const fixture=JSON.parse(readFileSync(resolve('../../data/synthetic/reference/expense_policies.json'),'utf8')).records[0];
 delete fixture.tenant_id;delete fixture.legal_entity_id;
 const identifier=randomUUID();fixture.id=identifier;fixture.version=1;
 fixture.policy_code='DEMO-PANEL-HOTEL-'+identifier.slice(0,8);fixture.label='DEMO / FICTIONAL PANEL HOTEL';
 fixture.dimensions.location='PANEL-CITY-'+identifier.slice(0,8);fixture.effective_from='2026-11-01';
 const staged=await post(page,'reference-imports',{source_system:'SYNTHETIC_PANEL',source_version:'v1',reason:'Prepare an isolated fictional panel policy; retain existing policy history.',records:[{kind:'expense_policies',payload:fixture}]});
 const validation=await post(page,'reference-imports/'+staged.id+'/validate',{});expect(validation.state).toBe('VALID');
 await post(page,'reference-imports/'+staged.id+'/activate',{reason:'Activate isolated fictional rehearsal policy with distinct location.'});
 await page.goto('/login');await page.getByRole('button',{name:'Policy administrator Policies and allowance versions',exact:true}).click();
 await page.getByRole('button',{name:'Allowances & receipts',exact:true}).click();
 await expect(page.getByLabel('Configuration record').locator('option[value="'+identifier+'"]')).toContainText(fixture.policy_code);
 await page.getByLabel('Configuration record').selectOption(identifier);
 await expect(page.getByText('Fictional sample configuration.',{exact:false})).toBeVisible();
 await page.getByLabel('New allowance',{exact:true}).fill('9000.00');
 await page.getByLabel('Effective from',{exact:true}).fill('2026-11-15');
 const reason='Fictional panel hotel allowance rises from INR 8000 to INR 9000 per eligible night, effective 15 November 2026.';
 await page.getByLabel('Configuration change reason').fill(reason);
 await page.getByRole('button',{name:'Validate and save draft',exact:true}).click();
 await expect(page.getByRole('button',{name:'Activate new version',exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Activate new version',exact:true}).click();
 await expect(page.getByText('New configuration version activated. Earlier versions and evaluations remain available.',{exact:true})).toBeVisible();
 await page.getByText('Policy versions and audit metadata',{exact:true}).click();
 await expect(page.locator('.policy-history')).toContainText('Version 2 · effective 2026-11-15');
 await expect(page.locator('.policy-history')).toContainText('INR 8000.00');await expect(page.locator('.policy-history')).toContainText('INR 9000.00');
 await expect(page.locator('.policy-history')).toContainText(reason);
 const versions=await get(page,'admin/records/'+identifier+'/versions');expect(versions.items.map((v:{version:number})=>v.version)).toEqual([1,2]);
 expect(versions.items[1].change.reason).toBe(reason);
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
 await screenshotBoth(page,'policy-version');await page.reload();await page.getByLabel('Configuration record').selectOption(identifier);
 await expect(page.getByLabel('New allowance',{exact:true})).toHaveValue('9000.00');
 await page.emulateMedia({reducedMotion:'reduce'});await page.getByLabel('New allowance',{exact:true}).focus();await expect(page.getByLabel('New allowance',{exact:true})).toBeFocused();
 await identity(page,'Synthetic finance reviewer');
 const current=await get(page,'admin/catalog');const old=current.items.filter((v:{id:string})=>v.id!==identifier);
 expect(catalogHash(old)).toBe(baseline);
 save('presentation-policy.json',{id:identifier,policyCode:fixture.policy_code,reason,versions,existingCatalogPreserved:true});
});

test('computed outcome citations history role boundaries and temporary list failure rehearse safely',async({page})=>{
 test.setTimeout(120000);await page.goto('/login');await identity(page,'Hackathon finance reviewer');
 const scenarios=await get(page,'development/scenarios');expect(scenarios.ready).toBe(true);
 const snapshots=[];
 for(const [key,label] of [['vlm-pass','Ready for processing'],['paid-duplicate','On hold'],['employee-allowance','Needs review']]){
  const sample=scenarios.items.find((s:{key:string})=>s.key===key);await page.goto(sample.case_url);
  await expect(page.locator('.result-summary h2')).toHaveText(label);await expect(page.getByRole('heading',{name:'Source documents',exact:true})).toBeVisible();
  const record=await get(page,'transactions/'+sample.case_url.split('/').at(-1));
  const report=await get(page,'evaluations/'+record.latest_evaluation_id+'/report');
  await screenshotBoth(page,key);await page.reload();
  expect(await get(page,'evaluations/'+record.latest_evaluation_id+'/report')).toEqual(report);
  snapshots.push({key,decision:record.decision,eligible:record.eligible});
 }
 await identity(page,'Synthetic finance workspace');
 await page.route('**/api/documents',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'Temporary local connection interruption. Reload to retry.'}})}));
 await page.goto('/documents');await expect(page.locator('.error[role="alert"]')).toContainText('Temporary local connection interruption');
 await screenshotBoth(page,'list-error');await page.unroute('**/api/documents');await page.reload();
 await expect(page.locator('.error[role="alert"]')).toHaveCount(0);await expect(page.getByRole('heading',{name:'Recent documents',exact:true})).toBeVisible();
 save('presentation-outcomes.json',{snapshots,temporaryReadFailureRecovered:true,mutationsInjected:false});
});
