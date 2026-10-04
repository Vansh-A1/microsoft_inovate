'use client';
import {useEffect,useState} from 'react';
import Link from 'next/link';
import {PRODUCT_NAME} from '@/lib/product';
import {workspaceIdentity} from '@/lib/presentation';
type Choice={label:string;roles:string[]};
const administration=['POLICY_ADMIN','REFERENCE_ADMIN','LEDGER_ADMIN','OPERATIONS_ADMIN','ML_ADMIN','ML_GOVERNANCE'];
function purpose(roles:string[]){
 if(roles.includes('POLICY_ADMIN'))return 'Policies and allowance versions';
 if(roles.includes('OPERATIONS_ADMIN'))return 'Service health, jobs and recovery';
 if(roles.includes('AUDITOR'))return 'Read-only evidence and audit history';
 if(roles.some(r=>['MANAGER','DEPARTMENT_HEAD','DIRECTOR','CFO'].includes(r)))return 'Approvals within configured authority';
 if(roles.includes('FINANCE_REVIEWER'))return 'Upload, source review and finance exceptions';
 if(roles.includes('EMPLOYEE'))return 'Employee expense submissions';
 if(roles.includes('ML_ADMIN')||roles.includes('ML_GOVERNANCE'))return 'Governed statistical intelligence';
 return 'Approvals within configured authority';
}
export function Login(){
 const [choices,setChoices]=useState<Choice[]|null>(null),[local,setLocal]=useState(false),[error,setError]=useState(''),[busy,setBusy]=useState('');
 const primary=(choice:Choice)=>['Synthetic finance workspace','Synthetic policy administrator'].includes(choice.label);
 useEffect(()=>{fetch('/api/development/session',{cache:'no-store'}).then(async r=>{if(!r.ok)throw new Error('Workspace access is unavailable. Ask your administrator to check the identity connection.');return r.json()}).then(d=>{setChoices(d.identities||[]);setLocal(d.development===true)}).catch(e=>setError(e.message))},[]);
 async function enter(choice:Choice){setBusy(choice.label);setError('');try{const r=await fetch('/api/development/session',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({label:choice.label})});if(!r.ok)throw new Error('This workspace could not be opened. Refresh the configured identities or contact an administrator.');window.location.assign(choice.roles.some(r=>administration.includes(r))&&!choice.roles.includes('FINANCE_REVIEWER')?'/admin':'/');}catch(e){setError((e as Error).message);setBusy('')}}
 const entry=(c:Choice)=><button className="identity-option secondary" key={c.label} disabled={!!busy} onClick={()=>void enter(c)}><strong>{busy===c.label?'Opening workspace…':workspaceIdentity(c.label)}</strong><span>{purpose(c.roles)}</span></button>;
 return <div className="access-shell"><a className="skip" href="#main">Skip to content</a><header className="landing-nav"><Link className="brand" href="/welcome"><span className="brand-mark" aria-hidden="true">{PRODUCT_NAME.slice(0,1).toLowerCase()}</span>{PRODUCT_NAME}</Link><Link href="/welcome">About {PRODUCT_NAME}</Link></header><main id="main"><section className="access-page"><div className="access-intro"><div className="access-monogram" aria-hidden="true">{PRODUCT_NAME.slice(0,1).toLowerCase()}</div><h1>Welcome to {PRODUCT_NAME}</h1><p>A little less paperwork.<br/>A lot more clarity.</p><p className="hint">Start in Finance to review a document. Open Admin to manage the rules and records behind each decision.</p></div><div className="access-options"><h2>{local?'Choose your workspace':'Sign in to your organization'}</h2>{error?<p className="error" role="alert">{error}</p>:null}{!choices&&!error?<p role="status">Loading configured access…</p>:local?<><p className="notice">Local sample company. These fictional identities use existing server-configured permissions. This is development access, not production sign-in.</p><div className="identity-options">{choices?.filter(primary).map(entry)}</div><details className="advanced"><summary>Other configured sample roles</summary><div className="identity-options">{choices?.filter(c=>!primary(c)&&!c.label.startsWith('Hackathon')).map(entry)}</div></details></>:choices?<><p>Use the identity provider configured by your organization. Your administrator controls workspace access and permissions.</p><a className="button" href="/.auth/login/aad?post_login_redirect_uri=/">Continue with Microsoft</a></>:null}</div></section><p className="workspace-limit">Access comes from the server. Choosing a workspace does not change your permissions or approve an invoice.</p></main></div>;
}
