import {expect,type Page} from '@playwright/test';
async function expand(page:Page,selector:string){const item=page.locator(selector);await expect(item).toBeAttached();if(!await item.evaluate(node=>node.hasAttribute('open')))await item.locator(':scope > summary').click();}
export const sourceFacts=(page:Page)=>expand(page,'details.all-source-facts');
export const businessReferences=(page:Page)=>expand(page,'details.business-matching');
export async function caseDetails(page:Page){const item=page.locator('details.case-disclosure').filter({has:page.getByText('Full facts and detailed checks',{exact:true})});await expect(item).toBeAttached();if(!await item.evaluate(node=>node.hasAttribute('open')))await item.locator(':scope > summary').click();}
export async function caseActions(page:Page){const item=page.locator('details.case-disclosure').filter({has:page.getByText('Resolve this case and manage approvals',{exact:true})});await expect(item).toBeAttached();if(!await item.evaluate(node=>node.hasAttribute('open')))await item.locator(':scope > summary').click();}
export async function auditHistory(page:Page){const item=page.locator('details.case-disclosure').filter({has:page.getByText('Audit history',{exact:true})});await expect(item).toBeAttached();if(!await item.evaluate(node=>node.hasAttribute('open')))await item.locator(':scope > summary').click();}
export const caseUtilities=(page:Page)=>expand(page,'details.case-utility');
