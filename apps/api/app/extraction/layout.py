"""Conservative geometric association of actual PDF spans / OCR words.

Only printed labels and column headings establish meaning. Coordinates are
measured regions, not confidence. Unknown, crossing and competing cells abstain.
The legacy labeled/pipe parser remains intact. No arithmetic supplies raw facts.
"""
import re

VERSION = 'printed-layout-v7'
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
    'quantity': 'quantity', 'qty': 'quantity', 'unit price': 'unit_price', 'price': 'unit_price', 'rate': 'unit_price',
    'sku': 'sku', 'barcode': 'barcode',
    'discount': 'discount_amount', 'disc': 'discount_amount', 'net': 'net_amount', 'net amount': 'net_amount',
    'tax rate': 'tax_rate', 'tax': 'tax_amount', 'tax amount': 'tax_amount',
    'gross': 'gross_amount', 'gross amount': 'gross_amount',
    'amount': 'amount', 'line total': 'amount', 'total': 'amount', 'uom': 'uom', 'unit': 'uom',
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
        if aliases is HEADER_ALIASES and re.fullmatch(r'(?:VAT|GST|sales tax|tax)\s+\d{1,2}(?:[.,]\d+)?\s*%',joined.strip(),re.IGNORECASE):
            return count,'tax_amount',parts  # printed summary label, never tax treatment/rate inference
    return None


def heading_columns(row):
    candidates=[]
    for start in range(len(row)):
        found=[];cursor=start
        while cursor<len(row):
            heading=label_at(row,cursor,COLUMN_ALIASES)
            if not heading:break
            count,field,parts=heading;found.append((field,union(parts)));cursor+=count
        names=[field for field,_ in found]
        if {'description','quantity','unit_price'}<=set(names) and set(names)&{'amount','net_amount','gross_amount'}:
            candidates.append(found)
    if not candidates:return None
    largest=max(map(len,candidates));best=[c for c in candidates if len(c)==largest]
    return best[0] if len(best)==1 else None  # competing independently printed schemas abstain


def table_groups(details):
    """Join two adjacent fragments only for one uniquely printed heading row.

    Axis-aligned OCR rectangles can miss a mild baseline slope. This association
    uses actual label regions only; generic header/value and item grouping stays
    unchanged. Competing labels, overlapping columns and nonlinear rows abstain.
    """
    rows=groups(details);out=[];index=0
    def labels_only(row):
        cursor=0
        while cursor<len(row):
            hit=label_at(row,cursor,COLUMN_ALIASES)
            if not hit:return False
            cursor+=hit[0]
        return True
    while index<len(rows):
        row=rows[index];merged=None
        if index+1<len(rows) and not heading_columns(row) and labels_only(row) and labels_only(rows[index+1]):
            candidate=sorted(row+rows[index+1],key=lambda s:s['bbox']['x1']);columns=heading_columns(candidate)
            if columns and len({field for field,_ in columns})==len(columns):
                boxes=[box for _,box in columns];height=min(b['y2']-b['y1'] for b in boxes)
                overlap=min(b['y2'] for b in boxes)-max(b['y1'] for b in boxes)
                separated=all(a['x2']<b['x1'] for a,b in zip(boxes,boxes[1:]))
                points=[((b['x1']+b['x2'])/2,(b['y1']+b['y2'])/2) for b in boxes]
                x,y=points[0];last_x,last_y=points[-1]
                if separated and height>0 and overlap>=height*.4 and last_x>x:
                    slope=(last_y-y)/(last_x-x)
                    if all(abs(py-(y+slope*(px-x)))<=height*.25 for px,py in points):merged=candidate
        if merged is not None:out.append(merged);index+=2
        else:out.append(row);index+=1
    return out


def first_cluster(parts):
    """One contiguous value, never a separate far column on the same baseline."""
    for i,(a,b) in enumerate(zip(parts,parts[1:]),1):
        if b['bbox']['x1']-a['bbox']['x2']>.06:return parts[:i]
    return parts


