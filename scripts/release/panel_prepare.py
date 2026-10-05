#!/usr/bin/env python3
"""Prepare one isolated fictional policy through existing authorized local APIs.

Uses established development identities; no credential setup, model control,
invoice processing, business master replacement or outcome generation.
"""
import json
import os
from pathlib import Path
import sys
from uuid import uuid4
import httpx

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from demo import private_json

ORIGIN = 'http://127.0.0.1:3000'
STATE = ROOT / 'runtime/kivo-panel/operator-policy.json'


def main():
    os.umask(0o077)
    if STATE.is_symlink() or STATE.exists() and STATE.stat().st_mode & 0o077:
        raise RuntimeError('Operator sample journal must be a private regular file.')
    if STATE.exists():
        state = json.loads(STATE.read_text())
    else:
        identifier = str(uuid4())
        payload = json.loads((ROOT / 'data/synthetic/reference/expense_policies.json').read_text())['records'][0]
        for field in ('tenant_id', 'legal_entity_id'):
            payload.pop(field)
        payload.update(id=identifier, policy_code='DEMO-PANEL-HOTEL-' + identifier[:8],
                       label='DEMO / FICTIONAL PANEL HOTEL', effective_from='2026-11-01')
        payload['dimensions']['location'] = 'PANEL-CITY-' + identifier[:8]
        state = {'payload': payload, 'stage_key': str(uuid4()), 'validate_key': str(uuid4()), 'activate_key': str(uuid4())}
        private_json(STATE, state)
    with httpx.Client(base_url=ORIGIN, timeout=30) as client:
        client.post('/api/development/session', headers={'Origin': ORIGIN},
                    json={'label': 'Synthetic finance reviewer'}).raise_for_status()
        def post(path, body, key):
            response = client.post('/api/' + path, json=body,
                                   headers={'Origin': ORIGIN, 'Idempotency-Key': key})
            response.raise_for_status()
            return response.json()
        if not state.get('activated'):
            staged = post('reference-imports', {'source_system': 'SYNTHETIC_PANEL_OPERATOR', 'source_version': 'v1',
                'reason': 'Prepare one isolated fictional operator policy; preserve all established records.',
                'records': [{'kind': 'expense_policies', 'payload': state['payload']}]}, state['stage_key'])
            valid = post('reference-imports/' + staged['id'] + '/validate', {}, state['validate_key'])
            if valid['state'] != 'VALID':
                raise RuntimeError('Fictional sample validation failed; no policy activated.')
            active = post('reference-imports/' + staged['id'] + '/activate',
                          {'reason': 'Activate fictional isolated panel hotel policy for its distinct sample location.'},
                          state['activate_key'])
            if active['state'] != 'ACTIVE':
                raise RuntimeError('Fictional sample activation did not complete.')
            state['activated'] = True
            private_json(STATE, state)
        result = client.get('/api/admin/catalog')
        result.raise_for_status()
        record = next(r for r in result.json()['items'] if r['id'] == state['payload']['id'])
        print(json.dumps({'fictional': True, 'policy_code': record['payload']['policy_code'],
                          'current_version': record['version'], 'allowance': record['payload']['allowance_amount'],
                          'source_file': 'data/kivo_panel/d01.pdf',
                          'limitations': 'Preparation only. Repeated execution preserves this record and all existing history; it does not reset a changed allowance.'}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # No response bodies, credentials or uploaded contents in operator output.
        print('Panel preparation failed: ' + (str(error) if isinstance(error, RuntimeError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
