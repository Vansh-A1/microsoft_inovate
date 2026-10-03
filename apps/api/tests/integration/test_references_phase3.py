from dataclasses import replace
from uuid import UUID,uuid4
from sqlalchemy import select,text
from app.db.models import ReferenceRecord,ReferenceSnapshot
from app.services.reference_imports import stage,validate,activate,active_records
from app.services.references import snapshot,pinned
from app.core.errors import DomainError
import pytest

def test_staged_validation_activation_snapshot_and_authorization(environment):
    db,ctx,other,client,cfg=environment;admin=replace(ctx,roles=ctx.roles|{'REFERENCE_ADMIN'})
    with db.session(ctx) as s:
        old=snapshot(s,ctx);vendor=next(r for r in active_records(s,ctx).values() if r.kind=='vendors');p=dict(vendor.payload);p['version']=2;p['legal_name']='Synthetic Updated Supplier'
    data={'source_system':'SYNTHETIC_PHASE3','source_version':'v2','reason':'Authorized synthetic update','records':[{'kind':'vendors','payload':p}]}
    with db.session(ctx) as s:
        with pytest.raises(DomainError) as error:stage(s,ctx,data,'test')
        assert error.value.status==403
    with db.session(admin) as s:
        batch=stage(s,admin,data,'test');bid=UUID(batch['id']);assert batch['state']=='STAGED'
        assert active_records(s,admin)[p['id']].version==1
        assert validate(s,admin,bid,'test')['state']=='VALID'
        assert activate(s,admin,bid,'Approve source version','test')['state']=='ACTIVE'
        new=snapshot(s,admin);assert new.id!=old.id
        assert pinned(s,admin,old.id)[p['id']]['version']==1 and pinned(s,admin,new.id)[p['id']]['version']==2
        assert active_records(s,admin)[p['id']].payload['import_batch_id']==str(bid)
    with db.session(other) as s:assert not s.scalar(select(ReferenceRecord).where(ReferenceRecord.id==UUID(p['id']),ReferenceRecord.version==2))
    assert client.post('/api/v1/reference-imports',json=data,headers={'Idempotency-Key':str(uuid4())}).status_code==403

def test_invalid_import_never_activates_and_new_tables_forced_rls(environment):
    db,ctx,other,client,cfg=environment;admin=replace(ctx,roles=ctx.roles|{'REFERENCE_ADMIN'})
    data={'source_system':'SYNTHETIC_PHASE3','source_version':'v1','reason':'Validate malformed import','records':[{'kind':'grn_lines','payload':{'id':str(uuid4()),'version':1,'po_id':str(uuid4()),'po_line_id':str(uuid4()),'accepted_quantity':'1','returned_quantity':'0','reversed_quantity':'0','uom':'EA'}}]}
    with db.session(admin) as s:
        bid=UUID(stage(s,admin,data,'test')['id']);r=validate(s,admin,bid,'test');assert r['state']=='INVALID' and any(e['code']=='BROKEN_LINK' for e in r['validation'])
        with pytest.raises(DomainError):activate(s,admin,bid,'Do not activate invalid batch','test')
        assert s.scalar(text("SELECT count(*) FROM pg_class WHERE relnamespace=current_schema()::regnamespace AND relkind='r' AND relrowsecurity AND relforcerowsecurity"))==47


def test_scale_catalog_activation_relationships_and_immutable_staging(environment):
    from dataclasses import replace
    from sqlalchemy import select,func,text
    from sqlalchemy.exc import DBAPIError
    import sys,pytest
    from app.core.config import ROOT
    from app.db.finance_models import ReferenceBatch
    from app.db.models import ReferenceLink
    sys.path.insert(0,str(ROOT/'scripts/seed'));from finance_catalog import activate_catalog
    db,ctx,other,client,cfg=environment;ctx=replace(ctx,roles=ctx.roles|{'REFERENCE_ADMIN'});r=activate_catalog(db,ctx);assert r['state']=='ACTIVE'
    with db.session(ctx) as s:
        assert s.scalar(select(func.count()).select_from(ReferenceLink))>=200
        row=s.scalar(select(ReferenceBatch));assert row
        with pytest.raises(DBAPIError):
            with s.begin_nested():s.execute(text("UPDATE reference_batches SET source_system='MUTATED'"))
