"""Explicit staged imports; only authorized activation makes a version evaluable."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
import re
from uuid import UUID, uuid4
from sqlalchemy import select, func
from rapidfuzz.fuzz import ratio
from app.core.errors import DomainError
from app.core.serialization import projection, utcnow
from app.db.models import ReferenceRecord,ReferenceLink
from app.db.finance_models import ReferenceBatch, ReferenceActivation
from app.db.session import scope_query
from app.services import finance
from app.services.references import number_key

KINDS={'vendors':('legal_name','status','approved_categories','payment_account_token'),
'employees':('name','status','grade','cost_center_id','department','roles','employment_from'),
'cost_centers':('department',), 'purchase_orders':('vendor_id','currency','status','budget_id','category','approved_ceiling_amount'),
'po_lines':('po_id','vendor_id','currency','ordered_quantity','unit_price','uom','tax_basis','tax_rate','tolerance'),
'goods_receipts':('po_id',), 'grn_lines':('po_id','po_line_id','accepted_quantity','returned_quantity','reversed_quantity','uom'),
'contracts':('vendor_id','currency','status','budget_id','category','approved_ceiling_amount','non_po_authorized','acceptance_required'),
'contract_lines':('contract_id','unit_price','uom','tolerance'),
'service_acceptances':('contract_id','contract_line_id','accepted_amount','accepted_quantity','accepter_id','status'),
'expense_policies':('category','currency','dimensions','unit','allowance_amount','submission_window_days','receipt_required','receipt_type','local_timezone'),
'approval_policies':('currency','branches','cost_center_id','department','bands','separation_of_duties'),
'budgets':('currency','basis','covered_categories','cost_center_id','ledger'),
'fx_rates':('from_currency','to_currency','rate','business_date','convention'),
'delegations':('delegator_id','delegate_id','purpose','roles','ceiling_amount','currency','cost_center_id'),
'uom_conversions':('from_uom','to_uom','factor','status'),
'payment_accounts':('vendor_id','equality_token','status'),
'company_payments':('employee_id','document_id','amount','currency','payment_type','status'),
'finance_profiles':('ruleset','currencies','duplicate_window_days','near_amount_absolute','fuzzy_number_cutoff','phash_distance','waivable_rules','waiver_roles','freshness_days'),
'documents':('facts','verification','source_type'),
'budget_ledger':('budget_id','entry_type','amount','currency'),
'waiver_policies':('rule_ids','roles','maximum_days','nonwaivable_rules')}
LINKS={'vendor_id':'vendors','employee_id':'employees','cost_center_id':'cost_centers','po_id':'purchase_orders','po_line_id':'po_lines','contract_id':'contracts','contract_line_id':'contract_lines','accepter_id':'employees','delegator_id':'employees','delegate_id':'employees','budget_id':'budgets','manager_id':'employees'}
PERIOD_KINDS={'vendors','employees','purchase_orders','contracts','expense_policies','approval_policies','budgets','delegations','uom_conversions','payment_accounts','waiver_policies','finance_profiles'}


def require(identity,role):
    if role not in identity.roles:raise DomainError(403,'FORBIDDEN',f'{role} permission is required.')


def active_records(session,identity,business_day=None):
    """Latest explicitly activated version; seeded legacy versions are grandfathered only at v1."""
    activated=set(session.execute(scope_query(select(ReferenceActivation.record_id,ReferenceActivation.record_version),ReferenceActivation,identity)).all())
    rows=session.scalars(scope_query(select(ReferenceRecord),ReferenceRecord,identity).where(ReferenceRecord.kind.not_in(['historical_transactions','matching_allocations'])).order_by(ReferenceRecord.id,ReferenceRecord.version).limit(2001)).all()
    if len(rows)>2000:raise DomainError(503,'REFERENCE_LIMIT','Narrow the reference catalog before activation.')
    selected={}
    applicable={}
    for r in rows:
        if not ((r.id,r.version) in activated or not r.payload.get('import_batch_id')):continue
        selected[str(r.id)]=r
        if business_day and r.kind in ('expense_policies','approval_policies','contracts','delegations','uom_conversions') and effective(r.payload,business_day):applicable[str(r.id)]=r
    selected.update(applicable)
    return selected


def validate_records(records,current,identity):
    errors=[];seen=set();sources=set();known=dict(current)
    for i,entry in enumerate(records):
        p=entry.get('payload',{});kind=entry.get('kind');rid=p.get('id');where=f'records.{i}'
        def error(code,field=''):errors.append({'field':where+('.'+field if field else ''),'code':code})
        try:UUID(rid);assert isinstance(p.get('version'),int) and not isinstance(p['version'],bool) and p['version']>0
        except (ValueError,TypeError,KeyError,AssertionError):error('IDENTITY_INVALID');continue
        if rid in seen:error('DUPLICATE_ID')
        seen.add(rid)
        source=p.get('source_record_id',rid)
        if (kind,source) in sources:error('DUPLICATE_SOURCE_ID')
        sources.add((kind,source))
        if kind not in KINDS:error('KIND_UNSUPPORTED');continue
        if any(p.get(k) is None for k in KINDS[kind]):error('REQUIRED_FIELD')
        if p.get('tenant_id') not in (None,str(identity.tenant_id)) or p.get('legal_entity_id') not in (None,str(identity.legal_entity_id)):error('FOREIGN_SCOPE')
        old=current.get(rid)
        if old and p['version']<=old.version:error('VERSION_NOT_NEW')
        if old and kind!=old.kind:error('KIND_IMMUTABLE')
        if kind in PERIOD_KINDS:
            try:assert date.fromisoformat(p['effective_from'])<date.fromisoformat(p['effective_to'])
            except (ValueError,KeyError,TypeError,AssertionError):error('PERIOD_INVALID')
        if p.get('currency') and p['currency'] not in ('INR','USD','EUR','GBP'):error('CURRENCY_UNKNOWN')
        def inspect(value,path='payload'):
            if isinstance(value,dict):
                for key,v in value.items():
                    if key in ('bank_account_number','iban','routing_number','account_number','bank_details') and v is not None:error('RAW_BANK_DATA_FORBIDDEN',path+'.'+key)
                    if any(t in key for t in ('amount','quantity','price','rate','factor')) and v is not None and not isinstance(v,(list,dict)):
                        try:assert isinstance(v,str) and re.fullmatch(r'\d{1,14}(?:\.\d{1,6})?',v) and Decimal(v).is_finite()
                        except (InvalidOperation,AssertionError,TypeError):error('DECIMAL_STRING_REQUIRED',path+'.'+key)
                    inspect(v,path+'.'+key)
            elif isinstance(value,list):
                for n,v in enumerate(value):inspect(v,f'{path}.{n}')
        inspect(p)
        if any(r.payload.get('source_record_id',str(getattr(r,'id','')))==source and r.kind==kind and key!=rid for key,r in current.items()):error('DUPLICATE_SOURCE_ID')
        if kind in ('po_lines','contract_lines'):
            t=p.get('tolerance',{})
            if t.get('operator') not in ('MAX','MIN','AND','OR') or any(k not in t for k in ('price_absolute_amount','price_relative_rate')):error('TOLERANCE_INVALID')
        if kind=='fx_rates':
            if p.get('from_currency') not in ('INR','USD','EUR','GBP') or p.get('to_currency') not in ('INR','USD','EUR','GBP') or p.get('from_currency')==p.get('to_currency'):error('FX_PAIR_INVALID')
            try:assert Decimal(p['rate']).is_finite() and Decimal(p['rate'])>0;date.fromisoformat(p['business_date'])
            except (ValueError,TypeError,KeyError,InvalidOperation,AssertionError):error('FX_RATE_INVALID')
        if kind=='grn_lines':
            try:assert Decimal(p['accepted_quantity'])>=Decimal(p['returned_quantity'])+Decimal(p['reversed_quantity'])
            except (InvalidOperation,TypeError,KeyError,AssertionError):error('GRN_NET_INVALID')
        if kind=='budgets':
            for ledger in p.get('ledger',[]):
                if ledger.get('entry_type') not in ('ALLOCATION','ADJUSTMENT','CONSUMPTION','PO_COMMITMENT','CLAIM_RESERVATION') or ledger.get('currency')!=p.get('currency'):error('BUDGET_LEDGER_INVALID')
                try:UUID(ledger['id']);assert Decimal(ledger['amount'])>=0
                except (KeyError,TypeError,ValueError,InvalidOperation,AssertionError):error('BUDGET_LEDGER_INVALID')
        if kind=='uom_conversions':
            try:approved=p.get('status')=='APPROVED' and isinstance(p.get('factor'),str) and Decimal(p['factor']).is_finite() and Decimal(p['factor'])>0
            except (InvalidOperation,ValueError,TypeError,KeyError):approved=False
            if not approved:error('UOM_NOT_APPROVED')
        if kind=='finance_profiles':
            if p.get('ruleset')!='rules-p3-v1' or p.get('currencies')!=['INR']:error('UNSUPPORTED_FINANCE_PROFILE')
            nonwaivable={'VEN-003','DUP-002','GRN-001','BUD-001','APR-001','APR-002','EXP-005','VAL-001','VAL-003'}
            nonwaivable.update({'REF-001','SYS-001','EXP-001','EXP-004'})
            if nonwaivable.intersection(p.get('waivable_rules',[])):error('NONWAIVABLE_CONTROL')
            for key,lower,upper in [('duplicate_window_days',0,31),('fuzzy_number_cutoff',50,100),('phash_distance',0,6),('freshness_days',1,365)]:
                value=p.get(key)
                if not isinstance(value,int) or isinstance(value,bool) or not lower<=value<=upper:error('CONFIGURATION_BOUNDS',key)
        known[rid]=type('Candidate',(),{'payload':p,'kind':kind,'version':p['version']})()
    for i,entry in enumerate(records):
        p=entry.get('payload',{});kind=entry.get('kind')
        for key,expected in LINKS.items():
            if p.get(key) and (str(p[key]) not in known or known[str(p[key])].kind!=expected):errors.append({'field':f'records.{i}.{key}','code':'BROKEN_LINK'})
        if kind=='grn_lines' and p.get('po_line_id') in known and known[p['po_line_id']].payload.get('po_id')!=p.get('po_id'):errors.append({'field':f'records.{i}.po_line_id','code':'ORPHAN_GRN'})
        if kind=='approval_policies':
            conditions=p.get('exception_roles',{})
            allowed={'PO-003','PO-004','DUP-001','DUP-003','GRN-001','EXP-002','EXP-003','EXP-004','EXP-005','EXP-006','PAT-001'}
            if not isinstance(conditions,dict) or any(k not in allowed or not isinstance(v,list) or not v or len(v)>4 or any(not isinstance(role,str) or len(role)>32 for role in v) for k,v in conditions.items()):errors.append({'field':f'records.{i}.exception_roles','code':'APPROVAL_CONDITIONS_INVALID'})
            bands=p.get('bands',[]);previous='0.00'
            for j,b in enumerate(bands):
                if b.get('lower_bound_amount')!=previous or j and not b.get('lower_inclusive') or b.get('upper_inclusive') or not b.get('required_roles'):errors.append({'field':f'records.{i}.bands.{j}','code':'POLICY_BAND_GAP_OR_OVERLAP'})
                previous=b.get('upper_bound_amount')
            if not bands or previous is not None:errors.append({'field':f'records.{i}.bands','code':'POLICY_BAND_GAP'})
    policies=[r for r in known.values() if r.kind in ('expense_policies','approval_policies','finance_profiles')]
    for i,a in enumerate(policies):
        for b in policies[i+1:]:
            x=a.payload;y=b.payload
            if a.kind!=b.kind:continue
            dims=('category','currency','cost_center_id','department')
            intersects=all(x.get(k) in (None,'ANY') or y.get(k) in (None,'ANY') or x.get(k)==y.get(k) for k in dims)
            if x.get('branches') and y.get('branches'):intersects=intersects and bool(set(x['branches'])&set(y['branches']))
            dx=x.get('dimensions',{});dy=y.get('dimensions',{})
            intersects=intersects and all(dx.get(k) in (None,'ANY') or dy.get(k) in (None,'ANY') or dx.get(k)==dy.get(k) for k in set(dx)|set(dy))
            if intersects and x.get('effective_from','')<y.get('effective_to','') and y.get('effective_from','')<x.get('effective_to',''):
                errors.append({'field':'policies','code':'POLICY_OVERLAP','ids':[x['id'],y['id']]})
    return errors


def stage(session,identity,data,correlation):
    require(identity,'REFERENCE_ADMIN')
    row=ReferenceBatch(**identity.scope(),source_system=data['source_system'],source_version=data['source_version'],actor_id=identity.actor_id,records=data['records'],state='STAGED',validation=[])
    session.add(row);session.flush();finance.audit(session,identity,'REFERENCE_STAGED',row.id,1,data['reason'],correlation,{'record_count':len(row.records)})
    return batch_view(row)


def batch_view(row):return projection({'id':row.id,'source_system':row.source_system,'source_version':row.source_version,'state':row.state,'records':row.records,'validation':row.validation,'imported_at':row.created_at})


def validate(session,identity,batch_id,correlation):
    require(identity,'REFERENCE_ADMIN');finance.scope_lock(session,identity);row=finance.get(session,ReferenceBatch,identity,batch_id)
    if row.state not in ('STAGED','VALID','INVALID'):raise DomainError(409,'BATCH_FINALIZED','This batch is already activated.')
    row.validation=validate_records(row.records,active_records(session,identity),identity)
    row.state='INVALID' if row.validation else 'VALID'
    finance.audit(session,identity,'REFERENCE_VALIDATED',row.id,1,'Staged references checked',correlation,{'state':row.state,'error_count':len(row.validation),'validation':row.validation})
    return batch_view(row)


def activate(session,identity,batch_id,reason,correlation):
    require(identity,'REFERENCE_ADMIN');finance.scope_lock(session,identity);row=finance.get(session,ReferenceBatch,identity,batch_id)
    if row.state=='ACTIVE':return batch_view(row)
    if row.state!='VALID':raise DomainError(409,'BATCH_NOT_VALID','Validate this reference batch first.')
    errors=validate_records(row.records,active_records(session,identity),identity)
    if errors:raise DomainError(409,'REFERENCE_CHANGED','Revalidate against the current activated catalog.',details=errors)
    for entry in row.records:
        p=dict(entry['payload']);kind=entry['kind'];p.update(tenant_id=str(identity.tenant_id),legal_entity_id=str(identity.legal_entity_id),source_system=row.source_system,source_record_id=p.get('source_record_id',p['id']),source_version=row.source_version,import_batch_id=str(row.id),imported_at=utcnow().isoformat(),validation_result='VALID')
        rid=UUID(p['id']);old=session.get(ReferenceRecord,(rid,p['version']))
        if old:raise DomainError(409,'VERSION_EXISTS','An immutable version already exists.')
        amt=p.get('total_amount',p.get('requested_amount',p.get('amount')));day=p.get('invoice_date',p.get('expense_date'))
        r=ReferenceRecord(**identity.scope(),id=rid,version=p['version'],kind=kind,label=p.get('legal_name',p.get('name',p.get('policy_code',p.get('code',p['id'])))),payload=p,amount=Decimal(amt) if amt else None,currency=p.get('currency'),business_date=date.fromisoformat(day) if day else None,party_id=UUID(p.get('vendor_id',p.get('employee_id'))) if p.get('vendor_id',p.get('employee_id')) else None,number_key=number_key(p.get('invoice_number',p.get('claim_number'))),effective_from=date.fromisoformat(p['effective_from']) if p.get('effective_from') else None,effective_to=date.fromisoformat(p['effective_to']) if p.get('effective_to') else None)
        session.add(r);session.flush();session.add(ReferenceActivation(**identity.scope(),batch_id=row.id,record_id=rid,record_version=p['version'],actor_id=identity.actor_id))
        if kind=='budgets':
            from app.services.finance_ledger import import_budget
            import_budget(session,identity,r,row.id)
    catalog=active_records(session,identity)
    session.flush()
    for entry in row.records:
        p=entry['payload']
        for field in LINKS:
            if p.get(field):
                parent=catalog[str(p[field])]
                session.add(ReferenceLink(**identity.scope(),child_id=UUID(p['id']),child_version=p['version'],parent_id=parent.id,parent_version=parent.version,relationship=field))
    row.state='ACTIVE';session.flush()
    finance.audit(session,identity,'REFERENCE_ACTIVATED',row.id,1,reason,correlation,{'versions':[{'id':e['payload']['id'],'version':e['payload']['version']} for e in row.records]})
    return batch_view(row)


def effective(p,day):return bool(day and p.get('effective_from','0001-01-01')<=day<p.get('effective_to','9999-12-31'))

def select_policy(refs,kind,p,day,employee=None):
    candidates=[]
    for r in refs.values():
        if r.get('_kind')!=kind or not effective(r,day):continue
        if r.get('currency') and r['currency']!=p.get('currency'):continue
        if r.get('category') and r['category']!=p.get('category'):continue
        if r.get('cost_center_id') and r['cost_center_id']!=p.get('cost_center_id'):continue
        if r.get('branches') and p['branch'] not in r['branches']:continue
        dims=r.get('dimensions',{})
        actual=dict(p);actual['grade']=(employee or {}).get('grade')
        if any(v not in (None,'ANY') and actual.get(k)!=v for k,v in dims.items()):continue
        candidates.append(r)
    return candidates[0] if len(candidates)==1 else None,candidates


def resolve(refs,kind,identifier=None,name=None,day=None):
    pool=[r for r in refs.values() if r.get('_kind')==kind and (day is None or effective(r,day))]
    exact=[r for r in pool if identifier and identifier in (r['id'],r.get('source_record_id'),r.get('employee_number'),r.get('tax_id'),r.get('tax_identifier'))]
    aliases=[r for r in pool if name and name.casefold().strip() in [a.casefold().strip() for a in [r.get('legal_name',r.get('name',''))]+r.get('aliases',[])]]
    found=exact if exact else aliases
    if len(found)==1:return {'state':'RESOLVED','method':'EXACT' if exact else 'CURATED_ALIAS','record':found[0],'candidates':[]}
    if found:return {'state':'AMBIGUOUS','method':'EXACT_OR_ALIAS','record':None,'candidates':found}
    ranked=[{'id':r['id'],'version':r['version'],'label':r.get('legal_name',r.get('name')),'similarity':ratio(name.casefold(),r.get('legal_name',r.get('name','')).casefold())} for r in pool] if name else []
    return {'state':'UNRESOLVED','method':'FUZZY_CANDIDATES','record':None,'candidates':sorted((r for r in ranked if r['similarity']>=65),key=lambda r:(-r['similarity'],r['id']))[:10]}
