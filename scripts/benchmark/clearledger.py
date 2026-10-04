#!/usr/bin/env python3
"""Frozen lawful synthetic layout benchmark, through the actual production router.

Expectations are compared only after extraction. No expected fields enter prompts.
Held-out means layout reserved before implementation, not real-world generalization.
Private artifacts stay under ignored runtime/clearledger. No external document fetch.
"""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'apps/api'))


def freeze():
    from reportlab.pdfgen import canvas
    from app.documents.processor import DocumentProcessor
    target = ROOT / 'runtime/clearledger/corpus'
    target.mkdir(parents=True, exist_ok=True)
    manifest = target / 'manifest.json'
    if manifest.exists():
        return manifest
    cases = []
    for name, split, compact, pages in [('columns', 'development', False, 1),
                                       ('scan', 'development', True, 1),
                                       ('continuation', 'held_out', False, 2)]:
        pdf = target / (name + '.pdf')
        c = canvas.Canvas(str(pdf), pagesize=(792, 612), invariant=1)
        expected_rows = []
        for page in range(pages):
            font = 'Courier' if split == 'held_out' else 'Helvetica'
            c.setFont(font, 12)
            c.drawString(36, 568, 'Fictional invoice for local extraction testing')
            left = [('Supplier', 'Cedar Supplies Ltd'), ('Currency', 'INR'),
                    ('Tax basis', 'EXCLUSIVE'), ('Subtotal', '300.00'), ('Tax', '54.00'),
                    ('Total', '354.00'), ('Discount', '0.00'), ('Shipping', '0.00'), ('Other charges', '0.00')]
            right = [('Invoice number', 'CL-' + name.upper()), ('Invoice date', '2026-09-17'),
                     ('Due date', '2026-10-17'), ('Purchase order', 'CL-PO-100'), ('Payment terms', '30 days')]
            if compact:
                left = [x for x in left if x[0] not in ('Tax basis', 'Discount', 'Shipping', 'Other charges')]
            for offset, pairs in [(36, left), (430, right)]:
                for n, (label, value) in enumerate(pairs):
                    c.setFont(font, 10)
                    c.drawString(offset, 534 - n * 20, label + ':')
                    c.drawString(offset + 132, 534 - n * 20, value)
            fields = ['description', 'quantity', 'unit_price', 'amount'] if compact else [
                'description', 'quantity', 'unit_price', 'discount_amount', 'net_amount', 'tax_rate', 'tax_amount', 'gross_amount', 'uom']
            labels = ['Description', 'Qty', 'Unit price', 'Amount'] if compact else [
                'Description', 'Qty', 'Unit price', 'Discount', 'Net', 'Tax rate', 'Tax', 'Gross', 'UOM']
            xs = [36, 350, 470, 625] if compact else [36, 255, 310, 385, 450, 515, 580, 645, 720]
            c.setFont(font, 9)
            for x, label in zip(xs, labels):
                c.drawString(x, 304, label)
            for row in range(1 if pages == 2 else 2):
                description = ('Notebook cases' if page == 0 and row == 0 else 'Storage folders')
                values = [description, '1', '150.00', '150.00'] if compact else [
                    description, '1', '150.00', '0.00', '150.00', '0.18', '27.00', '177.00', 'EA']
                expected_rows.append(dict(zip(fields, values)))
                for x, value in zip(xs, values):
                    c.drawString(x, 277 - row * 30, value)
            c.drawString(36, 36, f'Synthetic source. Page {page + 1} of {pages}. No company policy.')
            c.showPage()
        c.save()
        file = pdf
        if compact:
            file = target / (name + '.png')
            file.write_bytes(base64.b64decode(DocumentProcessor().process(pdf)['pages'][0]['preview_base64']))
        cases.append({'name': name, 'split': split, 'path': file.name,
                      'sha256': hashlib.sha256(file.read_bytes()).hexdigest(),
                      'expected': {'vendor_name': 'Cedar Supplies Ltd', 'invoice_number': 'CL-' + name.upper(),
                                   'invoice_date': '2026-09-17', 'currency': 'INR', 'total_amount': '354.00'},
                      'rows': expected_rows})
    manifest.write_text(json.dumps({'version': 'clearledger-layout-benchmark-v1', 'cases': cases}, indent=2) + '\n')
    return manifest


