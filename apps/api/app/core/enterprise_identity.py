"""Entra v2 access-token validation followed by server-owned tenant/entity membership."""
from functools import lru_cache
from uuid import UUID
import jwt
from app.core.identity import Identity
from app.core.errors import DomainError

@lru_cache(maxsize=8)
def jwks(tenant):
    return jwt.PyJWKClient(f'https://login.microsoftonline.com/{tenant}/discovery/v2.0/keys',cache_keys=True,lifespan=300,timeout=5)

def authenticate_enterprise(token,settings,*,key_resolver=None):
    if not token or len(token)>16384:return None
    config=settings.enterprise_identity
    tenant=str(UUID(config['tenant_id']))
    try:
        key=(key_resolver or jwks(tenant).get_signing_key_from_jwt)(token)
        claims=jwt.decode(token,getattr(key,'key',key),algorithms=['RS256'],audience=config['audience'],issuer=f'https://login.microsoftonline.com/{tenant}/v2.0',options={'require':['exp','iat','nbf','iss','aud','tid','oid','ver']},leeway=30)
        if claims['tid']!=tenant or claims['ver']!='2.0':return None
        oid=str(UUID(claims['oid']))
        # Do not trust a caller/token role, tenant scope or a raw UUID as authorization.
        membership=config['memberships'].get(oid)
        if not membership or not membership.get('enabled',False):return None
        allowed_clients=config.get('allowed_client_ids',[])
        if not allowed_clients or claims.get('azp') not in allowed_clients:return None
        return Identity(UUID(membership['tenant_id']),UUID(membership['legal_entity_id']),UUID(membership['actor_id']),frozenset(membership['roles']),membership.get('label','Enterprise user'))
    except jwt.PyJWKClientError:
        raise DomainError(503,'IDENTITY_UNAVAILABLE','Identity verification is temporarily unavailable.',retryable=True) from None
    except (jwt.InvalidTokenError,ValueError,TypeError,KeyError):return None
