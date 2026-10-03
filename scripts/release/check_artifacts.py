#!/usr/bin/env python3
"""Local approval/workflow contracts. No Azure login or resource changes."""
import copy
import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import patch

from deployment_gate import REQUIRED, validate
import pilot_dispatch

ROOT = Path(__file__).resolve().parents[2]


def approvals(parameters):
    return dict.fromkeys(REQUIRED, True) | {
        'subscription_id': '90000000-0000-4000-8000-000000000001',
        'region': 'syntheticregion', 'resource_group': 'synthetic-approved-pilot',
        'monthly_spend_ceiling': '1.00', 'gpu_disposition': 'DEFERRED_EXTERNAL',
        'approved_by': 'Synthetic contract reviewer', 'approved_at': '2026-10-04',
        'release_commit': 'a' * 40,
        'release_parameters_sha256': hashlib.sha256(parameters).hexdigest(),
    }


def check_approval_contract():
    parameters = json.dumps({'parameters': {
        'location': {'value': 'syntheticregion'},
        'registryHost': {'value': 'synthetic.azurecr.io'},
    }}).encode()
    approved = approvals(parameters)
    assert validate(approved)
    invalid = [dict(approved, **{key: None}) for key in REQUIRED]
    invalid += [dict(approved, monthly_spend_ceiling=value)
                for value in ('0', '-1', 'NaN', 'Infinity', 1)]
    invalid += [dict(approved, resource_group='unsafe/group'),
                dict(approved, approved_by=' ')]
    for value in invalid:
        try:
            validate(value)
        except (ValueError, TypeError, KeyError):
            continue
        raise AssertionError('Invalid deployment approval accepted.')
    with tempfile.TemporaryDirectory() as folder:
        parameter_file = Path(folder) / 'parameters.json'
        approval_file = Path(folder) / 'approval.json'
        parameter_file.write_bytes(parameters)
        environment = {
            'RELEASE_COMMIT': approved['release_commit'],
            'AP_RESOURCE_GROUP': approved['resource_group'],
            'AP_RELEASE_PARAMETERS': str(parameter_file),
            'APPROVAL_FILE': str(approval_file),
        }
        for difference in ('subscription', 'resource_group', 'region', 'digest'):
            value = copy.deepcopy(approved)
            subscription = approved['subscription_id']
            if difference == 'subscription':
                subscription = '90000000-0000-4000-8000-000000000002'
            elif difference == 'resource_group':
                value['resource_group'] = 'different-approved-group'
            elif difference == 'region':
                value['region'] = 'differentregion'
            else:
                value['release_parameters_sha256'] = 'b' * 64
            approval_file.write_text(json.dumps(value))
            with patch.dict(os.environ, environment), patch.object(
                pilot_dispatch.subprocess, 'run',
                return_value=subprocess.CompletedProcess([], 0, stdout=subscription + '\n'),
            ) as runner:
                try:
                    pilot_dispatch.main()
                except SystemExit:
                    pass
                else:
                    raise AssertionError('Mismatched deployment target accepted.')
                assert all(call.args[0][:3] == ['az', 'account', 'show']
                           for call in runner.call_args_list)
    print('Approval contracts: missing/invalid inputs and target/hash mismatches blocked before migrations or deployment.')


def check_workflows():
    import yaml  # isolated release-tools dependency; not part of the application
    pins = json.loads((ROOT / 'deploy/actions-pins.json').read_text())
    known = {item['action'] + '@' + item['sha'] for item in pins.values()}
    blocks = 0
    for path in sorted((ROOT / '.github/workflows').glob('*.yml')):
        document = yaml.load(path.read_text(), Loader=yaml.BaseLoader)
        for job in document['jobs'].values():
            for step in job['steps']:
                if 'uses' in step:
                    assert step['uses'] in known, 'Unreviewed workflow action.'
                if 'run' in step:
                    subprocess.run(['bash', '-n'], input=step['run'], text=True, check=True)
                    blocks += 1
    print(f'Workflow contracts: reviewed action pins, YAML parsing and {blocks} shell blocks passed; hosted execution remains deferred.')


if __name__ == '__main__':
    check_approval_contract()
    check_workflows()
