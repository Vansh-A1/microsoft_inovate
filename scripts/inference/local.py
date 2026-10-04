#!/usr/bin/env python3
"""Manage only this repository's user-owned experimental inference processes."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
import signal
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'runtime/inference'
MODEL_SOURCE='Qwen/Qwen2.5-VL-3B-Instruct'
MODEL_REVISION='66285546d2b821cf421d4f5eb2576359d3770cd3'
MODEL_NAME='qwen25-vl3b-local'
CONFIG=RUNTIME/'gateway_config.json'
STATE=RUNTIME/'local-state.json'
WEIGHT_HASHES={
    'model-00001-of-00002.safetensors':'41a8895c164b4d32bae6b302f4603fcbc1797f32dafa45c7e9bcda23c6755df8',
    'model-00002-of-00002.safetensors':'365531ff8752420e89dee707b79d021fb2d6e25abafe486f080555a4fe6972e4',
}
MINIMUM_FREE_VRAM_MIB=13*1024


def verify_weights(model):
    for name,expected in WEIGHT_HASHES.items():
        path=model/name
        if path.is_symlink() or not path.is_file():raise SystemExit('Pinned model shard is missing or unsafe.')
        with path.open('rb') as stream:actual=hashlib.file_digest(stream,'sha256').hexdigest()
        if actual!=expected:raise SystemExit('Pinned model shard integrity mismatch.')


def available_memory():
    code="import torch;print(torch.cuda.mem_get_info()[0]//(1024*1024) if torch.cuda.is_available() else 0)"
    return int(subprocess.check_output([str(RUNTIME/'env/bin/python'),'-c',code],cwd=ROOT,text=True))


def private_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream,indent=2);stream.write('\n')
    path.chmod(0o600)


def config():
    python=RUNTIME/'env/bin/python';client=RUNTIME/'client/bin/python';model=RUNTIME/'models/qwen2.5-vl-3b'
    if not python.is_file() or not client.is_file() or not (model/'config.json').is_file():raise SystemExit('Provision the isolated pinned environments and model using the local-inference runbook.')
    verify_weights(model)
    code="import json,platform,torch;from importlib.metadata import version;print(json.dumps({'serving_python':platform.python_version(),'sglang':version('sglang'),'torch':torch.__version__,'cuda_runtime':str(torch.version.cuda),'serving_transformers':version('transformers'),'gpu_status':'AVAILABLE' if torch.cuda.is_available() else 'UNAVAILABLE'}))"
    metadata=json.loads(subprocess.check_output([str(python),'-c',code],cwd=ROOT,text=True))
    gpu=metadata.pop('gpu_status')
    serving_python=metadata.pop('serving_python')
    if gpu!='AVAILABLE':raise SystemExit('Experimental runtime cannot see the GPU.')
    code="import json,platform;from importlib.metadata import version;print(json.dumps({'python':platform.python_version(),'typellm':version('typellm'),'transformers':version('transformers')}))"
    metadata.update(json.loads(subprocess.check_output([str(client),'-c',code],cwd=ROOT,text=True)))
    serving_transformers=metadata.pop('serving_transformers')
    if serving_python!='3.12.3' or metadata['sglang']!='0.4.6.post5' or metadata['typellm']!='0.5.1' or metadata['torch']!='2.6.0+cu124' or metadata['cuda_runtime']!='12.4' or serving_transformers!='4.51.1' or metadata['transformers']!='5.3.0' or metadata['python']!='3.12.3':
        raise SystemExit('Accepted runtime pin mismatch; do not upgrade or substitute automatically.')
    key=RUNTIME/'gateway.key'
    if not key.exists():
        fd=os.open(key,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
        with os.fdopen(fd,'w') as stream:stream.write(secrets.token_urlsafe(48)+'\n')
    if key.stat().st_mode&0o077:raise SystemExit('Gateway key must have mode 0600.')
    metadata.update(served_model=MODEL_NAME,model_source=MODEL_SOURCE,model_revision=MODEL_REVISION,
        precision='BF16',bridge='sglang-cu124-transport-v1',cache_isolation='SERIAL_FLUSH_PER_GENERATE')
    value={'model_path':str(model),'served_model':MODEL_NAME,'sglang_endpoint':'http://127.0.0.1:30000',
        'gateway_port':30001,'token_file':str(key),'gpu_status':gpu,'provider_metadata':metadata}
    private_json(CONFIG,value)
    return value


def environment():
    env=dict(os.environ)
    for key,folder in {'HF_HOME':'cache/hf','XDG_CACHE_HOME':'cache','TORCH_EXTENSIONS_DIR':'cache/torch',
        'TRITON_CACHE_DIR':'cache/triton','FLASHINFER_WORKSPACE_BASE':'cache/flashinfer','TMPDIR':'tmp'}.items():
        path=RUNTIME/folder;path.mkdir(parents=True,exist_ok=True);env[key]=str(path)
    env.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TORCHDYNAMO_DISABLE='1')
    includes=['usr/include/python3.12','usr/include/x86_64-linux-gnu/python3.12','usr/include']
    env['CPATH']=':'.join(str(RUNTIME/'headers'/p) for p in includes)
    return env


def supervise():
    cfg=config();env=environment();children=[]
    def stop(*args):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,stop)
    try:
        args=[str(RUNTIME/'env/bin/python'),'-m','sglang.launch_server','--model-path',cfg['model_path'],
            '--tokenizer-path',cfg['model_path'],'--served-model-name',MODEL_NAME,'--host','127.0.0.1','--port','30000',
            '--dtype','bfloat16','--context-length','8192','--mem-fraction-static','0.75','--max-running-requests','8',
            '--attention-backend','torch_native','--sampling-backend','pytorch','--grammar-backend','xgrammar',
            '--mm-attention-backend','sdpa','--disable-cuda-graph','--chunked-prefill-size','-1','--log-level','warning']
        children.append(subprocess.Popen(args,cwd=ROOT,env=env,start_new_session=True))
        deadline=time.monotonic()+120
        while time.monotonic()<deadline:
            if children[0].poll() is not None:raise RuntimeError('Model server exited')
            try:
                if urllib.request.urlopen(cfg['sglang_endpoint']+'/health',timeout=2).status==200:break
            except Exception:time.sleep(.5)
        else:raise RuntimeError('Model startup timeout')
        children.append(subprocess.Popen([str(RUNTIME/'client/bin/python'),str(ROOT/'scripts/inference/typellm_gateway.py'),'--config',str(CONFIG)],cwd=ROOT,env=env,start_new_session=True))
        private_json(STATE,{'supervisor':os.getpid(),'children':[c.pid for c in children],'started_at_utc':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat()})
        while all(c.poll() is None for c in children):time.sleep(.5)
        raise RuntimeError('Inference process exited')
    except KeyboardInterrupt:pass
    finally:
        for child in children:
            if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
        for child in children:
            try:child.wait(timeout=10)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
        if STATE.exists() and json.loads(STATE.read_text()).get('supervisor')==os.getpid():STATE.unlink()


def owned_supervisor():
    if not STATE.exists():return None
    pid=json.loads(STATE.read_text())['supervisor'];cmd=Path(f'/proc/{pid}/cmdline')
    if not cmd.exists():return None
    parts=cmd.read_bytes().split(b'\0')
    if str(Path(__file__).resolve()).encode() not in parts or b'supervise' not in parts:raise SystemExit('State does not identify this launcher; refusing to signal it.')
    if cmd.stat().st_uid!=os.getuid():raise SystemExit('Process ownership mismatch.')
    return pid


def stop_owned():
    pid=owned_supervisor()
    if not pid:print('This inference supervisor is not running.');return
    os.kill(pid,signal.SIGTERM)
    deadline=time.monotonic()+35
    while time.monotonic()<deadline and owned_supervisor():time.sleep(.2)
    if owned_supervisor():raise SystemExit('Owned inference shutdown timed out; refusing unrelated process cleanup.')
    print('Owned inference stopped; model caches and private artifacts retained.')


def start_owned():
    if owned_supervisor():raise SystemExit('This inference launcher is already running.')
    config()
    if available_memory()<MINIMUM_FREE_VRAM_MIB:raise SystemExit('Insufficient free GPU memory for the frozen BF16 baseline; CPU application can run with --no-vlm.')
    log=RUNTIME/'logs/local-server.log';log.parent.mkdir(parents=True,exist_ok=True)
    with log.open('ab') as output:
        child=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'supervise'],cwd=ROOT,stdout=output,stderr=output,start_new_session=True)
    private_json(STATE,{'supervisor':child.pid,'children':[]})
    print('Pinned inference starting. Run the authenticated health command to verify readiness.')


def cleanup(confirmed):
    if not confirmed:raise SystemExit('Cleanup requires --confirm-remove-runtime and deletes only runtime/inference. Back up private reports first.')
    if owned_supervisor():raise SystemExit('Stop inference before cleanup.')
    for path in Path('/proc').glob('[0-9]*/cmdline'):
        try:
            argv=path.read_bytes().split(b'\0')
            if str(ROOT/'scripts/dev/run.py').encode() in argv or str(ROOT/'scripts/demo.py').encode() in argv:
                raise SystemExit('Stop the owned application/demo before cleanup.')
        except (FileNotFoundError,PermissionError):pass
    if RUNTIME.is_symlink() or RUNTIME.resolve()!=ROOT/'runtime/inference':raise SystemExit('Unsafe runtime location; refusing cleanup.')
    shutil.rmtree(RUNTIME)
    print('Experimental inference runtime removed. Finance database, evidence and .venv preserved.')


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['configure','start','supervise','health','stop','restart','cleanup','app'])
    parser.add_argument('--confirm-remove-runtime',action='store_true')
    args=parser.parse_args()
    if args.action=='configure':
        cfg=config();settings=ROOT/'runtime/dev/settings.json';data=json.loads(settings.read_text())
        data['document_providers'].update(endpoint=f'http://127.0.0.1:{cfg["gateway_port"]}',model=MODEL_NAME,
            transport='TYPELLM_GATEWAY',timeout_seconds=120,model_revision=MODEL_REVISION)
        private_json(settings,data)
        print('Development document provider configured. Restart the app using the app command. No credentials printed.')
    elif args.action=='supervise':supervise()
    elif args.action=='start':start_owned()
    elif args.action=='stop':stop_owned()
    elif args.action=='restart':stop_owned();start_owned()
    elif args.action=='cleanup':cleanup(args.confirm_remove_runtime)
    elif args.action=='health':
        cfg=json.loads(CONFIG.read_text());key=Path(cfg['token_file']).read_text().strip()
        request=urllib.request.Request(f'http://127.0.0.1:{cfg["gateway_port"]}/health',headers={'Authorization':'Bearer '+key})
        try:
            with urllib.request.urlopen(request,timeout=4) as response:print(response.read().decode())
        except Exception:raise SystemExit('Inference gateway unavailable.') from None
    else:
        cfg=json.loads(CONFIG.read_text());env=dict(os.environ)
        env['AP_TYPELLM_GATEWAY_TOKEN']=Path(cfg['token_file']).read_text().strip()
        os.execve(str(ROOT/'.venv/bin/python'),[str(ROOT/'.venv/bin/python'),str(ROOT/'scripts/dev/run.py')],env)


if __name__=='__main__':main()
