"""Add narrow synthetic finance/policy identities without widening an existing role."""
import json,secrets,sys
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings

def main():
    settings=Settings.load()
    if not settings.development:raise ValueError('Synthetic development only.')
    path=ROOT/'runtime/dev/settings.json';data=json.loads(path.read_text());scope=next(iter(data['identities'].values()))
    choices=[('Synthetic policy administrator',['POLICY_ADMIN']),('Synthetic finance workspace',['FINANCE_REVIEWER','REPORT_EXPORTER'])]
    for label,roles in choices:
        existing=next((r for r in data['identities'].values() if r['label']==label),None)
        if existing:
            if set(existing['roles'])!=set(roles):raise ValueError('Existing identity roles differ; no automatic privilege change.')
            continue
        data['identities'][secrets.token_urlsafe(32)]={'tenant_id':scope['tenant_id'],'legal_entity_id':scope['legal_entity_id'],'actor_id':str(uuid4()),'roles':roles,'label':label}
    path.write_text(json.dumps(data,indent=2)+'\n');path.chmod(0o600)
    print(json.dumps({'configured_labels':[label for label,roles in choices],'existing_roles':'UNCHANGED','synthetic':True}))
if __name__=='__main__':main()
