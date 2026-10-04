import {sourceFacts,businessReferences} from './support/disclosure';
import {caseDetails} from './support/disclosure';
import {test,expect} from '@playwright/test';
import {resolve} from 'node:path';
const corpus=resolve('../../data/documents_phase2');

async function upload(page:import('@playwright/test').Page,name:string,purpose='VENDOR_INVOICE',state='READY'){
 await page.goto('/documents');await page.getByLabel('Document purpose').selectOption(purpose);
 await page.getByLabel('Document files').setInputFiles(resolve(corpus,name));
 await page.getByRole('button',{name:'Upload and process'}).click();await expect(page).toHaveURL(/\/documents\/[a-f0-9-]{36}$/);
 await expect(page.locator('.page-title')).toContainText(({READY:'Ready to verify',NEEDS_INPUT:'Needs your confirmation',QUARANTINED:'File quarantined'} as Record<string,string>)[state]||state,{timeout:30000});
 if(await page.locator('details.all-source-facts').count())await sourceFacts(page);if(await page.locator('details.business-matching').count())await businessReferences(page);
 return page.url().split('/').at(-1)!;
}

test('native PDF upload, actual field box, source verification and persisted finance case',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 const id=await upload(page,'vendor_native.pdf');
 await page.locator('button.evidence[data-field-path="total_amount"]').click();
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await expect(page.getByRole('img',{name:/vendor_native.pdf/})).toBeVisible();
 await page.getByRole('combobox',{name:'Preview zoom',exact:true}).selectOption('200');
 await expect(page.locator('.page-preview')).toHaveAttribute('style','width: 200%;');
 await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.screenshot({path:'../../output/playwright/document-native.png',fullPage:true});
 await page.getByLabel('Verification / correction reason').fill('Reviewed native invoice source and reference mapping');
 await page.getByText('I reviewed the source pages and confirm the observable facts.').click();
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);
 await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:25000});
 await caseDetails(page);await page.getByText('View detailed checks',{exact:true}).click();await expect(page.locator('.rule').filter({hasText:'DOC-001'}).getByText('PASS',{exact:true})).toBeVisible();
 await expect(page.getByRole('heading',{name:'Source documents'})).toBeVisible();
 await page.reload();await page.getByText('File details',{exact:true}).click();await expect(page.getByText('vendor_native.pdf · INVOICE',{exact:true})).toBeVisible();
 const doc=await page.request.get('/api/documents/'+id);expect((await doc.json()).original.sha256).toMatch(/^[a-f0-9]{64}$/);
 expect(errors).toEqual([]);
});

test('actual photo OCR and employee source produce finance result without approval authority',async({page})=>{
 await upload(page,'receipt_photo.jpg','EMPLOYEE_RECEIPT');
 await expect(page.locator('.observation-table tr').filter({has:page.locator('button.evidence[data-field-path="total_amount"]')})).toContainText('500.00');
 await expect(page.getByLabel('eligible nights',{exact:true})).toHaveValue('');
 await page.locator('button.evidence[data-field-path="total_amount"]').click();await expect(page.getByLabel('Actual source bounding box')).toBeVisible();
 await page.getByLabel('Verification / correction reason').fill('Receipt photograph and expense details reviewed');
 await page.getByText('I reviewed the source pages and confirm the observable facts.').click();
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();
 await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:25000});
 await caseDetails(page);await page.getByText('View detailed checks',{exact:true}).click();await expect(page.locator('.rule').filter({hasText:'DOC-001'}).getByText('PASS',{exact:true})).toBeVisible();
 await page.screenshot({path:'../../output/playwright/document-employee-case.png',fullPage:true});
});

test('ambiguous date requires source-linked correction, then a material revision retains history',async({page})=>{
 await upload(page,'ambiguous_date.pdf','VENDOR_INVOICE','NEEDS_INPUT');
 await page.getByLabel('Verification / correction reason').fill('Date confirmed with issuer context');
 await page.getByText('I reviewed the source pages and confirm the observable facts.').click();
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();
 await expect(page.locator('.error[role="alert"]')).toContainText('invoice_date');
 await page.locator('input[data-field-path="invoice_date"]').fill('2026-09-25');
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);
 await expect(page.locator('.result-summary h2')).toHaveText('On hold',{timeout:25000});
 await page.getByRole('link',{name:'View source / append correction →'}).click();await sourceFacts(page);
 await page.locator('input[data-field-path="invoice_date"]').fill('2026-09-26');
 await page.getByLabel('Verification / correction reason').fill('Correct source date in a new canonical version');
 await page.getByText('I reviewed the source pages and confirm the observable facts.').click();
 await page.getByRole('button',{name:'Verify facts and evaluate'}).click();await expect(page).toHaveURL(/\/cases\/[a-f0-9-]{36}$/);
 await expect(page.locator('.page-title')).toContainText('VERSION 2');
 await page.getByText('Source correction history',{exact:true}).click();
 await expect(page.locator('pre').filter({hasText:'03/04/2026'})).toBeVisible();
});

test('multi-page navigation, explicit page-level row evidence and uncertain bundle gate',async({page})=>{
 await upload(page,'vendor_multipage.pdf');await page.getByRole('combobox',{name:'Source page',exact:true}).selectOption('2');
 await expect(page.getByRole('img',{name:/page 2/})).toBeVisible();
 await page.locator('button.evidence[data-field-path="lines.1.quantity"]').click();
 await expect(page.locator('.source-viewer .hint')).toContainText('Page-level evidence. No field box is available.');
 await upload(page,'uncertain_bundle.pdf','VENDOR_INVOICE','NEEDS_INPUT');
 await expect(page.getByRole('button',{name:'Verify facts and evaluate'})).toBeDisabled();
 await page.getByText('Detailed validation findings',{exact:true}).click();await expect(page.locator('.notice').filter({hasText:'SEGMENTATION_UNCERTAIN'})).toBeVisible();
});

test('corrupt source quarantine, loading/error states and mobile document workspace',async({page})=>{
 await upload(page,'corrupt.pdf','VENDOR_INVOICE','QUARANTINED');
 await expect(page.locator('.error[role="status"]')).toContainText('corrupt document');await expect(page.getByRole('link',{name:'Download preserved original'})).toHaveCount(0);
 await page.setViewportSize({width:390,height:844});await page.goto('/documents');
 await expect(page.getByRole('heading',{name:'Upload a document',exact:true})).toBeVisible();
 expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
 await page.screenshot({path:'../../output/playwright/documents-mobile.png',fullPage:true});
 await page.route('**/api/documents',async route=>{await new Promise(r=>setTimeout(r,700));await route.fulfill({status:503,contentType:'application/json',body:JSON.stringify({error:{message:'Document provider unavailable'}})})});
 await page.goto('/documents');await expect(page.getByText('Loading documents…')).toBeVisible();await expect(page.locator('.error[role="alert"]')).toContainText('Document provider unavailable');
});
