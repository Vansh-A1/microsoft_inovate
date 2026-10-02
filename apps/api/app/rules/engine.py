"""Pure deterministic rules. No SQL, HTTP, model calls, clock reads or mutations."""
from dataclasses import asdict, dataclass
from datetime import date, datetime
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
import json
from uuid import UUID
from app.core.serialization import canonical_json, projection
from app.domain.money import Money
from app.domain.states import RuleStatus, DecisionEffect, ScreeningDecision
from app.domain.evidence import EvidenceReference, EvidenceKind, ImportCellLocator

RULESET = 'rules-p1-v5'
DECISION_POLICY = 'hold-first-p1-v1'
RULE_IDS = ('VAL-001','VAL-002','VAL-003','VEN-001','VEN-002','DUP-002','PO-001','PO-002','GRN-001','EMP-001','DOC-001','EXP-003','BUD-001','APR-001','SYS-001')
D = Decimal
ZERO = D('0')
TOLERANCE = D('0.01')


@dataclass(frozen=True)
class RuleContext:
    """Canonical JSON pins all supplied facts and context; caller mutation cannot affect a run."""
    encoded: str

    @classmethod
    def pin(cls, **inputs):
        return cls(canonical_json(inputs))


@dataclass(frozen=True)
class RuleResult:
    rule_id: str
    version: str
    status: str
    decision_effect: str
    reason: str
    observed: object
    expected: object
    tolerance: str | None
    evidence: tuple[EvidenceReference, ...]
    required: bool = True

    def __post_init__(self):
        RuleStatus(self.status)
        DecisionEffect(self.decision_effect)
        if self.status=='FAIL' and self.decision_effect=='NONE':raise ValueError('Failed required controls need an explicit escalation.')

    def json(self):
        return projection(asdict(self))


@dataclass(frozen=True)
class Decision:
    decision: str
    completeness: str
    eligible: bool
    results: tuple[RuleResult, ...]


def combine(results):
    if {r.rule_id for r in results} != set(RULE_IDS) or len(results) != len(RULE_IDS):
        raise ValueError('Every required control must have exactly one result.')
    complete = all(r.status not in ('UNKNOWN','ERROR') for r in results if r.required)
    hold = any(r.decision_effect == 'HOLD' for r in results)
    review = any(r.decision_effect == 'REVIEW' or (r.required and r.status in ('UNKNOWN','ERROR')) for r in results)
    decision = 'HOLD' if hold else 'REVIEW' if review else 'PASS'
    ScreeningDecision(decision)
    return Decision(decision, 'COMPLETE' if complete else 'INCOMPLETE', decision == 'PASS' and complete, tuple(results))


def evaluate(context: RuleContext):
    # All arithmetic is independent of process/thread ambient Decimal precision.
    with localcontext() as decimal_context:
        decimal_context.prec = 60
        decimal_context.rounding = ROUND_HALF_EVEN
        return _evaluate(json.loads(context.encoded))


