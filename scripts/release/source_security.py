#!/usr/bin/env python3
"""Review tracked/pending source paths and credential patterns without logging values.
This is a bounded repository scan, not a penetration test or a proof of no secrets.
"""
import re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
paths=subprocess.check_output(['git','ls-files','-co','--exclude-standard','-z'],cwd=ROOT).decode().split('\0')
forbidden=('runtime/','uploads/','storage/','exports/','model_weights/','ml/artifacts/')
patterns=[re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),re.compile(r'gh[pousr]_[A-Za-z0-9]{30,}'),re.compile(r'AKIA[0-9A-Z]{16}'),re.compile(r'postgresql(?:\+psycopg)?://[^\s/:]+:([A-Za-z0-9_-]{16,})@'),re.compile(r'(?i)(?:AP_DEV_TOKEN|client_secret|api_key)\s*[=:]\s*[\"\']([A-Za-z0-9_/-]{24,})[\"\']')]
issues=[];count=0
for path in sorted(set(paths)):
 if not path:continue
 file=ROOT/path
 if path.startswith(forbidden) or '/.env' in path and not path.endswith('.example') or path.endswith(('.dump','.safetensors','.pem','.key')):issues.append((path,'PRIVATE_ARTIFACT_PATH'))
 if not file.is_file() or file.stat().st_size>2_000_000:continue
 try:text=file.read_text()
 except UnicodeDecodeError:continue
 count+=1
 for n,pattern in enumerate(patterns):
  matches=list(pattern.finditer(text))
  if n==3 and path=='.github/workflows/validate.yml':matches=[m for m in matches if m.group(1)!='ci_disposable_only']
  if matches:issues.append((path,f'CREDENTIAL_PATTERN_{n}'))
if issues:
 for path,rule in issues:print(path+': '+rule+' (value redacted)')
 raise SystemExit(1)
print(f'Repository source scan: {count} text files; no forbidden runtime artifacts or configured credential patterns found.')
