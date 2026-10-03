from dataclasses import replace
from datetime import datetime,timezone
from types import SimpleNamespace
from uuid import uuid4
import hashlib
import json
import pytest
import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from app.core.config import Settings
from app.core.enterprise_identity import authenticate_enterprise
from app.core.identity import Identity
from app.core.errors import DomainError
from app.integrations.blob_storage import AzureBlobStorage,configured_storage

@pytest.fixture
def enterprise(tmp_path):
    tenant=str(uuid4());oid=str(uuid4());scope={'tenant_id':str(uuid4()),'legal_entity_id':str(uuid4()),'actor_id':str(uuid4()),'roles':['AUDITOR'],'enabled':True}
    config={'tenant_id':tenant,'audience':'synthetic-api','allowed_client_ids':['synthetic-web'],'memberships':{oid:scope}}
    settings=Settings('postgresql+psycopg://unused',{},tmp_path,development=False,enterprise_identity=config)
    now=int(datetime.now(timezone.utc).timestamp());claims={'iss':f'https://login.microsoftonline.com/{tenant}/v2.0','aud':'synthetic-api','tid':tenant,'oid':oid,'ver':'2.0','azp':'synthetic-web','iat':now,'nbf':now-1,'exp':now+300,'roles':['FINANCE_REVIEWER','CFO']}
    key=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    return settings,claims,key

def test_enterprise_signature_and_server_owned_membership(enterprise):
    settings,claims,key=enterprise;token=jwt.encode(claims,key,algorithm='RS256')
    ctx=authenticate_enterprise(token,settings,key_resolver=lambda t:key.public_key());assert ctx.roles==frozenset({'AUDITOR'})
    assert str(ctx.tenant_id)==settings.enterprise_identity['memberships'][claims['oid']]['tenant_id']

@pytest.mark.parametrize('change',[{'aud':'foreign-api'},{'tid':str(uuid4())},{'oid':str(uuid4())},{'azp':'unapproved-client'},{'exp':1},{'ver':'1.0'},{'iss':'https://attacker.example'}])
def test_enterprise_invalid_claims_never_authorize(enterprise,change):
    settings,claims,key=enterprise;token=jwt.encode(claims|change,key,algorithm='RS256');assert authenticate_enterprise(token,settings,key_resolver=lambda t:key.public_key()) is None

def test_wrong_signature_and_dependency_outage(enterprise):
    settings,claims,key=enterprise;other=rsa.generate_private_key(public_exponent=65537,key_size=2048)
    token=jwt.encode(claims,other,algorithm='RS256');assert authenticate_enterprise(token,settings,key_resolver=lambda t:key.public_key()) is None
    def unavailable(t):raise jwt.PyJWKClientError('Internal network diagnostics must not escape')
    with pytest.raises(DomainError) as error:authenticate_enterprise(token,settings,key_resolver=unavailable)
    assert error.value.code=='IDENTITY_UNAVAILABLE' and 'diagnostics' not in error.value.message

class Blob:
    def __init__(self):self.content=None;self.metadata={};self.unavailable=False
    def get_blob_properties(self,**kwargs):
        if self.unavailable:raise RuntimeError('sensitive provider exception')
        if self.content is None:
            error=RuntimeError('not found');error.status_code=404;raise error
        return SimpleNamespace(size=len(self.content),metadata=self.metadata)
    def upload_blob(self,content,overwrite,metadata,**kwargs):
        assert overwrite is False and self.content is None
        self.content=content.read();self.metadata=metadata
    def download_blob(self,**kwargs):return SimpleNamespace(readall=lambda:self.content)
class Container:
    def __init__(self):self.blobs={}
    def get_blob_client(self,key):return self.blobs.setdefault(key,Blob())

def test_private_blob_immutable_scoped_verified_cache_and_outage(tmp_path):
    ctx=Identity(uuid4(),uuid4(),uuid4(),frozenset({'FINANCE_REVIEWER'}));container=Container();storage=AzureBlobStorage(tmp_path,'https://syntheticaccount.blob.core.windows.net','documents',client=container)
    key,sha=storage.put(ctx,b'original evidence');assert sha==hashlib.sha256(b'original evidence').hexdigest();assert storage.get(ctx,key)==b'original evidence'
    blob=container.blobs[key];blob.unavailable=True
    with pytest.raises(DomainError) as error:storage.get(ctx,key)
    assert error.value.retryable and 'provider' not in error.value.message
    blob.unavailable=False;blob.content=None
    assert not storage.exists(ctx,key)
    with pytest.raises(FileNotFoundError):storage.get(ctx,key)
    with pytest.raises(ValueError):storage.get(replace(ctx,tenant_id=uuid4()),key)
    blob.content=b'tampered';storage.root.joinpath(key).unlink()
    with pytest.raises(ValueError):storage.get(ctx,key)

def test_enterprise_configuration_and_storage_fail_closed(tmp_path,monkeypatch):
    monkeypatch.setenv('AP_ENVIRONMENT','enterprise');monkeypatch.delenv('AP_CONFIG_FILE',raising=False);monkeypatch.delenv('AP_CONFIG_JSON',raising=False)
    with pytest.raises(ValueError,match='configuration'):Settings.load()
    with pytest.raises(ValueError,match='development-only'):configured_storage(Settings('unused',{},tmp_path,development=False))


def test_enterprise_tls_rejects_duplicate_mode_and_plaintext_provider(tmp_path,monkeypatch):
    import json
    config={'storage_mode':'AZURE_BLOB','blob_account_url':'https://syntheticaccount.blob.core.windows.net','enterprise_identity':{'tenant_id':str(uuid4()),'audience':'synthetic-api','allowed_client_ids':[str(uuid4())],'memberships':{'synthetic-approved-membership':{}}}}
    monkeypatch.setenv('AP_ENVIRONMENT','enterprise');monkeypatch.setenv('AP_CONFIG_JSON',json.dumps(config))
    monkeypatch.setenv('AP_DATABASE_URL','postgresql+psycopg://unused:unused@example.test/db?sslmode=verify-full')
    assert Settings.load().development is False
    monkeypatch.setenv('AP_DATABASE_URL','postgresql+psycopg://unused:unused@example.test/db?sslmode=verify-full&sslmode=require')
    with pytest.raises(ValueError,match='TLS'):Settings.load()
    monkeypatch.setenv('AP_DATABASE_URL','postgresql+psycopg://unused:unused@example.test/db?sslmode=verify-full')
    config['document_providers']={'endpoint':'http://example.test','model':'synthetic-contract-only'};monkeypatch.setenv('AP_CONFIG_JSON',json.dumps(config))
    with pytest.raises(ValueError,match='HTTPS'):Settings.load()