def run(label, only=None):
    from app.core.config import Settings
    from app.core.identity import Identity
    from app.documents.processor import DocumentProcessor
    from app.integrations.storage import LocalStorage
    from app.db.models import Base  # initialize the existing model registry first
    from app.services.document_worker import extract
    from app.domain.extraction import to_data
    from app.documents.normalizer import Normalizer, validate_draft
    manifest = freeze()
    config = Settings.load()
    os.environ.setdefault(config.document_providers.gateway_token_env,
                          (ROOT / 'runtime/inference/gateway.key').read_text().strip())
    identity = Identity(uuid4(), uuid4(), uuid4(), frozenset({'FINANCE_REVIEWER'}), 'Synthetic layout benchmark')
    storage = LocalStorage(ROOT / 'runtime/clearledger/storage')
    cases = json.loads(manifest.read_text())['cases']
    output = ROOT / 'runtime/clearledger' / (label + '.json')
    results = []
    for case in cases:
        if only and case['split'] != only:
            continue
        file = manifest.parent / case['path']
        if hashlib.sha256(file.read_bytes()).hexdigest() != case['sha256']:
            raise RuntimeError('Frozen source changed')
        samples = []
        stop = threading.Event()
        def sample():
            while not stop.is_set():
                try:
                    samples.append(int(subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used',
                        '--format=csv,noheader,nounits'], text=True, timeout=2).strip().splitlines()[0]))
                except (ValueError, OSError, subprocess.SubprocessError):
                    pass
                stop.wait(.5)
        thread = threading.Thread(target=sample, daemon=True)
        thread.start()
        started = time.monotonic()
        data = {'name': case['name'], 'split': case['split'], 'source_sha256': case['sha256']}
        try:
            pages = DocumentProcessor().process(file)['pages']
            for p in pages:
                p['preview_key'], _ = storage.put(identity, base64.b64decode(p.pop('preview_base64')),
                                                  maximum=config.document_limits.maximum_derived_bytes)
            result, diagnostics, routing = extract({'id': uuid4(), 'source_type': 'VENDOR_INVOICE'}, identity,
                                                   pages, storage, config.document_providers)
            result = to_data(result)
            observations = [o | {'id': str(uuid4())} for o in result['header_fields']]
            observations += [o | {'id': str(uuid4()), 'field_path': f'lines.{r["row_index"]-1}.{o["field_path"]}'}
                             for r in result['line_items'] for o in r['fields']]
            candidate, traces, findings = Normalizer().normalize(observations)
            findings += validate_draft(candidate, traces, 'VENDOR_INVOICE', diagnostics)
            # Independent expectations never enter extract(), bundle or provider prompts.
            by = {o['field_path']: o for o in result['header_fields']}
            header_checks = {k: by.get(k, {}).get('raw_value') == v and by.get(k, {}).get('state') == 'PRESENT'
                             for k, v in case['expected'].items()}
            row_checks = []
            for index, expected in enumerate(case['rows']):
                actual = {o['field_path']: o for o in result['line_items'][index]['fields']} if index < len(result['line_items']) else {}
                row_checks.extend(actual.get(k, {}).get('raw_value') == v and actual.get(k, {}).get('state') == 'PRESENT'
                                  for k, v in expected.items())
            data.update(result=result, routing=routing, diagnostics=diagnostics, candidate=candidate,
                        findings=findings, header_matches=sum(header_checks.values()), header_checked=len(header_checks),
                        row_matches=sum(row_checks), row_checked=len(row_checks),
                        expected_rows=len(case['rows']), actual_rows=len(result['line_items']))
        except Exception as e:
            data['failure'] = getattr(e, 'code', type(e).__name__)
        finally:
            stop.set()
            thread.join(timeout=3)
        data.update(seconds=round(time.monotonic() - started, 3), peak_whole_device_memory_mib=max(samples) if samples else None,
                    temperature='resident_model; first_request_after_idle' if not results else 'resident_model; subsequent_request')
        results.append(data)
        output.write_text(json.dumps({'version': 'clearledger-benchmark-v1', 'label': label,
            'limitations': 'Three synthetic layouts frozen before implementation; one reserved layout, no representative real accuracy claim. Whole-device VRAM includes other processes. Model already resident; not cold model loading.',
            'cases': results}, indent=2) + '\n')
        print(json.dumps({k: v for k, v in data.items() if k not in ('result', 'candidate', 'findings', 'routing', 'diagnostics')}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', action='store_true')
    parser.add_argument('--label', default='baseline')
    parser.add_argument('--split', choices=['development', 'held_out'])
    args = parser.parse_args()
    os.umask(0o077)
    if args.freeze:
        print(freeze())
    else:
        run(args.label, args.split)
