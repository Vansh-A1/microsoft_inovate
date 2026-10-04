"""Raw observations become conservative candidates with explicit immutable traces."""
from datetime import date, datetime
from decimal import Decimal, localcontext
import re
import unicodedata

NORMALIZER_VERSION='document-normalizer-v4'
CURRENCIES=frozenset(('INR','USD','EUR','GBP','JPY','CAD','AUD','CHF','SGD','AED'))
AMOUNTS=frozenset(('subtotal_amount','document_discount_amount','tax_amount','shipping_amount','other_charges_amount',
    'total_amount','unit_price','amount','discount_amount','net_amount','gross_amount','quantity','tax_rate','eligible_nights'))


class NormalizationError(ValueError):
    def __init__(self,code):self.code=code;super().__init__(code)


def normalize_currency(raw):
    value={'€':'EUR','₹':'INR'}.get(raw.strip(),raw.strip().upper())
    if value not in CURRENCIES:raise NormalizationError('CURRENCY_UNSUPPORTED_OR_AMBIGUOUS')
    return value


def money_lexeme(raw,currency):
    if not isinstance(raw,str):raise NormalizationError('AMOUNT_MUST_BE_STRING')
    value=unicodedata.normalize('NFKC',raw).strip().replace('\u00a0',' ')
    found=re.findall(r'\b[A-Z]{3}\b|[₹$€£¥]',value)
    symbols={'₹':'INR','€':'EUR','£':'GBP'}
    for token in found:
        unit=symbols.get(token,token if token in CURRENCIES else None)
        if token in ('$','¥'):
            possibilities={'$':{'USD','CAD','AUD','SGD'},'¥':{'JPY'}}[token]
            unit=currency if currency in possibilities else None
        if not unit:raise NormalizationError('CURRENCY_SYMBOL_AMBIGUOUS')
        if currency is None or unit!=currency:raise NormalizationError('CURRENCY_MISMATCH_OR_MISSING')
        value=value.replace(token,'').strip()
    if currency is None:raise NormalizationError('CURRENCY_MISSING')
    if value.startswith('(') and value.endswith(')'):value='-'+value[1:-1].strip()
    return value


def normalize_money(raw,currency,number_format='DECIMAL_POINT'):
    value=money_lexeme(raw,currency)
    if number_format=='DECIMAL_COMMA':
        if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:\.\d{3})+)(?:,\d{1,6})?',value):
            raise NormalizationError('AMOUNT_FORMAT_AMBIGUOUS')
        value=value.replace('.','').replace(',','.')
    elif number_format=='DECIMAL_POINT':
        if not re.fullmatch(r'-?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})(?:\.\d{1,6})?',value):
            raise NormalizationError('AMOUNT_FORMAT_AMBIGUOUS')
        value=value.replace(',','')
    else:
        raise NormalizationError('NUMBER_FORMAT_CONFLICT')
    parsed=Decimal(value)
    if not parsed.is_finite() or abs(parsed)>=Decimal('100000000000000'):raise NormalizationError('AMOUNT_RANGE')
    return format(parsed,'f')


def source_number_format(observations,currency):
    """Use printed monetary separators, never currency/country or arithmetic.

    A three-digit suffix alone cannot establish comma-decimal versus grouping.
    Strong opposing printed conventions make money unresolved. Quantity/rate
    syntax remains independently validated by the legacy dimensionless parser.
    """
    comma=[];point=[]
    for o in observations:
        name=o['field_path'].split('.')[-1]
        src=o.get('source');box=src.get('bbox') if isinstance(src,dict) else getattr(src,'bbox',None)
        if name not in AMOUNTS-{'quantity','tax_rate','eligible_nights'} or o['state']!='PRESENT' or box is None:continue
        try:value=money_lexeme(o['raw_value'],currency)
        except NormalizationError:continue
        if re.fullmatch(r'-?(?:\d+|\d{1,3}(?:\.\d{3})+),\d{1,6}',value) and len(value.rsplit(',',1)[1])!=3:
            comma.append(o['id'])
        if re.fullmatch(r'-?(?:\d+|\d{1,3}(?:,\d{3})+|\d{1,2}(?:,\d{2})*,\d{3})\.\d{1,6}',value) and len(value.rsplit('.',1)[1])!=3:
            point.append(o['id'])
    return ('CONFLICT' if comma and point else 'DECIMAL_COMMA' if comma else 'DECIMAL_POINT'),comma+point


