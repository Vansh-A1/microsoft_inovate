import type {Page} from '@playwright/test';

export async function selectLocalIdentity(page:Page,label:string){
 const selector=page.getByLabel('Configured demo identity');
 if(!await selector.isVisible())await page.getByText('Local sample access',{exact:true}).click();
 await Promise.all([page.waitForNavigation({waitUntil:'load'}),selector.selectOption(label)]);
 const me=await (await page.request.get('/api/me')).json();
 const finance=me.roles.some((r:string)=>['FINANCE_REVIEWER','AUDITOR','EMPLOYEE','FINANCE_CONTROLLER','MANAGER','DEPARTMENT_HEAD','CFO','DIRECTOR','APPROVER'].includes(r));
 const admin=me.roles.some((r:string)=>['POLICY_ADMIN','REFERENCE_ADMIN','LEDGER_ADMIN','OPERATIONS_ADMIN','ML_ADMIN','ML_GOVERNANCE'].includes(r));
 if(admin&&!finance&&!['/admin','/operations','/reference-imports','/intelligence'].includes(new URL(page.url()).pathname))await page.waitForURL(/\/admin$/,{waitUntil:'load'});
}
