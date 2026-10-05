import {test,expect} from '@playwright/test';
const origin='http://127.0.0.1:3000';

test('Kivo landing is honest and usable on laptop phone keyboard and reduced motion',async({page})=>{
 await page.setViewportSize({width:1440,height:900});await page.goto('/welcome');
 await expect(page.getByRole('heading',{name:'Less invoice fuss. More clarity.'})).toBeVisible();
 await expect(page.getByRole('img',{name:/Actual fictional invoice result/})).toBeVisible();
 await expect(page.getByText('A verified fictional example.',{exact:false})).toBeVisible();
 await expect(page.locator('body')).not.toContainText(/hackathon|ReviewDesk|ClearLedger/);
 await page.getByRole('link',{name:'Get started',exact:true}).focus();await expect(page.getByRole('link',{name:'Get started',exact:true})).toBeFocused();
 expect(await page.getByRole('link',{name:'Get started',exact:true}).evaluate(el=>getComputedStyle(el).outlineStyle)).toBe('solid');
 await page.screenshot({path:'../../output/playwright/kivo-landing-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/kivo-landing-phone.png',fullPage:true});
 await page.emulateMedia({reducedMotion:'reduce'});expect(await page.locator('.landing-hero').evaluate(el=>getComputedStyle(el).animationName)).toBe('none');
 await page.getByRole('link',{name:'Get started',exact:true}).click();await expect(page.getByRole('heading',{name:'Welcome to Kivo'})).toBeVisible();
 await expect(page.getByText('This is development access, not production sign-in.',{exact:false})).toBeVisible();
 await page.screenshot({path:'../../output/playwright/kivo-login-phone.png',fullPage:true});
});

test('Kivo keeps actual current readiness and progressively discloses controls',async({page})=>{
 test.skip(process.env.AP_RUN_FINAL_ACCEPTANCE!=='1','Existing computed local walkthrough required');
 await page.goto('/');expect((await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Hackathon finance reviewer'}})).status()).toBe(200);
 const data=await (await page.request.get('/api/development/scenarios')).json();expect(data.ready).toBe(true);
 const sample=data.items.find((s:{key:string})=>s.key==='vlm-pass');await page.goto(sample.case_url);
 await expect(page.locator('.result-summary h2')).toHaveText('Ready for processing');
 await expect(page.getByRole('heading',{name:'Rule findings'})).not.toBeVisible();await expect(page.getByRole('heading',{name:'Audit timeline'})).not.toBeVisible();
 await expect(page.getByRole('heading',{name:'Source documents'})).toBeVisible();
 await page.setViewportSize({width:1440,height:900});await page.screenshot({path:'../../output/playwright/kivo-ready-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/kivo-ready-phone.png',fullPage:true});
 const allowance=data.items.find((s:{key:string})=>s.key==='employee-allowance');await page.goto(allowance.case_url);
 await expect(page.locator('.result-summary h2')).toHaveText('Needs review');await expect(page.getByLabel('Screening result')).toContainText('Claims total INR 1800.00');await expect(page.getByLabel('Screening result')).toContainText('configured limit is INR 1500.00');
 await page.screenshot({path:'../../output/playwright/kivo-allowance-phone.png',fullPage:true});
});

test('Kivo scoped policy editor teaches scope currency unit dates and retained versions',async({page})=>{
 await page.goto('/login');await page.getByRole('button',{name:'Policy administrator Policies and allowance versions',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Business configuration'})).toBeVisible();
 await page.getByRole('button',{name:'Allowances & receipts',exact:true}).click();
 const data=await (await page.request.get('/api/admin/catalog')).json();const hotel=data.items.find((r:{kind:string;payload:{category:string}})=>r.kind==='expense_policies'&&r.payload.category==='HOTEL'&&(r.payload as {policy_code?:string}).policy_code==='DEMO-EXP-HOTEL');
 await page.getByLabel('Configuration record').selectOption(hotel.id);
 await expect(page.getByRole('heading',{name:'What this rule covers'})).toBeVisible();await expect(page.getByText('Allowance unit',{exact:true})).toBeVisible();
 await expect(page.locator('.policy-context')).toContainText('INR');await expect(page.locator('.policy-context')).toContainText('Eligible night');
 await expect(page.getByText('Fictional sample configuration.',{exact:false})).toBeVisible();
 await expect(page.getByRole('button',{name:'Activate new version'})).toHaveCount(0);
 await expect(page.getByRole('button',{name:'Validate and save draft'})).toBeVisible();
 await page.setViewportSize({width:1440,height:900});await page.screenshot({path:'../../output/playwright/kivo-policy-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);await page.screenshot({path:'../../output/playwright/kivo-policy-phone.png',fullPage:true});
 await page.getByText('Policy versions and audit metadata',{exact:true}).click();await expect(page.locator('.policy-history')).toContainText('Version '+hotel.version+' · effective');
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
});
