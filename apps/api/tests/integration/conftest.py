"""Each test gets a fresh migrated PostgreSQL schema owned by the non-superuser app role."""
from pathlib import Path
from dataclasses import replace
from uuid import uuid4, UUID
import sys
import pytest
from sqlalchemy import create_engine,text
from sqlalchemy.engine import make_url
from alembic.config import Config
from alembic import command
from fastapi.testclient import TestClient
from app.core.config import ROOT,Settings
from app.core.identity import authenticate,Identity
from app.db.session import Database
from app.services.references import seed_references
from app.main import create_app
sys.path.insert(0,str(ROOT/'scripts/seed'))
from phase1 import seed


@pytest.fixture
def environment(tmp_path):
    if not (ROOT/'runtime/dev/settings.json').exists():pytest.skip('Run scripts/dev/setup_database.py for real PostgreSQL integration tests.')
    settings=Settings.load();url=make_url(settings.database_url).set(database='ap_phase1_test');schema='test_'+uuid4().hex
    control=create_engine(url)
    with control.begin() as conn:conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    scoped_url=url.update_query_dict({'options':f'-csearch_path={schema}'})
    cfg=Config(str(ROOT/'apps/api/alembic.ini'));cfg.attributes['database_url']=scoped_url.render_as_string(hide_password=False)
    command.upgrade(cfg,'head')
    database=Database(scoped_url.render_as_string(hide_password=False));ctx=replace(authenticate(next(iter(settings.identities)),settings),roles=frozenset({'FINANCE_REVIEWER','DEVELOPMENT_ADMIN'}))
    second=Identity(UUID('10000000-0000-4000-8000-000000000002'),UUID('20000000-0000-4000-8000-000000000003'),uuid4(),frozenset({'FINANCE_REVIEWER'}),'Second synthetic tenant')
    identities={'test-reviewer':{'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':str(ctx.actor_id),'roles':list(ctx.roles),'label':ctx.label},'test-second':{'tenant_id':str(second.tenant_id),'legal_entity_id':str(second.legal_entity_id),'actor_id':str(second.actor_id),'roles':list(second.roles),'label':second.label},'test-reader':{'tenant_id':str(ctx.tenant_id),'legal_entity_id':str(ctx.legal_entity_id),'actor_id':str(uuid4()),'roles':['AUDITOR'],'label':'Read-only synthetic auditor'}}
    settings=replace(settings,database_url=scoped_url.render_as_string(hide_password=False),identities=identities,storage_root=tmp_path/'private')
    with database.session(ctx) as session:seed_references(session,ctx)
    with database.session(second) as session:seed_references(session,second)
    client=TestClient(create_app(settings,database));client.headers['Authorization']='Bearer test-reviewer'
    yield database,ctx,second,client,cfg
    client.close();database.engine.dispose()
    with control.begin() as conn:conn.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
    control.dispose()
