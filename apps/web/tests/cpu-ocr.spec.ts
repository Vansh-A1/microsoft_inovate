import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';

test.skip(process.env.AP_RUN_CPU_OCR_BROWSER!=='1','Opt-in pinned local CPU OCR required');

async function upload(page:import('@playwright/test').Page,caseId:string,corpus='clearledger_challenge',suffix='png'){
 await page.goto('/documents');
 await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');
 await page.getByLabel('Document files').setInputFiles(resolve('../../data/'+corpus+'/'+caseId+'.'+suffix));
 await page.getByRole('button',{name:'Upload and process'}).click();
 await expect(page.locator('.page-title')).toContainText('Needs your confirmation',{timeout:60000});
 const id=page.url().split('/').at(-1)!;
 const response=await page.request.get('/api/documents/'+id);expect(response.status()).toBe(200);
 return response.json();
}

test('actual CPU scan exposes measured source boxes and missing accounting without finance clearance',async({page})=>{
 const doc=await upload(page,'t04');
 expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 expect(doc.extraction_runs[0].metadata.provider_id).toBe('LOCAL_OCR');
 expect(doc.extraction_runs[0].metadata.routing.paths).not.toContain('ENTERPRISE_VLM');
 expect(doc.draft.candidate['lines.1.amount']).toBe('50.00');
 expect(doc.draft.candidate['lines.0.tax_amount']??null).toBeNull();
 await expect(page.getByLabel('Correct lines.0.tax_amount',{exact:true})).toHaveValue('');
 const firstLine=page.locator('.business-facts fieldset').filter({has:page.getByText('Invoice line 1',{exact:true})});
 await expect(firstLine.getByLabel('quantity',{exact:true})).toHaveValue('2');
 await expect(firstLine.getByLabel('unit price',{exact:true})).toHaveValue('75.00');
 for(const label of ['net amount','tax rate','tax amount','gross amount','uom'])await expect(firstLine.getByLabel(label,{exact:true})).toHaveValue('');
 await page.getByRole('button',{name:'lines.1.amount',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await expect(page.getByText('Extracted · confirm against source',{exact:false}).first()).toBeVisible();
 await page.screenshot({path:'../../output/playwright/clearledger-cpu-source-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/clearledger-cpu-source-mobile.png',fullPage:true});
});

test('spent wrapped scan recovers actual quantity box and keeps missing accounting reviewable',async({page})=>{
 const doc=await upload(page,'h04');
 expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 expect(doc.extraction_runs[0].metadata.provider_id).toBe('LOCAL_OCR');
 expect(doc.extraction_runs[0].metadata.routing.paths).not.toContain('ENTERPRISE_VLM');
 expect(doc.draft.candidate['lines.0.description']).toBe('Notebook cases recycled paper');
 expect(doc.draft.candidate['lines.1.quantity']).toBe('1');
 expect(doc.draft.candidate['lines.1.tax_amount']??null).toBeNull();
 await page.getByRole('button',{name:'lines.1.quantity',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await expect(page.getByLabel('Correct lines.1.tax_amount',{exact:true})).toHaveValue('');
 await page.screenshot({path:'../../output/playwright/cl06-wrapped-source-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/cl06-wrapped-source-phone.png',fullPage:true});
});

test('genuinely absent scan quantity remains unresolved and requires source review',async({page})=>{
 const doc=await upload(page,'r07','clearledger_reserved');
 expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 const by=Object.fromEntries(doc.observations.map((o:{field_path:string;state:string})=>[o.field_path,o]));
 expect(by['lines.1.quantity'].state).not.toBe('PRESENT');
 expect(doc.draft.candidate['lines.1.quantity']??null).toBeNull();
 expect(doc.extraction_runs[0].metadata.routing.paths).not.toContain('ENTERPRISE_VLM');
 expect(doc.extraction_runs[0].metadata.routing.source_rows).toHaveLength(3);
 expect(by['lines.1.quantity'].source.bbox).toBeNull();
 await expect(page.locator('.notice')).toContainText('What quantity is shown for line 2 (Desk index tabs) on page 1?');
 await page.getByRole('button',{name:'lines.1.quantity',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toHaveCount(0);
 await expect(page.locator('.observation-table tr').filter({has:page.getByRole('button',{name:'lines.1.quantity',exact:true})})).toContainText('Source value not read');
 await expect(page.getByLabel('Correct lines.1.quantity',{exact:true})).toHaveValue('');
 await page.screenshot({path:'../../output/playwright/cl07-missing-quantity-laptop.png',fullPage:true});
 await page.setViewportSize({width:390,height:844});
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 await expect(page.locator('.notice')).toContainText('What quantity is shown for line 2');
 await page.screenshot({path:'../../output/playwright/cl07-missing-quantity-phone.png',fullPage:true});
});

test('separate identical items across pages survive actual native extraction',async({page})=>{
 const doc=await upload(page,'q04','clearledger_row_identity','pdf');
 expect(doc.finance_decision).toBeNull();
 const rows=doc.extraction_runs[0].metadata.routing.source_rows;
 expect(rows.map((r:{page:number})=>r.page)).toEqual([1,2,3]);
 expect(new Set(rows.map((r:{identity:string})=>r.identity)).size).toBe(3);
 for(let i=0;i<3;i++){
  expect(doc.draft.candidate[`lines.${i}.quantity`]).toBe('2');
  await expect(page.locator('.observation-table tr').filter({has:page.getByRole('button',{name:`lines.${i}.description`,exact:true})})).toContainText('Canvas file pouches');
 }
});

test('actual unassigned VLM rows stay collapsed and noncanonical for source review',async({page})=>{
 test.setTimeout(90000);
 const doc=await upload(page,'q06','clearledger_row_identity','pdf');
 expect(doc.finance_decision).toBeNull();
 expect(doc.extraction_runs[0].metadata.routing.row_count_disagreement).toBeTruthy();
 expect(doc.draft.candidate['lines.0.quantity']).toBeNull();
 await expect(page.locator('.notice')).toContainText('Confirm the distinct printed line items against the original source.');
 const row=page.locator('.observation-table tr').filter({has:page.getByRole('button',{name:'lines.0.quantity',exact:true})});
 await expect(row).toContainText('Unassigned candidate');
 const detail=row.locator('details').filter({has:page.getByText('Unassigned model candidate',{exact:true})});
 await expect(detail).not.toHaveAttribute('open','');
 await expect(row.getByLabel('Correct lines.0.quantity',{exact:true})).toHaveValue('');
 await detail.locator('summary').click();
 const observed=doc.observations.find((o:{field_path:string})=>o.field_path==='lines.0.quantity');
 await expect(detail.locator('p')).toHaveText(observed.raw_value??'No value generated for this inventory slot.');
 await page.getByRole('button',{name:'lines.0.quantity',exact:true}).click();
 await expect(page.getByLabel('Actual source bounding box')).toHaveCount(0);
 await page.screenshot({path:'../../output/playwright/cl07-unassigned-model-review.png',fullPage:true});
});
