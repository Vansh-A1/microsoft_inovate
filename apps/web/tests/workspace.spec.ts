import {caseDetails} from './support/disclosure';
import { test,expect } from '@playwright/test';
const vendor='30000000-0000-4000-8000-000000000001';
const employee='30000000-0000-4000-8000-000000000005';
const duplicate='30000000-0000-4000-8000-000000000002';
const expense='30000000-0000-4000-8000-000000000008';
test('overview shows actual persisted cases and has no browser token',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/');await expect(page.getByRole('heading',{name:'Your finance workspace'})).toBeVisible();
 // The overview is bounded and ordered by recency; compare an actual returned record by UUID.
 const latest=(await (await page.request.get('/api/transactions?limit=25')).json()).items[0];
 const facts=latest.versions.at(-1).payload;
 await expect(page.locator('a[href="/cases/'+latest.id+'"]').filter({hasText:facts.invoice_number||facts.claim_number})).toBeVisible();
 const currentRow=page.locator('tbody tr').filter({has:page.locator('a[href="/cases/'+latest.id+'"]')});
 await expect(currentRow.locator('.badge')).toHaveText(latest.decision==='PASS'&&!latest.eligible?'Needs review':{PASS:'Ready for processing',REVIEW:'Needs review',HOLD:'On hold'}[latest.decision as 'PASS'|'REVIEW'|'HOLD']||'Awaiting screening');
 await expect(page.getByText('NOT_CONFIGURED',{exact:false})).toHaveCount(0);
 await page.screenshot({path:'../../output/playwright/overview.png',fullPage:true});
 const browserStorage=await page.evaluate(()=>({...localStorage,...sessionStorage}));expect(Object.keys(browserStorage)).toHaveLength(0);expect(errors).toEqual([]);
});
for(const [id,outcome] of [[vendor,'PASS'],[employee,'PASS'],[duplicate,'HOLD'],[expense,'REVIEW']]){
 test(`persisted case ${outcome} ${id.slice(-3)} resolves evidence and report`,async({page})=>{
  await page.goto('/cases/'+id);await caseDetails(page);await page.getByText('View detailed checks',{exact:true}).click();await expect(page.getByRole('heading',{name:'Rule findings'})).toBeVisible();
  const current=await (await page.request.get('/api/transactions/'+id)).json();
  const retained=await (await page.request.get('/api/evaluations/'+current.latest_evaluation_id)).json();
  expect(retained.decision).toBe(outcome);
  const requiresFresh=retained.evaluation_status!=='CURRENT'||outcome==='PASS'&&!current.eligible;
  await expect(page.locator('.result-summary h2')).toHaveText(requiresFresh&&outcome!=='HOLD'?'Needs review':{PASS:'Ready for processing',HOLD:'On hold',REVIEW:'Needs review'}[outcome as 'PASS'|'HOLD'|'REVIEW']);
  if(requiresFresh)await expect(page.getByText('A fresh screening is required. Evaluate the current version before processing.')).toBeVisible();
  await expect(page.locator('.rule')).toHaveCount(20);
  await page.locator('.rule').first().getByText('Observed, expected & evidence').click();
  await page.locator('.rule').first().getByRole('button',{name:/TRANSACTION/}).first().click();
  await expect(page.getByRole('heading',{name:'Resolved evidence'})).toBeVisible();
  await expect(page.getByText('no source image or bounding box',{exact:false})).toBeVisible();
  if(id===vendor)await page.screenshot({path:'../../output/playwright/vendor-case.png',fullPage:true});
  await page.getByRole('link',{name:'View report'}).click();
  await expect(page.getByRole('heading',{name:'Screening report',exact:true})).toBeVisible();
  await expect(page.frameLocator('iframe').getByRole('heading',{name:new RegExp(outcome+' — Synthetic')})).toBeVisible();
  await expect(page.getByText('Report downloads require explicit export permission.')).toBeVisible();
  if(id===employee)await page.screenshot({path:'../../output/playwright/employee-report.png',fullPage:true});
 });
}
for(const choice of ['vendor','employee']){
 test(`create ${choice} from actual API and await durable result`,async({page})=>{
  await page.goto('/create');await page.getByLabel('Transaction branch').selectOption(choice);
  const field=page.getByLabel(choice==='vendor'?'Invoice number':'Claim number',{exact:true});await expect(field).not.toHaveValue('');
  const number='UI-TEST-'+choice+'-'+Date.now();await field.fill(number);
  await page.getByRole('button',{name:'Create and evaluate'}).click();
  await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);
  await expect(page.getByRole('heading',{name:number,exact:true})).toBeVisible();
  await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:25000});
  await caseDetails(page);await page.getByText('View detailed checks',{exact:true}).click();await expect(page.locator('.rule').filter({hasText:'APR-001'}).getByText('FAIL',{exact:true})).toBeVisible();
  await page.reload();await expect(page.getByRole('heading',{name:number,exact:true})).toBeVisible();
 });
}
test('exception filters, empty state and mobile layout',async({page})=>{
 await page.goto('/queue');await page.getByRole('combobox',{name:'Decision',exact:true}).selectOption('HOLD');await page.getByLabel('Reason',{exact:true}).selectOption('APR-001');
 await expect(page.locator('tbody tr').first()).toBeVisible();
 await page.goto('/queue?reason=NO-SUCH-RULE');await expect(page.getByRole('heading',{name:'No open exceptions match'})).toBeVisible();
 await page.setViewportSize({width:390,height:844});await page.goto('/create');await expect(page.getByRole('heading',{name:'Create & import',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/mobile-create.png',fullPage:true});
});
test('CSV import preserves invalid row and commits real valid row',async({page})=>{
 await page.goto('/create');await expect(page.getByLabel('Invoice number')).not.toHaveValue('');
 const example=JSON.parse(await page.getByLabel('Canonical transaction JSON').inputValue());example.invoice_number='UI-IMPORT-'+Date.now();
 const escape=(s:string)=>'"'+s.replaceAll('"','""')+'"';const content='transaction_json\n'+escape(JSON.stringify(example))+'\n'+escape('{bad json')+'\n';
 await page.getByLabel('Synthetic import file').setInputFiles({name:'ui-test.csv',mimeType:'text/csv',buffer:Buffer.from(content)});
 await page.getByRole('button',{name:'Preview rows'}).click();await expect(page.getByText('1 valid · 1 invalid · PREVIEWED')).toBeVisible();
 await page.getByRole('button',{name:'Commit valid rows'}).click();await expect(page.getByText('1 valid · 1 invalid · COMMITTED')).toBeVisible();
 await expect(page.getByRole('link',{name:'Open imported case →'})).toBeVisible();await expect(page.getByText('Retained with errors')).toBeVisible();
});
test('loading and API error states remain visible and actionable',async({page})=>{
 await page.route('**/api/transactions?*',async route=>{await new Promise(resolve=>setTimeout(resolve,1200));await route.continue()});
 await page.goto('/transactions');await expect(page.getByRole('status')).toHaveText('Loading persisted records…');await expect(page.locator('tbody tr').first()).toBeVisible();
 await page.unroute('**/api/transactions?*');await page.route('**/api/transactions?*',route=>route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'API connection unavailable. Start the API and try again.'}})}));
 await page.reload();await expect(page.locator('.error[role=alert]')).toContainText('API connection unavailable');
 await page.unroute('**/api/transactions?*');await page.getByRole('button',{name:'Try loading again',exact:true}).click();
 await expect(page.locator('tbody tr').first()).toBeVisible();await expect(page.locator('.error[role=alert]')).toHaveCount(0);
});
test('proxy rejects a cross-origin mutation',async({request})=>{
 const result=await request.post('/api/transactions',{headers:{Origin:'https://untrusted.example','Idempotency-Key':'blocked-origin'},data:{branch:'VENDOR_INVOICE'}});
 expect(result.status()).toBe(403);expect((await result.json()).error.message).toContain('Same-origin');
});
