#!/usr/bin/env python3
"""Owned local demo lifecycle. No Docker, downloads, migrations or hidden fallback."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'apps/api'))
RUNTIME=ROOT/'runtime/demo'
STATE=RUNTIME/'state.json'
PYTHON=ROOT/'.venv/bin/python'
INFERENCE=ROOT/'scripts/inference/local.py'


def private_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    temp=path.with_name(path.name+'.'+uuid4().hex)
    fd=os.open(temp,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as stream:json.dump(value,stream)
    os.replace(temp,path)


def process_identity(pid,script,action=None):
    """Refuse stale/reused/unrelated process state rather than signaling blindly."""
    folder=Path('/proc')/str(pid)
    try:
        if folder.stat().st_uid!=os.getuid():raise RuntimeError('Process ownership mismatch')
        stat=(folder/'stat').read_text().rsplit(')',1)[1].split()
        if stat[0]=='Z':return None
        argv=(folder/'cmdline').read_bytes().split(b'\0')
        if str(script.resolve()).encode() not in argv or action and action.encode() not in argv:
            raise RuntimeError('Process command mismatch')
        return {'pid':pid,'start_ticks':stat[19]}
    except FileNotFoundError:return None


def owned():
    if not STATE.exists():return None
    if STATE.is_symlink() or STATE.stat().st_mode&0o077:raise RuntimeError('Demo state must be private')
    try:
        state=json.loads(STATE.read_text())
        if not isinstance(state['pid'],int) or state['pid']<=0 or not isinstance(state['process'],dict):raise ValueError()
    except (ValueError,KeyError,TypeError):raise RuntimeError('Demo state is malformed; refusing to signal any process') from None
    actual=process_identity(state['pid'],Path(__file__),'supervise')
    if actual is None:return None
    if actual!=state['process']:raise RuntimeError('Demo PID was reused; refusing to signal it')
    return state


def fetch(url,headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url,headers=headers or {}),timeout=3) as response:
            return json.load(response) if response.status==200 else {}
    except Exception:return {}


def inference_health():
    config=ROOT/'runtime/inference/gateway_config.json'
    try:
        cfg=json.loads(config.read_text());key=Path(cfg['token_file'])
        if key.stat().st_mode&0o077:return {'status':'UNAVAILABLE'}
        h=fetch(f'http://127.0.0.1:{cfg["gateway_port"]}/health',{'Authorization':'Bearer '+key.read_text().strip()})
        from importlib.util import spec_from_file_location,module_from_spec
        spec=spec_from_file_location('demo_inference',INFERENCE);module=module_from_spec(spec);spec.loader.exec_module(module)
        if h.get('status')=='AVAILABLE' and h.get('served_model')==module.MODEL_NAME and h.get('model_revision')==module.MODEL_REVISION and h.get('precision')=='BF16' and h.get('gpu')=='AVAILABLE':
            return {k:h[k] for k in ('status','model_source','model_revision','precision','gpu')}
    except Exception:pass
    return {'status':'PROVIDER_UNAVAILABLE'}


def prerequisite_database():
    from app.core.config import Settings
    from sqlalchemy import create_engine,text
    from sqlalchemy.engine import make_url
    settings=Settings.load()
    if not settings.development:raise RuntimeError('Demo lifecycle requires development configuration')
    url=make_url(settings.database_url)
    def check():
        engine=create_engine(settings.database_url,connect_args={'connect_timeout':3})
        try:
            with engine.connect() as conn:
                if conn.execute(text('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user')).one()!=(False,False):
                    raise RuntimeError('Application database role must not bypass isolation')
                if conn.execute(text('SELECT version_num FROM alembic_version')).scalar()!='0008_intelligence_audit':
                    raise RuntimeError('Reviewed migration head is required; run the explicit migration workflow')
        finally:engine.dispose()
    try:check();return
    except Exception:
        # Only start an initialized project-owned cluster; never initialize/reset
        # databases or alter credentials as a consequence of startup.
        data=ROOT/'runtime/postgres';binary=ROOT/'runtime/tools/postgres/usr/lib/postgresql/16/bin/pg_ctl'
        if url.host!='127.0.0.1' or url.port!=55432 or data.is_symlink() or not (data/'PG_VERSION').is_file() or not binary.is_file():
            raise RuntimeError('Database unavailable; follow the local setup/migration runbook') from None
        env=dict(os.environ,LD_LIBRARY_PATH=str(ROOT/'runtime/tools/postgres/usr/lib/x86_64-linux-gnu'))
        status=subprocess.run([str(binary),'-D',str(data),'status'],env=env,capture_output=True)
        if status.returncode!=0:
            subprocess.run([str(binary),'-D',str(data),'-l',str(ROOT/'runtime/dev/postgres.log'),'-w','start'],env=env,check=True,capture_output=True)
        check()


def health(require_vlm=False):
    api=fetch('http://127.0.0.1:8000/api/v1/health/ready')
    web=fetch('http://127.0.0.1:3000/health')
    state=owned();worker=False
    if state:
        app=process_identity(state.get('app_pid',0),ROOT/'scripts/dev/run.py')
        if app and app==state.get('app_process'):
            try:
                for pid in (Path('/proc')/str(app['pid'])/'task'/str(app['pid'])/'children').read_text().split():
                    folder=Path('/proc')/pid
                    argv=(folder/'cmdline').read_bytes().split(b'\0')
                    if folder.stat().st_uid==os.getuid() and b'app.services.worker' in argv and (folder/'cwd').resolve()==ROOT:
                        worker=True
            except FileNotFoundError:pass
    vlm=inference_health()
    cpu=api.get('status')=='ready' and web.get('status')=='alive' and worker
    result={'profile':'HACKATHON_LOCAL','status':'READY' if cpu and vlm['status']=='AVAILABLE' else 'DEGRADED' if cpu else 'NOT_READY',
        'api':'READY' if api.get('status')=='ready' else 'UNAVAILABLE',
        'web':'READY' if web.get('status')=='alive' else 'UNAVAILABLE','worker_supervisor':'RUNNING' if worker else 'UNAVAILABLE',
        'inference':vlm,'visual_extraction':'AVAILABLE' if vlm['status']=='AVAILABLE' else 'PROVIDER_UNAVAILABLE',
        'database_policy':'Preserved; stop does not shut down the shared local PostgreSQL cluster'}
    return result,0 if cpu and (not require_vlm or vlm['status']=='AVAILABLE') else 1


def supervise(no_vlm):
    child=None
    def stop(*_):raise KeyboardInterrupt()
    signal.signal(signal.SIGTERM,stop)
    try:
        # Keep a configured gateway credential even when the GPU is stopped:
        # actual connection outages then remain retryable provider failures.
        configured=(ROOT/'runtime/inference/gateway_config.json').is_file() and (ROOT/'runtime/inference/gateway.key').is_file()
        argv=[str(PYTHON),str(INFERENCE),'app'] if configured else [str(PYTHON),str(ROOT/'scripts/dev/run.py')]
        child=subprocess.Popen(argv,cwd=ROOT,start_new_session=True)
        deadline=time.monotonic()+10
        while time.monotonic()<deadline:
            try:app=process_identity(child.pid,ROOT/'scripts/dev/run.py')
            except RuntimeError:app=None
            if app:break
            if child.poll() is not None:raise RuntimeError('Application exited during startup')
            time.sleep(.1)
        else:raise RuntimeError('Application supervisor did not start')
        private_json(STATE,{'pid':os.getpid(),'process':process_identity(os.getpid(),Path(__file__),'supervise'),'app_pid':child.pid,'app_process':app})
        while child.poll() is None:time.sleep(.5)
        raise RuntimeError('Application child exited; inspect private demo log')
    except KeyboardInterrupt:pass
    finally:
        if child and child.poll() is None:
            child.terminate()
            try:child.wait(timeout=20)
            except subprocess.TimeoutExpired:raise RuntimeError('Graceful application stop timed out; do not kill unrelated processes')
        if STATE.exists() and json.loads(STATE.read_text()).get('pid')==os.getpid():STATE.unlink()


def stop():
    state=owned()
    if state:
        os.kill(state['pid'],signal.SIGTERM)
        deadline=time.monotonic()+30
        while time.monotonic()<deadline and owned():time.sleep(.2)
        if owned():raise RuntimeError('Demo shutdown timed out')
    subprocess.run([str(PYTHON),str(INFERENCE),'stop'],cwd=ROOT,check=True)
    print('Owned demo application and inference stopped. Database/evidence/model caches preserved.')


def start(no_vlm):
    if owned():
        result,code=health(not no_vlm);print(json.dumps(result,indent=2));return code
    if fetch('http://127.0.0.1:8000/api/v1/health/ready') or fetch('http://127.0.0.1:3000/health'):
        raise RuntimeError('An existing application is running outside this lifecycle; stop its owned supervisor first')
    prerequisite_database()
    subprocess.run([str(PYTHON),str(ROOT/'scripts/seed/hackathon.py'),'prepare'],cwd=ROOT,check=True)
    if not (ROOT/'apps/web/.next/BUILD_ID').is_file():raise RuntimeError('Production frontend build missing; run npm --prefix apps/web run build first')
    available=False
    if not no_vlm:
        try:
            if inference_health()['status']!='AVAILABLE':
                with (RUNTIME/'inference-start.log').open('ab') as output:
                    subprocess.run([str(PYTHON),str(INFERENCE),'start'],cwd=ROOT,check=True,stdout=output,stderr=output)
                deadline=time.monotonic()+150
                while time.monotonic()<deadline and inference_health()['status']!='AVAILABLE':time.sleep(.5)
            available=inference_health()['status']=='AVAILABLE'
        except Exception:pass
        if not available:print('VLM provider unavailable. Inspect runtime/demo/inference-start.log and runtime/inference/logs/local-server.log. Starting CPU application; visual documents cannot complete until inference is restored.',flush=True)
    RUNTIME.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (RUNTIME/'services.log').open('ab') as output:
        child=subprocess.Popen([str(PYTHON),str(Path(__file__).resolve()),'supervise']+(['--no-vlm'] if no_vlm or not available else []),cwd=ROOT,stdout=output,stderr=output,start_new_session=True)
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        if child.poll() is not None:raise RuntimeError('Demo supervisor exited; inspect runtime/demo/services.log')
        result,code=health()
        if code==0:
            print(json.dumps(result,indent=2));return 0
        time.sleep(.5)
    child.terminate();raise RuntimeError('Demo application did not become ready within 60 seconds')


def main():
    os.umask(0o077)
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['start','stop','restart','health','supervise'])
    parser.add_argument('--no-vlm',action='store_true',help='Start CPU services; visual extraction remains explicitly unavailable')
    parser.add_argument('--require-vlm',action='store_true',help='Health fails unless the pinned real VLM is available')
    args=parser.parse_args()
    if args.action=='supervise':supervise(args.no_vlm);return
    if args.action=='health':result,code=health(args.require_vlm);print(json.dumps(result,indent=2));raise SystemExit(code)
    RUNTIME.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (RUNTIME/'control.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        if args.action in ('stop','restart'):stop()
        if args.action in ('start','restart'):raise SystemExit(start(args.no_vlm))


if __name__=='__main__':
    try:main()
    except RuntimeError as error:raise SystemExit('Demo lifecycle: '+str(error)) from None
    except subprocess.CalledProcessError:raise SystemExit('Demo dependency command failed; inspect private service logs. No destructive recovery was attempted.') from None
