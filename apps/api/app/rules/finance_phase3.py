"""Versioned deterministic controls over fully pinned Phase-3 facts.

The legacy evaluator remains available for retained contexts. This extension is
selected by an explicitly activated reference profile, never by client authority.
"""
from dataclasses import replace
from datetime import date, datetime
from decimal import Decimal, localcontext
import json
from uuid import UUID
from app.core.serialization import projection
from app.domain.evidence import EvidenceReference,EvidenceKind
from app.rules.engine import RuleResult,Decision,RuleContext,RULE_IDS
from app.rules.document_sources import evaluate_sources
from app.services.reference_imports import effective, select_policy

RULESET='rules-p3-v1'
VERSION='3.0.0'
EXTRA_IDS=('REF-001','DUP-001','DUP-003','EXP-002','EXP-004','EXP-005','EXP-006','PAT-001')
D=Decimal
Z=D('0')


def combine(results,waivers=()):
    expected=set(RULE_IDS)|set(EXTRA_IDS)
    if len(results)!=len(expected) or {r.rule_id for r in results}!=expected:raise ValueError('All Phase-3 controls must return exactly one result.')
    waived={w['rule_id'] for w in waivers}
    active=[r for r in results if r.rule_id not in waived]
    complete=all(r.status not in ('UNKNOWN','ERROR') for r in active if r.required)
    decision='HOLD' if any(r.decision_effect=='HOLD' for r in active) else 'REVIEW' if any(r.decision_effect=='REVIEW' or r.required and r.status in ('UNKNOWN','ERROR') for r in active) else 'PASS'
    return Decision(decision,'COMPLETE' if complete else 'INCOMPLETE',decision=='PASS' and complete,tuple(results))


def evaluate(context):
    c=json.loads(context.encoded)
    if not c.get('finance_v3'):return evaluate_sources(context)
    with localcontext() as dc:
        dc.prec=60
        return _evaluate(c)


