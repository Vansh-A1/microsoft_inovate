"""Actual migrated snapshot membership, replay, RLS and atomic failure checks."""
import json
import os
import re
from time import perf_counter
from uuid import uuid4
import pytest
from sqlalchemy import select,func
from sqlalchemy.exc import IntegrityError
from app.core.config import ROOT
from app.db.models import ReferenceRecord,ReferenceSnapshot,SnapshotMember
from app.services.references import snapshot_records,pinned


def test_large_snapshot_keeps_exact_membership_replay_isolation_and_rollback(environment):
    db,ctx,other,client,cfg=environment
    ids=[uuid4() for _ in range(1700)]
    with db.session(ctx) as s:
        empty=snapshot_records(s,ctx,[])
        assert empty.manifest=={'records':[]} and pinned(s,ctx,empty.id)=={}
        s.add_all([ReferenceRecord(**ctx.scope(),id=rid,version=1,kind='cost_centers',label='Fictional snapshot load only',
            payload={'id':str(rid),'version':1,'name':f'Fictional snapshot {i}','department':'SYNTHETIC'}) for i,rid in enumerate(ids)])
    measurements=[]
    for index in range(3):
        records=[(rid,1) for rid in ids[:1700-index]]
        started=perf_counter()
        with db.session(ctx) as s:retained=snapshot_records(s,ctx,records+records[:2])
        measurements.append(round((perf_counter()-started)*1000,3))
        with db.session(ctx) as s:
            assert len(retained.manifest['records'])==len(records)
            members=s.scalars(select(SnapshotMember).where(SnapshotMember.snapshot_id==retained.id)).all()
            assert {(r.record_id,r.record_version) for r in members}==set(records)
            assert len({r.id for r in members})==len(records)
            assert all(r.tenant_id==ctx.tenant_id and r.legal_entity_id==ctx.legal_entity_id for r in members)
            assert set(pinned(s,ctx,retained.id))=={str(rid) for rid,_ in records}
            assert snapshot_records(s,ctx,list(reversed(records))).id==retained.id
        with db.session(other) as s:
            assert pinned(s,other,retained.id)=={}
            assert s.get(ReferenceSnapshot,retained.id) is None
    with db.session(ctx) as s:
        snapshots=s.scalar(select(func.count()).select_from(ReferenceSnapshot));members=s.scalar(select(func.count()).select_from(SnapshotMember))
    with pytest.raises(IntegrityError):
        with db.session(ctx) as s:snapshot_records(s,ctx,[(ids[0],1),(uuid4(),1)])
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(ReferenceSnapshot))==snapshots
        assert s.scalar(select(func.count()).select_from(SnapshotMember))==members
    label=os.getenv('AP_SNAPSHOT_MEASUREMENT_LABEL')
    if label:
        assert re.fullmatch('[a-z0-9-]{1,40}',label)
        target=ROOT/'runtime/kivo-reliability'/f'snapshot-{label}.json'
        assert not target.exists(),'Historical timings must not be overwritten'
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps({'label':label,'fictional':True,'member_counts':[1700,1699,1698],
            'transaction_ms':measurements,'scope':'Fresh migrated PostgreSQL schema, actual snapshot transaction including commit. Shared local host; no cloud or universal throughput claim.'},indent=2)+'\n')
