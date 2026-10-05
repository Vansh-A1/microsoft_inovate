import {caseActions} from './support/disclosure';
import {test,expect} from '@playwright/test';
const origin='http://127.0.0.1:3000';
test('loaded finance and administration views remain usable at laptop and fallback widths',async({page})=>{
 await page.goto('/');await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Synthetic finance workspace'}});
 await page.goto('/cases/30000000-0000-4000-8000-000000000002');await caseActions(page);await expect(page.getByRole('button',{name:'Refresh review',exact:true})).toBeVisible();await expect(page.getByText('Loading finance controls…',{exact:true})).toHaveCount(0);
 for(const [name,width,height] of [['laptop',1280,720],['small-laptop',1024,768],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`../../output/playwright/phase6-loaded-finance-${name}.png`});
 }
 await page.keyboard.press('Tab');expect(await page.evaluate(()=>document.activeElement?.tagName)).not.toBe('BODY');
 await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Synthetic policy administrator'}});await page.goto('/admin');
 const records=(await (await page.request.get('/api/admin/catalog')).json()).items;const hotel=records.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL'&&(r.payload as {policy_code?:string}).policy_code==='DEMO-EXP-HOTEL');await page.getByLabel('Configuration record').selectOption(hotel.id);await expect(page.getByLabel('New allowance',{exact:true})).toBeVisible();
 for(const [name,width,height] of [['laptop',1280,720],['small-laptop',1024,768],['mobile',390,844]] as const){
  await page.setViewportSize({width,height});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:`../../output/playwright/phase6-loaded-admin-${name}.png`});
 }
});