def _evaluate(c):
    p=c['transaction'];refs=c['references'];v=c['finance_v3'];vendor=p['branch']=='VENDOR_INVOICE';day=p.get('invoice_date' if vendor else 'expense_date');total=p.get('total_amount' if vendor else 'requested_amount');total=D(total) if total is not None else None
    # Authorized shares resolve receipt reuse, while source consistency is still checked.
    core=dict(c)
    if v.get('receipt_shares'):core['receipt_conflicts']=[]
    results={r.rule_id:r for r in evaluate_sources(RuleContext.pin(**core)).results}
    def ev(record=None,kind='TRANSACTION',field=None):
        record=record or {'id':c['transaction_id'],'version':c['transaction_version']}
        return EvidenceReference(EvidenceKind(kind),UUID(record['id']),record.get('version',1),UUID(c['tenant_id']),UUID(c['legal_entity_id']),field_path=field,snapshot_id=UUID(c['snapshot_id']))
    def put(rid,status,reason,observed=None,expected=None,evidence=(),failure='REVIEW',tolerance=None):
        results[rid]=RuleResult(rid,VERSION,status,'NONE' if status in ('PASS','NOT_APPLICABLE') else failure,reason,projection(observed),projection(expected),tolerance,tuple([ev()]+list(evidence)))
    def check(rid,ok,reason,observed=None,expected=None,evidence=(),failure='HOLD',tolerance=None):put(rid,'PASS' if ok else 'FAIL',reason,observed,expected,evidence,failure,tolerance)
    def na(rid,reason='Control does not apply to this branch.'):put(rid,'NOT_APPLICABLE',reason,p['branch'])
    def ref(key,kind):
        r=refs.get(str(p.get(key)));return r if r and r.get('_kind')==kind else None
    profile=v['profile'];employee=ref('employee_id','employees')
    selected,policy_candidates=select_policy(refs,'approval_policies',p,day,employee)
    expense,expense_candidates=select_policy(refs,'expense_policies',p,day,employee) if not vendor else (None,[])
    stale=v.get('stale_references',[]);policy_valid=selected and selected['id']==p.get('approval_policy_id') and (vendor or expense and expense['id']==p.get('expense_policy_id'))
    put('REF-001','PASS' if policy_valid and not stale else 'UNKNOWN','Exactly one effective policy and fresh activated source is required.',{'approval_candidates':[r['id'] for r in policy_candidates],'expense_candidates':[r['id'] for r in expense_candidates],'stale_reference_ids':stale},'Unique applicable versions', [ev(r,'POLICY_CLAUSE') for r in policy_candidates+expense_candidates],failure='REVIEW')
    comparisons=v.get('duplicates',[])
    confirmed=[r for r in comparisons if r.get('disposition')=='CONFIRMED_DUPLICATE' or r['classification']=='STRONG_BUSINESS_MATCH' and r.get('disposition') not in ('DISTINCT','SHARED_RECEIPT_ALLOCATION') and r['signals'].get('active_obligation')]
    possible=[r for r in comparisons if r not in confirmed and r.get('disposition') not in ('DISTINCT','SHARED_RECEIPT_ALLOCATION') and r['classification'] not in ('DISTINCT','SHARED_RECEIPT_ALLOCATION')]
    duplicate_ev=[ev(r,'HISTORICAL_AGGREGATE') for r in comparisons]
    exact_ids=set(results['DUP-002'].observed.get('matching_record_ids',[])) if vendor and isinstance(results['DUP-002'].observed,dict) else set()
    cleared={r['candidate_id'] for r in comparisons if r.get('disposition')=='DISTINCT'}
    if exact_ids and exact_ids<=cleared:
        put('DUP-002','PASS','All exact matches have an explicit DISTINCT disposition bound to both current versions.',{'matching_record_ids':sorted(exact_ids),'resolution_ids':[r['resolution_id'] for r in comparisons if r.get('disposition')=='DISTINCT']},'Authorized distinct obligations',duplicate_ev)
    check('DUP-001',not possible,'Image, file and fuzzy similarities produce candidates; they do not prove duplication.',{'comparisons':comparisons,'coverage':v.get('duplicate_coverage')},'Resolved candidate set',duplicate_ev,failure='REVIEW')
    check('DUP-003',not confirmed,'A corroborated active business match or explicit confirmed disposition blocks repeated reimbursement.',{'confirmed_comparison_ids':[r['id'] for r in confirmed]},'No confirmed repeated obligation',duplicate_ev)
    if vendor:
        _vendor(c,v,refs,p,total,day,put,check,ev)
        accounts=[r for r in refs.values() if r.get('_kind')=='payment_accounts' and r.get('vendor_id')==p.get('vendor_id')]
        if accounts:
            applicable=[r for r in accounts if effective(r,day) and r.get('status')=='APPROVED']
            source=ref('source_document_id','documents');source_token=source and source.get('facts',{}).get('payment_account_token')
            verified=bool(len(applicable)==1 and applicable[0].get('equality_token') and applicable[0]['equality_token']==p.get('payment_account_token')==source_token)
            put('VEN-003','PASS' if verified else 'FAIL','Payment instructions must exactly match the single effective approved account version and source; extracted changes never update masters.',{'applicable_account_ids':[r['id'] for r in applicable],'comparison':'VERIFIED_EQUAL' if verified else 'UNVERIFIED_OR_CHANGED'},'Exact approved equality token',[ev(r,'MASTER_RECORD') for r in accounts],failure='HOLD')
        current=v.get('current_vendor_restriction')
        if current and current.get('status')!='ACTIVE_APPROVED':check('VEN-002',False,'Current mandatory vendor restriction prevents eligibility even when the transaction-date master was approved.',{'current_status':current.get('status'),'current_version':current['version']},'Current ACTIVE_APPROVED master',[ev(current,'MASTER_RECORD')])
        for rid in ('EXP-002','EXP-004','EXP-005','EXP-006','PAT-001'):na(rid)
    else:
        _expense(c,v,refs,p,total,day,employee,expense,put,check,ev)
    budget=ref('budget_id','budgets');b=v.get('budget');valid=bool(budget and b and total is not None and effective(budget,day) and budget.get('basis')=='GROSS' and budget.get('currency')==p.get('currency') and p.get('category') in budget.get('covered_categories',[]) and budget.get('cost_center_id')==p.get('cost_center_id'))
    for field in ('department','project','fiscal_period'):
        if p.get(field) is not None:valid=bool(valid and budget and p[field]==budget.get(field))
    if valid:
        covered=D(b['po_commitment_coverage']);incremental=max(Z,total-covered)
        check('BUD-001',D(b['available'])>=incremental,'Incremental gross need is checked against allocation, adjustments, consumption, open commitments and active reservations.',b|{'incremental_exposure':str(incremental)},'Available >= incremental need',[ev(budget,'MASTER_RECORD')]+[ev({'id':i,'version':1},'BUDGET_LEDGER') for i in b['ledger_event_ids']])
    else:put('BUD-001','UNKNOWN','A matching explicit same-currency budget is required; missing dimensions do not imply unlimited capacity.',b,'Matching budget',failure='HOLD')
    a=v.get('approval',{});steps=a.get('steps',[]);complete=bool(a.get('policy_valid') and steps and all(s.get('state')=='APPROVED' and s.get('authorized') for s in steps))
    evidence=[ev(selected,'POLICY_CLAUSE')] if selected else []
    evidence += [ev({'id':s['record_id'],'version':1},'APPROVAL') for s in steps if s.get('record_id')]
    check('APR-001',complete,'Ordered current-version approval steps must be complete.',{'steps':steps,'policy_id':a.get('policy_id'),'policy_version':a.get('policy_version')},'Complete version-bound chain',evidence)
    check('APR-002',complete and a.get('authority_valid',False),'Server-bound approvers require role, scope, currency, ceiling, effective authority, valid delegation and separation of duties.',{'steps':steps},'Authorized distinct actors',evidence)
    if vendor and p.get('contract_id') and not p.get('po_id'):
        missing=[k for k in results['VAL-001'].observed.get('missing',[]) if k!='po_id']
        put('VAL-001','UNKNOWN' if missing else 'PASS','An authorized contract supplies the non-PO commercial route.',{'missing':missing},'Required contract-route facts')
    partial=not vendor and any(i.get('claimed_amount')!=i.get('receipt_total_amount') for i in p['items'])
    supported=p.get('document_type')=='ORDINARY' and p.get('currency') in profile['currencies'] and c.get('context_complete') is True and (not partial or bool(v.get('receipt_shares'))) and not v.get('already_consumed')
    put('SYS-001','PASS' if supported else 'UNKNOWN','RULES_ONLY context is supported; no risk score or payment execution.' if supported else 'Unsupported type/currency, incomplete context or unallocated partial receipt requires input.',{'model_status':'NOT_CONFIGURED','partial_receipt':partial},'Supported deterministic context')
    waivers=[w for w in v.get('waivers',[]) if w['rule_id'] in profile['waivable_rules'] and w['rule_version']==results.get(w['rule_id'],results['SYS-001']).version and w['expires_at']>c['evaluated_at']]
    return combine(list(results.values()),waivers)


