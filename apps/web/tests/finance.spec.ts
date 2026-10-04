import {selectLocalIdentity} from './support/identity';
import {test,expect,type APIRequestContext,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {randomUUID} from 'node:crypto';
const source=(kind:string)=>JSON.parse(readFileSync(resolve('../../data/synthetic/reference/'+kind+'.json'),'utf8')).records;
const caseInput=(path:string)=>JSON.parse(readFileSync(resolve('../../data/golden_cases/'+path+'.json'),'utf8')).transaction;
const origin='http://127.0.0.1:3000';
async function post(request:APIRequestContext,path:string,data:unknown){const r=await request.post('/api/'+path,{headers:{Origin:origin,'Idempotency-Key':randomUUID()},data});expect(r.ok(),await r.text()).toBeTruthy();return r.json();}
async function identity(request:APIRequestContext,label:string){return post(request,'development/session',{label});}
async function stage(request:APIRequestContext,records:unknown[]){const r=await post(request,'reference-imports',{source_system:'SYNTHETIC_BROWSER',source_version:randomUUID(),records,reason:'Explicit synthetic browser acceptance facts'});const checked=await post(request,'reference-imports/'+r.id+'/validate',{});expect(checked.state,JSON.stringify(checked.validation)).toBe('VALID');await post(request,'reference-imports/'+r.id+'/activate',{reason:'Activate validated fictional browser facts'});}
async function canonical(request:APIRequestContext,branch='vendor'){const r=await request.get('/api/development/templates/'+branch);expect(r.ok(),await r.text()).toBeTruthy();return r.json();}
async function vendor(request:APIRequestContext){
 const p=await canonical(request);p.invoice_number='SYNTHETIC-P3-'+randomUUID();const budget=structuredClone(source('budgets')[0]),po=structuredClone(source('purchase_orders')[0]),line=structuredClone(po.lines[0]),grn=structuredClone(source('goods_receipts')[0].lines[0]),doc=structuredClone(source('documents').find((d:{id:string})=>d.id===p.source_document_id));
 budget.id=randomUUID();budget.ledger=[{id:randomUUID(),entry_type:'ALLOCATION',amount:'1000000.00',currency:'INR'}];po.id=randomUUID();po.budget_id=budget.id;po.approved_ceiling_amount='1000000.00';delete po.lines;line.id=randomUUID();line.po_id=po.id;line.ordered_quantity='100';grn.id=randomUUID();grn.po_id=po.id;grn.po_line_id=line.id;grn.accepted_quantity='100';grn.returned_quantity='0';grn.reversed_quantity='0';doc.id=randomUUID();doc.facts.invoice_number=p.invoice_number;
 p.budget_id=budget.id;p.po_id=po.id;p.lines[0].po_line_id=line.id;p.lines[0].grn_line_id=grn.id;p.source_document_id=doc.id;
 await stage(request,[{kind:'budgets',payload:budget},{kind:'purchase_orders',payload:po},{kind:'po_lines',payload:line},{kind:'grn_lines',payload:grn},{kind:'documents',payload:doc}]);return p;
}
async function expense(request:APIRequestContext,name='employee/daily_meals'){
 const p=await canonical(request,'employee');const raw=caseInput(name);for(const key of Object.keys(p))if(key in raw)p[key]=raw[key];
 const items=raw.items.map((i:Record<string,unknown>)=>{const out:Record<string,unknown>={};for(const k of ['id','source_document_id','category','currency','expense_date','local_timezone','claimed_amount','receipt_total_amount','eligible_nights','company_paid_amount','applied_advance_amount'])out[k]=i[k];return out;});p.items=items;p.claim_number='SYNTHETIC-CLAIM-'+randomUUID();const did=p.items[0].source_document_id;const doc=structuredClone(source('documents').find((d:{id:string})=>d.id===did));doc.id=randomUUID();p.source_document_id=doc.id;for(const i of p.items)i.source_document_id=doc.id;
 // Separate fictional employee/policy dimensions keep repeated live runs from consuming each other's daily limits.
 const employee=structuredClone(source('employees').find((e:{id:string})=>e.id===p.employee_id));employee.id=randomUUID();employee.employee_number='SYNTHETIC-BROWSER-'+randomUUID();employee.grade='SYNTHETIC-'+randomUUID();p.employee_id=employee.id;
 const policy=structuredClone(source('expense_policies').find((e:{id:string})=>e.id===p.expense_policy_id));policy.id=randomUUID();policy.dimensions.grade=employee.grade;if(name==='employee/daily_meals')policy.allowance_amount='500.00';p.expense_policy_id=policy.id;
 await stage(request,[{kind:'employees',payload:employee},{kind:'expense_policies',payload:policy},{kind:'documents',payload:doc}]);return p;
}
async function create(request:APIRequestContext,p:unknown){const t=await post(request,'transactions',p);await post(request,'transactions/'+t.id+'/evaluate',{expected_version:1,reason:'Compute real synthetic browser screening'});await complete(request,t.id);return t.id as string;}
async function complete(request:APIRequestContext,id:string){await expect.poll(async()=>((await request.get('/api/transactions/'+id)).json()).then(d=>d.processing_state),{timeout:30000}).toBe('COMPLETED');return (await request.get('/api/transactions/'+id)).json();}
async function approvals(request:APIRequestContext,id:string){const r=await post(request,'transactions/'+id+'/approval-requests',{expected_version:1,reason:'Obtain ordered synthetic approval authority'});for(const step of r.requirements){await identity(request,step.role==='MANAGER'?'Synthetic manager':'Synthetic department head');await post(request,'approval-requests/'+r.id+'/actions',{expected_version:1,sequence:step.sequence,action:'APPROVED',reason:'Authenticated master authority reviewed current facts'});}await identity(request,'Synthetic finance reviewer');await complete(request,id);}
async function result(request:APIRequestContext,id:string){const t=await complete(request,id);return (await request.get('/api/evaluations/'+t.latest_evaluation_id)).json();}
async function reason(page:Page){await page.getByLabel('Control action reason').fill('Reviewed actual scoped evidence and current version');}

test('matching, budget and ordered approval actions work with server identities',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));const p=await vendor(page.request);const id=await create(page.request,p);await page.goto('/cases/'+id);
 await expect(page.getByRole('heading',{name:'Commercial matching',exact:true})).toBeVisible();await expect(page.locator('.budget-summary')).toContainText('1000000');await reason(page);await page.getByRole('button',{name:'Request current approvals'}).click();await expect(page.getByText('Request for v1',{exact:false})).toBeVisible();
 await selectLocalIdentity(page,'Synthetic manager');await reason(page);await page.getByRole('button',{name:'Approve step 1 · MANAGER'}).click();await expect(page.locator('.finance-controls table').filter({hasText:'Required role'})).toContainText('APPROVED');
 await selectLocalIdentity(page,'Synthetic department head');await reason(page);await page.getByRole('button',{name:'Approve step 2 · DEPARTMENT_HEAD'}).click();await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing',{timeout:30000});
 await expect(page.locator('.rule')).toHaveCount(28);await page.screenshot({path:'../../output/playwright/phase3-matching-approval.png',fullPage:true});expect(errors).toEqual([]);
});

