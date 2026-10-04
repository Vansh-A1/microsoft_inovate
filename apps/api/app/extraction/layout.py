"""Conservative geometric association of actual PDF spans / OCR words.

Only printed labels and column headings establish meaning. Coordinates are
measured regions, not confidence. Unknown, crossing and competing cells abstain.
The legacy labeled/pipe parser remains intact. No arithmetic supplies raw facts.
"""
import re

VERSION = 'printed-layout-v4'
HEADER_ALIASES = {
    'supplier': 'vendor_name', 'vendor': 'vendor_name', 'supplier name': 'vendor_name',
    'vendor name': 'vendor_name', 'seller': 'vendor_name', 'merchant': 'merchant_name',
    'invoice number': 'invoice_number', 'invoice no': 'invoice_number', 'invoice id': 'invoice_number', 'invoice': 'invoice_number',
    'receipt number': 'receipt_number', 'receipt no': 'receipt_number',
    'invoice date': 'invoice_date', 'issue date': 'invoice_date', 'expense date': 'expense_date', 'date': 'invoice_date',
    'due date': 'due_date', 'po reference': 'po_reference', 'purchase order': 'po_reference', 'po': 'po_reference',
    'currency': 'currency', 'subtotal': 'subtotal_amount', 'sub total': 'subtotal_amount',
    'discount': 'document_discount_amount', 'tax': 'tax_amount', 'sales tax': 'tax_amount',
    'shipping': 'shipping_amount', 'freight': 'shipping_amount', 'other charges': 'other_charges_amount',
    'total': 'total_amount', 'grand total': 'total_amount', 'payment terms': 'payment_terms',
    'tax basis': 'tax_basis', 'category': 'category', 'local timezone': 'local_timezone', 'receipt type': 'receipt_type',
}
COLUMN_ALIASES = {
    'description': 'description', 'item description': 'description', 'item': 'description',
    'quantity': 'quantity', 'qty': 'quantity', 'unit price': 'unit_price', 'rate': 'unit_price',
    'discount': 'discount_amount', 'net': 'net_amount', 'net amount': 'net_amount',
    'tax rate': 'tax_rate', 'tax': 'tax_amount', 'tax amount': 'tax_amount',
    'gross': 'gross_amount', 'gross amount': 'gross_amount',
    'amount': 'amount', 'line total': 'amount', 'uom': 'uom', 'unit': 'uom',
}


def key(text):
    return ' '.join(re.sub(r'[^\w\s]', '', text.casefold()).split())


def union(parts, source=False):
    return {name: (min if name.endswith('1') else max)((p.get('source_bbox',p['bbox']) if source else p['bbox'])[name] for p in parts)
            for name in ('x1', 'y1', 'x2', 'y2')}


def groups(details):
    spans = details.get('spans', [])
    # OCR retains both line regions for legacy evidence and granular words.
    words = [s for s in spans if s.get('kind') == 'word']
    spans = words or [s for s in spans if s.get('kind') != 'word']
    # Association uses the upright derived image; evidence remains in immutable
    # original-image coordinates after the exact inverse EXIF transform.
    spans = [s | {'bbox':s.get('layout_bbox',s.get('bbox')), 'source_bbox':s.get('bbox')} for s in spans]
    valid = [s for s in spans if s.get('bbox') and s.get('text', '').strip() and
             s['bbox']['x1'] < s['bbox']['x2'] and s['bbox']['y1'] < s['bbox']['y2']]
    rows = []
    for span in sorted(valid, key=lambda s: (s['bbox']['y1'], s['bbox']['x1'])):
        box = span['bbox']
        matches = []
        for row in rows[-8:]:
            anchor = row[0]['bbox']
            overlap = min(box['y2'], anchor['y2']) - max(box['y1'], anchor['y1'])
            height = min(box['y2'] - box['y1'], anchor['y2'] - anchor['y1'])
            if overlap >= height * .55:
                matches.append(row)
        if len(matches) == 1:
            matches[0].append(span)
        else:
            rows.append([span])
    return [sorted(row, key=lambda s: s['bbox']['x1']) for row in rows]


def label_at(row, index, aliases):
    for count in range(min(3, len(row) - index), 0, -1):
        parts = row[index:index + count]
        # Separate columns must never be fused into a multiword label.
        if any(b['bbox']['x1'] - a['bbox']['x2'] > .035 for a, b in zip(parts, parts[1:])):
            continue
        joined = ' '.join(p['text'] for p in parts)
        if key(joined) in aliases:
            return count, aliases[key(joined)], parts
    return None


def heading_columns(row):
    found=[];cursor=0
    while cursor<len(row):
        heading=label_at(row,cursor,COLUMN_ALIASES)
        if not heading:return None
        count,field,parts=heading;found.append((field,union(parts)));cursor+=count
    names=[field for field,_ in found]
    if {'description','quantity','unit_price'}<=set(names) and set(names)&{'amount','net_amount','gross_amount'}:
        return found
    return None


