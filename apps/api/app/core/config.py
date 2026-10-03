"""Explicit development configuration; no implicit live provider or identity."""
from dataclasses import dataclass, field
import json
import os
from pathlib import Path
from app.documents.config import DocumentLimits, ProviderSettings

ROOT = Path(__file__).resolve().parents[4]


@dataclass(frozen=True)
class Settings:
    database_url: str
    identities: dict
    storage_root: Path
    development: bool = True
    extraction_mode: str = 'STRUCTURED_SYNTHETIC'
    risk_mode: str = 'RULES_ONLY'
    enterprise_identity: dict = field(default_factory=dict)
    worker_scopes: list = field(default_factory=list)
    storage_mode: str = 'LOCAL'
    blob_account_url: str = ''
    blob_container: str = 'documents'
    managed_identity_client_id: str | None = None
    document_limits: DocumentLimits = field(default_factory=DocumentLimits)
    document_providers: ProviderSettings = field(default_factory=ProviderSettings)

    @classmethod
    def load(cls):
        development = os.environ.get('AP_ENVIRONMENT','development') == 'development'
        if not development and os.environ.get('AP_ENVIRONMENT') != 'enterprise':raise ValueError('Use development or enterprise environment explicitly.')
        if not development and not (os.environ.get('AP_CONFIG_FILE') or os.environ.get('AP_CONFIG_JSON')):raise ValueError('Enterprise server-owned configuration is required.')
        path = Path(os.environ.get('AP_CONFIG_FILE',str(ROOT / 'runtime/dev/settings.json')))
        data = json.loads(os.environ['AP_CONFIG_JSON']) if os.environ.get('AP_CONFIG_JSON') else (json.loads(path.read_text()) if path.exists() else {})
        url = os.environ.get('AP_DATABASE_URL', data.get('database_url', ''))
        if not url.startswith('postgresql+psycopg://'):
            raise ValueError('Configure a PostgreSQL AP_DATABASE_URL; SQLite is test-only.')
        identities = data.get('identities', {})
        if development and not identities:
            raise ValueError('Run development setup to configure isolated identities.')
        enterprise=data.get('enterprise_identity',{})
        if not development:
            if not all(enterprise.get(k) for k in ('tenant_id','audience','memberships','allowed_client_ids')):raise ValueError('Approved enterprise identity inputs are required.')
            if not data.get('blob_account_url','').startswith('https://') or data.get('storage_mode')!='AZURE_BLOB':raise ValueError('Private managed-identity Blob storage is required.')
            from sqlalchemy.engine import make_url
            if make_url(url).query.get('sslmode')!='verify-full':raise ValueError('Enterprise database TLS verification is required.')
            endpoint=data.get('document_providers',{}).get('endpoint')
            if endpoint and not endpoint.startswith('https://'):raise ValueError('Enterprise document providers require HTTPS.')
            if identities:raise ValueError('Development identities are forbidden in enterprise configuration.')
        return cls(url, identities, Path(os.environ.get('AP_STORAGE_ROOT',str(ROOT / 'runtime/storage'))),
            development=development,enterprise_identity=enterprise,worker_scopes=data.get('worker_scopes',[]),
            storage_mode=data.get('storage_mode','LOCAL'),blob_account_url=data.get('blob_account_url',''),blob_container=data.get('blob_container','documents'),managed_identity_client_id=os.environ.get('AP_MANAGED_IDENTITY_CLIENT_ID',data.get('managed_identity_client_id')),
            document_limits=DocumentLimits(**data.get('document_limits', {})),
            document_providers=ProviderSettings(**data.get('document_providers', {})))
