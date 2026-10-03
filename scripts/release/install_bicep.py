#!/usr/bin/env python3
"""Install the verified standalone compiler in project scope; no Azure login/deployment."""
import hashlib,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SHA='64c345a58e0c3e48b1bc98a4e62d6b3adb1d238281297de3400aeafb2697aa5a'
path=ROOT/'runtime/tools/bicep/bicep'
if not path.exists():
    with urllib.request.urlopen('https://github.com/Azure/bicep/releases/download/v0.47.16/bicep-linux-x64',timeout=60) as r:data=r.read()
    if hashlib.sha256(data).hexdigest()!=SHA:raise SystemExit('Bicep release checksum mismatch.')
    path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data);path.chmod(0o700)
if hashlib.sha256(path.read_bytes()).hexdigest()!=SHA:raise SystemExit('Installed compiler checksum mismatch.')
print('Verified Bicep 0.47.16 compiler available; no resources provisioned.')
