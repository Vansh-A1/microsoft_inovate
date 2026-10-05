"""CPU-only lifecycle tests: safe ownership and truthful degraded readiness."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
from uuid import uuid4
import pytest
from app.core.config import ROOT

spec=importlib.util.spec_from_file_location('demo_lifecycle',ROOT/'scripts/demo.py')
demo=importlib.util.module_from_spec(spec);spec.loader.exec_module(demo)


def test_private_state_atomic_and_not_world_readable(tmp_path):
    path=tmp_path/'state.json';demo.private_json(path,{'pid':42})
    assert json.loads(path.read_text())=={'pid':42}
    assert path.stat().st_mode&0o077==0
    assert list(tmp_path.iterdir())==[path]


def test_unrelated_real_process_cannot_be_signalled(tmp_path,monkeypatch):
    path=tmp_path/'state.json';demo.private_json(path,{'pid':os.getpid(),'process':{'pid':os.getpid(),'start_ticks':'0'}})
    monkeypatch.setattr(demo,'STATE',path)
    with pytest.raises(RuntimeError,match='command mismatch'):demo.owned()


def test_stale_dead_pid_returns_no_owned_supervisor(tmp_path,monkeypatch):
    path=tmp_path/'state.json';demo.private_json(path,{'pid':999999999,'process':{'pid':999999999,'start_ticks':'0'}})
    monkeypatch.setattr(demo,'STATE',path)
    assert demo.owned() is None
    # A crashed owned child can remain a zombie until its parent reaps it.
    # Its empty command line must not turn harmless stale state into a mismatch.
    import sys,time
    child=subprocess.Popen([sys.executable,'-c','pass'])
    try:
        deadline=time.monotonic()+3
        while time.monotonic()<deadline:
            stat=Path(f'/proc/{child.pid}/stat').read_text().rsplit(')',1)[1].split()
            if stat[0]=='Z':break
            time.sleep(.01)
        else:pytest.fail('Local child did not reach the expected stopped state')
        assert demo.process_identity(child.pid,ROOT/'scripts/demo.py','supervise') is None
    finally:child.wait(timeout=3)


def test_pid_reuse_is_rejected_before_any_signal(tmp_path,monkeypatch):
    path=tmp_path/'state.json';demo.private_json(path,{'pid':42,'process':{'pid':42,'start_ticks':'older'}})
    monkeypatch.setattr(demo,'STATE',path)
    monkeypatch.setattr(demo,'process_identity',lambda *a:{'pid':42,'start_ticks':'newer'})
    with pytest.raises(RuntimeError,match='reused'):demo.owned()


def test_private_state_symlink_is_rejected(tmp_path,monkeypatch):
    source=tmp_path/'private.json';demo.private_json(source,{'pid':42})
    path=tmp_path/'state.json';path.symlink_to(source);monkeypatch.setattr(demo,'STATE',path)
    with pytest.raises(RuntimeError,match='private'):demo.owned()


def test_malformed_state_never_signals(tmp_path,monkeypatch):
    path=tmp_path/'state.json';demo.private_json(path,{'pid':-1});monkeypatch.setattr(demo,'STATE',path)
    with pytest.raises(RuntimeError,match='malformed'):demo.owned()


def inference_module():
    spec=importlib.util.spec_from_file_location('demo_inference_tests',ROOT/'scripts/inference/local.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def test_model_integrity_rejects_changed_or_linked_shard(tmp_path,monkeypatch):
    import hashlib
    module=inference_module();path=tmp_path/'model.safetensors';path.write_bytes(b'synthetic test shard')
    monkeypatch.setattr(module,'WEIGHT_HASHES',{path.name:hashlib.sha256(path.read_bytes()).hexdigest()})
    module.verify_weights(tmp_path)
    path.write_bytes(b'changed')
    with pytest.raises(SystemExit,match='integrity'):module.verify_weights(tmp_path)
    path.unlink();source=tmp_path/'other';source.write_bytes(b'synthetic test shard');path.symlink_to(source)
    with pytest.raises(SystemExit,match='unsafe'):module.verify_weights(tmp_path)


def test_low_vram_refuses_launch_without_changing_environment(monkeypatch):
    module=inference_module();monkeypatch.setattr(module,'owned_supervisor',lambda:None)
    monkeypatch.setattr(module,'config',lambda:{})
    monkeypatch.setattr(module,'available_memory',lambda:module.MINIMUM_FREE_VRAM_MIB-1)
    with pytest.raises(SystemExit,match='Insufficient'):module.start_owned()


def test_cleanup_requires_confirmation_and_stopped_inference(monkeypatch):
    module=inference_module()
    with pytest.raises(SystemExit,match='confirm-remove-runtime'):module.cleanup(False)
    monkeypatch.setattr(module,'owned_supervisor',lambda:42)
    with pytest.raises(SystemExit,match='Stop inference'):module.cleanup(True)


@pytest.mark.parametrize('status,require,code',[('AVAILABLE',False,0),('PROVIDER_UNAVAILABLE',False,0),('PROVIDER_UNAVAILABLE',True,1)])
def test_cpu_readiness_and_required_gpu_are_separate(monkeypatch,status,require,code):
    monkeypatch.setattr(demo,'fetch',lambda url,*a:{'status':'ready' if ':8000' in url else 'alive'})
    app={'pid':os.getpid(),'start_ticks':'test'}
    monkeypatch.setattr(demo,'owned',lambda:{'app_pid':app['pid'],'app_process':app})
    monkeypatch.setattr(demo,'process_identity',lambda *a:app)
    # Only the process inventory is simulated; the score/degraded decision is real.
    original=Path.read_text
    monkeypatch.setattr(Path,'read_text',lambda p,*a,**k:'42' if p.name=='children' else original(p,*a,**k))
    monkeypatch.setattr(Path,'read_bytes',lambda p:b'python\0-m\0app.services.worker\0')
    monkeypatch.setattr(Path,'stat',lambda p:type('Stat',(),{'st_uid':os.getuid()})())
    monkeypatch.setattr(Path,'resolve',lambda p:ROOT if p.name=='cwd' else p)
    monkeypatch.setattr(demo,'inference_health',lambda:{'status':status})
    result,actual=demo.health(require)
    assert actual==code
    assert result['status']==('READY' if status=='AVAILABLE' else 'DEGRADED')
    assert result['visual_extraction']==('AVAILABLE' if status=='AVAILABLE' else 'PROVIDER_UNAVAILABLE')


def test_ready_http_without_owned_worker_is_not_ready(monkeypatch):
    monkeypatch.setattr(demo,'fetch',lambda url,*a:{'status':'ready' if ':8000' in url else 'alive'})
    monkeypatch.setattr(demo,'owned',lambda:None)
    monkeypatch.setattr(demo,'inference_health',lambda:{'status':'AVAILABLE'})
    result,code=demo.health()
    assert code==1 and result['worker_supervisor']=='UNAVAILABLE'


def test_existing_cpu_start_never_seeds_or_controls_inference(monkeypatch):
    monkeypatch.setattr(demo,'owned',lambda:{'pid':42})
    monkeypatch.setattr(demo,'health',lambda *a:({'status':'DEGRADED'},0))
    def forbidden(*a,**k):raise AssertionError('Existing CPU entry must not launch, seed or change inference')
    monkeypatch.setattr(demo,'cpu_prerequisites',forbidden)
    monkeypatch.setattr(demo.subprocess,'run',forbidden)
    monkeypatch.setattr(demo.subprocess,'Popen',forbidden)
    assert demo.start_cpu()==0


def test_cpu_restart_checks_prerequisites_before_any_signal(monkeypatch):
    def missing():raise RuntimeError('Production frontend build missing')
    monkeypatch.setattr(demo,'cpu_prerequisites',missing)
    monkeypatch.setattr(demo.os,'kill',lambda *a:pytest.fail('Do not stop working CPU services when preflight fails'))
    with pytest.raises(RuntimeError,match='build missing'):demo.restart_cpu()


def test_cpu_stop_signals_only_validated_cpu_supervisor(monkeypatch):
    states=iter([{'pid':42},None,None]);signals=[]
    monkeypatch.setattr(demo,'owned',lambda:next(states))
    monkeypatch.setattr(demo.os,'kill',lambda pid,sig:signals.append((pid,sig)))
    monkeypatch.setattr(demo.subprocess,'run',lambda *a,**k:pytest.fail('CPU stop must not control inference'))
    demo.stop_cpu()
    assert signals==[(42,demo.signal.SIGTERM)]


def test_cpu_start_preserves_provider_outage_and_only_launches_supervisor(tmp_path,monkeypatch):
    calls=[]
    monkeypatch.setattr(demo,'RUNTIME',tmp_path/'private')
    monkeypatch.setattr(demo,'owned',lambda:None)
    monkeypatch.setattr(demo,'fetch',lambda *a:{})
    monkeypatch.setattr(demo,'cpu_prerequisites',lambda:None)
    monkeypatch.setattr(demo,'health',lambda *a:({'status':'DEGRADED','inference':{'status':'PROVIDER_UNAVAILABLE'}},0))
    monkeypatch.setattr(demo.subprocess,'run',lambda *a,**k:pytest.fail('CPU launch must not seed or start/stop inference'))
    class Child:
        def poll(self):return None
    monkeypatch.setattr(demo.subprocess,'Popen',lambda args,**k:calls.append(args) or Child())
    assert demo.start_cpu()==0
    assert calls==[[str(demo.PYTHON),str(Path(demo.__file__).resolve()),'supervise']]
