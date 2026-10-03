#!/usr/bin/env python3
"""Compare a retained actual-document report across an owned app restart."""
import argparse,hashlib,json,sys,urllib.request
from pathlib import Path
from sqlalchemy import select
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'apps/api'))
from app.core.config import Settings
from app.core.identity import authenticate
from app.db.session import Database,scope_query
from app.db.models import Transaction
from app.db.document_models import TransactionDocument

def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['record','verify']);args=p.parse_args();settings=Settings.load()
    if not settings.development:raise SystemExit('Owned local development application only.')
    token=next(iter(settings.identities));ctx=authenticate(token,settings)
    def get(path):
        with urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:8000/api/v1/'+path,headers={'Authorization':'Bearer '+token}),timeout=30) as response:return json.load(response)
    file=ROOT/'runtime/release/persistence.json'
    if args.action=='record':
        db=Database(settings.database_url)
        with db.session(ctx) as s:
            q=scope_query(select(Transaction),Transaction,ctx).join(TransactionDocument,TransactionDocument.transaction_id==Transaction.id).where(Transaction.processing_state=='COMPLETED',Transaction.latest_evaluation_id.is_not(None)).order_by(Transaction.created_at.desc())
            row=s.scalar(q.limit(1))
            if not row:raise SystemExit('No retained evaluated actual-document transaction.')
            data={'transaction_id':str(row.id),'evaluation_id':str(row.latest_evaluation_id),'version':row.latest_version}
        db.engine.dispose();report=get('evaluations/'+data['evaluation_id']+'/report');data['report_sha256']=hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest();file.write_text(json.dumps(data));file.chmod(0o600)
        print('Actual-document transaction/version/report digest recorded privately before restart.')
    else:
        data=json.loads(file.read_text());record=get('transactions/'+data['transaction_id']);report=get('evaluations/'+data['evaluation_id']+'/report')
        assert record['version']==data['version'] and record['latest_evaluation_id']==data['evaluation_id'] and record['processing_state']=='COMPLETED'
        assert hashlib.sha256(json.dumps(report,sort_keys=True,separators=(',',':')).encode()).hexdigest()==data['report_sha256']
        print('Actual-document transaction/version/evaluation/report unchanged after API/worker/web restart.')
if __name__=='__main__':main()
