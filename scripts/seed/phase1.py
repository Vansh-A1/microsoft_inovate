"""Idempotent development seed. Existing fixtures supply inputs, never decisions."""
import json
from datetime import datetime
from pathlib import Path
import sys
from uuid import UUID
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.core.identity import authenticate
from app.db.session import Database
from app.db.models import Transaction, ApprovalRecord
from app.services.references import seed_references
from app.services.finance import create_transaction,enqueue,audit,scope_lock
from app.services.worker import run_once
from app.schemas.canonical import fixture_canonical

DEMO_CASES=['vendor/clean','vendor/paid_duplicate','employee/clean_taxi','employee/daily_meals','vendor/approval_pending']


def seed_case(session,identity,name):
    case=json.loads((ROOT/f'data/golden_cases/{name}.json').read_text());p=case['transaction'];rid=UUID(p['id'])
    if session.get(Transaction,rid):return rid
    create_transaction(session,identity,fixture_canonical(p),'Trusted synthetic fixture seed','development-seed',rid)
    for a in p['approvals']:
        session.add(ApprovalRecord(**identity.scope(),id=UUID(a['id']),transaction_id=rid,transaction_version=a['transaction_version'],policy_id=UUID(a['approval_policy_id']),policy_version=1,actor_id=UUID(a['actor_id']),role=a['role'],sequence=a['sequence'],state=a['state'],approved_at=datetime.fromisoformat(a['approved_at'].replace('Z','+00:00'))))
    session.flush();audit(session,identity,'SYNTHETIC_APPROVALS_IMPORTED',rid,1,'Trusted development seed only','development-seed',{'count':len(p['approvals'])})
    enqueue(session,identity,rid,1,'Evaluate synthetic fixture','development-seed',f'seed:{name}',datetime.fromisoformat(case['evaluation_at'].replace('Z','+00:00')))
    return rid


def seed(database,identity,names=DEMO_CASES):
    with database.session(identity) as session:
        scope_lock(session,identity);snap=seed_references(session,identity)
        for name in names:seed_case(session,identity,name)
    while run_once(database,identity):pass
    with database.session(identity) as session:
        from app.services.finance import transaction_detail
        return [transaction_detail(session,identity,UUID(json.loads((ROOT/f'data/golden_cases/{name}.json').read_text())['transaction']['id'])) for name in names]


if __name__=='__main__':
    settings=Settings.load();identity=authenticate(next(iter(settings.identities)),settings)
    output=seed(Database(settings.database_url),identity)
    print(json.dumps([{'id':r['id'],'decision':r['decision'],'state':r['processing_state'],'version':r['version']} for r in output],indent=2))
