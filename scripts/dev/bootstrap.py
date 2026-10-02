#!/usr/bin/env python3
"""Reproduce the tested Ubuntu 24.04 x86_64 user-space toolchain. No system changes."""
import hashlib,os,platform,subprocess,sys,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
TOOLS=ROOT/'runtime/tools';DOWNLOADS=TOOLS/'downloads'
NODE='node-v24.21.0-linux-x64'
NODE_SHA='fd8e59d5a511510f6a298afb548f18c7d2b1be404d8b4a27d94fbe49f56cb2d6'
DEBS={
 'libpq5':'3f96dd36bcd7841172c1ead4965da20a193bb9ccf9a93a3f5a3ac7f56369dbb1',
 'postgresql-16':'d60ae76fb862cd4cca7bfdcdcdcc271c5e1d75f6b7915305ce2d962735a4b666',
 'postgresql-client-16':'4796f72e1a7270ad8c17b1ecb025cd453f692b42c10aaf89f6b476da61761eac'}
VERSION='16.15-0ubuntu0.24.04.1'


def verify(path,expected):
    if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:raise SystemExit('Tool archive checksum mismatch: '+path.name)


def run(args,**kwargs):subprocess.run([str(v) for v in args],check=True,**kwargs)


def main():
    if os.getuid()==0:raise SystemExit('Run as an ordinary user.')
    if platform.machine()!='x86_64' or platform.system()!='Linux':raise SystemExit('Use the runbook external-runtime option for this platform.')
    DOWNLOADS.mkdir(parents=True,exist_ok=True)
    archive=DOWNLOADS/(NODE+'.tar.xz')
    if not archive.exists():urllib.request.urlretrieve('https://nodejs.org/dist/v24.21.0/'+archive.name,archive)
    verify(archive,NODE_SHA)
    if not (TOOLS/NODE/'bin/node').exists():
        with tarfile.open(archive) as stream:stream.extractall(TOOLS,filter='data')
    for package,sha in DEBS.items():
        file=DOWNLOADS/f'{package}_{VERSION}_amd64.deb'
        if not file.exists():run(['apt-get','download',package+'='+VERSION],cwd=DOWNLOADS)
        verify(file,sha)
        run(['dpkg-deb','-x',file,TOOLS/'postgres'])
    python=ROOT/'.venv/bin/python'
    if not python.exists():run([sys.executable,'-m','venv',ROOT/'.venv'])
    run([python,'-m','pip','install','-r',ROOT/'apps/api/requirements.lock'])
    run([python,'-m','pip','check'])
    env=dict(os.environ);env['PATH']=str(TOOLS/NODE/'bin')+':'+env.get('PATH','')
    run([TOOLS/NODE/'bin/npm','ci','--no-audit','--no-fund'],cwd=ROOT/'apps/web',env=env)
    run([python,ROOT/'scripts/dev/setup_database.py'])
    print('Verified project tools, locked dependencies and local PostgreSQL are ready.')


if __name__=='__main__':main()
