import {test,expect} from '@playwright/test';
const origin='http://127.0.0.1:3000';
async function identity(page:import('@playwright/test').Page,label:string){
 const response=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label}});expect(response.status()).toBe(200);await page.reload();
 const me=await (await page.request.get('/api/me')).json();
 const finance=me.roles.some((r:string)=>['FINANCE_REVIEWER','AUDITOR','EMPLOYEE','FINANCE_CONTROLLER','MANAGER','DEPARTMENT_HEAD','CFO','DIRECTOR','APPROVER'].includes(r));
 const admin=me.roles.some((r:string)=>['POLICY_ADMIN','REFERENCE_ADMIN','LEDGER_ADMIN','OPERATIONS_ADMIN','ML_ADMIN','ML_GOVERNANCE'].includes(r));
 if(admin&&!finance&&!['/admin','/operations','/reference-imports','/intelligence'].includes(new URL(page.url()).pathname))await page.waitForURL(/\/admin$/,{waitUntil:'load'});
}
test('scoped walkthrough reads actual evaluations and connects source, correction history and laptop/mobile views',async({page})=>{
 await page.goto('/');await identity(page,'Hackathon finance reviewer');await page.getByText('Local sample access',{exact:true}).click();await page.getByRole('link',{name:'Sample walkthrough',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Hackathon walkthrough',exact:true})).toBeVisible();
 const data=await (await page.request.get('/api/development/scenarios')).json();
 if(data.ready){
  expect(data.items).toHaveLength(8);
  const visual=data.items.find((r:{key:string})=>r.key==='vlm-pass');expect(visual.provider).toBe('ENTERPRISE_VLM');
  const record=await (await page.request.get('/api'+visual.report_url.replace('/reports/','/evaluations/'))).json();expect(record.decision).toBe('PASS');expect(record.transaction_version).toBe(visual.transaction_version);
  await page.setViewportSize({width:1280,height:800});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/final-demo-laptop.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/final-demo-mobile.png',fullPage:true});
  await page.setViewportSize({width:1280,height:800});await page.getByRole('link',{name:'View original HOLD',exact:true}).click();await expect(page.getByRole('heading',{name:'Screening report',exact:true})).toBeVisible();await expect(page.locator('main .badge')).toHaveText('On hold');
  await page.goto(visual.document_url);await expect(page.getByRole('heading',{name:'Original source page'})).toBeVisible();await expect(page.getByRole('combobox',{name:/^Source page/})).toHaveValue('1');await page.getByRole('link',{name:'Download preserved original'}).focus();await expect(page.getByRole('link',{name:'Download preserved original'})).toBeFocused();
 }else{await expect(page.getByRole('heading',{name:'Prepare the walkthrough'})).toBeVisible();}
 await identity(page,'Synthetic finance workspace');const other=await (await page.request.get('/api/development/scenarios')).json();expect(other.items).toHaveLength(0);if(data.ready)expect(other.message).toContain('Select Hackathon');
});

test('provider outage is understandable and does not display a finance decision',async({page})=>{
 await page.goto('/');await identity(page,'Hackathon finance reviewer');
 const rows=(await (await page.request.get('/api/documents')).json()).items;
 const failed=rows.find((r:{last_error:string})=>r.last_error==='PROVIDER_UNAVAILABLE');
 // Ordinary CPU CI never starts a GPU. Actual offline drill creates this
 // retained failure for the local hardware acceptance run.
 test.skip(!failed,'Actual configured-provider outage drill is opt-in.');
 await page.goto('/documents/'+failed.id);await expect(page.getByText(/Visual extraction service is unavailable/)).toBeVisible();await expect(page.getByText(/No finance decision has been made/)).toBeVisible();await expect(page.getByRole('button',{name:'Verify facts and evaluate'})).toHaveCount(0);await page.screenshot({path:'../../output/playwright/final-provider-outage.png',fullPage:true});
});

test('operations shows only persisted timing samples and safe dependency information',async({page})=>{
 await page.goto('/');await identity(page,'Hackathon operations');await page.goto('/operations');await expect(page.getByRole('heading',{name:'Observed processing latency'})).toBeVisible();
 const response=await page.request.get('/api/operations/measurements');expect(response.status()).toBe(200);const measured=await response.json();expect(measured.audit_failures.count).toBeNull();expect(measured.interpretation).toContain('not production SLA');
 await expect(page.getByText(measured.interpretation,{exact:true})).toBeVisible();
 const identities=(await (await page.request.get('/api/development/session')).json()).identities;const employee=identities.find((i:{roles:string[]})=>i.roles.includes('EMPLOYEE'));expect(employee).toBeTruthy();await identity(page,employee.label);expect((await page.request.get('/api/operations/measurements')).status()).toBe(403);
});