def _vendor(c,v,refs,p,total,day,put,check,ev):
    po=refs.get(str(p.get('po_id')));contract=refs.get(str(p.get('contract_id')));route=po if p.get('po_id') else contract;contract_route=not p.get('po_id') and contract is not None
    kind='CONTRACT' if contract_route else 'MASTER_RECORD'
    valid=bool(route and effective(route,day) and route.get('status')=='APPROVED_OPEN' and (not contract_route or route.get('non_po_authorized') is True))
    check('PO-001',valid,'Explicit PO takes priority; a non-PO route requires an effective approved contract and cited authorization.',{'route':route and route['id'],'contract_route':contract_route},'Approved commercial route',[ev(route,kind)] if route else [])
    association=bool(route and all(route.get(k)==p.get(k) for k in ('vendor_id','currency','budget_id','category')))
    check('PO-002',association,'Commercial route must match vendor, currency, category and budget.',{'reference_candidates':v.get('commercial_candidates',[])},'Exact owned association',[ev(route,kind)] if route else [])
    rows=[];commercial_ev=[];quantity_ok=bool(p['lines']);price_ok=bool(p['lines']);received_ok=bool(p['lines']);unknown=False;receive_unknown=False;price_failure='HOLD'
    allocations=v.get('allocations',[])
    def used(resource,dimension):return sum((D(r[dimension]) for r in allocations if r['resource_id']==resource),Z)
    for line in p['lines']:
        lid=line.get('contract_line_id') if contract_route else line.get('po_line_id');master=refs.get(str(lid));expected_kind='contract_lines' if contract_route else 'po_lines'
        if not master or master.get('_kind')!=expected_kind or any(line.get(k) is None for k in ('quantity','unit_price','gross_amount','uom')):
            unknown=True;receive_unknown=True;continue
        conversion=Z
        if line['uom']==master['uom']:conversion=D('1')
        else:
            found=[r for r in refs.values() if r.get('_kind')=='uom_conversions' and r.get('from_uom')==line['uom'] and r.get('to_uom')==master['uom'] and r.get('status')=='APPROVED' and effective(r,day)]
            if len(found)==1:conversion=D(found[0]['factor']);commercial_ev.append(ev(found[0],'MASTER_RECORD'))
            else:unknown=True;receive_unknown=True;continue
        qty=D(line['quantity'])*conversion;price=D(line['unit_price'])/conversion
        terms=master.get('tolerance',{});absolute=D(terms.get('price_absolute_amount','0'));relative=abs(D(master['unit_price']))*D(terms.get('price_relative_rate','0'));operator=terms.get('operator');delta=abs(price-D(master['unit_price']))
        tolerance=max(absolute,relative) if operator in ('MAX','OR') else min(absolute,relative) if operator in ('MIN','AND') else None
        if tolerance is None:unknown=True
        price_ok=bool(price_ok and tolerance is not None and delta<=tolerance and master.get('po_id' if not contract_route else 'contract_id')==route['id'] and master.get('currency',p['currency'])==p['currency'] and master.get('vendor_id',p['vendor_id'])==p['vendor_id'] and master.get('tax_basis',p['tax_basis'])==p['tax_basis'] and master.get('tax_rate',line.get('tax_rate'))==line.get('tax_rate'))
        if terms.get('failure_effect')=='REVIEW':price_failure='REVIEW'
        limit=master.get('ordered_quantity',master.get('maximum_quantity'))
        historical=sum((D(r['quantity']) for r in refs.values() if r.get('_kind')=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('po_line_id')==lid),Z)
        prior=historical+used(lid,'quantity');remaining=D(limit)-prior if limit is not None else None
        quantity_ok=bool(quantity_ok and (contract_route and limit is None or remaining is not None and qty>0 and qty<=remaining))
        receipt_id=line.get('service_acceptance_id') if contract_route or route and route.get('acceptance_type')=='SERVICE' else line.get('grn_line_id');receipt=refs.get(str(receipt_id));receipt_remaining=None
        if contract_route or route and route.get('acceptance_type')=='SERVICE':
            mandatory=route.get('acceptance_required',True)
            accepter=refs.get(str(receipt.get('accepter_id'))) if receipt else None
            valid_receipt=bool(receipt and receipt.get('_kind')=='service_acceptances' and receipt.get('contract_id',route['id'])==route['id'] and receipt.get('contract_line_id',lid)==lid and receipt.get('status')=='ACCEPTED' and accepter and accepter.get('status')=='ACTIVE' and 'SERVICE_ACCEPTER' in accepter.get('roles',[]) and effective(accepter,receipt.get('accepted_date',day)))
            if mandatory and not valid_receipt:received_ok=False
            if valid_receipt:
                receipt_remaining=D(receipt['accepted_quantity'])-used(receipt['id'],'quantity')
                received_ok=bool(received_ok and qty<=receipt_remaining and D(line['gross_amount'])<=D(receipt['accepted_amount'])-used(receipt['id'],'amount'))
            if not mandatory:received_ok=received_ok and True
        else:
            if not receipt or receipt.get('_kind')!='grn_lines':receive_unknown=True
            else:
                prior_receipt=sum((D(r['quantity']) for r in refs.values() if r.get('_kind')=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('grn_line_id')==receipt_id),Z)+used(receipt_id,'quantity')
                receipt_remaining=D(receipt['accepted_quantity'])-D(receipt['returned_quantity'])-D(receipt['reversed_quantity'])-prior_receipt
                received_ok=bool(received_ok and receipt.get('po_line_id')==lid and receipt.get('po_id')==p.get('po_id') and receipt.get('uom')==master['uom'] and qty>0 and qty<=receipt_remaining)
        commercial_ev.append(ev(master,'CONTRACT' if contract_route else 'PO_LINE'))
        if receipt:commercial_ev.append(ev(receipt,'CONTRACT' if contract_route else 'GRN_LINE'))
        eligible=min(remaining,receipt_remaining) if remaining is not None and receipt_remaining is not None else receipt_remaining
        rows.append({'line_id':line['id'],'commercial_line_id':lid,'receipt_id':receipt_id,'conversion_factor':str(conversion),'requested_quantity':str(qty),'prior_quantity':str(prior),'ordered_remaining':str(remaining) if remaining is not None else None,'received_remaining':str(receipt_remaining) if receipt_remaining is not None else None,'eligible_new_quantity':str(eligible) if eligible is not None else None,'quantity_shortfall':str(max(Z,qty-eligible)) if eligible is not None else None,'unit_price_variance':str(price-D(master['unit_price'])),'absolute_tolerance':str(absolute),'relative_tolerance':str(relative),'tolerance_operator':operator,'applied_tolerance':str(tolerance) if tolerance is not None else None,'amount':line['gross_amount'],'allocation_kind':'CONTRACT' if contract_route else 'PO_LINE','receipt_kind':'SERVICE' if contract_route or route and route.get('acceptance_type')=='SERVICE' else 'GRN_LINE'})
    for charge in ('shipping_amount','other_charges_amount'):
        if p.get(charge) is None:unknown=True
        elif D(p[charge])!=0 and (not route or D(p[charge])!=D(route.get('approved_charges',{}).get(charge,'0'))):price_ok=False
    # Aggregate repeated commercial/receipt line claims; a per-row check alone is unsafe.
    for field,remaining_field in [('commercial_line_id','ordered_remaining'),('receipt_id','received_remaining')]:
        for key in {r[field] for r in rows if r[field]}:
            selected=[r for r in rows if r[field]==key];requested=sum((D(r['requested_quantity']) for r in selected),Z);available=selected[0][remaining_field]
            if available is not None and requested>D(available):
                if field=='commercial_line_id':quantity_ok=False
                else:received_ok=False
    for key in {r['receipt_id'] for r in rows if r['receipt_id'] and r['receipt_kind']=='SERVICE'}:
        requested=sum((D(r['amount']) for r in rows if r['receipt_id']==key),Z)
        if requested>D(refs[key]['accepted_amount'])-used(key,'amount'):received_ok=False
    prior_value=sum((D(r['amount']) for r in allocations if r['kind'] in ('PO_LINE','CONTRACT') and r.get('metadata',{}).get('commercial_id')==(route and route['id'])),Z)
    prior_value+=sum((D(r['amount']) for r in refs.values() if r.get('_kind')=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('po_id')==p.get('po_id')),Z) if not contract_route else Z
    ceiling=D(route['approved_ceiling_amount'])-prior_value if route else None
    quantity_ok=bool(quantity_ok and total is not None and ceiling is not None and Z<total<=ceiling)
    if contract_route and p.get('service_from') and p.get('service_to'):quantity_ok=bool(quantity_ok and route['effective_from']<=p['service_from']<=p['service_to']<route['effective_to'])
    put('PO-003','UNKNOWN' if unknown else 'PASS' if price_ok else 'FAIL','Approved UOM conversion and explicit absolute/relative tolerance operator govern price variance.',rows,'Approved commercial terms',commercial_ev,failure='HOLD' if unknown else price_failure)
    put('PO-004','UNKNOWN' if unknown or ceiling is None else 'PASS' if quantity_ok else 'FAIL','Cumulative ordered quantity and commercial ceiling include prior reserved/settled allocations exactly once.',{'lines':rows,'remaining_value':str(ceiling) if ceiling is not None else None,'prior_value':str(prior_value)},'Remaining capacity covers current request',commercial_ev,failure='HOLD')
    put('GRN-001','UNKNOWN' if receive_unknown else 'PASS' if received_ok else 'FAIL','Accepted goods net of returns/reversals or independently authorized service acceptance must cover current lines.',rows,'Accepted remaining delivery capacity',commercial_ev,failure='HOLD')


