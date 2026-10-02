#!/usr/bin/env python3
"""Start only this workspace's loopback API, worker and production web server."""
import os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PYTHON=ROOT/'.venv/bin/python';NODE=ROOT/'runtime/tools/node-v24.21.0-linux-x64/bin'


def main():
    env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'apps/api');env['PATH']=str(NODE)+':'+env.get('PATH','')
    children=[]
    try:
        commands=[([PYTHON,'-m','uvicorn','app.main:create_app','--factory','--host','127.0.0.1','--port','8000','--no-access-log'],ROOT),([PYTHON,'-m','app.services.worker'],ROOT),([NODE/'npm','start'],ROOT/'apps/web')]
        for args,cwd in commands:children.append(subprocess.Popen([str(v) for v in args],cwd=cwd,env=env,start_new_session=True))
        print('AP Review Desk: http://127.0.0.1:3000 — Ctrl+C stops these three child processes.',flush=True)
        while all(child.poll() is None for child in children):time.sleep(.5)
        raise SystemExit('A child process exited; inspect its output.')
    except KeyboardInterrupt:pass
    finally:
        for child in children:
            if child.poll() is None:os.killpg(child.pid,signal.SIGTERM)
        for child in children:
            try:child.wait(timeout=5)
            except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()


if __name__=='__main__':main()