def table_columns(details):
    """Independent printed schema, never row values supplied to a model."""
    schemas=[tuple(field for field,_ in found) for row in groups(details) if (found:=heading_columns(row))]
    if not schemas or any(len(set(s))!=len(s) or set(s)!=set(schemas[0]) for s in schemas):return None
    return schemas[0]


def stacked_headers(rows):
    """Associate an all-label row with the immediately aligned value row.

    Competing labels, large gaps, crossing columns or another label abstain.
    The evidence box is the union of actual label/value regions, not a guess.
    """
    out=[];claimed=set()
    for index,row in enumerate(rows[:-1]):
        if index in claimed:continue
        labels=[];cursor=0
        while cursor<len(row):
            hit=label_at(row,cursor,HEADER_ALIASES)
            if not hit:break
            count,field,parts=hit
            if not any(':' in p['text'] or '#' in p['text'] for p in parts):break
            labels.append((field,parts));cursor+=count
        if cursor!=len(row) or not labels or len({f for f,_ in labels})!=len(labels):continue
        values=rows[index+1]
        gap=min(p['bbox']['y1'] for p in values)-max(p['bbox']['y2'] for p in row)
        if not 0<=gap<=.04 or any(key(p['text']) in HEADER_ALIASES for p in values):continue
        associations=[];used=[]
        for n,(field,parts) in enumerate(labels):
            left=parts[0]['bbox']['x1']
            right=labels[n+1][1][0]['bbox']['x1']-.015 if n+1<len(labels) else 1
            assigned=[p for p in values if left-.018<=p['bbox']['x1'] and p['bbox']['x2']<=right]
            if not assigned or abs(assigned[0]['bbox']['x1']-left)>.03:break
            used.extend(assigned)
            associations.append((field,' '.join(p['text'].strip() for p in assigned),union(parts+assigned,source=True)))
        if len(associations)==len(labels) and len(used)==len(values):
            out.extend(associations);claimed.update((index,index+1))
    return out,claimed


def column_cells(row,columns):
    bounds=[(a[1]['x2']+b[1]['x1'])/2 for a,b in zip(columns,columns[1:])]
    cells=[[] for _ in columns];crossing=False
    for span in row:
        box=span['bbox'];center=(box['x1']+box['x2'])/2
        cells[sum(center>=b for b in bounds)].append(span)
        crossing |= any(box['x1']<b<box['x2'] for b in bounds)
    return cells,crossing


def readable_partial_row(cells,columns):
    missing=[field for (field,_),cell in zip(columns,cells) if not cell]
    present={field for (field,_),cell in zip(columns,cells) if cell}
    return (len(missing)==1 and missing[0] in ('quantity','unit_price','amount','net_amount','gross_amount')
            and 'description' in present and len(present)>=3)


def table_retry_regions(details, maximum=3):
    """Bounded OCR retries for one absent numeric cell in a measured table row.

    Three independently detected cells and unique complete headings establish
    a candidate row region, never its missing value. Crossing/multiple missing
    cells, notes and isolated descriptions cannot request retries. Crop extents
    are routing metadata; only the new detector's measured box is evidence.
    """
    rows=groups(details);columns=None;table_y=None;out=[]
    for row in rows:
        found=heading_columns(row)
        if found:
            columns=found if len({f for f,_ in found})==len(found) else None
            table_y=max(p['bbox']['y2'] for p in row)
            continue
        if not columns:continue
        if min(p['bbox']['y1'] for p in row)-(table_y or 0)>.08:
            columns=None;continue
        cells,crossing=column_cells(row,columns)
        missing=[i for i,c in enumerate(cells) if not c]
        description=next(i for i,(field,_) in enumerate(columns) if field=='description')
        if cells[description] and not any(c for i,c in enumerate(cells) if i!=description):
            table_y=max(p['bbox']['y2'] for p in row);continue
        if crossing or not cells[description]:columns=None;continue
        if len(missing)==1 and len(columns)>=4 and columns[missing[0]][0] in ('quantity','unit_price','amount','net_amount','gross_amount'):
            i=missing[0];box=union(row);height=box['y2']-box['y1']
            bounds=[0]+[(a[1]['x2']+b[1]['x1'])/2 for a,b in zip(columns,columns[1:])]+[1]
            crop={'x1':max(0,min(box['x1'],columns[0][1]['x1'])-.02),
                  'x2':min(1,max(box['x2'],columns[-1][1]['x2'])+.02),
                  'y1':max(0,box['y1']-height*.7),'y2':min(1,box['y2']+height*.7)}
            out.append({'field':columns[i][0],'crop':crop,'cell':{'x1':bounds[i],'x2':bounds[i+1],'y1':box['y1'],'y2':box['y2']}})
            if len(out)>=maximum:break
        table_y=max(p['bbox']['y2'] for p in row)
    return out


