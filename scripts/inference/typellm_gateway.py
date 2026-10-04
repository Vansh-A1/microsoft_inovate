"""Authenticated, serial TypeLLM 0.5.1 bridge for the isolated CUDA-12 server.

No GPU packages in the finance application. No document/prompt/reasoning logs.
This gateway uses the real TypeLLM compiler and candidate scoring; the legacy
bridge adapts transport differences only. It never supplies extracted answers.
"""
from dataclasses import dataclass
import base64
import hmac
from io import BytesIO
import json
from pathlib import Path
import re
import threading
import time
from typing import Any
import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


class Generate(BaseModel):
    model_config=ConfigDict(extra='forbid')
    model:str=Field(min_length=1,max_length=200)
    context:str=Field(max_length=32000)
    questions:dict[str,dict[str,Any]]=Field(min_length=1,max_length=64)
    images:list[str]|None=Field(default=None,max_length=1)
    timeout:float=Field(ge=1,le=120)


def legacy_payload(payload):
    """0.4.6 has no sampling_seed. Greedy decoding makes it unnecessary."""
    payload=dict(payload);params=payload.get('sampling_params')
    rows=params if isinstance(params,list) else [params] if isinstance(params,dict) else []
    cleaned=[]
    for row in rows:
        row=dict(row)
        if 'sampling_seed' in row:
            if row.get('temperature',0)!=0:raise ValueError('Legacy bridge requires greedy decoding')
            row.pop('sampling_seed')
        cleaned.append(row)
    if rows:payload['sampling_params']=cleaned if isinstance(params,list) else cleaned[0]
    return payload


def single_payloads(payload):
    """Avoid the legacy multimodal batch completion-before-wait race.

    Preserve every actual prompt, grammar and candidate logprob request. The
    returned list remains the TypeLLM native batch shape, in original order.
    """
    if not isinstance(payload.get('text'),list):return [payload],False
    out=[]
    for i,text in enumerate(payload['text']):
        item={**payload,'text':text}
        if isinstance(payload.get('sampling_params'),list):item['sampling_params']=payload['sampling_params'][i]
        ids=payload.get('token_ids_logprob')
        if isinstance(ids,list) and ids and isinstance(ids[0],list):item['token_ids_logprob']=ids[i]
        out.append(item)
    return out,True


def real_client(config):
    from importlib.metadata import version
    if version('typellm')!='0.5.1':raise ValueError('Pinned TypeLLM required')
    from typellm import TypeLLMClient
    from typellm.sglang import SGLangClient
    from transformers import AutoTokenizer
    class Cuda12Client(SGLangClient):
        def single_token(self,label):
            # Legacy SGLang lacks /v1/tokenize. The very same pinned tokenizer
            # is provisioned locally, with no remote code/downloads.
            tok=self._get_chat_tokenizer();ids=tok.encode(label,add_special_tokens=False)
            if len(ids)!=1 or tok.decode(ids)!=label:raise ValueError('Labels must be exact single tokens')
            return ids[0],label
        def _generate(self,payload):
            payloads,batch=single_payloads(legacy_payload(payload))
            responses=[super(Cuda12Client,self)._generate(p) for p in payloads]
            return responses if batch else responses[0]
    path=Path(config['model_path']).resolve()
    client=TypeLLMClient(config['sglang_endpoint'],model=config['served_model'],tokenizer=str(path),
        timeout=120,max_retries=0,text_max_tokens=128,seed=0,temperature=0)
    client.sglang=Cuda12Client(config['sglang_endpoint'],config['served_model'],120,tokenizer=str(path),text_max_tokens=128)
    client.sglang._chat_tokenizer=AutoTokenizer.from_pretrained(path,local_files_only=True,trust_remote_code=False)
    return client


def validate_questions(questions):
    from_names={}
    for key,value in questions.items():
        if not re.fullmatch(r'[a-z][a-z0-9_]{0,79}',key) or any(x in key for x in ('decision','approved','reimbursable','budget_valid')):raise HTTPException(422,'INVALID_OBSERVABLE_FIELD')
        allowed={'type','enum','instructions','thinking','depends_on'}
        if set(value)-allowed or value.get('thinking') is not False:raise HTTPException(422,'INVALID_QUESTION_SCHEMA')
        if value.get('type') not in ('string',['string','null']):raise HTTPException(422,'STRING_OBSERVATIONS_REQUIRED')
        if not isinstance(value.get('instructions'),str) or len(value['instructions'])>3000:raise HTTPException(422,'INVALID_INSTRUCTIONS')
        if 'enum' in value and value['enum']!=['PRESENT','MISSING','ILLEGIBLE','AMBIGUOUS','NOT_APPLICABLE']:raise HTTPException(422,'INVALID_OBSERVATION_STATES')
        depends=value.get('depends_on',[])
        if not isinstance(depends,list) or any(d not in questions for d in depends):raise HTTPException(422,'INVALID_DEPENDENCIES')
        # "vendor_name_state" invites US-state names on small VLMs. Use an
        # unambiguous provider-only name; retain the application wire contract.
        from_names[key.replace('_state','_observation_status')]=key
    if len(from_names)!=len(questions):raise HTTPException(422,'DUPLICATE_OBSERVABLE_FIELD')
    return from_names


