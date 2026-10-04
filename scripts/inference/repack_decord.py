#!/usr/bin/env python3
"""Repair the verified upstream Decord wheel's tags/RECORD, preserving runtime bytes."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[2]
RUNTIME=ROOT/'runtime/inference'
UPSTREAM_SHA='51997f20be8958e23b7c4061ba45d0efcd86bffd5fe81c695d0befee0d442976'
NAME='decord-0.6.0-py3-none-manylinux2010_x86_64.whl'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--install',action='store_true',help='Install only into runtime/inference/env')
    args=parser.parse_args();original=args.archive.resolve()
    if hashlib.sha256(original.read_bytes()).hexdigest()!=UPSTREAM_SHA:
        raise SystemExit('Upstream archive SHA-256 mismatch; refusing to repackage.')
    build=RUNTIME/'repacked';build.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=build,prefix='decord-build-') as tmp:
        folder=Path(tmp)
        with zipfile.ZipFile(original) as package:
            for info in package.infolist():
                path=(folder/info.filename).resolve()
                if not path.is_relative_to(folder):raise SystemExit('Unsafe archive path')
                if info.is_dir():path.mkdir(parents=True,exist_ok=True);continue
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(package.read(info))
        wheel=folder/'decord-0.6.0.dist-info/WHEEL'
        old='Tag: cp36-cp36m-manylinux2010_x86_64'
        if wheel.read_text().count(old)!=1:raise SystemExit('Unexpected upstream wheel metadata')
        wheel.write_text(wheel.read_text().replace(old,'Tag: py3-none-manylinux2010_x86_64'))
        env=dict(os.environ,PYTHONPATH=str(RUNTIME/'packaging'))
        subprocess.run([str(RUNTIME/'client/bin/python'),'-m','wheel','pack',str(folder),'-d',str(build)],env=env,check=True)
    corrected=build/NAME
    with zipfile.ZipFile(original) as a,zipfile.ZipFile(corrected) as b:
        names={n for n in a.namelist() if not n.endswith('/')}
        if names!=set(b.namelist()):raise SystemExit('Repackaged file inventory changed')
        changed={n for n in names if a.read(n)!=b.read(n)}
        if changed!={'decord-0.6.0.dist-info/RECORD','decord-0.6.0.dist-info/WHEEL'}:
            raise SystemExit('Runtime bytes changed; refusing to install')
    print('Verified: only WHEEL/RECORD changed; all upstream runtime bytes identical.')
    print('Built SHA-256:',hashlib.sha256(corrected.read_bytes()).hexdigest())
    if args.install:
        subprocess.run([str(RUNTIME/'env/bin/python'),'-m','pip','install','--force-reinstall','--no-deps',str(corrected)],check=True)


if __name__=='__main__':main()
