import {api,mutate} from './api';

// Keys bind to scoped logical actions. Persist fingerprints and random keys only.
const memory=new Map<string,string>();
const pending=new Map<string,Promise<unknown>>();
const prefix='kivo:mutation:v1:';
function ordered(value:unknown):unknown {
 if(Array.isArray(value))return value.map(ordered);
 if(value&&typeof value==='object')return Object.fromEntries(Object.entries(value).sort(([a],[b])=>a.localeCompare(b)).map(([key,item])=>[key,ordered(item)]));
 return value;
}
async function action(path:string,body:unknown){
 const identity=await api<{tenant_id:string;legal_entity_id:string;actor_id:string}>('me');
 const input=JSON.stringify([identity.tenant_id,identity.legal_entity_id,identity.actor_id,path,ordered(body)]);
 const bytes=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(input));
 return prefix+Array.from(new Uint8Array(bytes),b=>b.toString(16).padStart(2,'0')).join('');
}
function keyFor(action:string){
 let key=memory.get(action);
 try{key=sessionStorage.getItem(action)||key}catch{/* Restricted storage: replay is retained within this page. */}
 if(!key){key=crypto.randomUUID();try{sessionStorage.setItem(action,key)}catch{/* Never persist document facts or credentials. */}}
 memory.set(action,key);return key;
}
export async function replayMutation<T>(path:string,body:unknown,retireOnSuccess=false):Promise<T>{
 const intent=await action(path,body),inFlight=pending.get(intent);
 if(inFlight)return inFlight as Promise<T>;
 const request=mutate<T>(path,body,keyFor(intent));pending.set(intent,request);
 try{const result=await request;if(retireOnSuccess){memory.delete(intent);try{sessionStorage.removeItem(intent)}catch{/* Storage may be unavailable. */}}return result}finally{pending.delete(intent)}
}
