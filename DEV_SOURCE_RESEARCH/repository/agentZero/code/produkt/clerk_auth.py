from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient


class AuthenticationError(PermissionError):
    pass


_JWKS_CACHE_LIFESPAN_SECONDS = 300
_JWKS_FETCH_TIMEOUT_SECONDS = 5


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
        requested_jwks_url = (os.environ.get("CLERK_JWKS_URL") or "").strip()
        audience = os.environ.get("CLERK_AUDIENCE") or None
        parties = tuple(
            x.strip()
            for x in os.environ.get("CLERK_AUTHORIZED_PARTIES", "").split(",")
            if x.strip()
        )
        if not issuer:
            raise RuntimeError("CLERK_ISSUER is required")
        canonical_jwks_url = f"{issuer}/.well-known/jwks.json"
        if not jwt_key and requested_jwks_url and requested_jwks_url != canonical_jwks_url:
            raise RuntimeError("CLERK_JWKS_URL must match the CLERK_ISSUER JWKS endpoint")
        jwks_url = None if jwt_key else (requested_jwks_url or canonical_jwks_url)
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
    PyJWKClient uses only its finite-lived JWKS-set cache: the per-signing-key LRU is
    intentionally disabled so an already-seen kid cannot bypass key-set refresh forever.
    Only RS256 is accepted and the Clerk authorized-party claim must match the
    configured web origin set. Baseline ClayVerse admits direct sessions, rejects
    impersonation, and rejects any explicitly non-active Clerk session status. Clerk's
    `sts` claim is optional for ordinary authenticated sessions, so absence of `sts`
    does not itself invalidate an otherwise verified session JWT.
    """

    def __init__(self, config: ClerkConfig):
        self.config = config
        if not config.jwt_key:
            canonical_jwks_url = f"{config.issuer.rstrip('/')}/.well-known/jwks.json"
            if config.jwks_url != canonical_jwks_url:
                raise RuntimeError("network Clerk JWKS URL must match the configured issuer")
        self._jwks = (
            PyJWKClient(
                config.jwks_url,
                cache_keys=False,
                cache_jwk_set=True,
                lifespan=_JWKS_CACHE_LIFESPAN_SECONDS,
                timeout=_JWKS_FETCH_TIMEOUT_SECONDS,
            )
            if not config.jwt_key
            else None
        )

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
        session_status = claims.get("sts")
        if session_status is not None and session_status != "active":
            raise AuthenticationError("Clerk session is not active")
        if "act" in claims:
            raise AuthenticationError("Clerk impersonated sessions are not admitted")
        return claims

    @staticmethod
    def bearer(authorization: str | None) -> str:
        if not authorization or not authorization.startswith("Bearer "):
            raise AuthenticationError("missing bearer token")
        token = authorization[7:].strip()
        if not token:
            raise AuthenticationError("missing bearer token")
        return token
