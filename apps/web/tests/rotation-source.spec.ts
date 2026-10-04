import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

test.skip(process.env.AP_RUN_ROTATION_BROWSER!=='1','Opt-in actual CL-10 upload measurements required');
const origin='http://127.0.0.1:3000';
async function source(page:Page,file:string){
 const saved=JSON.parse(readFileSync(resolve('../../runtime/clearledger/'+file),'utf8')).cases[0];
 const session=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Synthetic finance workspace'}});
 expect(session.status()).toBe(200);
 await page.goto('/documents/'+saved.document.id);
 const response=await page.request.get('/api/documents/'+saved.document.id);expect(response.status()).toBe(200);
 const doc=await response.json();expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 expect(doc.original.sha256).toBe(saved.source_sha256);
 await expect(page.locator('.page-title')).toContainText('Needs your confirmation');
 await expect(page.getByRole('button',{name:'Verify facts and evaluate'})).toBeDisabled();return doc;
}

test('actual rotated source boxes highlight original bytes at laptop and phone sizes',async({page})=>{
 const doc=await source(page,'public-cl10-d03.json');
 expect(doc.extraction_runs[0].metadata.routing.paths).toEqual(['LOCAL_OCR']);
 const by=Object.fromEntries(doc.observations.map((o:{field_path:string})=>[o.field_path,o]));
 expect(by['lines.0.amount'].raw_value).toBe('42.75');
 const box=by['lines.0.amount'].source.bbox;expect(box.x1).toBeGreaterThan(.23);expect(box.y2).toBeLessThan(.11);
 await page.getByRole('button',{name:'lines.0.amount',exact:true}).click();
 const overlay=page.getByLabel('Actual source bounding box');await expect(overlay).toBeVisible();
 await overlay.scrollIntoViewIfNeeded();
 await page.screenshot({path:'../../output/playwright/cl10-rotation-source-laptop.png'});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await overlay.scrollIntoViewIfNeeded();await page.screenshot({path:'../../output/playwright/cl10-rotation-source-phone.png'});
});

test('actual skewed partial source keeps both unread cells and exact next questions',async({page})=>{
 const doc=await source(page,'public-cl10-r06.json');
 expect(doc.draft.candidate['lines.1.description']).toBe('Braided file loops');
 expect(doc.draft.candidate['lines.1.quantity']).toBeNull();expect(doc.draft.candidate['lines.1.unit_price']).toBeNull();
 const questions=doc.draft.findings.filter((f:{code:string;field:string})=>f.code==='SOURCE_CELL_UNREAD'&&f.field.startsWith('lines.1.'));
 expect(questions).toHaveLength(2);
 expect(questions.every((f:{message:string})=>f.message.includes('Braided file loops')&&f.message.includes('do not calculate'))).toBe(true);
 for(const question of questions)await expect(page.getByText(question.message,{exact:true})).toBeVisible();
 await page.getByRole('button',{name:'lines.1.amount',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/cl10-partial-source-laptop.png'});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.getByLabel('Actual source bounding box').scrollIntoViewIfNeeded();
 await page.screenshot({path:'../../output/playwright/cl10-partial-source-phone.png'});
});


test('actual final public deskew keeps valid tax source and reports excluded border region',async({page})=>{
 const doc=await source(page,'public-cl10-p02-safety-final.json');
 const routing=doc.extraction_runs[0].metadata.routing;
 expect(routing.ocr_provenance[0].provider).toBe('RAPIDOCR_CPU');
 expect(routing.ocr_provenance[0].runtime.aligned_pixel_read.excluded_source_regions).toHaveLength(1);
 expect(routing.enterprise.calls).toBe(1);
 const tax=doc.observations.find((o:{field_path:string})=>o.field_path==='tax_amount');
 expect(tax.state).toBe('PRESENT');expect(tax.raw_value).toBe('AED 3.00');
 expect(doc.draft.candidate.tax_basis??null).toBeNull();
 await page.getByRole('button',{name:'tax_amount',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.getByLabel('Actual source bounding box').scrollIntoViewIfNeeded();
 await page.screenshot({path:'../../output/playwright/cl10-public-deskew-source-laptop.png'});
});


test('current Admin catalog loads retained business records with finance access denied',async({page})=>{
 await page.goto('/login');
 await page.getByRole('button',{name:'Policy administrator Policies and allowance versions',exact:true}).click();
 await expect(page.getByRole('heading',{name:'Business configuration'})).toBeVisible();
 await expect(page.getByText('Loading business configuration...',{exact:true})).toHaveCount(0);
 await expect.poll(()=>page.getByLabel('Configuration record').locator('option').count()).toBeGreaterThan(1);
 expect((await page.request.get('/api/admin/catalog')).status()).toBe(200);
 expect((await page.request.get('/api/transactions')).status()).toBe(403);
 await page.screenshot({path:'../../output/playwright/cl10-admin-loaded-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/cl10-admin-loaded-phone.png',fullPage:true});
});
