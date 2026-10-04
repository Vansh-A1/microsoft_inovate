"""Development-only, scoped walkthrough of independently computed outcomes."""
import json
from uuid import UUID
from fastapi import Depends
from app.core.config import ROOT
from app.core.errors import DomainError
from app.db.models import Evaluation,Transaction
from app.db.document_models import Document
from app.services import finance,operations

MANIFEST=ROOT/'runtime/demo/scenarios.json'
TEMPLATES=ROOT/'runtime/demo/templates'

def prepared_template(identity,branch):
    path=TEMPLATES/f'{branch}.json'
    if not path.is_file():return None
    if path.is_symlink() or path.stat().st_mode&0o077:raise DomainError(503,'DEMO_UNAVAILABLE','Prepared templates must be private.')
    data=json.loads(path.read_text())
    if data.get('tenant_id')==str(identity.tenant_id) and data.get('legal_entity_id')==str(identity.legal_entity_id):return data['transaction']
    return None

def mount(app,settings,database,identity):
    @app.get('/api/v1/development/scenarios')
    def scenarios(ctx=Depends(identity)):
        if not settings.development:raise DomainError(404,'NOT_FOUND','Development walkthrough is disabled.')
        operations.read_permission(ctx)
        if not MANIFEST.is_file():return {'synthetic':True,'ready':False,'items':[],'message':'Run ./scripts/prepare-demo.sh to compute the prepared scenarios.'}
        if MANIFEST.is_symlink() or MANIFEST.stat().st_mode&0o077:raise DomainError(503,'DEMO_UNAVAILABLE','Demo manifest must be private.')
        try:data=json.loads(MANIFEST.read_text())
        except (ValueError,OSError):raise DomainError(503,'DEMO_UNAVAILABLE','Prepared scenario metadata is unavailable.') from None
        if data.get('tenant_id')!=str(ctx.tenant_id) or data.get('legal_entity_id')!=str(ctx.legal_entity_id):
            return {'synthetic':True,'ready':False,'items':[],'message':'Select Hackathon finance reviewer in the development identity selector.'}
        rows=[]
        with database.session(ctx) as s:
            for row in data.get('scenarios',[])[:20]:
                # Decisions always come from retained, authorized evaluations;
                # a seed manifest cannot author an outcome or cross-scope link.
                evaluation=finance.get(s,Evaluation,ctx,UUID(row['evaluation_id']))
                transaction=finance.get(s,Transaction,ctx,evaluation.transaction_id)
                if row.get('document_id'):finance.get(s,Document,ctx,UUID(row['document_id']))
                if row.get('original_evaluation_id'):finance.get(s,Evaluation,ctx,UUID(row['original_evaluation_id']))
                rows.append({'key':row['key'],'label':row['label'],'decision':evaluation.decision,
                    'transaction_version':evaluation.transaction_version,'current_version':transaction.latest_version,
                    'case_url':'/cases/'+str(transaction.id),'report_url':'/reports/'+str(evaluation.id),
                    'document_url':'/documents/'+str(UUID(row['document_id'])) if row.get('document_id') else None,
                    'original_report_url':'/reports/'+str(UUID(row['original_evaluation_id'])) if row.get('original_evaluation_id') else None,
                    'provider':row.get('provider'),'source_corrections':row.get('source_corrections')})
        return {'synthetic':True,'ready':bool(data.get('complete')),'items':rows,'message':'Computed synthetic scenarios. Open each case to inspect current eligibility, source evidence and retained history.'}
