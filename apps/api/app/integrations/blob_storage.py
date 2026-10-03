"""Private immutable Blob objects, with bounded private CPU materialization cache.

Every read confirms the remote object and verifies its authoritative ingest digest.
No account keys, SAS links, public URLs or shared developer credential fallback.
"""
import asyncio
import hashlib
import os
import re
from urllib.parse import urlparse
from uuid import uuid4
from app.integrations.storage import LocalStorage
from app.core.errors import DomainError

class AzureBlobStorage(LocalStorage):
    def __init__(self,root,account_url,container,client_id=None,*,client=None):
        super().__init__(root)
        host=urlparse(account_url)
        if host.scheme!='https' or not re.fullmatch(r'[a-z0-9]{3,24}\.blob\.core\.windows\.net',host.netloc) or host.path not in ('','/') or host.query or host.fragment:raise ValueError('Use a managed-identity Azure Blob account endpoint.')
        if not re.fullmatch(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]',container):raise ValueError('Invalid private container name.')
        if client is None:
            from azure.identity import ManagedIdentityCredential
            from azure.storage.blob import BlobServiceClient
            client=BlobServiceClient(account_url,credential=ManagedIdentityCredential(client_id=client_id),logging_enable=False,connection_timeout=5,read_timeout=30,retry_total=2).get_container_client(container)
        self.client=client
    def path(self,identity,key):
        path=super().path(identity,key)
        try:
            blob=self.client.get_blob_client(key);properties=blob.get_blob_properties(timeout=10)
            size=properties.size;sha=properties.metadata.get('sha256','')
            if size>64*1024*1024 or not re.fullmatch('[a-f0-9]{64}',sha):raise ValueError('Invalid immutable object metadata.')
            if path.is_symlink():raise ValueError('Symlink objects are forbidden.')
            if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==sha:return path
            content=blob.download_blob(max_concurrency=1,timeout=30).readall()
            if len(content)!=size or hashlib.sha256(content).hexdigest()!=sha:raise ValueError('Object integrity verification failed.')
            path.parent.mkdir(parents=True,exist_ok=True);os.chmod(path.parent,0o700)
            temporary=path.with_name(path.name+'.'+uuid4().hex+'.part')
            try:
                with temporary.open('xb') as stream:os.chmod(temporary,0o600);stream.write(content);stream.flush();os.fsync(stream.fileno())
                os.replace(temporary,path)
            finally:temporary.unlink(missing_ok=True)
            return path
        except ValueError:raise
        except Exception as error:
            if getattr(error,'status_code',None)==404:raise FileNotFoundError('Private object is missing.') from None
            raise DomainError(503,'STORAGE_UNAVAILABLE','Private storage is temporarily unavailable.',retryable=True) from None
    def exists(self,identity,key):
        try:return self.path(identity,key).is_file()
        except FileNotFoundError:return False
    def _publish(self,key,path,sha):
        try:
            with path.open('rb') as content:self.client.get_blob_client(key).upload_blob(content,overwrite=False,metadata={'sha256':sha},timeout=30)
        except Exception:raise DomainError(503,'STORAGE_UNAVAILABLE','Private storage could not preserve the object.',retryable=True) from None
    def put(self,identity,content,*,maximum=2*1024*1024):
        # Stage locally using the established UUID key contract before immutable publication.
        local=LocalStorage(self.root);key,sha=local.put(identity,content,maximum=maximum);self._publish(key,local.path(identity,key),sha);return key,sha
    async def ingest(self,identity,chunks,*,maximum,timeout_seconds=60):
        local=LocalStorage(self.root);key,sha,size=await local.ingest(identity,chunks,maximum=maximum,timeout_seconds=timeout_seconds)
        await asyncio.to_thread(self._publish,key,local.path(identity,key),sha)
        return key,sha,size

def configured_storage(settings):
    if settings.storage_mode=='LOCAL':
        if not settings.development:raise ValueError('Local originals are development-only.')
        return LocalStorage(settings.storage_root)
    if settings.storage_mode=='AZURE_BLOB':return AzureBlobStorage(settings.storage_root,settings.blob_account_url,settings.blob_container,settings.managed_identity_client_id)
    raise ValueError('Unsupported storage mode.')
