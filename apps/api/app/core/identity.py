from dataclasses import dataclass
import hmac
from uuid import UUID


@dataclass(frozen=True)
class Identity:
    tenant_id: UUID
    legal_entity_id: UUID
    actor_id: UUID
    roles: frozenset[str]
    label: str = 'Development identity'

    def scope(self):
        return dict(tenant_id=self.tenant_id, legal_entity_id=self.legal_entity_id)


def authenticate(token, settings):
    if not settings.development:
        raise ValueError('Enterprise identity is not implemented; development mode required.')
    for expected, record in settings.identities.items():
        if hmac.compare_digest(token, expected):
            return Identity(UUID(record['tenant_id']), UUID(record['legal_entity_id']),
                            UUID(record['actor_id']), frozenset(record['roles']), record['label'])
    return None