test('duplicate field comparisons and explicit DISTINCT resolution are version bound',async({page})=>{
 const p=await vendor(page.request);const first=await create(page.request,p);await approvals(page.request,first);expect((await result(page.request,first)).decision).toBe('PASS');
 const second=await create(page.request,p);await approvals(page.request,second);expect((await result(page.request,second)).decision).toBe('HOLD');await page.goto('/cases/'+second);await expect(page.getByRole('heading',{name:'Current facts',exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'Compared facts',exact:true})).toBeVisible();await page.getByText('Signals, field differences and lifecycle').click();await expect(page.locator('.comparison')).toContainText('active_obligation');await reason(page);await page.getByRole('button',{name:'DISTINCT',exact:true}).click();await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing',{timeout:30000});await page.screenshot({path:'../../output/playwright/phase3-duplicate.png',fullPage:true});
});

test('receipt authorization creates actual source-bound share and capacity result',async({page})=>{
 const p=await expense(page.request,'employee/shared_within');const id=await create(page.request,p);await approvals(page.request,id);const t=(await page.request.get('/api/transactions/'+id));const item=(await t.json()).versions.at(-1).payload.items[0];await page.goto('/cases/'+id);await page.getByText('Authorize a receipt share',{exact:true}).click();await page.getByLabel('Expense item for receipt share').selectOption(item.id);await page.getByLabel('Authorized share amount').fill(item.claimed_amount);await page.getByLabel('Receipt share quantity').fill('1');await reason(page);await page.getByRole('button',{name:'Authorize share',exact:true}).click();await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing',{timeout:30000});await expect(page.locator('.finance-controls table').filter({hasText:'Authorized share'})).toContainText('600');await page.screenshot({path:'../../output/playwright/phase3-receipt-share.png',fullPage:true});
});

test('waiver action preserves original finding and records explicit disposition',async({page})=>{
 const p=await expense(page.request);const id=await create(page.request,p);await approvals(page.request,id);expect((await result(page.request,id)).decision).toBe('REVIEW');await page.goto('/cases/'+id);await reason(page);await page.getByRole('button',{name:'Request configured waiver'}).click();await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing',{timeout:30000});await expect(page.locator('.rule').filter({hasText:'EXP-003'})).toContainText('FAIL');await expect(page.locator('.finance-controls')).toContainText('Original findings remain visible.');await page.screenshot({path:'../../output/playwright/phase3-waiver.png',fullPage:true});
});

