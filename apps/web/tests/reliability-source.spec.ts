import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

// Opt-in inspection of the measured spent development repair. No model/fixture
// substitution; regular CI does not need a private hardware measurement file.
test.skip(process.env.AP_RUN_RELIABILITY_BROWSER!=='1','Actual local repaired scan measurement required');
test('actual repaired scan has distinct measured rows, precise questions and a source-confirmation hold',async({page})=>{
 const saved=JSON.parse(readFileSync(resolve('../../runtime/kivo-reliability/measurement-repaired-spent-scan-warm.json'),'utf8')).cases[0];
 await page.goto('/');expect((await page.request.post('/api/development/session',{headers:{Origin:'http://127.0.0.1:3000'},data:{label:'Synthetic finance workspace'}})).status()).toBe(200);
 await page.goto('/documents/'+saved.document.id);await expect(page.locator('.page-title')).toContainText('Needs your confirmation');
 const doc=await(await page.request.get('/api/documents/'+saved.document.id)).json();expect(doc.original.sha256).toBe(saved.document.original.sha256);expect(doc.finance_decision).toBeNull();
 const routing=doc.extraction_runs[0].metadata.routing;expect(routing.paths).toEqual(['LOCAL_OCR']);expect(routing.vlm_status).toBe('CONFIGURED_NOT_NEEDED');
 for(const field of ['invoice_date','currency','tax_basis','lines.1.quantity','lines.1.unit_price'])expect(doc.draft.candidate[field]).toBeNull();
 for(const field of ['lines.0.description','lines.0.quantity','lines.0.unit_price','lines.0.amount','lines.1.description','lines.1.amount']){const observation=doc.observations.find((o:{field_path:string})=>o.field_path===field);expect(observation.state).toBe('PRESENT');expect(observation.source.bbox).toBeTruthy();}
 await expect(page.getByRole('listitem').filter({hasText:'What quantity is shown for line 2'})).toBeVisible();await expect(page.getByRole('listitem').filter({hasText:'What unit price is shown for line 2'})).toBeVisible();await page.getByText('Review all extracted facts and correct values',{exact:true}).click();
 await page.locator('button.evidence[data-field-path="lines.1.description"]').click();await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.setViewportSize({width:1366,height:900});await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'../../output/playwright/reliability-repaired-scan-laptop.png'});
 await page.getByLabel('Verification / correction reason').fill('Confirm printed source only; date and currency remain unknown');await page.getByRole('checkbox').check();
 const response=page.waitForResponse(r=>r.url().endsWith('/commit')&&r.request().method()==='POST');await page.getByRole('button',{name:'Verify facts and evaluate'}).click();const rejected=await response;expect(rejected.status()).toBe(422);const request=rejected.request().postDataJSON();expect(request.transaction.lines).toHaveLength(2);expect(request.transaction.lines.every((line:{id?:string})=>!line.id)).toBe(true);expect((await rejected.json()).error.code).toBe('CANONICAL_SOURCE_UNRESOLVED');await expect(page.locator('.error[role="alert"]')).toContainText(/invoice_date|currency/);await expect(page).toHaveURL('/documents/'+doc.id);
});
