#!/usr/bin/env python3
"""Protected private-runner release; no automatic foundation/GPU provisioning."""
import hashlib,json,os,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]

def main():
    commit=os.environ.get('RELEASE_COMMIT','');group=os.environ.get('AP_RESOURCE_GROUP','');parameter_file=Path(os.environ.get('AP_RELEASE_PARAMETERS','/nonexistent'))
    if not re.fullmatch('[a-f0-9]{40}',commit) or not re.fullmatch('[a-zA-Z0-9._-]{1,90}',group):raise SystemExit('Approved release commit/resource group required.')
    if not parameter_file.is_file():raise SystemExit('Private reviewed release parameters are missing.')
    from deployment_gate import validate
    approvals=json.loads(Path(os.environ.get('APPROVAL_FILE','/nonexistent')).read_text());validate(approvals)
    if approvals['release_commit']!=commit or approvals['release_parameters_sha256']!=hashlib.sha256(parameter_file.read_bytes()).hexdigest():raise SystemExit('Release inputs differ from the explicitly approved commit or parameters.')
    active_subscription=subprocess.run(['az','account','show','--query','id','--output','tsv'],check=True,capture_output=True,text=True).stdout.strip()
    config=json.loads(parameter_file.read_text())['parameters'];registry=config['registryHost']['value']
    if active_subscription!=approvals['subscription_id'] or group!=approvals['resource_group'] or config['location']['value']!=approvals['region']:raise SystemExit('Active account, resource group or region differs from explicit approval.')
    for name in ('apiImage','webImage'):
        if not re.fullmatch(re.escape(registry)+r'/[-a-z0-9/]+@sha256:[a-f0-9]{64}',config[name]['value']):raise SystemExit('Use verified registry image digests, not mutable tags.')
    folder=ROOT/'runtime/release';folder.mkdir(parents=True,exist_ok=True);folder.chmod(0o700)
    if os.environ.get('ROLLBACK')!='true':
        # Separate reviewed migration credentials on the runner; never migrate in app startup.
        subprocess.run([sys.executable,'-m','alembic','-c',str(ROOT/'apps/api/alembic.ini'),'upgrade','head'],cwd=ROOT,check=True)
    for command in ('what-if','create'):
        args=['az','deployment','group',command,'--resource-group',group,'--template-file',str(ROOT/'infra/azure/release.bicep'),'--parameters','@'+str(parameter_file)]
        result=subprocess.run(args,capture_output=True)
        log=folder/f'{commit}-{command}.log';log.write_bytes(result.stdout+result.stderr);log.chmod(0o600)
        if result.returncode:raise SystemExit(f'Pilot {command} failed; diagnostics are retained privately. No destructive rollback performed.')
    print('Reviewed CPU image release submitted. Authorization/recovery/monitoring smoke checks remain required; no GPU provisioning.')
if __name__=='__main__':main()
