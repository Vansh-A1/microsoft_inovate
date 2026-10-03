"""Configure explicitly fictional loopback demo identities; no Git credentials involved."""
from pathlib import Path
import json,secrets,sys
from uuid import UUID
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'apps/api'),str(ROOT/'scripts/seed')]
from app.core.config import Settings
from app.core.identity import authenticate
from app.db.session import Database
from app.services.reference_imports import active_records,stage,validate,activate
from finance_catalog import uid,activate_catalog
from phase3 import enable

def main():
    path=ROOT/'runtime/dev/settings.json';private=json.loads(path.read_text());default=next(iter(private['identities'].values()))
    default['roles']=sorted(set(default['roles'])|{'FINANCE_SUBMITTER','REFERENCE_ADMIN','DUPLICATE_REVIEWER','RECEIPT_ALLOCATOR','FINANCE_CONTROLLER','LEDGER_ADMIN'})
    choices=[('Synthetic manager','51000000-0000-4000-8000-000000000003',['MANAGER','FINANCE_REVIEWER']),('Synthetic department head','51000000-0000-4000-8000-000000000004',['DEPARTMENT_HEAD','FINANCE_REVIEWER']),('Synthetic director',uid('employee-28'),['DIRECTOR','FINANCE_REVIEWER']),('Synthetic CFO',uid('employee-29'),['CFO','FINANCE_REVIEWER']),('Synthetic employee','51000000-0000-4000-8000-000000000002',['EMPLOYEE'])]
    for label,actor,roles in choices:
        if not any(i['label']==label for i in private['identities'].values()):private['identities'][secrets.token_urlsafe(32)]={k:default[k] for k in ('tenant_id','legal_entity_id')}|{'actor_id':actor,'roles':roles,'label':label}
    path.write_text(json.dumps(private,indent=2)+'\n');path.chmod(0o600)
    settings=Settings.load();ctx=authenticate(next(iter(settings.identities)),settings);db=Database(settings.database_url);db.settings=settings;enable(db,ctx);activate_catalog(db,ctx)
    with db.session(ctx) as s:
        current=active_records(s,ctx);records=[]
        for name,actor,roles in choices:
            if name not in ('Synthetic director','Synthetic CFO'):continue
            old=current[actor];needed=next(r for r in roles if r!='FINANCE_REVIEWER')
            if needed in old.payload['roles']:continue
            p=dict(old.payload);p.update(version=old.version+1,roles=old.payload['roles']+[needed]);records.append({'kind':'employees','payload':p})
        if records:
            batch=stage(s,ctx,{'source_system':'SYNTHETIC_LOCAL_AUTHORITY','source_version':'v1','records':records,'reason':'Explicit fictional director and CFO authority'},'finance-identities');bid=UUID(batch['id']);result=validate(s,ctx,bid,'finance-identities')
            if result['state']!='VALID':raise ValueError(result['validation'])
            activate(s,ctx,bid,'Approved synthetic local approval roles','finance-identities')
    print(json.dumps({'configured_identity_labels':[i['label'] for i in private['identities'].values()],'scope':'Loopback synthetic development only','credentials':'Private ignored files; no token output'}))

if __name__=='__main__':main()
