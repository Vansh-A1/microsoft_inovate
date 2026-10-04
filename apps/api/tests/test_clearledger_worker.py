"""Safe worker recovery: real errors are distinguished from transient DB faults."""
import json
from types import SimpleNamespace
import pytest
from sqlalchemy.exc import OperationalError
from app.services import worker,document_worker
from app.core.observability import log


def fault(state,invalidated=False):
    return OperationalError('private SQL',{'private':'invoice value'},
        SimpleNamespace(sqlstate=state),connection_invalidated=invalidated)


@pytest.mark.parametrize('stage',['FINANCE','DOCUMENT'])
@pytest.mark.parametrize('state',['55P03','40001','40P01','08006'])
def test_transient_fault_remains_safe_and_next_cycle_runs(monkeypatch,stage,state):
    events=[];calls=[];failed=[False]
    monkeypatch.setattr(log,'warning',lambda message:events.append(json.loads(message)))
    def action(name):
        def run(*args):
            calls.append(name)
            if name==stage and not failed[0]:
                failed[0]=True;raise fault(state)
            return False
        return run
    monkeypatch.setattr(worker,'run_once',action('FINANCE'))
    monkeypatch.setattr(document_worker,'run_once',action('DOCUMENT'))
    assert worker.run_scoped_cycle(None,None,None,None) is False
    assert events==[{'event':'worker_backoff','stage':stage,'reason':'DATABASE_UNAVAILABLE' if state.startswith('08') else 'DATABASE_CONTENTION'}]
    assert worker.run_scoped_cycle(None,None,None,None) is True
    assert calls[-2:]==['FINANCE','DOCUMENT']


def test_invalidated_connection_is_retried_without_driver_text(monkeypatch):
    events=[]
    monkeypatch.setattr(log,'warning',events.append)
    monkeypatch.setattr(worker,'run_once',lambda *args:(_ for _ in ()).throw(fault(None,True)))
    assert worker.run_scoped_cycle(None,None,None,None) is False
    assert json.loads(events[0])=={'event':'worker_backoff','stage':'FINANCE','reason':'DATABASE_UNAVAILABLE'}
    assert 'private' not in events[0]


@pytest.mark.parametrize('state',['42501','42P01',None])
def test_nontransient_fault_is_not_hidden(monkeypatch,state):
    monkeypatch.setattr(worker,'run_once',lambda *args:(_ for _ in ()).throw(fault(state)))
    with pytest.raises(OperationalError):worker.run_scoped_cycle(None,None,None,None)


def test_business_failure_is_not_hidden(monkeypatch):
    monkeypatch.setattr(worker,'run_once',lambda *args:(_ for _ in ()).throw(ValueError('Invalid business configuration')))
    with pytest.raises(ValueError):worker.run_scoped_cycle(None,None,None,None)
