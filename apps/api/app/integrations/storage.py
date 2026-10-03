"""Private development storage; server-generated keys, scoped reads, staged writes."""
import hashlib
import asyncio
import os
from pathlib import Path
import re
from uuid import uuid4


class LocalStorage:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)

    def path(self, identity, key):
        prefix = f'{identity.tenant_id}/{identity.legal_entity_id}/'
        if not isinstance(key, str) or not key.startswith(prefix) or not re.fullmatch(r'[0-9a-f-]{36}/[0-9a-f-]{36}/[0-9a-f-]{36}', key):
            raise ValueError('Invalid scoped internal object key')
        path = self.root / key
        if path.resolve().parent != (self.root / prefix).resolve() or not path.resolve().is_relative_to(self.root):
            raise ValueError('Unsafe storage path')
        return path

    def put(self, identity, content, *, maximum=2 * 1024 * 1024):
        if not isinstance(content, bytes) or len(content) > maximum:
            raise ValueError('Structured import exceeds storage limit')
        key = f'{identity.tenant_id}/{identity.legal_entity_id}/{uuid4()}'
        path = self.path(identity, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        temporary = path.with_suffix('.part')
        with temporary.open('xb') as stream:
            os.chmod(temporary, 0o600)
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        return key, hashlib.sha256(content).hexdigest()

    def get(self, identity, key):
        path = self.path(identity, key)
        if path.is_symlink():
            raise ValueError('Symlink objects are forbidden')
        return path.read_bytes()

    async def ingest(self, identity, chunks, *, maximum, timeout_seconds=60):
        """Incremental authoritative hash and bound; incomplete owned objects removed."""
        key = f'{identity.tenant_id}/{identity.legal_entity_id}/{uuid4()}'
        path = self.path(identity, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(path.parent, 0o700)
        temporary = path.with_suffix('.part')
        size = 0
        checksum = hashlib.sha256()
        try:
            with temporary.open('xb') as stream:
                os.chmod(temporary, 0o600)
                async with asyncio.timeout(timeout_seconds):
                    async for chunk in chunks:
                        if not isinstance(chunk, bytes): raise ValueError('Invalid binary upload')
                        size += len(chunk)
                        if size > maximum: raise ValueError('DOCUMENT_SIZE_LIMIT')
                        checksum.update(chunk)
                        stream.write(chunk)
                stream.flush()
                os.fsync(stream.fileno())
            if size == 0: raise ValueError('EMPTY_DOCUMENT')
            os.replace(temporary, path)
            return key, checksum.hexdigest(), size
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
