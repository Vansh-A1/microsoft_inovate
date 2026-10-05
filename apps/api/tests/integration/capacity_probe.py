"""Opt-in real transaction timings; no SQL, parameters or business facts logged."""
from contextlib import contextmanager
import json
import os
import re
from threading import local, Lock
from time import perf_counter
from sqlalchemy import event
from app.core.config import ROOT


class CapacityProbe:
    def __init__(self, database, kind):
        self.engine=database.engine;self.kind=kind;self.round=1
        self.label=os.getenv('AP_CAPACITY_MEASUREMENT_LABEL')
        if self.label and not re.fullmatch('[a-z0-9-]{1,40}',self.label):
            raise ValueError('Bounded measurement label required')
        self.records=[];self.local=local();self.guard=Lock()

    def __enter__(self):
        if self.label:
            event.listen(self.engine,'before_cursor_execute',self.before)
            event.listen(self.engine,'after_cursor_execute',self.after)
            event.listen(self.engine,'handle_error',self.error)
        return self

    def before(self,connection,cursor,statement,parameters,context,executemany):
        record=getattr(self.local,'record',None)
        if record is not None:
            record['sql_calls']+=1
            if 'pg_advisory_xact_lock(' in statement:
                context.capacity_wait_started=perf_counter()

    def wait(self,context):
        started=getattr(context,'capacity_wait_started',None)
        record=getattr(self.local,'record',None)
        if started is not None and record is not None:
            record['advisory_wait_ms'].append(round((perf_counter()-started)*1000,3))
            context.capacity_wait_started=None

    def after(self,connection,cursor,statement,parameters,context,executemany):
        self.wait(context)

    def error(self,context):
        self.wait(context.execution_context)

    @contextmanager
    def sample(self):
        if not self.label:
            yield;return
        record={'round':self.round,'outcome':'COMMITTED','sql_calls':0,'advisory_wait_ms':[]}
        self.local.record=record;started=perf_counter()
        try:yield
        except BaseException as exc:
            record['outcome']='ROLLED_BACK'
            record['sqlstate']=getattr(getattr(exc,'orig',None),'sqlstate',None)
            raise
        finally:
            record['transaction_ms']=round((perf_counter()-started)*1000,3)
            self.local.record=None
            with self.guard:self.records.append(record)

    def __exit__(self,*exception):
        if not self.label:return
        event.remove(self.engine,'before_cursor_execute',self.before)
        event.remove(self.engine,'after_cursor_execute',self.after)
        event.remove(self.engine,'handle_error',self.error)
        target=ROOT/'runtime/kivo-concurrency'/f'{self.label}-{self.kind.lower()}.json'
        target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('x') as file:
            json.dump({'label':self.label,'kind':self.kind,'concurrency':8,
                'conditions':'Actual unchanged finalization and commit in fresh migrated PostgreSQL schema. Shared host; no concurrent heavy test runner or inference request. No SQL/facts/IDs logged.',
                'lock_timeout_ms':5000,'statement_timeout_ms':10000,'records':self.records},file,indent=2)
            file.write('\n')
