#!/usr/bin/env python3
"""Initialize ONLY a fresh ephemeral CI service; never reuse a developer database."""
import json,os,secrets,sys
from pathlib import Path
from urllib.parse import quote
from uuid import uuid4
import psycopg
from psycopg import sql
ROOT=Path(__file__).resolve().parents[2]

def main():
    if os.environ.get('CI')!='true' or not os.environ.get('AP_CI_ADMIN_DATABASE_URL'):raise SystemExit('Explicit disposable CI service required.')
    if (ROOT/'runtime/dev/settings.json').exists():raise SystemExit('Refusing to replace existing private configuration.')
    password=secrets.token_urlsafe(32);token=secrets.token_urlsafe(32)
    with psycopg.connect(os.environ['AP_CI_ADMIN_DATABASE_URL'],autocommit=True) as c:
        if c.execute("SELECT 1 FROM pg_roles WHERE rolname='ap_app'").fetchone():raise SystemExit('CI database is not fresh.')
        c.execute(sql.SQL('CREATE ROLE ap_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}').format(sql.Literal(password)))
        for name in ['ap_phase1','ap_phase1_test']:c.execute(sql.SQL('CREATE DATABASE {} OWNER ap_app').format(sql.Identifier(name)))
    identity={'tenant_id':'10000000-0000-4000-8000-000000000001','legal_entity_id':'20000000-0000-4000-8000-000000000001','actor_id':'51000000-0000-4000-8000-000000000001','roles':['FINANCE_REVIEWER','DEVELOPMENT_ADMIN'],'label':'Synthetic finance reviewer'}
    folder=ROOT/'runtime/dev';folder.mkdir(parents=True);folder.chmod(0o700)
    file=folder/'settings.json';file.write_text(json.dumps({'database_url':f'postgresql+psycopg://ap_app:{quote(password)}@127.0.0.1:5432/ap_phase1','identities':{token:identity},'document_providers':{'ocr_executable':'/usr/bin/tesseract'}}));file.chmod(0o600)
    env=ROOT/'apps/web/.env.local';env.write_text(f'AP_API_ORIGIN=http://127.0.0.1:8000\nAP_DEV_TOKEN={token}\nAP_ENABLE_DEMO_IDENTITIES=1\n');env.chmod(0o600)
    print('Fresh disposable CI app role configured; no credential output.')
if __name__=='__main__':main()
