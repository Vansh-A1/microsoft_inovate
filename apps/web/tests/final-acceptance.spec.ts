import {test,expect,type Page} from '@playwright/test';

// Read retained fictional history only. No uploads, evaluations, approvals,
// configuration activation or inference calls; local session selection is the
// only POST. Ordinary CI need not have the opt-in local judge dataset.
test.skip(process.env.AP_RUN_FINAL_ACCEPTANCE!=='1','Existing local fictional judge walkthrough required');
const origin='http://127.0.0.1:3000';
async function get(page:Page,path:string){
 const response=await page.request.get('/api/'+path);expect(response.status()).toBe(200);return response.json();
}
async function walkthrough(page:Page){
 await page.goto('/');
 const response=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Hackathon finance reviewer'}});
 expect(response.status()).toBe(200);await page.reload();
 const data=await get(page,'development/scenarios');expect(data.ready).toBe(true);expect(data.items).toHaveLength(8);
 return data.items as {key:string;case_url:string;document_url:string|null;report_url:string}[];
}
async function current(page:Page,url:string){
 const record=await get(page,'transactions/'+url.split('/').at(-1));
 const evaluation=await get(page,'evaluations/'+record.latest_evaluation_id);
 expect(evaluation.evaluation_status).toBe('CURRENT');expect(evaluation.rules).toHaveLength(28);
 const retainedReport=await get(page,'evaluations/'+record.latest_evaluation_id+'/report');
 return {record,evaluation,retainedReport};
}

test('current clean source-confirmed invoice displays readiness only with finance prerequisites',async({page})=>{
 const scenarios=await walkthrough(page);const sample=scenarios.find(s=>s.key==='vlm-pass')!;
 const {record,evaluation,retainedReport}=await current(page,sample.case_url);
 expect(record.decision).toBe('PASS');expect(record.eligible).toBe(true);
 for(const id of ['VAL-003','VEN-001','VEN-002','DOC-001','PO-004','GRN-001','BUD-001','APR-001']){
  expect(evaluation.rules.find((r:{rule_id:string})=>r.rule_id===id).status).toBe('PASS');
 }
 const sources=await get(page,'transactions/'+record.id+'/sources');
 expect(sources.documents.some((d:{verified:boolean})=>d.verified)).toBe(true);
 await page.goto(sample.case_url);await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing');
 await expect(page.getByLabel('Screening result')).toContainText('The current facts satisfy the applicable checks. Payment remains a separate process.');
 await expect(page.getByRole('heading',{name:'Rule findings'})).not.toBeVisible();
 await expect(page.getByRole('heading',{name:'Audit timeline',exact:true})).toBeVisible();
 await page.screenshot({path:'../../output/playwright/acceptance-ready-laptop.png',fullPage:true});
 await page.getByLabel('Screening result').screenshot({path:'../../output/playwright/acceptance-ready-result-laptop.png'});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/acceptance-ready-phone.png',fullPage:true});
 await page.getByLabel('Screening result').screenshot({path:'../../output/playwright/acceptance-ready-result-phone.png'});
 expect(await get(page,'evaluations/'+record.latest_evaluation_id+'/report')).toEqual(retainedReport);
 const after=await current(page,sample.case_url);expect(after.record.eligible).toBe(record.eligible);expect(after.evaluation.decision).toBe(evaluation.decision);expect(after.evaluation.transaction_version).toBe(evaluation.transaction_version);
});

