from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient


class AuthenticationError(PermissionError):
    pass


@dataclass(frozen=True)
class ClerkConfig:
    issuer: str
    jwt_key: str | None = None
    jwks_url: str | None = None
    audience: str | None = None
    authorized_parties: tuple[str, ...] = ()
    leeway_seconds: int = 5

    @classmethod
    def from_env(cls) -> "ClerkConfig":
        issuer = os.environ.get("CLERK_ISSUER", "").strip().rstrip("/")
        jwt_key = os.environ.get("CLERK_JWT_KEY") or None
        jwks_url = os.environ.get("CLERK_JWKS_URL") or (f"{issuer}/.well-known/jwks.json" if issuer else None)
        audience = os.environ.get("CLERK_AUDIENCE") or None
        parties = tuple(
            x.strip()
            for x in os.environ.get("CLERK_AUTHORIZED_PARTIES", "").split(",")
            if x.strip()
        )
        if not issuer:
            raise RuntimeError("CLERK_ISSUER is required")
        if not jwt_key and not jwks_url:
            raise RuntimeError("CLERK_JWT_KEY or CLERK_JWKS_URL is required")
        if not parties:
            raise RuntimeError("CLERK_AUTHORIZED_PARTIES is required")
        return cls(
            issuer=issuer,
            jwt_key=jwt_key,
            jwks_url=jwks_url,
            audience=audience,
            authorized_parties=parties,
        )


class ClerkTokenVerifier:
    """Fail-closed verifier for Clerk session JWTs.

    Networkless verification is preferred when CLERK_JWT_KEY is supplied. Otherwise
    PyJWKClient fetches/caches the instance JWKS. Only RS256 is accepted and the Clerk
    authorized-party claim must match the configured web origin set.
    """

    def __init__(self, config: ClerkConfig):
        self.config = config
        self._jwks = PyJWKClient(config.jwks_url, cache_keys=True) if not config.jwt_key else None

    def verify(self, token: str) -> dict[str, Any]:
        if not token:
            raise AuthenticationError("missing session token")
        try:
            key: Any = self.config.jwt_key
            if key is None:
                key = self._jwks.get_signing_key_from_jwt(token).key
            kwargs: dict[str, Any] = {
                "algorithms": ["RS256"],
                "issuer": self.config.issuer,
                "leeway": self.config.leeway_seconds,
                "options": {"require": ["exp", "nbf", "sid", "sub"]},
            }
            if self.config.audience:
                kwargs["audience"] = self.config.audience
            else:
                kwargs["options"]["verify_aud"] = False
            claims = jwt.decode(token, key=key, **kwargs)
        except Exception as exc:
            raise AuthenticationError("invalid Clerk session token") from exc
        azp = claims.get("azp")
        if azp not in self.config.authorized_parties:
            raise AuthenticationError("unauthorized Clerk party")
        if not claims.get("sid"):
            raise AuthenticationError("Clerk token missing session ID")
        if not claims.get("sub"):
            raise AuthenticationError("Clerk token missing subject")
        if "act" in claims:
            raise AuthenticationError("Clerk impersonated sessions are not admitted")
        if claims.get("sts") == "pending":
            raise AuthenticationError("pending Clerk session is not admitted")
        return claims

    @staticmethod
    def bearer(authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("missing bearer token")
        token = authorization[7:].strip()
        if not token:
            raise AuthenticationError("missing bearer token")
        return token
