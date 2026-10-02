#!/usr/bin/env python3
"""Start a project-owned development PostgreSQL cluster, without sudo or Docker."""
import json
import os
from pathlib import Path
import secrets
import subprocess
from urllib.parse import quote

import psycopg
from psycopg import sql

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / 'runtime/dev'
BIN = ROOT / 'runtime/tools/postgres/usr/lib/postgresql/16/bin'
DATA = ROOT / 'runtime/postgres'
PORT = 55432


def private_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')
    path.chmod(0o600)


def main():
    if os.getuid() == 0:
        raise SystemExit('Run development setup as an ordinary user.')
    libraries = ROOT / 'runtime/tools/postgres/usr/lib/x86_64-linux-gnu'
    os.environ['LD_LIBRARY_PATH'] = str(libraries) + ':' + os.environ.get('LD_LIBRARY_PATH', '')
    DEV.mkdir(parents=True, exist_ok=True)
    DEV.chmod(0o700)
    settings_path = DEV / 'settings.json'
    admin_path = DEV / 'admin.json'
    if not (BIN / 'initdb').exists():
        raise SystemExit('Install/extract the documented PostgreSQL tools or configure an existing development database.')
    if not (DATA / 'PG_VERSION').exists():
        if DATA.exists() and any(DATA.iterdir()):
            raise SystemExit('Refusing to initialize a non-empty database directory.')
        admin_password = secrets.token_urlsafe(32)
        pwfile = DEV / 'init-password'
        pwfile.write_text(admin_password)
        pwfile.chmod(0o600)
        try:
            subprocess.run([str(BIN / 'initdb'), '-D', str(DATA), '-U', 'ap_bootstrap',
                '--auth-local=trust', '--auth-host=scram-sha-256', '--pwfile=' + str(pwfile),
                '--encoding=UTF8', '--locale=C.UTF-8', '-L', str(BIN.parent.parent.parent.parent / 'share/postgresql/16')], check=True)
        finally:
            pwfile.unlink(missing_ok=True)
        private_json(admin_path, {'password': admin_password})
        with (DATA / 'postgresql.conf').open('a') as conf:
            conf.write(f"\nlisten_addresses = '127.0.0.1'\nport = {PORT}\nunix_socket_directories = '{DEV}'\n")
    status = subprocess.run([str(BIN / 'pg_ctl'), '-D', str(DATA), 'status'], capture_output=True)
    if status.returncode != 0:
        subprocess.run([str(BIN / 'pg_ctl'), '-D', str(DATA), '-l', str(DEV / 'postgres.log'), '-w', 'start'], check=True)
    admin_password = json.loads(admin_path.read_text())['password']
    with psycopg.connect(host='127.0.0.1', port=PORT, user='ap_bootstrap', password=admin_password, dbname='postgres', autocommit=True) as conn:
        role_exists = conn.execute("SELECT 1 FROM pg_roles WHERE rolname='ap_app'").fetchone()
        if not role_exists:
            app_password = secrets.token_urlsafe(32)
            conn.execute(sql.SQL('CREATE ROLE ap_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOBYPASSRLS PASSWORD {}').format(sql.Literal(app_password)))
        elif not settings_path.exists():
            raise SystemExit('Existing application role has no local settings; refusing to reset its credentials.')
        else:
            app_password = None
        for name in ['ap_phase1', 'ap_phase1_test']:
            if not conn.execute('SELECT 1 FROM pg_database WHERE datname=%s', (name,)).fetchone():
                conn.execute(sql.SQL('CREATE DATABASE {} OWNER ap_app').format(sql.Identifier(name)))
        flags = conn.execute("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname='ap_app'").fetchone()
        if flags != (False, False):
            raise SystemExit('Application role unexpectedly bypasses tenant policies.')
    if not settings_path.exists():
        default = {'tenant_id': '10000000-0000-4000-8000-000000000001',
            'legal_entity_id': '20000000-0000-4000-8000-000000000001',
            'actor_id': '51000000-0000-4000-8000-000000000001',
            'roles': ['FINANCE_REVIEWER', 'DEVELOPMENT_ADMIN'], 'label': 'Synthetic finance reviewer'}
        token = secrets.token_urlsafe(32)
        url = f'postgresql+psycopg://ap_app:{quote(app_password)}@127.0.0.1:{PORT}/ap_phase1'
        private_json(settings_path, {'database_url': url, 'identities': {token: default}})
        web = ROOT / 'apps/web'
        web.mkdir(parents=True, exist_ok=True)
        (web / '.env.local').write_text(f'AP_API_ORIGIN=http://127.0.0.1:8000\nAP_DEV_TOKEN={token}\n')
        (web / '.env.local').chmod(0o600)
    print('Project-owned PostgreSQL ready on loopback port 55432; ap_app is NOSUPERUSER/NOBYPASSRLS. Credentials remain in ignored private runtime files.')


if __name__ == '__main__':
    main()
