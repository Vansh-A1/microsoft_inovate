import { NextRequest } from 'next/server';
export const dynamic = 'force-dynamic';
async function proxy(request:NextRequest,context:{params:Promise<{path:string[]}>}) {
  const {path}=await context.params;
  if(path.some(part=>!/^[-a-zA-Z0-9_]+$/.test(part)))return Response.json({error:{message:'Invalid API path'}},{status:400});
  const origin=process.env.AP_API_ORIGIN;
  const token=process.env.AP_DEV_TOKEN;
  if(!origin||!token)return Response.json({error:{message:'Development API connection is not configured.'}},{status:503});
  const allowedOrigins=new Set(['http://127.0.0.1:3000','http://localhost:3000']);
  const host=request.headers.get('host')||'';
  const requestOrigin=request.headers.get('origin');
  if(!allowedOrigins.has('http://'+host) || (request.method!=='GET' && (!requestOrigin || !allowedOrigins.has(requestOrigin) || new URL(requestOrigin).host!==host)))
    return Response.json({error:{message:'Same-origin request required.'}},{status:403});
  let body:ArrayBuffer|undefined;
  const binaryOriginal=path.length===3&&path[0]==='uploads'&&path[2]==='bytes';
  const documentMaximum=Number(process.env.AP_DOCUMENT_MAXIMUM_BYTES||25*1024*1024);
  if(!Number.isSafeInteger(documentMaximum)||documentMaximum<1)return Response.json({error:{message:'Document limit configuration is invalid.'}},{status:503});
  const maximum=binaryOriginal?documentMaximum:2300000;
  if(request.method!=='GET'){
    const reader=request.body?.getReader();const chunks:Uint8Array[]=[];let length=0;
    if(reader){while(true){const chunk=await reader.read();if(chunk.done)break;length+=chunk.value.byteLength;if(length>maximum){await reader.cancel();return Response.json({error:{message:'Request exceeds the configured intake limit.'}},{status:413});}chunks.push(chunk.value);}}
    body=new ArrayBuffer(length);const bytes=new Uint8Array(body);let offset=0;for(const chunk of chunks){bytes.set(chunk,offset);offset+=chunk.length;}
  }
  const headers=new Headers({Authorization:`Bearer ${token}`});
  for(const name of ['content-type','idempotency-key']){const v=request.headers.get(name);if(v)headers.set(name,v);}
  try{
    const response=await fetch(`${origin}/api/v1/${path.join('/')}${request.nextUrl.search}`,{method:request.method,headers,body,cache:'no-store',signal:AbortSignal.timeout(15000)});
    const resultHeaders=new Headers({'Content-Type':response.headers.get('content-type')||'application/json','Cache-Control':'no-store'});
    for(const name of ['x-correlation-id','content-security-policy','content-disposition','x-content-type-options']){const v=response.headers.get(name);if(v)resultHeaders.set(name,v);}
    return new Response(await response.arrayBuffer(),{status:response.status,headers:resultHeaders});
  }catch{return Response.json({error:{code:'API_UNAVAILABLE',message:'API connection unavailable. Start the API and try again.'}},{status:503});}
}
export const GET=proxy;export const POST=proxy;