def table_columns(details):
    """Independent printed schema, never row values supplied to a model."""
    schemas=[tuple(field for field,_ in found) for row in table_groups(details) if (found:=heading_columns(row))]
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
        labels=[];cursor=0;unrelated=[]
        while cursor<len(row):
            hit=label_at(row,cursor,HEADER_ALIASES)
            if not hit:
                unrelated.append(row[cursor]);cursor+=1;continue
            count,field,parts=hit
            if key(' '.join(p['text'] for p in parts)) in ('invoice','po') and not any(':' in p['text'] or '#' in p['text'] for p in parts):break
            labels.append((field,parts));cursor+=count
        if cursor!=len(row) or not labels or len({f for f,_ in labels})!=len(labels):continue
        if any(not all(p['bbox']['x2']+.06<=parts[0]['bbox']['x1'] or p['bbox']['x1']>=parts[-1]['bbox']['x2']+.06 for _,parts in labels) for p in unrelated):continue
        # Unrelated text may belong to an independently separated left column.
        # Text to the right of a label can be its inline value; never claim
        # that row as stacked and replace it with the following row's text.
        if any(0<=p['bbox']['x1']-parts[-1]['bbox']['x2']<=.22 for p in unrelated for _,parts in labels):continue
        values=rows[index+1]
        # PDF font extents can overlap even when consecutive printed baselines
        # are distinct. Limit this allowance to measured native font spans;
        # OCR boxes and material overlap still cannot associate labels/values.
        associations=[];used=[]
        for n,(field,parts) in enumerate(labels):
            left=parts[0]['bbox']['x1']
            right=labels[n+1][1][0]['bbox']['x1']-.015 if n+1<len(labels) else 1
            assigned=[p for p in values if left-.018<=p['bbox']['x1'] and p['bbox']['x2']<=right]
            if not assigned or abs(assigned[0]['bbox']['x1']-left)>.03:break
            assigned=first_cluster(assigned)
            if any(key(p['text']) in HEADER_ALIASES for p in assigned):break
            # Check this independently owned column, not distant table cells
            # on a slightly different baseline. Tiny detector-box overlap is
            # allowed only between vertically ordered label/value centers.
            gap=min(p['bbox']['y1'] for p in assigned)-max(p['bbox']['y2'] for p in parts)
            height=min(p['bbox']['y2']-p['bbox']['y1'] for p in parts+assigned)
            allowance=.25 if all(0<p.get('font_size_points',0)<=512 for p in parts+assigned) else .10
            if not -height*allowance<=gap<=.04:break
            used.extend(assigned)
            associations.append((field,' '.join(p['text'].strip() for p in assigned),union(parts+assigned,source=True)))
        unassigned=[p for p in values if p not in used]
        separated=all(all(p['bbox']['x2']+.06<=v['bbox']['x1'] or p['bbox']['x1']>=v['bbox']['x2']+.06 for v in used) for p in unassigned)
        if len(associations)==len(labels) and separated:
            out.extend(associations)
            if not unrelated:claimed.add(index)
            if not unassigned:claimed.add(index+1)
    return out,claimed


