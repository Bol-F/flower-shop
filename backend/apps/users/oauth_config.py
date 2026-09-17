"""Pure OAuth configuration helpers shared by settings and runtime code."""

import re

MICROSOFT_TENANT_ALIASES = frozenset({'common', 'organizations', 'consumers'})
MICROSOFT_TENANT_ID_RE = re.compile(
    r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$',
    re.IGNORECASE,
)


def normalize_microsoft_tenant(value: object, default: str = 'common') -> str:
    return str(value or default).strip().lower()


def valid_microsoft_tenant(value: object) -> bool:
    tenant = normalize_microsoft_tenant(value, default='')
    return tenant in MICROSOFT_TENANT_ALIASES or bool(MICROSOFT_TENANT_ID_RE.fullmatch(tenant))
