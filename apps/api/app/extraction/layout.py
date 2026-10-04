"""Conservative geometric association of actual PDF spans / OCR words.

Only printed labels and column headings establish meaning. Coordinates are
measured regions, not confidence. Unknown, crossing and competing cells abstain.
The legacy labeled/pipe parser remains intact. No arithmetic supplies raw facts.
"""
import re

VERSION = 'printed-layout-v1'
HEADER_ALIASES = {
    'supplier': 'vendor_name', 'vendor': 'vendor_name', 'supplier name': 'vendor_name',
    'vendor name': 'vendor_name', 'merchant': 'merchant_name',
    'invoice number': 'invoice_number', 'invoice no': 'invoice_number', 'invoice': 'invoice_number',
    'receipt number': 'receipt_number', 'receipt no': 'receipt_number',
    'invoice date': 'invoice_date', 'expense date': 'expense_date', 'date': 'invoice_date',
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


def printed_layout(details):
    """Return header candidates, measured table rows and explicit diagnostics."""
    rows = groups(details)
    headers, items, diagnostics = [], [], []
    columns = None
    table_y = None
    for row in rows:
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
        found = []
        cursor = 0
        while cursor < len(row):
            heading = label_at(row, cursor, COLUMN_ALIASES)
            if not heading:
                break
            count, field, parts = heading
            found.append((field, union(parts)))
            cursor += count
        names = [field for field, _ in found]
        if cursor == len(row) and {'description', 'quantity', 'unit_price'} <= set(names) and set(names) & {'amount', 'net_amount', 'gross_amount'}:
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
        bounds = [(a[1]['x2'] + b[1]['x1']) / 2 for a, b in zip(columns, columns[1:])]
        cells = [[] for _ in columns]
        crossing = False
        for span in row:
            box = span['bbox']
            center = (box['x1'] + box['x2']) / 2
            index = sum(center >= b for b in bounds)
            cells[index].append(span)
            if any(box['x1'] < b < box['x2'] for b in bounds):
                crossing = True
        if not cells[0] or not any(cells[1:]):
            # Footers and isolated text cannot become a payable row. A wrapped
            # continuation is currently incomplete rather than silently appended.
            diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
            columns = None
            continue
        if crossing or any(not c for c in cells):
            diagnostics.append('TABLE_COVERAGE_UNCERTAIN')
            columns = None
            continue
        if len(items) >= 200:
            diagnostics.append('TABLE_ROW_LIMIT')
            break
        items.append([(field, ' '.join(p['text'].strip() for p in cell), union(cell,source=True))
                      for (field, _), cell in zip(columns, cells)])
        table_y = max(p['bbox']['y2'] for p in row)
    return headers, items, list(dict.fromkeys(diagnostics))