def column_cells(row,columns):
    row=[p for p in row if p['bbox']['x2']>columns[0][1]['x1']-.06]
    bounds=[(a[1]['x2']+b[1]['x1'])/2 for a,b in zip(columns,columns[1:])]
    text_fields={'sku','barcode','description'}
    ordered=sorted(row,key=lambda span:span['bbox']['x1'])
    metadata=any(field in ('sku','barcode') for field,_ in columns)
    separated=lambda blocks:all(max(p['bbox']['x2'] for p in left)<=min(p['bbox']['x1'] for p in right) for left,right in zip(blocks,blocks[1:]))
    if metadata and len(ordered)==len(columns) and separated([[p] for p in ordered]):
        # Metadata/description headings may be centered/right-aligned within
        # wide cells. Exact ordered independent regions and all numeric/unit
        # anchors establish this row; broad/crossing financial cells do not.
        anchored=True
        for i,((field,_),p) in enumerate(zip(columns,ordered)):
            if field in text_fields:continue
            box=p['bbox'];center=(box['x1']+box['x2'])/2
            anchored &= sum(center>=b for b in bounds)==i and not any(box['x1']<b<box['x2'] for b in bounds)
        if anchored:return [[p] for p in ordered],False
    cells=[[] for _ in columns];crossing=False
    financial_crossing=False
    for span in row:
        box=span['bbox'];center=(box['x1']+box['x2'])/2
        i=sum(center>=b for b in bounds);cells[i].append(span)
        crossed=any(box['x1']<b<box['x2'] for b in bounds)
        crossing |= crossed;financial_crossing |= crossed and columns[i][0] not in text_fields
    if metadata and crossing and not financial_crossing and all(cells) and separated(cells):crossing=False
    return cells,crossing


def readable_partial_row(cells,columns):
    missing=[field for (field,_),cell in zip(columns,cells) if not cell]
    present={field for (field,_),cell in zip(columns,cells) if cell}
    return ('description' in present and (
        len(missing)==1 and missing[0] in ('quantity','unit_price','amount','net_amount','gross_amount') and len(present)>=3 or
        set(missing)=={'quantity','unit_price'} and bool(present&{'amount','net_amount','gross_amount'})))


def table_retry_regions(details, maximum=3):
    """Bounded OCR retries for one absent numeric cell in a measured table row.

    Three independently detected cells and unique complete headings establish
    a candidate row region, never its missing value. Crossing/multiple missing
    cells, notes and isolated descriptions cannot request retries. Crop extents
    are routing metadata; only the new detector's measured box is evidence.
    """
    rows=table_groups(details);columns=None;table_y=None;out=[]
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


def printed_layout(details, _split_panels=True):
    """Return header candidates, measured table rows and explicit diagnostics."""
    rows = table_groups(details)
    # A table printed wholly in a separate right panel must not use a nearby
    # left header as its row baseline. Split only on an independently measured
    # complete schema and a clear gap; crossing regions stay with the table and
    # retain the existing uncertainty checks. Source boxes are never changed.
    if _split_panels:
        starts=[found[0][1]['x1'] for row in rows if (found:=heading_columns(row))]
        if starts and min(starts)>=.3 and max(starts)-min(starts)<=.02:
            boundary=min(starts)-.06
            left=[s for s in details.get('spans',[]) if s.get('layout_bbox',s.get('bbox',{})).get('x2',1)<=boundary]
            right=[s for s in details.get('spans',[]) if s not in left]
            if left and right:
                lh,li,ld=printed_layout(details|{'spans':left},False)
                rh,ri,rd=printed_layout(details|{'spans':right},False)
                return lh+rh,li+ri,list(dict.fromkeys(ld+rd))
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
            accepted = False;outside_table=columns is not None
            for n, (start, count, field, parts) in enumerate(anchors):
                end = anchors[n + 1][0] if n + 1 < len(anchors) else len(expanded)
                values = first_cluster(expanded[start + count:end])
                if not values:
                    continue
                gap = values[0]['bbox']['x1'] - parts[-1]['bbox']['x2']
                if gap > .22:
                    continue
                raw = ' '.join(p['text'].strip() for p in values).strip()
                headers.append((field, raw, union(parts + values,source=True)))
                outside_table &= union(parts+values)['x2']<=columns[0][1]['x1']-.06 if columns else False
                accepted = True
            if accepted and not outside_table:
                columns = None
                continue
        if not columns:
            continue
        if all(p['bbox']['x2']<=columns[0][1]['x1']-.06 for p in row):continue
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
