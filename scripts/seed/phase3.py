"""Explicit fictional reference activation for the approved Phase-3 local demo."""
from pathlib import Path
import json,sys
from copy import deepcopy
from uuid import UUID,uuid5
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.core.identity import authenticate
from app.db.session import Database
from app.services.reference_imports import stage,validate,activate,active_records
from app.core.serialization import digest
NS=UUID('84e4d29e-73c8-418e-a573-26146008b0ba')

def uid(name):return str(uuid5(NS,name))

def entries():
    root=ROOT/'data/synthetic/reference';ap=deepcopy(json.loads((root/'approval_policies.json').read_text())['records'][0]);ap['version']=2;ap['authority_limits']={role:{'currency':'INR','ceiling_amount':'10000000'} for role in ('MANAGER','DEPARTMENT_HEAD','DIRECTOR','CFO')}
    profile={'id':uid('finance-profile'),'version':1,'synthetic':True,'effective_from':'2026-01-01','effective_to':'2027-01-01','ruleset':'rules-p3-v1','currencies':['INR'],'duplicate_window_days':7,'near_amount_absolute':'10.00','fuzzy_number_cutoff':85,'phash_distance':6,'waivable_rules':['EXP-003','EXP-002','PAT-001'],'waiver_roles':['FINANCE_CONTROLLER'],'waiver_maximum_days':7,'freshness_days':30}
    return [{'kind':'approval_policies','payload':ap},{'kind':'finance_profiles','payload':profile}]

def enable(database,identity):
    from dataclasses import replace
    admin=replace(identity,roles=identity.roles|{'REFERENCE_ADMIN'})
    with database.session(admin) as s:
        if any(r.kind=='finance_profiles' for r in active_records(s,admin).values()):return {'state':'ALREADY_ACTIVE'}
        data={'source_system':'SYNTHETIC_PHASE3','source_version':'phase3-demo-v1','reason':'Activate explicitly fictional Phase-3 controls','records':entries()};batch=stage(s,admin,data,'phase3-demo-seed');bid=UUID(batch['id']);result=validate(s,admin,bid,'phase3-demo-seed')
        if result['state']!='VALID':raise ValueError(result['validation'])
        return activate(s,admin,bid,'Approved Phase-3 synthetic catalog','phase3-demo-seed')

if __name__=='__main__':
    settings=Settings.load();identity=authenticate(next(iter(settings.identities)),settings);database=Database(settings.database_url);database.settings=settings
    result=enable(database,identity);print(json.dumps({'state':result['state'],'record_count':len(result.get('records',[]))}))