def _expense(c,v,refs,p,total,day,employee,policy,put,check,ev):
    delegation=v.get('submission_delegation');on_behalf=employee and c['author_id']!=employee['id']
    employee_ok=bool(employee and effective(employee,day) and employee.get('status')=='ACTIVE' and employee.get('employment_from','0001-01-01')<=day<(employee.get('employment_to') or '9999-12-31') and employee.get('cost_center_id')==p.get('cost_center_id') and employee.get('department')==p.get('department'))
    # Finance intake is an explicit trusted submission role, not a receipt inference.
    submission_ok=not on_behalf or v.get('finance_submission_authorized') or bool(delegation)
    check('EMP-001',employee_ok and submission_ok,'Claimant master and submitter are resolved separately; on-behalf submission requires configured authority or delegation.',{'employee_id':p.get('employee_id'),'submitter_id':c['author_id'],'on_behalf':on_behalf,'delegation_id':delegation and delegation['id']},'Active scoped claimant and authorized submitter',[ev(employee,'MASTER_RECORD')] if employee else [])
    constraints=[];missing=[];failed=[]
    if not policy:missing.append('unique_effective_policy')
    else:
        if policy.get('allowed') is False:failed.append('category_not_allowed')
        if policy.get('business_purpose_required') and not p.get('business_purpose'):missing.append('business_purpose')
        if policy.get('attendees_required') and not p.get('attendees'):missing.append('attendees')
        if policy.get('travel_classes') and p.get('travel_class') not in policy['travel_classes']:failed.append('travel_class')
        if policy.get('merchant_denylist') and p.get('merchant') in policy['merchant_denylist']:failed.append('merchant_restriction')
        if policy.get('preapproval_required') and not v.get('verified_preapproval'):missing.append('verified_preapproval')
        if p.get('submission_date') and (date.fromisoformat(p['submission_date'])-date.fromisoformat(day)).days>policy['submission_window_days']:failed.append('submission_window')
        for unit,key in [('ITEM','per_item_limit'),('TRIP','trip_limit'),('MONTH','monthly_limit')]:
            if policy.get(key):
                aggregate=v.get('aggregates',{}).get(unit)
                if aggregate is None:missing.append(unit+'_context')
                else:
                    constraints.append({'unit':unit,'amount':aggregate['amount'],'limit':policy[key],'related_ids':aggregate['related_ids']})
                    if D(aggregate['amount'])>D(policy[key]):failed.append(key)
    put('EXP-002','UNKNOWN' if missing else 'FAIL' if failed else 'PASS','Policy prerequisites and configured item/trip/month limits apply to exact dimensions.',{'missing':missing,'failed':failed,'limits':constraints},'Configured requirements satisfied',[ev(policy,'POLICY_CLAUSE')] if policy else [],failure='REVIEW')
    payments=v.get('company_payments',[]);computed=Z;parts=[];offset_unknown=False
    for item in p['items']:
        confirmed=[r for r in payments if r.get('document_id')==item.get('source_document_id') and r.get('employee_id')==p.get('employee_id') and r.get('status')=='CONFIRMED' and r.get('currency')==p.get('currency')]
        paid=sum((D(r['amount']) for r in confirmed if r.get('payment_type')=='COMPANY_CARD'),Z);advance=sum((D(r['amount']) for r in confirmed if r.get('payment_type')=='ADVANCE'),Z)
        claimed=item.get('claimed_amount')
        if claimed is None:offset_unknown=True;continue
        stated_paid=item.get('company_paid_amount');stated_advance=item.get('applied_advance_amount')
        # Explicit zero with no confirmed payment is valid; positive offsets require ledger proof.
        if stated_paid is None or stated_advance is None or D(stated_paid)!=paid or D(stated_advance)!=advance:offset_unknown=True
        eligible=D(item.get('eligible_business_amount') or claimed);reimbursement=eligible-paid-advance;computed+=reimbursement
        parts.append({'item_id':item['id'],'eligible_business_amount':str(eligible),'company_paid_amount':str(paid),'applied_advance':str(advance),'computed_reimbursement':str(reimbursement),'requested_share':claimed,'payment_ids':[r['id'] for r in confirmed]})
    double=bool(total is not None and computed<total and payments)
    put('EXP-004','UNKNOWN' if offset_unknown else 'PASS' if total is not None and computed==total else 'FAIL','Requested reimbursement is preserved separately from eligible business amount less verified company-card/advance offsets.',{'requested':str(total),'computed_reimbursement':str(computed),'items':parts},'Requested equals supported reimbursement',[ev(r,'MASTER_RECORD') for r in payments],failure='HOLD' if double else 'REVIEW')
    shares=v.get('receipt_shares',[]);prior=v.get('receipt_usage',[]);receipt_rows=[];over=False;share_missing=False
    for item in p['items']:
        did=item.get('source_document_id');amount=item.get('claimed_amount');capacity=item.get('receipt_total_amount');owned=[r for r in shares if r['item_id']==item['id'] and r['employee_id']==p.get('employee_id') and r['document_id']==did]
        others=[r for r in prior if r['resource_id']==did];used=sum((D(r['amount']) for r in others),Z)
        if amount is None or capacity is None:share_missing=True;continue
        all_current=sum((D(i['claimed_amount']) for i in p['items'] if i.get('source_document_id')==did and i.get('claimed_amount') is not None),Z)
        if D(amount)!=D(capacity) and (len(owned)!=1 or D(owned[0]['amount'])!=D(amount)):share_missing=True
        if others and not owned:share_missing=True
        over=over or used+all_current>D(capacity)
        receipt_rows.append({'document_id':did,'eligible_total':capacity,'prior_amount':str(used),'current_amount':str(all_current),'remaining':str(D(capacity)-used),'excess':str(max(Z,used+all_current-D(capacity))),'allocation_ids':[r['id'] for r in others],'share_ids':[r['id'] for r in owned]})
    put('EXP-005','FAIL' if over else 'UNKNOWN' if share_missing else 'PASS','Actual receipt capacity is shared only through authorized item/claimant shares; cumulative allocation cannot exceed eligible value.',receipt_rows,'Authorized shares within receipt capacity',[ev(r,'HISTORICAL_AGGREGATE') for r in prior]+[ev(r,'HISTORICAL_AGGREGATE') for r in shares],failure='HOLD' if over else 'REVIEW')
    check('EXP-006',not double,'Confirmed company-card/advance-covered expense cannot be requested for reimbursement again.',{'computed_reimbursement':str(computed),'requested':str(total),'payment_ids':[r['id'] for r in payments]},'No confirmed double reimbursement',[ev(r,'MASTER_RECORD') for r in payments])
    split=v.get('split_pattern');put('PAT-001','FAIL' if split else 'PASS','Related near-threshold claims are a possible split pattern requiring review; no intent is inferred.',split or {'related_ids':[]},'No unresolved configured split pattern',[ev(r,'HISTORICAL_AGGREGATE') for r in (split or {}).get('related_records',[])],failure='REVIEW')