def _evaluate(c):
    p=c['transaction'];refs=c['references'];vendor=p['branch']=='VENDOR_INVOICE'
    results=[]
    def ev(record=None,field=None,kind='TRANSACTION'):
        record=record or {'id':c['transaction_id'],'version':c['transaction_version']}
        return EvidenceReference(EvidenceKind(kind),UUID(record['id']),record['version'],UUID(c['tenant_id']),UUID(c['legal_entity_id']),field_path=field,snapshot_id=UUID(c['snapshot_id']))
    def ref(key,kind=None):
        r=refs.get(str(p.get(key)))
        return r if r and (not kind or r['_kind']==kind) else None
    def effective(r,day):
        return bool(r and day and (not r.get('effective_from') or r['effective_from']<=day) and (not r.get('effective_to') or day<r['effective_to']))
    def result(rid,status,reason,observed=None,expected=None,evidence=(),effect=None,tolerance=None):
        effect=effect or ('NONE' if status in ('PASS','NOT_APPLICABLE') else 'REVIEW')
        results.append(RuleResult(rid,'1.0.4',status,effect,reason,projection(observed),projection(expected),tolerance,tuple([ev()]+list(evidence))))
    def check(rid,ok,reason,observed=None,expected=None,evidence=(),failure='REVIEW',tolerance=None):
        result(rid,'PASS' if ok else 'FAIL',reason,observed,expected,evidence,'NONE' if ok else failure,tolerance)
    def na(rid):result(rid,'NOT_APPLICABLE','Control does not apply to this transaction branch.',p['branch'],'Applicable branch only')
    def amount(k):
        if p.get(k) is None:return None
        return Money(p[k],p['currency']).amount if p.get('currency') else D(p[k])
    total=amount('total_amount' if vendor else 'requested_amount')
    business_day=p.get('invoice_date' if vendor else 'expense_date')
    primary=ref('vendor_id' if vendor else 'employee_id','vendors' if vendor else 'employees')
    required=['currency','submission_date','category','cost_center_id','approval_policy_id','budget_id']+(['vendor_id','invoice_number','invoice_date','subtotal_amount','tax_amount','total_amount','tax_basis','document_discount_amount','shipping_amount','other_charges_amount','po_id'] if vendor else ['employee_id','claim_number','expense_date','requested_amount','expense_policy_id','local_timezone','business_purpose'])
    missing=[k for k in required if p.get(k) is None or p.get(k)=='']
    if not p.get('lines' if vendor else 'items'):missing.append('lines' if vendor else 'items')
    result('VAL-001','UNKNOWN' if missing else 'PASS','Missing required facts need correction.' if missing else 'Required structured facts are present.',{'missing':missing},'All required facts present')
    if vendor:
        fields=['quantity','unit_price','discount_amount','net_amount','tax_rate','tax_amount','gross_amount','currency']
        unknown=not p.get('currency') or any(line.get('currency')!=p.get('currency') for line in p['lines']) or any(any(line.get(k) is None for k in fields) for line in p['lines']) or any(p.get(k) is None for k in ['subtotal_amount','tax_amount','total_amount','document_discount_amount','shipping_amount','other_charges_amount'])
        if unknown:result('VAL-002','UNKNOWN','Arithmetic needs explicit line amounts, discounts, tax and totals. Missing tax is not zero.')
        elif p.get('tax_basis')!='EXCLUSIVE':result('VAL-002','UNKNOWN','This slice supports explicit exclusive-tax ordinary invoices only.',p.get('tax_basis'),'EXCLUSIVE')
        else:
            observations=[];ok=True
            for line in p['lines']:
                net=D(line['quantity'])*D(line['unit_price'])-D(line['discount_amount']);tax=(net*D(line['tax_rate'])).quantize(D('.01'));gross=net+tax
                line_ok=all(abs(a-D(line[k]))<=TOLERANCE for a,k in [(net,'net_amount'),(tax,'tax_amount'),(gross,'gross_amount')]) and line['currency']==p['currency'] and all(D(line[k])>=ZERO for k in fields if k!='currency')
                ok=ok and line_ok
                observations.append({'line_id':line['id'],'computed_net':net,'computed_tax':tax,'computed_gross':gross,'matches':line_ok})
            subtotal=sum((D(l['net_amount']) for l in p['lines']),ZERO);tax=sum((D(l['tax_amount']) for l in p['lines']),ZERO)
            computed=(Money(subtotal,p['currency'])-Money(p['document_discount_amount'],p['currency'])+Money(p['tax_amount'],p['currency'])+Money(p['shipping_amount'],p['currency'])+Money(p['other_charges_amount'],p['currency'])).amount
            ok=ok and abs(subtotal-D(p['subtotal_amount']))<=TOLERANCE and abs(tax-D(p['tax_amount']))<=TOLERANCE and abs(computed-total)<=TOLERANCE and total>ZERO and D(p['document_discount_amount'])<=subtotal and all(D(p[k])>=ZERO for k in ['document_discount_amount','shipping_amount','other_charges_amount','tax_amount'])
            check('VAL-002',ok,'Exclusive-tax line and document totals reconcile.' if ok else 'Line or document arithmetic does not reconcile.',{'lines':observations,'computed_total':computed},{'stated_total':total,'rounding':'HALF_EVEN / 0.01'},tolerance='0.01')
    else:
        fields=['claimed_amount','receipt_total_amount','company_paid_amount','applied_advance_amount','currency']
        if total is None or not p.get('currency') or any(i.get('currency')!=p.get('currency') for i in p['items']) or any(any(i.get(k) is None for k in fields) for i in p['items']):result('VAL-002','UNKNOWN','Requested amount and explicit receipt, company-paid and advance values are required.')
        else:
            computed=sum((D(i['claimed_amount'])-D(i['company_paid_amount'])-D(i['applied_advance_amount']) for i in p['items']),ZERO)
            ok=total>ZERO and abs(computed-total)<=TOLERANCE and all(i['currency']==p['currency'] and ZERO<=D(i['claimed_amount'])<=D(i['receipt_total_amount']) and ZERO<=D(i['company_paid_amount'])+D(i['applied_advance_amount'])<=D(i['claimed_amount']) and D(i['company_paid_amount'])>=ZERO and D(i['applied_advance_amount'])>=ZERO for i in p['items'])
            check('VAL-002',ok,'Net reimbursement reconciles.' if ok else 'Reimbursement or receipt amounts conflict.',{'computed_requested':computed},{'stated_requested':total},tolerance='0.01')
    if business_day and p.get('submission_date'):
        check('VAL-003',business_day<=p['submission_date']<=c['evaluated_at'][:10],'Dates must be ordered and cannot be in the future.',{'business_date':business_day,'submission_date':p['submission_date']},c['evaluated_at'][:10])
    else:result('VAL-003','UNKNOWN','Explicit, unambiguous dates are required.')
    if vendor:
        check('VEN-001',bool(primary and effective(primary,business_day) and primary.get('status')=='ACTIVE_APPROVED'),'Vendor must be active and approved in the pinned master.',primary and primary.get('status'),'ACTIVE_APPROVED',[ev(primary,'status','MASTER_RECORD')] if primary else [],failure='HOLD')
        doc=ref('source_document_id','documents');master_token=primary and primary.get('payment_account_token');source_token=doc and doc['facts'].get('payment_account_token')
        if not master_token or not source_token or not p.get('payment_account_token'):result('VEN-002','UNKNOWN','Verified synthetic account token comparison is incomplete.',expected='Submitted and document token equal approved vendor token')
        else:check('VEN-002',master_token==source_token==p['payment_account_token'],'Submitted account token must match approved vendor and source.',{'submitted':'[synthetic token redacted]'},'Approved master equality',[ev(primary,'payment_account_token','MASTER_RECORD'),ev(doc,'facts.payment_account_token','DOCUMENT_FIELD')],failure='HOLD')
        dup=c['duplicates']
        check('DUP-002',not dup,'Confirmed exact duplicates must be held.' if dup else 'Scoped exact duplicate search completed with no match.',{'matching_record_ids':[r['id'] for r in dup]},'No active same-vendor number/date/amount/currency record',[ev(r,None,'HISTORICAL_AGGREGATE') if r.get('_kind') else ev(r) for r in dup],failure='HOLD')
        po=ref('po_id','purchase_orders')
        check('PO-001',bool(po and effective(po,business_day) and po.get('status')=='APPROVED_OPEN' and po.get('vendor_id')==p.get('vendor_id') and po.get('currency')==p.get('currency') and po.get('budget_id')==p.get('budget_id') and po.get('category')==p.get('category')),'Approved PO must belong to this vendor, currency, category and budget.',po and po.get('status'),'APPROVED_OPEN',[ev(po,'status','MASTER_RECORD')] if po else [],failure='HOLD')
        po_ok=True;grn_ok=True;missing_po=False;missing_grn=False;po_obs=[];grn_obs=[];po_ev=[];grn_ev=[]
        for line in p['lines']:
            pl=refs.get(str(line.get('po_line_id')));gl=refs.get(str(line.get('grn_line_id')))
            if not pl or pl['_kind']!='po_lines' or any(line.get(k) is None for k in ['quantity','unit_price','uom','tax_rate']):missing_po=True;continue
            consumed=sum((D(r['quantity']) for r in refs.values() if r['_kind']=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('po_line_id')==pl['id']),ZERO)
            live=D(c['capacity'].get(pl['id'],{}).get('quantity','0'))
            remaining=D(pl['ordered_quantity'])-consumed-live
            requested=sum((D(x['quantity']) for x in p['lines'] if x.get('po_line_id')==pl['id'] and x.get('quantity') is not None),ZERO)
            tol=max(D(pl['tolerance']['price_absolute_amount']),D(pl['unit_price'])*D(pl['tolerance']['price_relative_rate']))
            po_ok=po_ok and pl['po_id']==p.get('po_id') and pl['vendor_id']==p.get('vendor_id') and pl['currency']==p.get('currency') and pl['tax_basis']==p.get('tax_basis') and D(pl['tax_rate'])==D(line['tax_rate']) and pl['uom']==line['uom'] and abs(D(pl['unit_price'])-D(line['unit_price']))<=tol and ZERO<requested<=remaining
            po_ev.extend(ev(r,None,'HISTORICAL_AGGREGATE') for r in refs.values() if r['_kind']=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('po_line_id')==pl['id'])
            po_obs.append({'po_line_id':pl['id'],'requested':requested,'remaining':remaining,'price_tolerance':tol});po_ev.append(ev(pl,None,'PO_LINE'))
            if not gl or gl['_kind']!='grn_lines':missing_grn=True;continue
            used=sum((D(r['quantity']) for r in refs.values() if r['_kind']=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('grn_line_id')==gl['id']),ZERO)
            grn_remaining=D(gl['accepted_quantity'])-D(gl['returned_quantity'])-D(gl['reversed_quantity'])-used-D(c['capacity'].get(gl['id'],{}).get('quantity','0'))
            requested_grn=sum((D(x['quantity']) for x in p['lines'] if x.get('grn_line_id')==gl['id'] and x.get('quantity') is not None),ZERO)
            grn_ok=grn_ok and gl['po_line_id']==pl['id'] and gl['po_id']==p.get('po_id') and gl['uom']==line['uom'] and ZERO<requested_grn<=grn_remaining
            grn_ev.extend(ev(r,None,'HISTORICAL_AGGREGATE') for r in refs.values() if r['_kind']=='matching_allocations' and r.get('lifecycle')=='CONSUMED' and r.get('grn_line_id')==gl['id'])
            grn_obs.append({'grn_line_id':gl['id'],'accepted_net_remaining':grn_remaining,'requested':requested_grn});grn_ev.append(ev(gl,None,'GRN_LINE'))
        result('PO-002','UNKNOWN' if missing_po else 'PASS' if po_ok else 'FAIL','Compare PO line identity, units, price, tax and remaining quantity.',po_obs,'Within approved PO',po_ev,'HOLD' if missing_po or not po_ok else 'NONE')
        result('GRN-001','UNKNOWN' if missing_grn else 'PASS' if grn_ok else 'FAIL','Accepted receipts less returns, reversals and active allocations must cover the invoice.',grn_obs,'Quantity covered by accepted goods',grn_ev,'HOLD' if missing_grn or not grn_ok else 'NONE')
        na('EMP-001')
    else:
        for rid in ['VEN-001','VEN-002','DUP-002','PO-001','PO-002','GRN-001']:na(rid)
        ok=bool(primary and effective(primary,business_day) and primary.get('status')=='ACTIVE' and primary.get('employment_from')<=business_day and (not primary.get('employment_to') or business_day<primary['employment_to']) and primary.get('cost_center_id')==p.get('cost_center_id') and primary.get('department')==p.get('department'))
        check('EMP-001',ok,'Employee must be active on the expense date with matching master dimensions.',primary and primary.get('status'),'ACTIVE',[ev(primary,None,'MASTER_RECORD')] if primary else [],failure='HOLD')
    docs=[];doc_ok=True;doc_missing=False
    if vendor:
        doc=ref('source_document_id','documents');docs=[doc] if doc else []
        if not doc:doc_missing=True
        else:
            facts=doc['facts'];doc_ok=doc.get('verification')=='ADJUDICATED_SYNTHETIC_FACTS' and doc.get('source_type')=='VENDOR_INVOICE' and facts.get('invoice_number')==p.get('invoice_number') and facts.get('invoice_date')==business_day and facts.get('currency')==p.get('currency') and facts.get('total_amount') is not None and total is not None and D(facts['total_amount'])==total and primary is not None and facts.get('vendor_name')==primary.get('legal_name')
    else:
        for item in p['items']:
            doc=refs.get(str(item.get('source_document_id')))
            if not doc or doc['_kind']!='documents':doc_missing=True;continue
            docs.append(doc);facts=doc['facts']
            doc_ok=doc_ok and doc.get('verification')=='ADJUDICATED_SYNTHETIC_FACTS' and facts.get('readable') is True and facts.get('receipt_type')=='ITEMIZED' and facts.get('currency')==item.get('currency')==p.get('currency') and facts.get('category')==item.get('category')==p.get('category') and facts.get('expense_date')==item.get('expense_date')==business_day and facts.get('local_timezone')==item.get('local_timezone')==p.get('local_timezone') and facts.get('receipt_total_amount') is not None and item.get('receipt_total_amount') is not None and D(facts['receipt_total_amount'])==D(item['receipt_total_amount'])
        # Reusing a receipt across Phase-1 claims requires a later allocation workflow.
        if len({i.get('source_document_id') for i in p['items']})!=len(p['items']) or c.get('receipt_conflicts'):doc_ok=False
    result('DOC-001','UNKNOWN' if doc_missing else 'PASS' if doc_ok else 'FAIL','Submitted values must reconcile with pinned synthetic source facts; source pages and boxes are unavailable.',{'source_ids':[d['id'] for d in docs],'active_receipt_conflicts':c.get('receipt_conflicts',[])},'Verified consistent synthetic document facts',[ev(d,'facts','DOCUMENT_FIELD') for d in docs])
    if vendor:na('EXP-003')
    else:
        policy=ref('expense_policy_id','expense_policies');observed={};evidence=[];unknown=False;over=False
        if not effective(policy,business_day) or not primary or not policy or total is None:unknown=True
        else:
            evidence=[ev(policy,None,'POLICY_CLAUSE')]
            dimensions=policy['dimensions'];valid=policy['category']==p.get('category') and policy['currency']==p.get('currency') and dimensions['grade']==primary.get('grade') and dimensions['country']==p.get('country')==primary.get('country') and dimensions['location']==p.get('location') and policy['local_timezone']==p.get('local_timezone') and p.get('submission_date') and ZERO<=D((date.fromisoformat(p['submission_date'])-date.fromisoformat(business_day)).days)<=D(policy['submission_window_days'])
            if not valid:unknown=True
            elif policy['unit']=='ELIGIBLE_NIGHT':
                nights=ZERO
                for item in p['items']:
                    doc=refs.get(str(item.get('source_document_id')));n=doc and doc['facts'].get('eligible_nights')
                    if doc:evidence.append(ev(doc,'facts.eligible_nights','DOCUMENT_FIELD'))
                    if n is None or item.get('eligible_nights') is None or D(n)!=D(item['eligible_nights']) or D(n)<=ZERO:unknown=True
                    else:
                        nights+=D(n);evidence.append(ev(doc,'facts.eligible_nights','DOCUMENT_FIELD'))
                if not unknown:
                    per_night=sum((D(i['claimed_amount']) for i in p['items']),ZERO)/nights;over=per_night>D(policy['allowance_amount']);observed={'eligible_nights':nights,'claimed_per_night':per_night,'limit_per_night':policy['allowance_amount']}
            elif policy['unit']=='EMPLOYEE_LOCAL_DAY':
                history=c['daily_history'];aggregate=sum((D(i['claimed_amount']) for i in p['items'] if i.get('claimed_amount') is not None),ZERO)+sum((D(r['claimed_amount']) for r in history),ZERO)
                observed={'local_date':business_day,'timezone':p['local_timezone'],'aggregate_amount':aggregate,'daily_limit':policy['allowance_amount'],'related_transaction_ids':[r['id'] for r in history]};over=aggregate>D(policy['allowance_amount']);evidence += [ev(r,None,'HISTORICAL_AGGREGATE') if r.get('_kind') else ev(r) for r in history]
            else:unknown=True
        result('EXP-003','UNKNOWN' if unknown else 'FAIL' if over else 'PASS','Allowance uses verified eligible nights or the employee local-day aggregate.',observed,'Within matching synthetic allowance policy',evidence)
    budget=ref('budget_id','budgets');po=ref('po_id','purchase_orders') if vendor else None
    if not effective(budget,business_day) or total is None or not budget or budget.get('basis')!='GROSS' or budget['currency']!=p.get('currency') or p.get('category') not in budget['covered_categories'] or budget['cost_center_id']!=p.get('cost_center_id'):
        result('BUD-001','UNKNOWN','A matching, effective, same-currency gross budget is required. Missing is not unlimited.',expected='Configured same-scope budget',effect='HOLD')
    else:
        ledger=budget['ledger'];allocated=sum((D(r['amount']) for r in ledger if r['entry_type']=='ALLOCATION'),ZERO);consumed=sum((D(r['amount']) for r in ledger if r['entry_type']!='ALLOCATION'),ZERO)
        reserved=D(c['capacity'].get(budget['id'],{}).get('amount','0'));available=allocated-consumed-reserved
        covered=sum((D(r['amount']) for r in ledger if r['entry_type']=='PO_COMMITMENT' and r.get('owner_id')==p.get('po_id')),ZERO) if po and po.get('budget_id')==budget['id'] else ZERO
        covered-=D(c['po_commitment_used'].get(str(p.get('po_id')),'0'))
        incremental=max(ZERO,total-max(ZERO,covered));valid=all(r['currency']==p['currency'] for r in ledger)
        check('BUD-001',valid and available>=incremental,'Compare incremental exposure with budget capacity; existing PO commitment is counted once.',{'basis':'GROSS','allocation':allocated,'ledger_used':consumed,'active_reservations':reserved,'available':available,'po_commitment_coverage':max(ZERO,covered),'incremental_exposure':incremental},'Sufficient explicit budget capacity',[ev(budget,None,'MASTER_RECORD')]+[ev(r,None,'BUDGET_LEDGER') for r in ledger],failure='HOLD')
    approval=ref('approval_policy_id','approval_policies');required_roles=[];approvals=c['approvals'];valid_policy=effective(approval,business_day) and total is not None and approval and approval['currency']==p.get('currency') and p['branch'] in approval['branches'] and approval['cost_center_id']==p.get('cost_center_id')
    if valid_policy:
        bands=[b for b in approval['bands'] if (total>D(b['lower_bound_amount']) or b['lower_inclusive'] and total==D(b['lower_bound_amount'])) and (b['upper_bound_amount'] is None or total<D(b['upper_bound_amount']) or b['upper_inclusive'] and total==D(b['upper_bound_amount']))]
        valid_policy=len(bands)==1
        if valid_policy:required_roles=bands[0]['required_roles']
    valid=bool(valid_policy and required_roles and len(approvals)==len(required_roles) and len({a['actor_id'] for a in approvals})==len(approvals));previous=None;steps=[]
    for index,role in enumerate(required_roles,1):
        step=next((a for a in approvals if a['sequence']==index),None);actor=refs.get(step['actor_id']) if step else None
        valid=valid and bool(step and actor and actor['_kind']=='employees' and actor['status']=='ACTIVE' and role in actor['roles'] and step['role']==role and step['state']=='APPROVED' and step['policy_id']==approval['id'] and step['policy_version']==approval['version'] and step['transaction_version']==c['transaction_version'] and step['actor_id'] not in (p.get('employee_id'),c['author_id']) and datetime.fromisoformat(step['approved_at'].replace('Z','+00:00'))<=datetime.fromisoformat(c['evaluated_at'].replace('Z','+00:00')) and effective(actor,step['approved_at'][:10]) and actor.get('cost_center_id')==approval['cost_center_id'] and actor.get('department')==approval['department'] and (role!='MANAGER' or vendor or primary and primary.get('manager_id')==step['actor_id']) and (previous is None or previous<=datetime.fromisoformat(step['approved_at'].replace('Z','+00:00'))))
        steps.append({'sequence':index,'required_role':role,'present':step is not None,'actor_has_role':bool(actor and role in actor.get('roles',[])),'version_bound':bool(step and step['transaction_version']==c['transaction_version'])})
        if step:previous=datetime.fromisoformat(step['approved_at'].replace('Z','+00:00'))
    check('APR-001',valid,'Complete, authoritative, version-bound approval chain is required.',{'required_roles':required_roles,'steps':steps,'record_ids':[a['id'] for a in approvals]},'All policy steps approved by authorized distinct people',[ev(approval,None,'POLICY_CLAUSE')] if approval else [],failure='HOLD')
    # Include actual approvals as evidence, never fabricate an ID for a missing step.
    if approvals:
        authority=[ev(refs[a['actor_id']],'roles','MASTER_RECORD') for a in approvals if a['actor_id'] in refs]
        r=results[-1];results[-1]=RuleResult(r.rule_id,r.version,r.status,r.decision_effect,r.reason,r.observed,r.expected,r.tolerance,r.evidence+tuple(ev(a,None,'APPROVAL') for a in approvals)+tuple(authority))
    full_receipts=vendor or all(i.get('claimed_amount') is not None and i.get('receipt_total_amount') is not None and D(i['claimed_amount'])==D(i['receipt_total_amount']) for i in p['items'])
    supported=p.get('document_type')=='ORDINARY' and p.get('currency')=='INR' and c.get('context_complete') is True and full_receipts
    result('SYS-001','PASS' if supported else 'UNKNOWN','Rules-only context is complete; risk model NOT_CONFIGURED.' if supported else 'Unsupported currency/type, partial receipt allocation or incomplete context requires review.',{'mode':'RULES_ONLY','model_status':'NOT_CONFIGURED','extraction':'STRUCTURED_SYNTHETIC','currency':p.get('currency')},'Complete supported deterministic context')
    # Original import-cell provenance accompanies every finding on imported records.
    if c.get('import_source'):
        source=c['import_source'];cell=ImportCellLocator(UUID(source['batch_id']),source['sheet'],source['row_number'],'transaction_json')
        imported=EvidenceReference(EvidenceKind.IMPORT_CELL,UUID(source['id']),1,UUID(c['tenant_id']),UUID(c['legal_entity_id']),snapshot_id=UUID(c['snapshot_id']),import_cell=cell)
        results=[RuleResult(r.rule_id,r.version,r.status,r.decision_effect,r.reason,r.observed,r.expected,r.tolerance,r.evidence+(imported,)) for r in results]
    return combine(results)
