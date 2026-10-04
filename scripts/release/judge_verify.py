#!/usr/bin/env python3
"""Read-only acceptance of the existing computed fictional judge walkthrough.

No uploads, approvals, reevaluation, policy changes or expected answers to a
model. Credentials remain in the existing local server configuration. Current
eligibility and retained historical evidence are checked separately.
"""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'apps/api'), str(ROOT / 'scripts'), str(ROOT / 'scripts/seed')]
from hackathon import Runner


def main():
    runner = Runner()
    scenarios = runner.saved['scenarios']
    expected = {'vlm-pass': 'PASS', 'paid-duplicate': 'HOLD',
                'employee-clean': 'PASS', 'employee-allowance': 'REVIEW',
                'partial-delivery': 'HOLD', 'shared-receipt': 'PASS',
                'shared-overflow': 'HOLD', 'correction': 'PASS'}
    if {row['key'] for row in scenarios} != set(expected):
        raise RuntimeError('Prepare the complete existing fictional walkthrough first')
    checks = []
    for scenario in scenarios:
        name = scenario['key']
        detail = runner.request('GET', 'transactions/' + scenario['transaction_id'])
        current = runner.request('GET', 'evaluations/' + detail['latest_evaluation_id'])
        retained = runner.request('GET', 'evaluations/' + scenario['evaluation_id'])
        if retained['decision'] != expected[name] or retained['transaction_version'] != scenario['transaction_version']:
            raise RuntimeError('Retained computed report changed: ' + name)
        if detail['decision'] != expected[name] or current['evaluation_status'] != 'CURRENT':
            raise RuntimeError('Current computed screening requires attention: ' + name)
        if detail['eligible'] != (expected[name] == 'PASS'):
            raise RuntimeError('Current eligibility differs from the judge expectation: ' + name)
        if len(current['rules']) != 28:
            raise RuntimeError('Incomplete current finance controls: ' + name)
        findings = [rule for rule in current['rules'] if rule['decision_effect'] != 'NONE']
        if expected[name] != 'PASS' and not any(rule['evidence'] for rule in findings):
            raise RuntimeError('Exception lacks retained citations: ' + name)
        if name == 'vlm-pass':
            document = runner.request('GET', 'documents/' + scenario['document_id'])
            run = next(r for r in document['extraction_runs'] if r['id'] == scenario['extraction_run'])
            versions = {v['name']: v['version'] for v in run['metadata']['runtime_versions']}
            if run['metadata']['provider_id'] != 'ENTERPRISE_VLM' or versions.get('model_revision') != '66285546d2b821cf421d4f5eb2576359d3770cd3':
                raise RuntimeError('Retained visual source lacks the accepted actual provider')
            sources = runner.request('GET', 'transactions/' + detail['id'] + '/sources')
            if not any(d['verified'] for d in sources['documents']):
                raise RuntimeError('Clean case lacks explicit source verification')
        if name == 'correction':
            original = runner.request('GET', 'evaluations/' + scenario['original_evaluation_id'])
            if original['decision'] != 'HOLD' or original['transaction_version'] != scenario['original_version']:
                raise RuntimeError('Original correction HOLD was not retained')
        checks.append({'case': name, 'decision': current['decision'],
                       'current_version': detail['version'], 'eligible': detail['eligible'],
                       'rules': len(current['rules']), 'cited_findings': sum(bool(r['evidence']) for r in findings)})
    print(json.dumps({'synthetic': True, 'read_only': True, 'scenarios': checks,
                      'limitations': 'Existing local fictional history, not a production acceptance corpus. Policy version UI is checked separately.'}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        # Do not expose HTTP bodies, source content, configuration or credentials.
        print('Judge verification failed: ' + (str(error) if isinstance(error, RuntimeError) else type(error).__name__), file=sys.stderr)
        raise SystemExit(1)
