import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';

test.skip(process.env.AP_RUN_CPU_OCR_BROWSER!=='1','Opt-in pinned local CPU OCR required');

async function upload(page:import('@playwright/test').Page,caseId:string){
 await page.goto('/documents');
 await page.getByLabel('Document purpose').selectOption('VENDOR_INVOICE');
 await page.getByLabel('Document files').setInputFiles(resolve('../../data/clearledger_challenge/'+caseId+'.png'));
 await page.getByRole('button',{name:'Upload and process'}).click();
 await expect(page.locator('.page-title')).toContainText('Needs your confirmation',{timeout:30000});
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

test('reserved wrapped scan retains actual model disagreement and reviewer uncertainty',async({page})=>{
 const doc=await upload(page,'h04');
 expect(doc.state).toBe('NEEDS_INPUT');expect(doc.finance_decision).toBeNull();
 expect(doc.extraction_runs[0].metadata.provider_id).toBe('ENTERPRISE_VLM');
 const by=Object.fromEntries(doc.observations.map((o:{field_path:string;state:string})=>[o.field_path,o]));
 expect(by['lines.0.quantity'].state).toBe('AMBIGUOUS');
 expect(doc.draft.candidate['lines.0.quantity']).toBeNull();
 await page.getByText('Detailed validation findings',{exact:true}).click();
 await expect(page.locator('.notice').filter({hasText:'TABLE_COVERAGE_UNCERTAIN'})).toBeVisible();
 await page.getByRole('button',{name:'lines.0.quantity',exact:true}).click();
 await expect(page.locator('.observation-table tr').filter({has:page.getByRole('button',{name:'lines.0.quantity',exact:true})})).toContainText(/ambiguous|uncertain/i);
 await page.screenshot({path:'../../output/playwright/clearledger-wrapped-review-laptop.png',fullPage:true});
});
