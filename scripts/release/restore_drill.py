#!/usr/bin/env python3
"""Actual local restore into an owned disposable DB and private object-copy directory.
No production/cloud claim, no modification or reset of the source database/storage.
"""
import hashlib,json,os,shutil,subprocess,sys
from datetime import timezone
from pathlib import Path
from time import perf_counter
from uuid import uuid4
import psycopg
from psycopg import sql
from sqlalchemy.engine import make_url
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.core.serialization import digest,projection


def snapshot(conn):
    tables=[r[0] for r in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")]
    counts={name:conn.execute(sql.SQL('SELECT count(*) FROM {}').format(sql.Identifier(name))).fetchone()[0] for name in tables}
    reports=list(conn.execute('SELECT id,content_digest FROM reports ORDER BY id'))
    return {'counts':counts,'report_manifest_digest':digest([[str(i),h] for i,h in reports]),'audit_tip':list(conn.execute('SELECT id,audit_sequence,audit_hash FROM tenants ORDER BY id'))}


def main():
    settings=Settings.load()
    if not settings.development:raise SystemExit('Use the separately approved cloud restore procedure for enterprise data.')
    url=make_url(settings.database_url)
    if url.host!='127.0.0.1' or url.port!=55432 or url.database!='ap_phase1':raise SystemExit('This drill is limited to the project-owned local cluster.')
    admin=json.loads((ROOT/'runtime/dev/admin.json').read_text())['password'];name='ap_restore_'+uuid4().hex
    folder=ROOT/'runtime/release'/name;folder.mkdir(parents=True);folder.chmod(0o700)
    bindir=ROOT/'runtime/tools/postgres/usr/lib/postgresql/16/bin'
    env=dict(os.environ,PGHOST='127.0.0.1',PGPORT='55432',PGUSER='ap_bootstrap',PGPASSWORD=admin,LD_LIBRARY_PATH=str(ROOT/'runtime/tools/postgres/usr/lib/x86_64-linux-gnu'))
    started=perf_counter();created=False
    try:
        with psycopg.connect(host=url.host,port=url.port,user='ap_bootstrap',password=admin,dbname='postgres',autocommit=True) as control:
            control.execute(sql.SQL('CREATE DATABASE {} OWNER ap_app').format(sql.Identifier(name)));created=True
        dump=folder/'snapshot.dump'
        # Hold an exported database snapshot through pg_dump and manifest collection.
        with psycopg.connect(host=url.host,port=url.port,user='ap_bootstrap',password=admin,dbname=url.database) as source:
            source.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
            token=source.execute('SELECT pg_export_snapshot()').fetchone()[0];before=snapshot(source)
            subprocess.run([str(bindir/'pg_dump'),'--dbname',url.database,'--format=custom','--no-owner','--no-privileges','--snapshot',token,'--file',str(dump)],env=env,check=True,capture_output=True)
        dump.chmod(0o600)
        subprocess.run([str(bindir/'pg_restore'),'--dbname',name,'--exit-on-error','--no-owner','--no-privileges',str(dump)],env=env,check=True,capture_output=True)
        with psycopg.connect(host=url.host,port=url.port,user='ap_bootstrap',password=admin,dbname=name) as restored:
            after=snapshot(restored);assert before==after,'Database retained-data manifest mismatch'
            # Only objects in the newly created disposable database change ownership.
            for table in before['counts']:restored.execute(sql.SQL('ALTER TABLE {} OWNER TO ap_app').format(sql.Identifier(table)))
            flags=restored.execute("SELECT count(*),count(*) FILTER (WHERE relrowsecurity AND relforcerowsecurity) FROM pg_class WHERE relnamespace='public'::regnamespace AND relkind='r'").fetchone()
            assert flags==(62,61),flags
            # Verify the retained chain for every tenant, using stored events, not re-extraction.
            tenants=list(restored.execute('SELECT id,audit_sequence,audit_hash FROM tenants ORDER BY id'))
            verified=0
            for tenant,sequence,tip in tenants:
                previous='0'*64
                events=restored.execute('SELECT id,tenant_id,legal_entity_id,sequence,actor_id,action,object_id,object_version,reason,correlation_id,created_at,payload,previous_hash,event_hash FROM audit_events WHERE tenant_id=%s ORDER BY sequence',(tenant,))
                for row in events:
                    data=dict(zip(('id','tenant_id','legal_entity_id','sequence','actor_id','action','object_id','object_version','reason','correlation_id','created_at','payload'),row[:12]))
                    data['created_at']=data['created_at'].astimezone(timezone.utc)
                    assert row[12]==previous and digest({'previous_hash':previous,'event':projection(data)})==row[13],'Retained audit digest mismatch'
                    previous=row[13];verified+=1
                assert previous==tip
        target=folder/'objects'
        if any(p.is_symlink() for p in settings.storage_root.rglob('*')):raise ValueError('Refusing a symlink in private evidence backup.')
        shutil.copytree(settings.storage_root,target)
        manifests=[]
        for original in settings.storage_root.rglob('*'):
            if not original.is_file() or original.is_symlink() or original.suffix=='.part':continue
            relative=original.relative_to(settings.storage_root);copied=target/relative
            a=hashlib.sha256(original.read_bytes()).hexdigest();assert hashlib.sha256(copied.read_bytes()).hexdigest()==a
            manifests.append((relative.as_posix(),a))
        # Permission/isolation check using the restored non-bypass application role.
        with psycopg.connect(host=url.host,port=url.port,user=url.username,password=url.password,dbname=name) as app:
            assert app.execute('SELECT count(*) FROM transactions').fetchone()[0]==0
            assert app.execute('SELECT rolsuper,rolbypassrls FROM pg_roles WHERE rolname=current_user').fetchone()==(False,False)
        result={'status':'VERIFIED_LOCAL_RESTORE','source_modified':False,'tables':flags[0],'forced_rls_tables':flags[1],'retained_counts':before['counts'],'report_manifest_digest':before['report_manifest_digest'],'audit_events_verified':verified,'objects_verified':len(manifests),'object_manifest_digest':digest(sorted(manifests)),'elapsed_seconds':round(perf_counter()-started,3),'cloud_restore':'DEFERRED_EXTERNAL'}
        (folder/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
    except subprocess.CalledProcessError as error:
        # Preserve diagnostics privately. Connection values/document rows never reach stdout.
        (folder/'failure.log').write_bytes(error.stderr or b'');raise SystemExit('Restore failed; inspect the private drill diagnostics.') from None
    finally:
        if created:
            with psycopg.connect(host=url.host,port=url.port,user='ap_bootstrap',password=admin,dbname='postgres',autocommit=True) as control:
                control.execute(sql.SQL('DROP DATABASE {}').format(sql.Identifier(name)))
if __name__=='__main__':main()