test('reference stage validate activate and unauthorized action errors are visible',async({page})=>{
 await page.goto('/reference-imports');const tag='SYNTHETIC-UI-'+randomUUID();await page.getByLabel('Source system',{exact:true}).fill(tag);await page.getByLabel('Import / activation reason').fill('Activate explicit fictional browser source');await page.getByLabel('Reference records JSON').fill(JSON.stringify([{kind:'cost_centers',payload:{id:randomUUID(),version:1,name:tag,department:'DEMO-ENGINEERING'}}]));await page.getByRole('button',{name:'Stage import'}).click();const batch=page.locator('.reference-batch').filter({hasText:tag});await expect(batch).toContainText('STAGED');await batch.getByRole('button',{name:'Validate batch'}).click();await expect(batch).toContainText('VALID');await batch.getByRole('button',{name:'Activate validated batch'}).click();await expect(batch).toContainText('ACTIVE');await page.screenshot({path:'../../output/playwright/phase3-reference.png',fullPage:true});
 await selectLocalIdentity(page,'Synthetic employee');await expect(page.locator('.error[role=alert]')).toContainText('cannot open');expect((await page.request.get('/api/reference-imports')).status()).toBe(403);
 const forged=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Synthetic employee',roles:['CFO']}});expect(forged.status()).toBe(422);
});

test('a delayed initial reference response cannot erase the newly staged batch',async({page})=>{
 let first=true;let captured!:()=>void;let release!:()=>void;let delivered!:()=>void;
 const snapshot=new Promise<void>(resolve=>{captured=resolve});const held=new Promise<void>(resolve=>{release=resolve});const completed=new Promise<void>(resolve=>{delivered=resolve});
 await page.route('**/api/reference-imports',async route=>{
  if(route.request().method()==='GET'&&first){first=false;const response=await route.fetch();captured();await held;await route.fulfill({response});delivered();}
  else await route.continue();
 });
 try{
  await page.goto('/reference-imports');await snapshot;
  const tag='SYNTHETIC-DELAY-'+randomUUID();await page.getByLabel('Source system',{exact:true}).fill(tag);
  await page.getByLabel('Import / activation reason').fill('Verify stale response protection with a real scoped import');
  await page.getByLabel('Reference records JSON').fill(JSON.stringify([{kind:'cost_centers',payload:{id:randomUUID(),version:1,name:tag,department:'DEMO-ENGINEERING'}}]));
  await page.getByRole('button',{name:'Stage import',exact:true}).click();
  const batch=page.locator('.reference-batch').filter({hasText:tag});await expect(batch).toContainText('STAGED');
  release();await completed;await batch.getByRole('button',{name:'Validate batch',exact:true}).click();await expect(batch).toContainText('VALID');
 }finally{release();}
});

test('finance control loading error empty and mobile views remain usable',async({page})=>{
 const id='30000000-0000-4000-8000-000000000004';await page.route('**/api/transactions/'+id+'/finance-controls',async route=>{await new Promise(r=>setTimeout(r,900));await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'Finance controls temporarily unavailable'}})});});await page.goto('/cases/'+id);await expect(page.getByText('Loading finance controls…')).toBeVisible();await expect(page.locator('.finance-controls .error[role=alert]')).toContainText('Finance controls temporarily unavailable');await page.unroute('**/api/transactions/'+id+'/finance-controls');await page.reload();await expect(page.getByText('No Phase-3 budget result for this version.')).toBeVisible();await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/phase3-controls-mobile.png',fullPage:true});
});

test('actual uploaded receipt pages can be compared together with page-level evidence',async({page})=>{
 async function documentClaim(){
  await page.goto('/documents');await page.getByLabel('Document purpose').selectOption('EMPLOYEE_RECEIPT');await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/receipt_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});const did=page.url().split('/').at(-1)!;
  await page.getByText('Canonical draft and reference mapping',{exact:true}).click();const field=page.getByLabel('Document canonical JSON');await expect(field).not.toHaveValue('');const facts=JSON.parse(await field.inputValue());facts.claim_number='SYNTHETIC-DOCUMENT-'+randomUUID();await field.fill(JSON.stringify(facts));await page.getByLabel('Verification / correction reason').fill('Reviewed actual synthetic receipt and mapped claimant');await page.getByText('I reviewed the source pages and confirm the observable facts.').click();await page.getByRole('button',{name:'Verify facts and evaluate'}).click();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);const tid=page.url().split('/').at(-1)!;await complete(page.request,tid);return {did,tid};
 }
 const first=await documentClaim(),second=await documentClaim();await page.reload();const comparison=page.locator('.comparison').filter({has:page.getByRole('button',{name:'View compared source '+first.did.slice(-8),exact:true})});await expect(comparison).toHaveCount(1);await comparison.getByRole('button',{name:'View source '+second.did.slice(-8),exact:true}).click();await comparison.getByRole('button',{name:'View compared source '+first.did.slice(-8),exact:true}).click();await expect(page.locator('.comparison-source img')).toHaveCount(2);await expect(page.locator('.comparison-source')).toContainText(['Page-level evidence','Page-level evidence']);await page.locator('.comparison-source').first().scrollIntoViewIfNeeded();await page.screenshot({path:'../../output/playwright/phase3-actual-source-comparison.png'});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.locator('.comparison-source').first().scrollIntoViewIfNeeded();await page.screenshot({path:'../../output/playwright/phase3-source-comparison-mobile.png'});
});
