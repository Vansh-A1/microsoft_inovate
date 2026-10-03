"""Versioned, cutoff-safe business features. Money operands remain decimal strings."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
import hashlib
import math
import statistics
from app.core.serialization import digest, projection

VERSION = 'features-p5-v1'
MAXIMUM_HISTORY = 10000
MINIMUM_COHORT = 5
CLIP = 1_000_000_000
DEFINITIONS = [
    ('log_amount','number','log1p of positive canonical amount'),
    ('vendor_amount_ratio','number','amount / prior same-currency submitted vendor median'),
    ('employee_category_ratio','number','amount / prior same-currency submitted employee/category median'),
    ('robust_amount_z','number','absolute amount deviation / (1.4826 * median absolute deviation)'),
    ('po_value_ratio','number','current amount / pinned remaining PO value'),
    ('price_variance_ratio','number','absolute line-price difference / comparable expected line total'),
    ('receipt_shortfall','number','positive billed quantity minus verified available acceptance'),
    ('policy_limit_ratio','number','comparable policy-unit amount / pinned allowance'),
    ('budget_utilization_after','number','projected same-basis exposure / allocated budget'),
    ('max_duplicate_similarity','number','highest completed comparable candidate similarity, 0 only for completed no-match search'),
    ('min_phash_distance','number','closest actual comparable 64-bit image hash distance'),
    ('same_amount_count_30d','integer','prior cohort submissions at the same exact amount in 30 business days'),
    ('days_since_previous','number','business-date days since most recent prior cohort submission'),
    ('vendor_tenure_days','number','days since explicitly recorded approved onboarding date'),
    ('payment_account_changed','boolean','verified requested account differs from approved master; no account token in vector'),
    ('claims_near_limit_7d','integer','prior comparable policy-unit claims with ratio in [0.9,1.0] in 7 days'),
    ('submission_delay_days','number','actual submitted business-local date minus canonical business date'),
    ('quality_and_freshness','number','fraction of known critical source observations unresolved; absent source metrics are missing'),
    ('history_count','integer','number of prior submitted comparable canonical observations'),
    ('cold_start','boolean','complete cohort has fewer than 5 observations, or history coverage is incomplete'),
]


def schema():
    return {'version':VERSION, 'order':[n for n,_,_ in DEFINITIONS],
        'features':[{'name':n,'type':t,'definition':d,'missing':'null with explicit missing indicator/reason',
                     'normalization':'none','clipping':[-CLIP,CLIP] if t=='number' else None,
                     'category_vocabulary':None} for n,t,d in DEFINITIONS],
        'history_semantics':'prior submitted facts, never clean/paid labels',
        'excluded_predictors':['raw identifiers','names','accounts','email','phone','protected attributes',
            'approval outcomes','settlement outcomes','reviewer outcomes','labels','future corrections','future dispositions']}


def code_version():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def instant(value):
    result=value if isinstance(value,datetime) else datetime.fromisoformat(value.replace('Z','+00:00'))
    if result.tzinfo is None:raise ValueError('Cutoff/knowledge timestamps must include a timezone.')
    return result.astimezone(timezone.utc)


def decimal(value):
    if not isinstance(value,(str,Decimal)):return None
    try:
        result=Decimal(value)
        return result if result.is_finite() else None
    except InvalidOperation:return None


def number(value):
    if value is None:return None
    value=float(value)
    return round(max(-CLIP,min(CLIP,value)),8) if math.isfinite(value) else None


def build(transaction, transaction_id, transaction_version, cutoff, reference_snapshot,
          history, *, operands=None, submitted_date=None, coverage=True):
    """History inputs carry immutable identity/version/known_at and their declared facts.

    Do not consume changing transaction lifecycle/approvals/labels. Select temporal
    versions before cohort filters, so a later party/currency correction cannot leak.
    """
    cutoff=instant(cutoff);operands=operands or {};vendor=transaction['branch']=='VENDOR_INVOICE'
    day_raw=transaction.get('invoice_date' if vendor else 'expense_date')
    day=date.fromisoformat(day_raw) if day_raw else None
    amount=decimal(transaction.get('total_amount' if vendor else 'requested_amount'))
    party=transaction.get('vendor_id' if vendor else 'employee_id');currency=transaction.get('currency')
    category=transaction.get('category');latest={};unknown_time=0
    for row in history:
        rid=str(row['object_id'])
        if rid==str(transaction_id):continue
        if not row.get('known_at'):unknown_time+=1;continue
        known=instant(row['known_at'])
        if known>=cutoff:continue
        prior=latest.get(rid)
        if prior is None or (row['version'],known)>(prior['version'],instant(prior['known_at'])):latest[rid]=row|{'known_at':known.isoformat()}
    cohort=[]
    for row in latest.values():
        p=row['facts'];rday=p.get('invoice_date' if vendor else 'expense_date')
        if p.get('branch')!=transaction['branch'] or p.get('currency')!=currency or not currency:continue
        if p.get('vendor_id' if vendor else 'employee_id')!=party or not party:continue
        if not vendor and p.get('category')!=category:continue
        if not rday or not day or date.fromisoformat(rday)>min(day,cutoff.date()):continue
        value=decimal(p.get('total_amount' if vendor else 'requested_amount',p.get('claimed_amount')))
        if value is None or value<=0:continue
        cohort.append(row|{'amount':value,'day':date.fromisoformat(rday)})
    coverage=coverage and len(cohort)<=MAXIMUM_HISTORY
    cohort=sorted(cohort,key=lambda r:(r['known_at'],r['object_id'],r['version']))[:MAXIMUM_HISTORY]
    values={n:None for n,_,_ in DEFINITIONS};reasons={n:'SOURCE_UNAVAILABLE' for n,_,_ in DEFINITIONS}
    traces={};count=len(cohort);cold=not coverage or count<MINIMUM_COHORT
    def set_value(name,value,reason='SOURCE_UNAVAILABLE',lineage=None):
        kind=next(t for n,t,_ in DEFINITIONS if n==name)
        if value is not None and kind=='number':value=number(value)
        values[name]=value;reasons[name]=None if value is not None else reason
        if lineage is not None:traces[name]=projection(lineage)
    set_value('cold_start',cold);set_value('history_count',count if coverage else None,'HISTORY_INCOMPLETE')
    if amount is not None and amount>0:set_value('log_amount',math.log1p(float(amount)))
    else:reasons['log_amount']='INVALID_AMOUNT'
    cohort_manifest=[{'object_id':r['object_id'],'version':r['version'],'known_at':r['known_at'],
        'source_kind':r.get('source_kind','CANONICAL'),'digest':digest(r['facts'])} for r in cohort]
    with localcontext() as dc:
        dc.prec=60
        if not cold and amount is not None and amount>0:
            median=statistics.median(r['amount'] for r in cohort)
            mad=statistics.median(abs(r['amount']-median) for r in cohort)
            key='vendor_amount_ratio' if vendor else 'employee_category_ratio'
            lineage={'amount':str(amount),'currency':currency,'historical_median':str(median),'mad':str(mad),
                'history_count':count,'history_manifest_digest':digest(cohort_manifest)}
            set_value(key,amount/median if median>0 else None,'ZERO_DENOMINATOR',lineage)
            set_value('robust_amount_z',abs(amount-median)/(Decimal('1.4826')*mad) if mad>0 else None,'ZERO_MAD',lineage)
        else:
            for key in ('vendor_amount_ratio','employee_category_ratio','robust_amount_z'):reasons[key]='COLD_START' if coverage else 'HISTORY_INCOMPLETE'
        reasons['employee_category_ratio' if vendor else 'vendor_amount_ratio']='NOT_APPLICABLE'
        if coverage and day and amount is not None:
            recent=[r for r in cohort if 0<=(day-r['day']).days<30]
            set_value('same_amount_count_30d',sum(r['amount']==amount for r in recent),lineage={'window_days':30,'anchor':str(day),'history_manifest_digest':digest(cohort_manifest)})
            set_value('days_since_previous',(day-max(r['day'] for r in cohort)).days if cohort else None,'FIRST_SUBMISSION')
        basis_known=bool(operands.get('known_at') and instant(operands['known_at'])<=cutoff and operands.get('currency')==currency)
        def ratio(name,numerator,denominator):
            a=decimal(operands.get(numerator));b=decimal(operands.get(denominator))
            set_value(name,a/b if basis_known and a is not None and b is not None and b>0 else None,
                'ZERO_DENOMINATOR' if basis_known and b==0 else 'PINNED_BASIS_UNAVAILABLE',operands.get('lineage'))
        if vendor:
            set_value('po_value_ratio',amount/decimal(operands['po_remaining_amount']) if basis_known and amount is not None and decimal(operands.get('po_remaining_amount')) is not None and decimal(operands['po_remaining_amount'])>0 else None,'PINNED_PO_CAPACITY_UNAVAILABLE',operands.get('lineage'))
            ratio('price_variance_ratio','price_difference_amount','expected_line_amount')
            set_value('receipt_shortfall',decimal(operands.get('receipt_shortfall')) if basis_known else None,'PINNED_ACCEPTANCE_UNAVAILABLE',operands.get('lineage'))
        else:
            ratio('policy_limit_ratio','policy_unit_amount','policy_allowance_amount')
            allowance=decimal(operands.get('policy_allowance_amount'))
            if basis_known and coverage and day and allowance is not None and allowance>0 and operands.get('policy_unit')=='PER_CLAIM':
                set_value('claims_near_limit_7d',sum(Decimal('0.9')<=r['amount']/allowance<=1 for r in cohort if 0<=(day-r['day']).days<7),lineage={'threshold':['0.9','1.0'],'window_days':7,'allowance_amount':str(allowance),'currency':currency,'history_manifest_digest':digest(cohort_manifest)})
        ratio('budget_utilization_after','budget_post_exposure_amount','budget_allocated_amount')
    for key in ('max_duplicate_similarity','min_phash_distance','quality_and_freshness'):
        set_value(key,operands.get(key) if basis_known else None,'MEASURED_SOURCE_UNAVAILABLE',operands.get('lineage'))
    number_key='invoice_number' if vendor else 'claim_number'
    if coverage and party and currency and day and transaction.get(number_key) and all(r['facts'].get(number_key) for r in cohort):
        from rapidfuzz.fuzz import ratio as similarity
        set_value('max_duplicate_similarity',max([similarity(transaction[number_key],r['facts'][number_key]) for r in cohort],default=0),
            lineage={'scope':'COMPLETE_PRIOR_SAME_PARTY_CURRENCY_BRANCH_NUMBER_COHORT','history_count':count,
                'history_manifest_digest':digest(cohort_manifest),'range':[0,100],'algorithm':'rapidfuzz-ratio'})
    if vendor:
        onboarding=operands.get('approved_onboarding_date')
        set_value('vendor_tenure_days',(day-date.fromisoformat(onboarding)).days if basis_known and day and onboarding and date.fromisoformat(onboarding)<=day else None,'ONBOARDING_DATE_UNKNOWN')
        set_value('payment_account_changed',operands.get('payment_account_changed') if basis_known else None,'VERIFIED_ACCOUNT_COMPARISON_UNAVAILABLE')
    if submitted_date and day:set_value('submission_delay_days',(date.fromisoformat(submitted_date)-day).days)
    return {'schema_version':VERSION,'schema_digest':digest(schema()),'feature_code_version':code_version(),
        'transaction_id':str(transaction_id),'transaction_version':transaction_version,'cutoff':cutoff.isoformat(),
        'reference_snapshot_id':str(reference_snapshot),'feature_names':[n for n,_,_ in DEFINITIONS],
        'types':{n:t for n,t,_ in DEFINITIONS},'values':values,'missing':{n:v is None for n,v in values.items()},
        'missing_reasons':reasons,'lineage':traces,'history_manifest':cohort_manifest,
        'history_manifest_digest':digest(cohort_manifest),'history_coverage':'COMPLETE' if coverage else 'INCOMPLETE',
        'excluded_unknown_knowledge_time':unknown_time,'cold_start':cold}
