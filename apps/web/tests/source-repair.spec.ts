import {sourceFacts} from './support/disclosure';
import {test,expect,type Page} from '@playwright/test';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';

test.skip(process.env.AP_RUN_SOURCE_REPAIR_BROWSER!=='1','Opt-in preserved actual public development measurement required');
const origin='http://127.0.0.1:3000';
type Source={id:string;document:{id:string}};
function measured(id:string):Source {
 const data=JSON.parse(readFileSync(resolve('../../runtime/clearledger/public-cl09-final.json'),'utf8'));
 const item=data.cases.find((c:Source)=>c.id===id);expect(item).toBeDefined();
 expect(item.document.id).toMatch(/^[a-f0-9-]{36}$/);return item;
}
async function source(page:Page,id:string){
 const session=await page.request.post('/api/development/session',{headers:{Origin:origin},data:{label:'Synthetic finance workspace'}});
 expect(session.status()).toBe(200);
 const saved=measured(id);await page.goto('/documents/'+saved.document.id);
 const response=await page.request.get('/api/documents/'+saved.document.id);expect(response.status()).toBe(200);
 const doc=await response.json();expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 expect(doc.draft.normalizer_version).toBe('document-normalizer-v4');
 await expect(page.locator('.page-title')).toContainText('Needs your confirmation');await sourceFacts(page);return doc;
}

test('actual repaired dense tax and European values retain measured evidence and require confirmation',async({page})=>{
 let doc=await source(page,'p01');
 expect(doc.draft.candidate.tax_amount).toBe('11.85');
 const tax=doc.observations.find((o:{field_path:string})=>o.field_path==='tax_amount');
 expect(tax.raw_value).toBe('AED 11.85');expect(tax.source.bbox).not.toBeNull();
 expect(doc.extraction_runs[0].metadata.routing.enterprise.calls).toBe(1);
 expect(doc.extraction_runs[0].metadata.routing.enterprise.reused_tables[0].rows).toBe(3);
 await page.locator('button.evidence[data-field-path="tax_amount"]').click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/cl09-dense-source-laptop.png',fullPage:true});
 doc=await source(page,'p03');
 expect(doc.draft.candidate.currency).toBe('EUR');expect(doc.draft.candidate.total_amount).toBe('1198.93');
 expect(doc.draft.candidate.tax_basis??null).toBeNull();
 const total=page.locator('.observation-table tr').filter({has:page.locator('button.evidence[data-field-path="total_amount"]')});
 await expect(total).toContainText('1.198,93 €');await expect(total).toContainText('1198.93');
 await page.locator('button.evidence[data-field-path="total_amount"]').click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await expect(page.getByRole('button',{name:'Verify facts and evaluate'})).toBeDisabled();
 await page.screenshot({path:'../../output/playwright/cl09-european-source-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/cl09-european-source-phone.png',fullPage:true});
});

test('actual multi-page headers keep original page ownership and ambiguous dollar currency',async({page})=>{
 const doc=await source(page,'p04');
 expect(doc.draft.candidate.currency??null).toBeNull();expect(doc.draft.candidate.total_amount??null).toBeNull();
 const total=doc.observations.find((o:{field_path:string})=>o.field_path==='total_amount');
 expect(total.state).toBe('PRESENT');expect(total.raw_value).toBe('$5,906.74');expect(total.source.page).toBe(2);
 expect(doc.extraction_runs[0].metadata.routing.enterprise.calls).toBe(1);
 expect(doc.extraction_runs[0].metadata.routing.enterprise.reused_tables.map((r:{rows:number})=>r.rows)).toEqual([8,4]);
 await page.locator('button.evidence[data-field-path="total_amount"]').click();
 await expect(page.getByRole('combobox',{name:/^Source page/})).toHaveValue('2');
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 const row=page.locator('.observation-table tr').filter({has:page.locator('button.evidence[data-field-path="currency"]')});
 await expect(row).toContainText('Ambiguous');await expect(row).toContainText('Unresolved');
 await expect(page.locator('input[data-field-path="currency"]')).toHaveValue('');
 await page.screenshot({path:'../../output/playwright/cl09-multipage-source-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/cl09-multipage-source-phone.png',fullPage:true});
});
