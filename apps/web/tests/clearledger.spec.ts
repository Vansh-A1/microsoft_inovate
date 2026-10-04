import {sourceFacts} from './support/disclosure';
import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';

test('local role entry opens only server-configured finance and admin access',async({page})=>{
 await page.goto('/login');
 await expect(page.getByRole('heading',{name:'Welcome to Kivo'})).toBeVisible();
 await expect(page.getByText('Local sample company.',{exact:false})).toBeVisible();
 await page.getByRole('button',{name:'Policy administrator Policies and allowance versions',exact:true}).click();
 await expect(page).toHaveURL(/\/admin$/);
 await expect(page.getByRole('heading',{name:'Business configuration'})).toBeVisible();
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
 await page.screenshot({path:'../../output/playwright/clearledger-admin.png',fullPage:true});
 await page.goto('/login');
 await page.getByRole('button',{name:'Finance workspace Upload, source review and finance exceptions',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Your finance workspace'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Admin Console',exact:true})).toHaveCount(0);
 await expect(page.getByRole('navigation')).not.toContainText(/hackathon|ReviewDesk/i);
 expect((await page.request.get('/api/admin/catalog')).status()).toBe(403);
 const storage=await page.evaluate(()=>Object.keys({...localStorage,...sessionStorage}));expect(storage).toEqual([]);
 await page.screenshot({path:'../../output/playwright/clearledger-finance.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/clearledger-finance-mobile.png',fullPage:true});
});

test('Auto uses printed purpose and retains uncertainty before finance submission',async({page})=>{
 await page.goto('/documents');
 await expect(page.getByLabel('Document purpose')).toHaveValue('AUTO');
 await expect(page.getByText('Malware scanner: not configured.',{exact:false})).toBeVisible();
 await page.getByLabel('Document files').setInputFiles(resolve('../../data/documents_phase2/vendor_native.pdf'));
 await page.getByRole('button',{name:'Upload and process'}).click();
 await expect(page.locator('.page-title')).toContainText('Ready to verify',{timeout:30000});
 const id=page.url().split('/').at(-1)!;
 const doc=await (await page.request.get('/api/documents/'+id)).json();
 expect(doc.intake_hint).toBe('AUTO');expect(doc.source_type).toBe('VENDOR_INVOICE');expect(doc.finance_decision).toBeNull();
 expect(doc.jobs[0].metadata.classification.state).toBe('SUGGESTED');
 await expect(page.getByLabel('Document progress')).toHaveCount(1);
 await sourceFacts(page);await expect(page.getByText('Extracted · confirm against source',{exact:false}).first()).toBeVisible();
 await expect(page.getByRole('button',{name:'Verify facts and evaluate'})).toBeDisabled();
 await expect(page.locator('button.evidence[data-field-path="total_amount"]')).toHaveText('Total');
 await page.screenshot({path:'../../output/playwright/clearledger-source.png',fullPage:true});
});

test('enterprise sign-in offers configured identity provider without local impersonation controls',async({page})=>{
 await page.route('**/api/development/session',route=>route.fulfill({json:{development:false,identities:[]}}));
 await page.goto('/login');
 await expect(page.getByRole('heading',{name:'Sign in to your organization'})).toBeVisible();
 await expect(page.getByRole('link',{name:'Continue with Microsoft'})).toHaveAttribute('href','/.auth/login/aad?post_login_redirect_uri=/');
 await expect(page.locator('.identity-option')).toHaveCount(0);
 await page.emulateMedia({reducedMotion:'reduce'});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/clearledger-login-mobile.png',fullPage:true});
});