def printed_layout(details):
    """Return header candidates, measured table rows and explicit diagnostics."""
    rows = groups(details)
    headers, claimed = stacked_headers(rows)
    items, diagnostics = [], []
    columns = None
    table_y = None
    for row_index,row in enumerate(rows):
        if row_index in claimed:continue
        if any('|' in p['text'] for p in row):
            continue  # the retained parser owns pipe tables
        # Split actual inline colon spans; the same measured span remains the
        # locator for both pieces. We do not pretend it is a precise value box.
        expanded = []
        for p in row:
            match = re.fullmatch(r'([^:]{1,40}):\s*(.+)', p['text'].strip())
            if match and key(match[1]) in HEADER_ALIASES:
                expanded.extend([p | {'text': match[1] + ':'}, p | {'text': match[2]}])
            else:
                expanded.append(p)
        # A complete recognized heading row starts a bounded table.
        found = heading_columns(row)
        if found:
            names = [field for field, _ in found]
            if len(set(names)) != len(names):
                diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
                columns = None
            else:
                columns = found
                table_y = max(p['bbox']['y2'] for p in row)
            continue
        # Header key/value rows terminate a table, so totals cannot become items.
        anchors = []
        cursor = 0
        while cursor < len(expanded):
            hit = label_at(expanded, cursor, HEADER_ALIASES)
            if hit:
                count, field, parts = hit
                if columns and len(expanded)>=len(columns) and not any(':' in p['text'] or '#' in p['text'] for p in parts):
                    cursor += count
                    continue
                # Require a printed delimiter for bare "Invoice" / "PO".
                if field in ('invoice_number', 'po_reference') and count == 1 and key(parts[0]['text']) in ('invoice', 'po') and not any(c in parts[0]['text'] for c in ':#'):
                    cursor += count
                    continue
                anchors.append((cursor, count, field, parts))
                cursor += count
            else:
                cursor += 1
        if anchors:
            accepted = False
            for n, (start, count, field, parts) in enumerate(anchors):
                end = anchors[n + 1][0] if n + 1 < len(anchors) else len(expanded)
                values = expanded[start + count:end]
                if not values:
                    continue
                gap = values[0]['bbox']['x1'] - parts[-1]['bbox']['x2']
                if gap > .22:
                    continue
                raw = ' '.join(p['text'].strip() for p in values).strip()
                headers.append((field, raw, union(parts + values,source=True)))
                accepted = True
            if accepted:
                columns = None
                continue
        if not columns:
            continue
        if table_y is not None and min(p['bbox']['y1'] for p in row)-table_y > .08:
            columns = None
            continue
        cells,crossing=column_cells(row,columns)
        description=next(i for i,(field,_) in enumerate(columns) if field=='description')
        if cells[description] and not any(c for i,c in enumerate(cells) if i!=description) and not crossing and items and row_index+1<len(rows):
            # A close description continuation must be followed by another
            # complete numeric item under the same headings. Last-row notes and
            # footers remain uncertain; no row is created from isolated text.
            following,overlap=column_cells(rows[row_index+1],columns)
            gap=min(p['bbox']['y1'] for p in row)-(table_y or 0)
            next_gap=min(p['bbox']['y1'] for p in rows[row_index+1])-max(p['bbox']['y2'] for p in row)
            if 0<=gap<=.025 and 0<=next_gap<=.06 and (all(following) or readable_partial_row(following,columns)) and not overlap and not heading_columns(rows[row_index+1]):
                field,raw,box=items[-1][description]
                continued=union(cells[description],source=True)
                joined=union([{'bbox':box},{'bbox':continued}])
                items[-1][description]=(field,raw+' '+' '.join(p['text'].strip() for p in cells[description]),joined)
                table_y=max(p['bbox']['y2'] for p in row)
                continue
        if not cells[description] or not any(c for i,c in enumerate(cells) if i!=description):
            diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
            columns = None
            continue
        if crossing or (any(not c for c in cells) and not readable_partial_row(cells,columns)):
            diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
            columns = None
            continue
        if any(not c for c in cells):diagnostics.append('TABLE_CELL_UNREAD')
        if len(items) >= 200:
            diagnostics.append('TABLE_ROW_LIMIT')
            break
        items.append([(field, ' '.join(p['text'].strip() for p in cell) if cell else None, union(cell,source=True) if cell else None)
                      for (field, _), cell in zip(columns, cells)])
        table_y = max(p['bbox']['y2'] for p in row)
    return headers, items, list(dict.fromkeys(diagnostics))
