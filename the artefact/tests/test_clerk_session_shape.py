import time

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from clayverse.adapters import AuthenticationError, ClerkConfig, ClerkTokenVerifier


def _keypair():
    private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode()
    return private, public_pem


def _verifier(public_pem):
    return ClerkTokenVerifier(ClerkConfig(
        issuer="https://clerk.example",
        jwt_key=public_pem,
        authorized_parties=("https://clay.example",),
    ))


def _claims(now, *, sid="sess_1"):
    claims = {
        "iss": "https://clerk.example",
        "sub": "user_g",
        "sid": sid,
        "azp": "https://clay.example",
        "iat": now,
        "nbf": now - 1,
        "exp": now + 60,
        "jti": "jwt_1",
        "v": 2,
        "sts": "active",
    }
    return claims


def test_clerk_boundary_accepts_session_bound_token_and_rejects_custom_jwt_shape():
    private, public_pem = _keypair()
    verifier = _verifier(public_pem)
    now = int(time.time())

    session_token = _claims(now)
    assert verifier.verify(jwt.encode(session_token, private, algorithm="RS256"))["sid"] == "sess_1"

    custom_jwt_shape = dict(session_token)
    custom_jwt_shape.pop("sid")
    with pytest.raises(AuthenticationError):
        verifier.verify(jwt.encode(custom_jwt_shape, private, algorithm="RS256"))

    empty_sid = _claims(now, sid="")
    with pytest.raises(AuthenticationError):
        verifier.verify(jwt.encode(empty_sid, private, algorithm="RS256"))


def test_clerk_boundary_requires_active_non_impersonated_session():
    private, public_pem = _keypair()
    verifier = _verifier(public_pem)
    now = int(time.time())

    pending = {**_claims(now), "sts": "pending"}
    with pytest.raises(AuthenticationError, match="not active"):
        verifier.verify(jwt.encode(pending, private, algorithm="RS256"))

    missing_status = _claims(now)
    missing_status.pop("sts")
    with pytest.raises(AuthenticationError, match="not active"):
        verifier.verify(jwt.encode(missing_status, private, algorithm="RS256"))

    impersonated = {
        **_claims(now),
        "act": {
            "iss": "https://dashboard.clerk.com",
            "sid": "sess_actor",
            "sub": "user_actor",
        },
    }
    with pytest.raises(AuthenticationError, match="impersonation"):
        verifier.verify(jwt.encode(impersonated, private, algorithm="RS256"))
