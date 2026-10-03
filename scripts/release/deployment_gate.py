#!/usr/bin/env python3
"""Validate explicit operator approvals; never provision or invent missing inputs."""
import argparse,json,re,sys
from decimal import Decimal
from pathlib import Path
from uuid import UUID
REQUIRED=('subscription_id','region','permissions_verified','monthly_spend_ceiling','identity_approved','network_approved','data_residency_approved','gpu_disposition','approved_by','approved_at','private_runner_verified','cloud_restore_verified','authorization_smoke_verified','rollback_verified','release_commit','release_parameters_sha256')

def validate(data):
    missing=[k for k in REQUIRED if not data.get(k)]
    if missing:raise ValueError('Missing deployment gate inputs: '+', '.join(missing))
    if not re.fullmatch('[a-f0-9]{40}',data['release_commit']) or not re.fullmatch('[a-f0-9]{64}',data['release_parameters_sha256']):raise ValueError('Verified commit and reviewed parameter digest required.')
    UUID(data['subscription_id'])
    if not re.fullmatch('[a-z0-9]+',data['region']):raise ValueError('Approved Azure region required.')
    if not isinstance(data['monthly_spend_ceiling'],str) or not Decimal(data['monthly_spend_ceiling']).is_finite() or Decimal(data['monthly_spend_ceiling'])<=0:raise ValueError('Explicit finite decimal spend ceiling required.')
    for key in ('permissions_verified','identity_approved','network_approved','data_residency_approved','private_runner_verified','cloud_restore_verified','authorization_smoke_verified','rollback_verified'):
        if data[key] is not True:raise ValueError('Deployment gate not verified: '+key)
    if data['gpu_disposition'] not in ('DEFERRED_EXTERNAL','SEPARATELY_APPROVED'):raise ValueError('Explicit inference authorization disposition required.')
    return True

def main():
    parser=argparse.ArgumentParser();parser.add_argument('approval_file',type=Path);args=parser.parse_args()
    try:validate(json.loads(args.approval_file.read_text()))
    except (OSError,ValueError,TypeError,KeyError):raise SystemExit('DEFERRED_EXTERNAL: deployment approvals are absent or incomplete. No provisioning authorized.') from None
    print('Explicit operator deployment gates validated; this does not deploy resources.')
if __name__=='__main__':main()
