"""Narrow fictional ML author/governor identities; no finance role widening."""
import json,secrets,sys
from pathlib import Path
from uuid import uuid4
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings

def main():
    settings=Settings.load()
    if not settings.development:raise ValueError('Synthetic development configuration required.')
    path=ROOT/'runtime/dev/settings.json';private=json.loads(path.read_text());original=next(iter(private['identities'].values()))
    choices=[('Synthetic ML author',['ML_ADMIN']),('Synthetic ML governor',['ML_GOVERNANCE'])]
    for label,roles in choices:
        existing=next((r for r in private['identities'].values() if r['label']==label),None)
        if existing:
            if set(existing['roles'])!=set(roles):raise ValueError('Existing identity roles differ; no automatic privilege change.')
            continue
        private['identities'][secrets.token_urlsafe(32)]={'tenant_id':original['tenant_id'],'legal_entity_id':original['legal_entity_id'],
            'actor_id':str(uuid4()),'roles':roles,'label':label}
    path.write_text(json.dumps(private,indent=2)+'\n');path.chmod(0o600)
    print(json.dumps({'configured_labels':[r[0] for r in choices],'existing_identity_roles':'UNCHANGED','scope':'Synthetic local entity only'}))
if __name__=='__main__':main()
