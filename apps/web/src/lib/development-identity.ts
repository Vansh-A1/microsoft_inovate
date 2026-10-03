import {readFile} from 'node:fs/promises';
import path from 'node:path';
export async function configuredIdentities(){
 if(process.env.AP_ENVIRONMENT==='enterprise')throw new Error('Development identities are disabled.');
 const file=process.env.AP_IDENTITY_FILE||path.resolve(process.cwd(),'../../runtime/dev/settings.json');
 const data=JSON.parse(await readFile(file,'utf8')) as {identities:Record<string,{label:string;actor_id:string;roles:string[]}>};
 return Object.entries(data.identities).map(([token,identity])=>({token,...identity}));
}
export async function serverIdentityToken(label?:string){
 if(process.env.AP_ENVIRONMENT==='enterprise')return undefined;
 if(label&&process.env.AP_ENABLE_DEMO_IDENTITIES==='1'){const identities=await configuredIdentities();const selected=identities.find(i=>i.label===label);if(selected)return selected.token;}
 return process.env.AP_DEV_TOKEN;
}
