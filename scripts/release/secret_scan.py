#!/usr/bin/env python3
"""Pinned Gitleaks on tracked/pending sources, with redaction and a detection probe."""
import hashlib,json,secrets,shutil,subprocess,tarfile,tempfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SHA='551f6fc83ea457d62a0d98237cbad105af8d557003051f41f3e7ca7b3f2470eb'
folder=ROOT/'runtime/tools/gitleaks';folder.mkdir(parents=True,exist_ok=True)
archive=folder/'gitleaks_8.30.1_linux_x64.tar.gz'
if not archive.exists():
    with urllib.request.urlopen('https://github.com/gitleaks/gitleaks/releases/download/v8.30.1/gitleaks_8.30.1_linux_x64.tar.gz',timeout=60) as response:data=response.read()
    if hashlib.sha256(data).hexdigest()!=SHA:raise SystemExit('Secret scanner release checksum mismatch.')
    archive.write_bytes(data)
if hashlib.sha256(archive.read_bytes()).hexdigest()!=SHA:raise SystemExit('Secret scanner archive integrity failure.')
with tarfile.open(archive) as package:
    member=package.getmember('gitleaks');source=package.extractfile(member)
    if source is None:raise SystemExit('Scanner binary missing.')
    executable=folder/'gitleaks';executable.write_bytes(source.read());executable.chmod(0o700)
with tempfile.TemporaryDirectory(dir=ROOT/'runtime',prefix='release-scan-') as tmp:
    temp=Path(tmp);snapshot=temp/'source';snapshot.mkdir()
    paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
    for name in sorted(set(paths)):
        if not name:continue
        file=ROOT/name
        if file.is_symlink():raise SystemExit('Review source symlink before release scanning.')
        if file.is_file():
            destination=snapshot/name;destination.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(file,destination)
    def scan(path,report):
        result=subprocess.run([str(executable),'dir',str(path),'--config',str(ROOT/'.gitleaks.toml'),'--redact=100','--no-banner','--report-format','json','--report-path',str(report)],capture_output=True)
        if result.returncode not in (0,1):raise SystemExit('Scanner execution failed; no clean-scan claim.')
        return result.returncode,json.loads(report.read_text()) if report.exists() else []
    code,findings=scan(snapshot,temp/'findings.json')
    if code or findings:raise SystemExit(f'Release blocked by {len(findings)} redacted scanner findings; inspect privately.')
    probe=temp/'probe';probe.mkdir();(probe/'probe.txt').write_text('api_key = "'+secrets.token_urlsafe(36)+'"\n')
    code,findings=scan(probe,temp/'probe.json')
    if code!=1 or len(findings)!=1:raise SystemExit('Scanner detection probe failed; no clean-scan claim.')
print('Gitleaks 8.30.1: zero source findings; synthetic detection probe found one credential-format sample. Values redacted.')
