"""Explicit development configuration; no implicit live provider or identity."""
from dataclasses import dataclass
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    database_url: str
    identities: dict
    storage_root: Path
    development: bool = True
    extraction_mode: str = 'STRUCTURED_SYNTHETIC'
    risk_mode: str = 'RULES_ONLY'

    @classmethod
    def load(cls):
        path = ROOT / 'runtime/dev/settings.json'
        data = json.loads(path.read_text()) if path.exists() else {}
        url = os.environ.get('AP_DATABASE_URL', data.get('database_url', ''))
        if not url.startswith('postgresql+psycopg://'):
            raise ValueError('Configure a PostgreSQL AP_DATABASE_URL; SQLite is test-only.')
        identities = data.get('identities', {})
        if not identities:
            raise ValueError('Run development setup to configure isolated identities.')
        return cls(url, identities, ROOT / 'runtime/storage')
