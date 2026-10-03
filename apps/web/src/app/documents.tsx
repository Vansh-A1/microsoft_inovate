'use client';
import Link from 'next/link';
import {useEffect,useState} from 'react';
import {useRouter} from 'next/navigation';
import {api,mutate,type Canonical} from '@/lib/api';

type Box={x1:number;y1:number;x2:number;y2:number};
type Source={page:number|null;bbox:Box|null;document_id:string};
type Observation={id:string;field_path:string;state:string;raw_value:string|null;source:Source|null;diagnostic:string|null};
type Document={id:string;display_name:string;source_type:string;state:string;last_error:string|null;segmentation_state:string;
 pages:{page:number;preview_url:string;transform:{exif_orientation?:number};route:string;quality:Record<string,number>}[];
 observations:Observation[];draft:{id:string;candidate:Record<string,string|null>;findings:{field:string;code:string}[];traces:unknown[]}|null;
 original:{sha256:string;byte_size:number;detected_mime:string}|null;
 jobs:{stage:string;state:string;attempts:number;metadata:unknown}[];
 extraction_runs:{adapter:string;metadata:unknown;status:string}[]};
export type DocumentDetail=Document;
type DocList={id:string;display_name:string;source_type:string;state:string;last_error:string|null};
export type DocumentEvidence={document:Document;reference:Source;source_image_available:boolean};
const working=new Set(['QUEUED','PROCESSING','FAILED_RETRYABLE']);

function derivedBox(box:Box,orientation:number):Box {
 const point=(u:number,v:number):number[]=>({1:[u,v],2:[1-u,v],3:[1-u,1-v],4:[u,1-v],5:[v,u],6:[1-v,u],7:[1-v,1-u],8:[v,1-u]}[orientation]||[u,v]);
 const points=[point(box.x1,box.y1),point(box.x1,box.y2),point(box.x2,box.y1),point(box.x2,box.y2)];
 return {x1:Math.min(...points.map(p=>p[0])),y1:Math.min(...points.map(p=>p[1])),x2:Math.max(...points.map(p=>p[0])),y2:Math.max(...points.map(p=>p[1]))};
}

export function SourceViewer({document,source}:{document:Document;source?:Source|null}) {
 const [page,setPage]=useState(source?.page||1);
 const [zoom,setZoom]=useState(100);
 useEffect(()=>{if(source?.page)setPage(source.page)},[source]);
 const p=document.pages.find(p=>p.page===page);const bbox=source?.page===page&&source.bbox?derivedBox(source.bbox,p?.transform.exif_orientation||1):null;
 return <section className="panel source-viewer" aria-label="Document source viewer"><div className="section-title"><h2>Original source page</h2><label>Source page<select value={page} onChange={e=>setPage(Number(e.target.value))}>{document.pages.map(p=><option key={p.page} value={p.page}>Page {p.page}</option>)}</select></label></div>
 {p?<><label className="source-zoom">Preview zoom<select aria-label="Preview zoom" value={zoom} onChange={e=>setZoom(Number(e.target.value))}>{[100,150,200,300].map(value=><option key={value} value={value}>{value}%</option>)}</select></label><div className="source-scroll" tabIndex={0} aria-label="Scrollable source preview"><div className="page-preview" style={{width:`${zoom}%`}}><img src={p.preview_url.replace('/api/v1/','/api/')} alt={`${document.display_name}, page ${page}`} />{bbox?<span className="source-box" aria-label="Actual source bounding box" style={{left:`${bbox.x1*100}%`,top:`${bbox.y1*100}%`,width:`${(bbox.x2-bbox.x1)*100}%`,height:`${(bbox.y2-bbox.y1)*100}%`}}/>:null}</div></div><p className="hint">{bbox?'Highlighted measured text region.':'Page-level evidence. No field box is available.'} The preserved original is unchanged.</p></>:<p className="empty">No safely rendered page available.</p>}
 {document.original&&document.pages.length&&document.state!=='QUARANTINED'?<a href={`/api/documents/${document.id}/original`} download>Download preserved original</a>:null}</section>
}

