from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
import hashlib
import json
from uuid import UUID


def utcnow():
    return datetime.now(timezone.utc)


def json_default(value):
    if isinstance(value, Decimal):
        return format(value, 'f')
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    raise TypeError('Unsupported serialized value')


def canonical_json(value):
    return json.dumps(value, default=json_default, sort_keys=True, separators=(',', ':'), ensure_ascii=True, allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def projection(value):
    return json.loads(canonical_json(value))