test('duplicate allowance and delivery exceptions match actual pinned evidence and next actions',async({page})=>{
 const scenarios=await walkthrough(page);
 for(const name of ['paid-duplicate','employee-allowance','partial-delivery']){
  const sample=scenarios.find(s=>s.key===name)!;const {record,evaluation,retainedReport}=await current(page,sample.case_url);
  expect(record.eligible).toBe(false);await page.goto(sample.case_url);
  await expect(page.locator('.result-summary h2')).toHaveText(name==='employee-allowance'?'Needs review':'On hold');
  const summary=page.getByLabel('Screening result');await expect(summary).toContainText('What to do next');
  const id=name==='paid-duplicate'?'DUP-002':name==='employee-allowance'?'EXP-003':'GRN-001';
  const finding=evaluation.rules.find((r:{rule_id:string})=>r.rule_id===id);expect(finding.status).toBe('FAIL');
  const kind=name==='paid-duplicate'?'HISTORICAL_AGGREGATE':name==='employee-allowance'?'POLICY_CLAUSE':'GRN_LINE';
  const evidence=finding.evidence.find((e:{reference:{kind:string}})=>e.reference.kind===kind);
  const resolved=await get(page,'evidence/'+evidence.id);expect(resolved.reference.record_version).toBe(evidence.reference.record_version);
  if(name==='paid-duplicate'){
   const canonical=record.versions.at(-1).payload;
   for(const field of ['vendor_id','invoice_number','invoice_date','total_amount','currency'])expect(resolved.source[field]).toBe(canonical[field]);
   expect(resolved.source.settlement_status).toBe('PAID');
   await expect(summary).toContainText(finding.reason);
   await expect(summary).toContainText('Inspect the possible duplicate and record its disposition.');
  }else if(name==='employee-allowance'){
   expect(finding.observed.daily_limit).toBe(resolved.source.allowance_amount);
   expect(finding.observed.aggregate_amount).toBe('1800.00');expect(finding.observed.daily_limit).toBe('1500.00');
   const canonical=record.versions.at(-1).payload;
   expect(resolved.source.id).toBe(canonical.expense_policy_id);expect(resolved.source.synthetic).toBe(true);
   for(const e of finding.evidence.filter((e:{reference:{kind:string}})=>e.reference.kind==='HISTORICAL_AGGREGATE')){
    const previous=await get(page,'evidence/'+e.id);expect(previous.source.claimed_amount).toBe('600.00');
    expect(previous.source.employee_id).toBe(canonical.employee_id);expect(previous.source.expense_date).toBe(finding.observed.local_date);
   }
   expect(canonical.requested_amount).toBe('600.00');await expect(summary).toContainText(finding.reason);
   await expect(summary).toContainText('Review the allowance calculation and record an authorized resolution.');
  }else{
   const line=finding.observed[0];expect(line.requested_quantity).toBe('70');expect(line.eligible_new_quantity).toBe('50.0000');expect(line.quantity_shortfall).toBe('20.0000');
   expect(resolved.source.accepted_quantity).toBe(line.accepted_quantity);
   await expect(summary).toContainText(`Goods receipt covers ${line.eligible_new_quantity} units; this line bills ${line.requested_quantity}. Verify the remaining ${line.quantity_shortfall} units or correct the invoice.`);
   await expect(summary).toContainText('Verify goods receipt or correct the billed quantity.');
  }
  await page.getByText('View detailed checks',{exact:true}).click();
  const rule=page.locator('article.rule').filter({has:page.locator('.rule-head strong',{hasText:new RegExp('^'+id+'$')})});
  await rule.getByText('Observed, expected & evidence',{exact:true}).click();
  await rule.getByRole('button',{name:new RegExp('^'+kind)}).first().click();
  await expect(page.getByLabel('Resolved evidence')).toBeVisible();
  await expect(page.getByLabel('Resolved evidence')).toContainText(resolved.reference.record_id);
  await page.screenshot({path:'../../output/playwright/acceptance-'+name+'-laptop.png',fullPage:true});
  await summary.screenshot({path:'../../output/playwright/acceptance-'+name+'-result-laptop.png'});
  expect(await get(page,'evaluations/'+record.latest_evaluation_id+'/report')).toEqual(retainedReport);
  const after=await current(page,sample.case_url);expect(after.record.eligible).toBe(record.eligible);expect(after.evaluation.decision).toBe(evaluation.decision);expect(after.evaluation.transaction_version).toBe(evaluation.transaction_version);
 }
});

test('retained future allowance form and audit history load without policy activation',async({page})=>{
 await page.goto('/login');await page.getByRole('button',{name:'Policy administrator Policies and allowance versions',exact:true}).click();
 await expect(page).toHaveURL(/\/admin$/);await expect(page.getByRole('heading',{name:'Business configuration'})).toBeVisible();
 const catalog=await get(page,'admin/catalog');const hotel=catalog.items.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL');
 expect(hotel.payload.allowance_amount).toBe('9000.00');expect(hotel.payload.effective_from).toBe('2026-11-01');
 const versions=await get(page,'admin/records/'+hotel.id+'/versions');const latest=versions.items.at(-1);
 expect(versions.items.some((v:{payload:{allowance_amount:string}})=>v.payload.allowance_amount==='8000.00')).toBe(true);
 expect(latest.version).toBe(hotel.version);expect(latest.payload.allowance_amount).toBe('9000.00');
 expect(latest.change.actor_id).toBeTruthy();expect(latest.change.reason).toContain('Future synthetic hotel allowance release demonstration');
 await page.getByLabel('Configuration record').selectOption(hotel.id);
 await expect(page.getByLabel('New allowance',{exact:true})).toHaveValue('9000.00');
 await expect(page.getByLabel('Effective from',{exact:true})).toHaveValue('2026-11-01');
 await expect(page.getByText('Fictional sample configuration.',{exact:false})).toBeVisible();
 await expect(page.getByLabel('Configuration change reason')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/acceptance-policy-form-laptop.png'});
 await page.getByText('Policy versions and audit metadata',{exact:true}).click();
 await expect(page.getByText(`Version ${hotel.version} · effective`,{exact:false})).toBeVisible();
 await expect(page.getByText(latest.change.reason,{exact:false}).first()).toBeVisible();
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
 await expect(page.getByRole('link',{name:'Review queue',exact:true})).toHaveCount(0);
 await page.screenshot({path:'../../output/playwright/acceptance-policy-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/acceptance-policy-phone.png',fullPage:true});
 expect(await get(page,'admin/records/'+hotel.id+'/versions')).toEqual(versions);
 await page.goto('/login');await page.getByRole('button',{name:'Finance workspace Upload, source review and finance exceptions',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Finance dashboard'})).toBeVisible();
 expect((await page.request.get('/api/admin/catalog')).status()).toBe(403);
 await expect(page.getByRole('link',{name:'Admin Console',exact:true})).toHaveCount(0);
 expect(await page.evaluate(()=>Object.keys({...localStorage,...sessionStorage}))).toEqual([]);
});