def validate_images(images):
    from PIL import Image
    for image in images or []:
        if not image.startswith('data:image/png;base64,') or len(image)>16*1024*1024:raise HTTPException(422,'BOUNDED_PNG_REQUIRED')
        try:
            data=base64.b64decode(image.split(',',1)[1],validate=True)
            with Image.open(BytesIO(data)) as decoded:
                if decoded.format!='PNG' or decoded.width*decoded.height>9_000_000 or max(decoded.size)>3000:raise ValueError()
                decoded.verify()
        except Exception:raise HTTPException(422,'INVALID_IMAGE') from None


def create_app(config,token,client=None,backend=None):
    app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
    lock=threading.Lock();client=client or real_client(config)
    backend=backend or httpx.Client(base_url=config['sglang_endpoint'],timeout=3,follow_redirects=False)
    poisoned=False
    metadata=config['provider_metadata']

    @app.middleware('http')
    async def guard(request:Request,call_next):
        if not hmac.compare_digest(request.headers.get('authorization',''),'Bearer '+token):return JSONResponse({'detail':'UNAUTHORIZED'},status_code=401)
        if len(await request.body())>20*1024*1024:return JSONResponse({'detail':'REQUEST_TOO_LARGE'},status_code=413)
        return await call_next(request)

    def flush():
        response=backend.get('/flush_cache')
        if response.status_code!=200 or not response.text.startswith('Cache flushed.'):raise RuntimeError('CACHE_ISOLATION_UNAVAILABLE')

    @app.get('/health')
    def health():
        try:
            if poisoned:raise RuntimeError()
            backend.get('/health').raise_for_status()
            model=backend.get('/get_model_info').json()
            if str(Path(model['model_path']).resolve())!=str(Path(config['model_path']).resolve()):raise RuntimeError()
            return {'status':'AVAILABLE','served_model':config['served_model'],'model_source':metadata['model_source'],
                'model_revision':metadata['model_revision'],'precision':metadata['precision'],'gpu':config['gpu_status']}
        except Exception:return JSONResponse({'status':'UNAVAILABLE'},status_code=503)

    @app.post('/generate')
    def generate(data:Generate):
        nonlocal poisoned
        if data.model!=config['served_model']:raise HTTPException(422,'MODEL_MISMATCH')
        names=validate_questions(data.questions);validate_images(data.images)
        start=time.monotonic()
        if not lock.acquire(timeout=data.timeout):raise HTTPException(504,'PROVIDER_TIMEOUT')
        try:
            if poisoned:raise HTTPException(503,'CACHE_ISOLATION_UNAVAILABLE')
            flush()
            mapped={new:{**data.questions[old],**({'depends_on':[d.replace('_state','_observation_status') for d in data.questions[old]['depends_on']]} if 'depends_on' in data.questions[old] else {})} for new,old in names.items()}
            remaining=data.timeout-(time.monotonic()-start)
            if remaining<=0:raise HTTPException(504,'PROVIDER_TIMEOUT')
            try:
                response=client.generate(context=data.context,questions=mapped,images=data.images,timeout=remaining,seed=0,temperature=0)
                result={names[k]:v for k,v in response.result.items()}
                if set(result)!=set(data.questions) or any(v is not None and not isinstance(v,str) for v in result.values()):raise ValueError()
                return {'result':result,'provider_metadata':metadata}
            except Exception:raise HTTPException(503,'PROVIDER_GENERATION_FAILED') from None
            finally:
                # Fail closed if a timeout left work running in the legacy
                # server. A subsequent tenant cannot reuse that cache.
                try:flush()
                except Exception:poisoned=True
        except HTTPException:raise
        except Exception:
            poisoned=True
            raise HTTPException(503,'CACHE_ISOLATION_UNAVAILABLE') from None
        finally:lock.release()
    return app


def main():
    import argparse,os,uvicorn
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True)
    args=parser.parse_args();config=json.loads(args.config.read_text())
    key=Path(config['token_file'])
    if key.stat().st_mode & 0o077:raise ValueError('Gateway token file must be private')
    token=key.read_text().strip()
    if len(token)<32:raise ValueError('Gateway token required')
    os.umask(0o077)
    uvicorn.run(create_app(config,token),host='127.0.0.1',port=config['gateway_port'],access_log=False,log_level='warning')


if __name__=='__main__':main()