def normalize_date(raw,date_order=None):
    value=raw.strip()
    if re.fullmatch(r'\d{4}-\d{2}-\d{2}',value):
        try:return date.fromisoformat(value).isoformat()
        except ValueError:raise NormalizationError('DATE_INVALID') from None
    if re.fullmatch(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}',value):
        if date_order not in ('DMY','MDY'):raise NormalizationError('DATE_AMBIGUOUS')
        a,b,y=[int(v) for v in re.split('[/-]',value)]
        try:return date(y,b,a).isoformat() if date_order=='DMY' else date(y,a,b).isoformat()
        except ValueError:raise NormalizationError('DATE_INVALID') from None
    for pattern in ('%d %b %Y','%d %B %Y','%B %d, %Y'):
        try:return datetime.strptime(value,pattern).date().isoformat()
        except ValueError:pass
    raise NormalizationError('DATE_INVALID_OR_AMBIGUOUS')


def number_keys(raw):
    conservative=' '.join(unicodedata.normalize('NFKC',raw).strip().upper().split())
    aggressive=re.sub(r'[^A-Z0-9]','',conservative)
    return {'conservative':conservative,'candidate':aggressive}


def normalized_value(field,raw,currency=None,date_order=None,number_format='DECIMAL_POINT'):
    name=field.split('.')[-1]
    if name=='currency':return normalize_currency(raw),['trim','supported_explicit_currency_or_unique_symbol','supported_currency_allowlist']
    if name in AMOUNTS:
        # Quantities/rates are dimensionless, but still authoritative decimal strings.
        if name in ('quantity','tax_rate','eligible_nights') and (not isinstance(raw,str) or re.search(r'[A-Za-z₹$€£¥]',raw)):
            raise NormalizationError('DIMENSIONLESS_VALUE_HAS_UNIT')
        dimensionless=name in ('quantity','tax_rate','eligible_nights')
        convention='DECIMAL_POINT' if dimensionless else number_format
        return normalize_money(raw,'INR' if dimensionless else currency,convention),['NFKC','validate_explicit_units',
            'source_decimal_comma_convention' if convention=='DECIMAL_COMMA' else 'validated_decimal_point_convention','validate_grouping','Decimal_from_string']
    if name.endswith('_date'):return normalize_date(raw,date_order),['explicit_date_order' if date_order else 'unambiguous_date_only','ISO_business_date']
    value=' '.join(unicodedata.normalize('NFKC',raw).strip().split())
    if not value:raise NormalizationError('EMPTY_VALUE')
    if len(value)>500:raise NormalizationError('TEXT_VALUE_LIMIT')
    return value,['NFKC','trim','collapse_whitespace']


class Normalizer:
    def normalize(self,observations,*,date_order=None):
        currency=None
        for o in observations:
            if o['field_path']=='currency' and o['state']=='PRESENT':
                try:currency=normalize_currency(o['raw_value'])
                except NormalizationError:pass
        number_format,format_sources=source_number_format(observations,currency)
        candidate={};traces=[];findings=[]
        for o in observations:
            field=o['field_path'];value=None;steps=[];status=o['state'];code=None
            if status=='PRESENT':
                try:
                    if field.split('.')[-1] in AMOUNTS-{'quantity','tax_rate','eligible_nights'} and not format_sources and currency is not None:
                        if re.fullmatch(r'-?\d{1,3}[.,]\d{3}',money_lexeme(o['raw_value'],currency)):
                            raise NormalizationError('AMOUNT_GROUPING_OR_DECIMAL_AMBIGUOUS')
                    value,steps=normalized_value(field,o['raw_value'],currency,date_order,number_format);status='NORMALIZED'
                except NormalizationError as exc:status='AMBIGUOUS';code=exc.code
            trace={'source_observation_id':o['id'],'field_path':field,'raw_value':o['raw_value'],
                'rule_version':NORMALIZER_VERSION,'steps':steps,'canonical_candidate':value,'status':status,
                'source':o.get('source'),'diagnostic':code,'observation_diagnostic':o.get('diagnostic',o.get('diagnostic_note'))}
            if field.split('.')[-1] in AMOUNTS-{'quantity','tax_rate','eligible_nights'}:
                trace['number_format']=number_format;trace['number_format_source_observation_ids']=format_sources
            if field=='currency' and (trace['observation_diagnostic'] or '').startswith('DERIVED_SOURCE_CURRENCY:'):
                trace['steps'].append('derive_only_from_printed_monetary_currency_tokens')
            if field in ('invoice_number','receipt_number') and value:
                trace['number_keys']=number_keys(value)
            if code:findings.append({'field':field,'code':code,'state':status})
            traces.append(trace);candidate[field]=value
        return candidate,traces,findings


