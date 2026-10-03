import {NextRequest} from 'next/server';
import {configuredIdentities} from '@/lib/development-identity';
export const dynamic='force-dynamic';
export async function GET(){
 if(process.env.AP_ENVIRONMENT==='enterprise'||process.env.AP_ENABLE_DEMO_IDENTITIES!=='1')return Response.json({identities:[],development:false});
 try{return Response.json({development:true,identities:(await configuredIdentities()).map(({label,actor_id,roles})=>({label,actor_id,roles}))},{headers:{'Cache-Control':'no-store'}});}
 catch{return Response.json({error:{message:'Configured development identities are unavailable.'}},{status:503});}
}
export async function POST(request:NextRequest){
 if(process.env.AP_ENVIRONMENT==='enterprise'||process.env.AP_ENABLE_DEMO_IDENTITIES!=='1')return Response.json({error:{message:'Demo identity selection is disabled.'}},{status:403});
 const host=request.headers.get('host');const origin=request.headers.get('origin');
 if(!origin||!['http://127.0.0.1:3000','http://localhost:3000'].includes(origin)||new URL(origin).host!==host)return Response.json({error:{message:'Same-origin request required.'}},{status:403});
 const body=await request.json() as Record<string,unknown>;
 if(Object.keys(body).some(k=>k!=='label')||typeof body.label!=='string')return Response.json({error:{message:'Select one configured demo identity.'}},{status:422});
 const identities=await configuredIdentities();const selected=identities.find(i=>i.label===body.label);
 if(!selected)return Response.json({error:{message:'This identity is not configured.'}},{status:403});
 const response=Response.json({label:selected.label,development:true});
 response.headers.append('Set-Cookie',`ap-demo-identity=${encodeURIComponent(selected.label)}; HttpOnly; SameSite=Strict; Path=/; Max-Age=3600`);
 return response;
}