export function Documents({id}:{id?:string}) {
 const router=useRouter();const [items,setItems]=useState<DocList[]|null>(null),[document,setDocument]=useState<Document|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
 const [files,setFiles]=useState<File[]>([]),[kind,setKind]=useState('VENDOR_INVOICE'),[source,setSource]=useState<Source|null>(null);
 const [edits,setEdits]=useState<Record<string,{value:string;page:number}>>({}),[reason,setReason]=useState(''),[confirmed,setConfirmed]=useState(false),[canonical,setCanonical]=useState(''),[existing,setExisting]=useState(''),[version,setVersion]=useState(1);
 useEffect(()=>{let active=true;let timer:ReturnType<typeof setTimeout>;
  async function load(){try{if(id){const d=await api<Document>('documents/'+id);if(active){setDocument(d);if(working.has(d.state))timer=setTimeout(load,900)}}else{const r=await api<{items:DocList[]}>('documents');if(active)setItems(r.items)}}catch(e){if(active)setError((e as Error).message)}}
  void load();return()=>{active=false;clearTimeout(timer)};
 },[id]);
 useEffect(()=>{if(!document?.draft)return;const branch=document.source_type==='EMPLOYEE_RECEIPT'?'employee':'vendor';
  const caseId=new URLSearchParams(window.location.search).get('case');
  if(caseId){void api<{version:number;versions:{payload:Canonical}[]}>('transactions/'+caseId).then(record=>{
   setExisting(caseId);setVersion(record.version);setCanonical(JSON.stringify(record.versions.at(-1)!.payload,null,2));
  }).catch(e=>setError((e as Error).message));return;}
  api<Canonical>('development/templates/'+branch).then(template=>{
   const candidate=document.draft!.candidate;const p={...template};
   if(branch==='vendor'){for(const k of ['invoice_number','invoice_date','currency','total_amount','subtotal_amount','tax_amount','document_discount_amount','shipping_amount','other_charges_amount','tax_basis'] as const){if(k in candidate)(p as Record<string,unknown>)[k]=candidate[k]}p.source_document_id=document.id;
    const indices=[...new Set(Object.keys(candidate).filter(k=>k.startsWith('lines.')).map(k=>k.split('.')[1]))];p.lines=indices.map((i,n)=>({...template.lines?.[Math.min(n,(template.lines?.length||1)-1)],...Object.fromEntries(Object.entries(candidate).filter(([k])=>k.startsWith(`lines.${i}.`)&&!k.endsWith('.description')).map(([k,v])=>[k.split('.').at(-1)!,v])),currency:candidate.currency}));
   }else{p.expense_date=candidate.expense_date;p.currency=candidate.currency;p.requested_amount=candidate.total_amount;p.items=[{...template.items?.[0],source_document_id:document.id,expense_date:candidate.expense_date,currency:candidate.currency,category:candidate.category,local_timezone:candidate.local_timezone,receipt_total_amount:candidate.total_amount,claimed_amount:candidate.total_amount}];}
   setCanonical(JSON.stringify(p,null,2));
  }).catch(e=>setError((e as Error).message));
 },[document?.draft?.id]);
 async function upload(){setBusy(true);setError('');try{
  let last='';for(const file of files){const key=crypto.randomUUID();const mime=file.type||(/\.pdf$/i.test(file.name)?'application/pdf':/\.png$/i.test(file.name)?'image/png':'image/jpeg');
   const s=await mutate<{id:string;document_id:string;bytes_url:string;maximum_bytes:number}>('uploads',{filename:file.name,mime,source_type:kind},key);
   if(file.size>s.maximum_bytes)throw new Error(`Document exceeds the configured ${s.maximum_bytes} byte limit.`);
   const stored=await api<{error?:string}>(s.bytes_url.replace('/api/v1/',''),{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file});
   if(stored.error)throw new Error(stored.error);
   await mutate('uploads/'+s.id+'/finalize',{},key+'-finalize');last=s.document_id;
  }router.push('/documents/'+last);
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 async function commit(){if(!document?.draft)return;setBusy(true);setError('');try{
  const body={draft_id:document.draft.id,transaction:JSON.parse(canonical),source_confirmed:confirmed,reason,
   corrections:Object.entries(edits).map(([field_path,e])=>({field_path,value:e.value,page:e.page,reason})),
   ...(existing?{transaction_id:existing,expected_version:version}:{})};
  const result=await mutate<{id:string}>('documents/'+document.id+'/commit',body,crypto.randomUUID());router.push('/cases/'+result.id);
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 if(!id)return <><div className="page-title"><div><p className="eyebrow">DOCUMENT INTAKE</p><h1>Documents</h1><p>Preserved originals, extracted observations, and source verification.</p></div></div>{error?<div role="alert" className="error">{error}</div>:null}<section className="panel"><h2>Upload documents</h2><p className="hint">PDF, PNG or JPEG. Initial limits: 25 MiB, 30 PDF pages, 40 megapixels. Malware scanning is NOT_CONFIGURED in local development. Source facts need human verification.</p><label>Document purpose<select value={kind} onChange={e=>setKind(e.target.value)}><option value="VENDOR_INVOICE">Vendor invoice</option><option value="EMPLOYEE_RECEIPT">Employee receipt</option><option value="SUPPORTING_DOCUMENT">Supporting document / PO</option></select></label><label>Document files<input type="file" accept=".pdf,.png,.jpg,.jpeg" multiple onChange={e=>setFiles(Array.from(e.target.files||[]))}/></label><button onClick={upload} disabled={busy||!files.length}>{busy?'Storing originals…':'Upload and process'}</button></section><section className="panel"><h2>Recent documents</h2>{items?<div className="table-wrap"><table><thead><tr><th>Source</th><th>Purpose</th><th>Processing</th></tr></thead><tbody>{items.map(d=><tr key={d.id}><td><Link href={'/documents/'+d.id}>{d.display_name}</Link></td><td>{d.source_type}</td><td>{d.state}<small>{d.last_error}</small></td></tr>)}</tbody></table>{!items.length?<p className="empty">No uploaded documents yet.</p>:null}</div>:<p role="status">Loading documents…</p>}</section></>;
 if(!document)return <p role="status">{error||'Loading source document…'}</p>;
 return <><Link href="/documents" className="back">← Documents</Link><div className="page-title"><div><p className="eyebrow">PRESERVED SOURCE</p><h1>{document.display_name}</h1><p>{document.state} · {document.source_type}</p></div></div>{error?<div role="alert" className="error">{error}</div>:null}
 {working.has(document.state)?<div role="status" className="notice">Processing document stages. This view updates automatically.</div>:null}
 {document.last_error?<div role="status" className="error">{document.last_error}. No finance decision has been made for this file.</div>:null}
 <div className="document-grid"><SourceViewer document={document} source={source}/><section className="panel"><h2>Source observations</h2><p className="hint">EXTRACTED text stays immutable. NORMALIZED values are candidates. HUMAN_CORRECTED values create a new canonical version with your reason.</p>
 {document.draft?.findings.length?<div className="notice">Needs input: {document.draft.findings.map(f=>`${f.field}: ${f.code}`).join('; ')}</div>:null}
 {document.observations.length?<div className="table-wrap"><table className="observation-table"><thead><tr><th>Field / state</th><th>EXTRACTED</th><th>NORMALIZED</th><th>HUMAN_CORRECTED</th></tr></thead><tbody>{document.observations.map(o=><tr key={o.id}><td><button className="evidence" onClick={()=>setSource(o.source)}>{o.field_path}</button><small>{o.state} · {o.source?.page?`page ${o.source.page}`:'source unknown'}</small></td><td>{o.raw_value??'UNKNOWN'}</td><td>{document.draft?.candidate[o.field_path]??'UNKNOWN'}</td><td><input aria-label={'Correct '+o.field_path} value={edits[o.field_path]?.value??''} placeholder="Leave unchanged" onChange={e=>setEdits(previous=>{const next={...previous};if(e.target.value)next[o.field_path]={value:e.target.value,page:previous[o.field_path]?.page||o.source?.page||1};else delete next[o.field_path];return next})}/>{edits[o.field_path]?<label>Correction source page<select value={edits[o.field_path].page} onChange={e=>setEdits(p=>({...p,[o.field_path]:{...p[o.field_path],page:Number(e.target.value)}}))}>{document.pages.map(p=><option key={p.page}>{p.page}</option>)}</select></label>:null}</td></tr>)}</tbody></table></div>:<p className="empty">No extraction observations are available. Resolve the displayed provider or safety status.</p>}
 <details><summary>Processing, provider and source metadata</summary><pre>{JSON.stringify({original:document.original,jobs:document.jobs,providers:document.extraction_runs,pages:document.pages},null,2)}</pre></details></section></div>
 {document.draft&&document.source_type!=='SUPPORTING_DOCUMENT'?<section className="panel"><h2>Verify source and create canonical version</h2><p>Choose master/reference IDs and map each extracted line. The editable synthetic example supplies reference choices; verify them. The server applies verified source amounts and dates, then runs the existing finance controls. New submissions have no approval chain.</p><label>Verification / correction reason<input value={reason} onChange={e=>setReason(e.target.value)} minLength={3}/></label><label className="check-label"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>I reviewed the source pages and confirm the observable facts.</label><details><summary>Canonical draft and reference mapping</summary><label>Document canonical JSON<textarea value={canonical} onChange={e=>setCanonical(e.target.value)} rows={20}/></label></details><details><summary>Append a source-linked revision to an existing case</summary><label>Existing transaction UUID<input value={existing} onChange={e=>setExisting(e.target.value)}/></label><label>Expected current version<input type="number" min={1} value={version} onChange={e=>setVersion(Number(e.target.value))}/></label><p className="hint">Use the current case facts above to retain its other receipt items. Historical evaluations remain unchanged.</p></details><button onClick={commit} disabled={busy||working.has(document.state)||!confirmed||reason.length<3||document.segmentation_state==='UNCERTAIN'}>{busy?'Saving verified version…':'Verify facts and evaluate'}</button></section>:null}</>;
}

export function CaseSources({id}:{id:string}) {
 const [data,setData]=useState<{transaction_version:number;documents:{role:string;verified:boolean;document:Document}[];corrections:unknown[]}|null>(null),[error,setError]=useState('');
 const [available,setAvailable]=useState<DocList[]>([]),[selected,setSelected]=useState(''),[role,setRole]=useState('SUPPORT'),[item,setItem]=useState(0),[reason,setReason]=useState(''),[busy,setBusy]=useState(false);
 useEffect(()=>{api<typeof data>('transactions/'+id+'/sources').then(setData).catch(e=>setError(e.message));api<{items:DocList[]}>('documents').then(r=>setAvailable(r.items.filter(d=>['READY','NEEDS_INPUT','DEPENDENCY_UNAVAILABLE'].includes(d.state)))).catch(()=>{})},[id]);
 async function attach(){if(!data)return;setBusy(true);setError('');try{
  await mutate('transactions/'+id+'/attachments',{expected_version:data.transaction_version,document_id:selected,role,reason,...role==='RECEIPT'?{item_index:item}:{}},crypto.randomUUID());window.location.reload();
 }catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 return <section className="panel"><h2>Document lineage & attachments</h2><p className="hint">CANONICAL values are screened against HUMAN_VERIFIED source facts and MASTER/REFERENCE records. Raw extraction remains separate. A receipt needs an actual document link and source verification.</p>{error?<p role="alert" className="error">{error}</p>:null}
 {data?.documents.map(link=><p key={link.document.id}><Link href={'/documents/'+link.document.id}>{link.document.display_name}</Link> · {link.role} · {link.verified?'HUMAN_VERIFIED':'UNVERIFIED'} <Link href={'/documents/'+link.document.id+'?case='+id}>View source / append correction →</Link></p>)}
 {data?.corrections.length?<details><summary>HUMAN_CORRECTED history</summary><pre>{JSON.stringify(data.corrections,null,2)}</pre></details>:null}
 <details><summary>Attach another document</summary><label>Stored document<select value={selected} onChange={e=>setSelected(e.target.value)}><option value="">Choose a stored document</option>{available.map(d=><option key={d.id} value={d.id}>{d.display_name} · {d.id.slice(-8)}</option>)}</select></label><label>Attachment role<select value={role} onChange={e=>setRole(e.target.value)}><option>SUPPORT</option><option>PO</option><option>RECEIPT</option><option>INVOICE</option></select></label>{role==='RECEIPT'?<label>Expense item index (first item = 0)<input type="number" min={0} max={199} value={item} onChange={e=>setItem(Number(e.target.value))}/></label>:null}<label>Attachment reason<input value={reason} onChange={e=>setReason(e.target.value)}/></label><button onClick={attach} disabled={busy||!selected||reason.length<3}>Append version with attachment</button><p className="hint">Attachment creates a version; evaluate it again. Unverified source facts cannot clear the source control.</p></details></section>;
}
