from contextlib import contextmanager
import hashlib
from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import Session


class ScopedSession(Session):
    pass


@event.listens_for(ScopedSession, 'after_begin')
def bind_scope(session, transaction, connection):
    identity = session.info.get('identity')
    if connection.dialect.name == 'postgresql':
        if identity is None:
            raise ValueError('Business database session requires server identity.')
        connection.execute(text("SELECT set_config('app.tenant_id', :tenant, true), set_config('app.legal_entity_id', :entity, true)"),
            {'tenant': str(identity.tenant_id), 'entity': str(identity.legal_entity_id)})
        connection.execute(text("SELECT set_config('statement_timeout', '10000', true), set_config('lock_timeout', '5000', true)"))


class Database:
    def __init__(self, url, *, test_fallback=False):
        if url.startswith('sqlite') and not test_fallback:
            raise ValueError('SQLite is a test fallback only.')
        options = {'connect_args': {'check_same_thread': False}} if url.startswith('sqlite') else {'pool_pre_ping': True}
        self.engine = create_engine(url, **options)
        if url.startswith('sqlite'):
            @event.listens_for(self.engine, 'connect')
            def enforce_fks(dbapi, record):
                dbapi.execute('PRAGMA foreign_keys=ON')

    @contextmanager
    def session(self, identity):
        with ScopedSession(self.engine, expire_on_commit=False, info={'identity': identity, 'settings':getattr(self,'settings',None)}) as session:
            with session.begin():
                yield session


def scope_query(query, model, identity):
    return query.where(model.tenant_id == identity.tenant_id, model.legal_entity_id == identity.legal_entity_id)


def advisory_lock(session, key):
    if session.bind.dialect.name == 'postgresql':
        value = int.from_bytes(hashlib.sha256(key.encode()).digest()[:8], 'big', signed=True)
        session.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': value})
