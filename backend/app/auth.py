"""OIDC token validation and tenant-bound access control for MemGuard."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any


class AuthenticationError(Exception):
    """Raised when a request does not carry a valid OIDC access token."""


class TenantAccessError(Exception):
    """Raised when request data attempts to cross the token's tenant boundary."""


@dataclass(frozen=True)
class TenantPrincipal:
    subject: str
    tenant_id: str
    claims: dict[str, Any]


def enforce_tenant(token_tenant_id: str, requested_tenant_id: str | None) -> str:
    """Return the token tenant or reject a request that names another tenant."""
    if requested_tenant_id and requested_tenant_id != token_tenant_id:
        raise TenantAccessError("Token tenant does not match requested tenant")
    return token_tenant_id


@lru_cache(maxsize=1)
def _jwks_client(jwks_url: str):
    import jwt

    return jwt.PyJWKClient(jwks_url)


def authenticate_bearer_token(authorization: str | None) -> TenantPrincipal:
    """Validate a Keycloak-issued bearer token and extract its tenant claim."""
    if not authorization or not authorization.startswith("Bearer "):
        raise AuthenticationError("Missing bearer token")

    issuer = os.getenv("MEMGUARD_OIDC_ISSUER")
    if not issuer:
        raise AuthenticationError("OIDC issuer is not configured")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise AuthenticationError("Missing bearer token")

    try:
        import jwt

        jwks_url = os.getenv(
            "MEMGUARD_OIDC_JWKS_URL",
            f"{issuer.rstrip('/')}/protocol/openid-connect/certs",
        )
        signing_key = _jwks_client(jwks_url).get_signing_key_from_jwt(token).key
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            audience=os.getenv("MEMGUARD_OIDC_AUDIENCE", "memguard-api"),
            issuer=issuer,
        )
    except Exception as exc:
        raise AuthenticationError("Invalid bearer token") from exc

    tenant_claim = os.getenv("MEMGUARD_TENANT_CLAIM", "tenant_id")
    tenant_id = claims.get(tenant_claim)
    subject = claims.get("sub")
    if not isinstance(tenant_id, str) or not tenant_id or not isinstance(subject, str) or not subject:
        raise AuthenticationError("Bearer token is missing required tenant identity")
    return TenantPrincipal(subject=subject, tenant_id=tenant_id, claims=claims)
