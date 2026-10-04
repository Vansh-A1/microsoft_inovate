import {test,expect} from '@playwright/test';
import {randomUUID} from 'node:crypto';
import {resolve} from 'node:path';
const origin='http://127.0.0.1:3000';
async function identity(page:import('@playwright/test').Page,label:string){
 const r=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label}});expect(r.status()).toBe(200);await page.reload();
}

test('finance workspace has a small authorized navigation and business result',async({page})=>{
 await page.goto('/');await identity(page,'Synthetic finance workspace');
 await expect(page.getByRole('heading',{name:'Finance dashboard'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Admin Console',exact:true})).toHaveCount(0);
 await expect(page.getByRole('link',{name:'Upload invoice or receipt'})).toBeVisible();
 await page.goto('/cases/30000000-0000-4000-8000-000000000002');await expect(page.getByLabel('Screening result')).toContainText(/On hold|Needs review/);
 await expect(page.getByText('View detailed checks',{exact:true})).toBeVisible();await expect(page.getByRole('heading',{name:'Rule findings'})).not.toBeVisible();
 await page.getByText('View detailed checks',{exact:true}).click();await expect(page.getByRole('heading',{name:'Rule findings'})).toBeVisible();
 await page.goto('/admin');await expect(page.locator('main .error[role=alert]')).toContainText('cannot open');
 const denied=await page.request.get('/api/admin/catalog');expect(denied.status()).toBe(403);
 await page.setViewportSize({width:1024,height:768});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/phase6-small-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
});

test('policy business form creates a future hotel version and retains history and reports',async({page})=>{
 await page.goto('/');const evaluation=(await (await page.request.get('/api/transactions/30000000-0000-4000-8000-000000000001')).json()).latest_evaluation_id;
 const before=await (await page.request.get('/api/evaluations/'+evaluation+'/report')).json();
 await identity(page,'Synthetic policy administrator');await expect(page.getByRole('heading',{name:'Business configuration'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Review queue',exact:true})).toHaveCount(0);
 const records=(await (await page.request.get('/api/admin/catalog')).json()).items;
 const hotel=records.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL');
 await page.getByLabel('Configuration record').selectOption(hotel.id);
 await expect(page.getByText('Fictional sample configuration.',{exact:false})).toBeVisible();
 if(hotel.payload.allowance_amount==='9000.00'){
  await page.getByLabel('New allowance',{exact:true}).fill('8000.00');await page.getByLabel('Configuration change reason').fill('Prepare the reversible future synthetic allowance demonstration');await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByText('Draft valid',{exact:true})).toBeVisible();await page.getByRole('button',{name:'Activate validated draft'}).click();await expect(page.getByRole('status')).toContainText('New configuration version activated');await expect(page.getByLabel('New allowance',{exact:true})).toHaveValue('8000.00');
 }
 await page.getByLabel('New allowance',{exact:true}).fill('9000.00');await page.getByLabel('Effective from',{exact:true}).fill('2026-11-01');
 await page.getByLabel('Configuration change reason').fill('Future synthetic hotel allowance release demonstration '+randomUUID());
 await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByText('Draft valid',{exact:true})).toBeVisible();
 await expect(page.getByText('Review the policy change',{exact:true})).toBeVisible();
 await page.getByLabel('New allowance',{exact:true}).fill('9100.00');
 await expect(page.getByRole('button',{name:'Activate validated draft'})).toHaveCount(0);
 await page.getByLabel('New allowance',{exact:true}).fill('9000.00');
 await page.getByRole('button',{name:'Save draft',exact:true}).click();await expect(page.getByText('Draft valid',{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'Activate validated draft'}).click();await expect(page.getByRole('status')).toContainText('New configuration version activated');
 const versions=(await (await page.request.get('/api/admin/records/'+hotel.id+'/versions')).json()).items;expect(versions.some((v:{payload:{allowance_amount:string}})=>v.payload.allowance_amount==='8000.00')).toBe(true);expect(versions.at(-1).payload.allowance_amount).toBe('9000.00');expect(versions.at(-1).change.reason).toContain('Future synthetic hotel allowance release demonstration');expect(versions.at(-1).change.actor_id).toBeTruthy();
 await page.getByText('Policy versions and audit metadata',{exact:true}).click();await expect(page.getByText(/Version 1 · effective/)).toBeVisible();
 await page.screenshot({path:'../../output/playwright/phase6-admin-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/phase6-admin-mobile.png',fullPage:true});
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
 await identity(page,'Synthetic finance workspace');const after=await (await page.request.get('/api/evaluations/'+evaluation+'/report')).json();expect(after).toEqual(before);
});

test('actual invoice to result report and audit works without JSON editing and persists on reload',async({page})=>{
 await page.goto('/');await identity(page,'Synthetic finance workspace');await page.getByRole('link',{name:'Upload invoice or receipt'}).click();
 await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();
 await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});
 await expect(page.getByLabel('Vendor',{exact:true})).toBeVisible();await expect(page.getByLabel('Invoice number',{exact:true})).not.toBeEditable();
 await page.getByLabel('Verification / correction reason').fill('Inspected source invoice and business reference choices');await page.getByText('I reviewed the source pages and confirm the observable facts.').click();
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:30000});
 await expect(page.getByLabel('Screening result')).toContainText('What to do next');await expect(page.getByRole('heading',{name:'Audit timeline',exact:true})).toBeVisible();
 const id=page.url().split('/').at(-1)!;await page.reload();await expect(page.getByLabel('Screening result')).toContainText('On hold');
 await page.screenshot({path:'../../output/playwright/phase6-finance-result.png',fullPage:true});
 await page.getByRole('link',{name:'View report',exact:true}).click();await expect(page.getByRole('heading',{name:'Screening report',exact:true})).toBeVisible();
 const record=(await (await page.request.get('/api/transactions/'+id)).json());expect(record.processing_state).toBe('COMPLETED');expect(record.versions).toHaveLength(1);
});


test('enterprise presentation maps a real native invoice without development templates',async({page})=>{
 await page.goto('/');await identity(page,'Synthetic finance workspace');
 let templateCalls=0;
 await page.route('**/api/me',async route=>{const response=await route.fetch();const me=await response.json();await route.fulfill({response,json:{...me,development:false}})});
 await page.route('**/api/development/templates/**',route=>{templateCalls++;return route.fulfill({status:503,json:{error:{message:'Development templates are unavailable'}}})});
 await page.goto('/documents');await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));await page.getByRole('button',{name:'Upload and process'}).click();
 await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});
 await expect(page.getByLabel('Invoice number',{exact:true})).not.toBeEditable();await expect(page.getByLabel('Category',{exact:true})).toBeEditable();await page.getByLabel('Category',{exact:true}).fill('SUPPLIES');
 const records=(await (await page.request.get('/api/references')).json()).records;
 for(const [label,kind] of [['Vendor','vendors'],['Cost centre','cost_centers'],['Budget','budgets'],['Purchase order','purchase_orders'],['Approval policy','approval_policies'],['Purchase order line','po_lines'],['Goods receipt line','grn_lines']]){
  const record=records.find((r:{kind:string})=>r.kind===kind);await page.getByLabel(label,{exact:true}).selectOption(record.id);
 }
 await page.getByLabel('Verification / correction reason').fill('Manual source and business reference mapping without a development template');await page.getByText('I reviewed the source pages and confirm the observable facts.').click();await page.getByRole('button',{name:'Verify facts and evaluate'}).click();
 await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:30000});expect(templateCalls).toBe(0);
});