def validate_draft(candidate,traces,source_type,diagnostics=()):
    required=('vendor_name','invoice_number','invoice_date','currency','subtotal_amount','tax_amount','total_amount',
        'document_discount_amount','shipping_amount','other_charges_amount','tax_basis') if source_type=='VENDOR_INVOICE' else (
        'merchant_name','receipt_number','expense_date','currency','total_amount','receipt_type','category','local_timezone')
    findings=[{'field':key,'code':'CRITICAL_UNRESOLVED','state':'NEEDS_INPUT'} for key in required if candidate.get(key) is None]
    if any((t.get('observation_diagnostic') or '').startswith('ROW_ASSOCIATION_UNCONFIRMED:') for t in traces):
        findings.append({'field':'lines','code':'MODEL_ROW_ASSOCIATION_UNCONFIRMED','state':'NEEDS_INPUT',
            'message':'Confirm the distinct printed line items against the original source. Model candidates could not be assigned to separate source rows; do not use their quantities or amounts.'})
    for key in required:
        trace=next((t for t in traces if t['field_path']==key),None)
        if trace and trace['canonical_candidate'] is not None and not trace.get('source'):
            findings.append({'field':key,'code':'SOURCE_COVERAGE_MISSING','state':'NEEDS_INPUT'})
    if any(code in diagnostics for code in ('SEGMENTATION_UNCERTAIN','TABLE_COVERAGE_UNCERTAIN','TABLE_ROW_LIMIT','TABLE_CELL_UNREAD')):
        findings.extend({'field':'document','code':code,'state':'NEEDS_INPUT'} for code in diagnostics)
    if source_type=='VENDOR_INVOICE':
        line_indexes=sorted({key.split('.')[1] for key in candidate if key.startswith('lines.')},key=int)
        if not line_indexes:findings.append({'field':'lines','code':'TABLE_COVERAGE_UNCERTAIN','state':'NEEDS_INPUT'})
        with localcontext() as dc:
            dc.prec=60
            net_sum=tax_sum=Decimal('0');complete=True
            for i in line_indexes:
                for field,label in (('quantity','quantity'),('unit_price','unit price'),('amount','line amount')):
                    trace=next((t for t in traces if t['field_path']==f'lines.{i}.{field}'),None)
                    if trace and trace['status']=='MISSING' and candidate.get(f'lines.{i}.{field}') is None and not (trace.get('observation_diagnostic') or '').startswith('ROW_ASSOCIATION_UNCONFIRMED:'):
                        description=candidate.get(f'lines.{i}.description')
                        context=next((t for t in traces if t['field_path']==f'lines.{i}.description'),None)
                        page=(context or {}).get('source',{});page=(page or {}).get('page')
                        item=f' ({description[:120]})' if isinstance(description,str) else ''
                        where=f' on page {page}' if page else ''
                        findings.append({'field':f'lines.{i}.{field}','code':'SOURCE_CELL_UNREAD','state':'NEEDS_INPUT',
                            'message':f'What {label} is shown for line {int(i)+1}{item}{where}? No value was independently read. If the source is blank or unreadable, obtain a source-backed correction; do not calculate it from other amounts.'})
                row={k:candidate.get(f'lines.{i}.{k}') for k in ('quantity','unit_price','discount_amount','net_amount','tax_rate','tax_amount','gross_amount')}
                if any(v is None for v in row.values()):
                    findings.append({'field':f'lines.{i}','code':'LINE_UNRESOLVED','state':'NEEDS_INPUT'});complete=False;continue
                net=Decimal(row['quantity'])*Decimal(row['unit_price'])-Decimal(row['discount_amount'])
                tax=(net*Decimal(row['tax_rate'])).quantize(Decimal('.01'))
                if any(abs(a-Decimal(row[k]))>Decimal('.01') for a,k in ((net,'net_amount'),(tax,'tax_amount'),(net+tax,'gross_amount'))):
                    findings.append({'field':f'lines.{i}','code':'LINE_ARITHMETIC_MISMATCH','state':'NEEDS_INPUT'})
                net_sum+=Decimal(row['net_amount']);tax_sum+=Decimal(row['tax_amount'])
            keys=('subtotal_amount','tax_amount','document_discount_amount','shipping_amount','other_charges_amount','total_amount')
            if complete and all(candidate.get(k) is not None for k in keys):
                s,t,d,ship,other,total=[Decimal(candidate[k]) for k in keys]
                if abs(net_sum-s)>Decimal('.01') or abs(tax_sum-t)>Decimal('.01') or abs(s+t-d+ship+other-total)>Decimal('.01'):
                    findings.append({'field':'total_amount','code':'TOTAL_ARITHMETIC_MISMATCH','state':'NEEDS_INPUT'})
    # No automation eligibility here; verification of actual source remains explicit.
    return findings
