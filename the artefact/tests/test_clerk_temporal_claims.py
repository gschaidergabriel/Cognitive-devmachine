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


def _claims(now):
    return {
        "iss": "https://clerk.example",
        "sub": "user_g",
        "sid": "sess_1",
        "azp": "https://clay.example",
        "iat": now,
        "nbf": now - 1,
        "exp": now + 60,
        "v": 2,
        "sts": "active",
    }


def _verifier(public_pem):
    return ClerkTokenVerifier(ClerkConfig(
        issuer="https://clerk.example",
        jwt_key=public_pem,
        authorized_parties=("https://clay.example",),
    ))


def test_clerk_session_token_requires_nbf_and_enforces_not_before():
    private, public_pem = _keypair()
    verifier = _verifier(public_pem)
    now = int(time.time())

    valid = _claims(now)
    assert verifier.verify(jwt.encode(valid, private, algorithm="RS256"))["sub"] == "user_g"

    missing_nbf = dict(valid)
    missing_nbf.pop("nbf")
    with pytest.raises(AuthenticationError):
        verifier.verify(jwt.encode(missing_nbf, private, algorithm="RS256"))

    future_nbf = {**valid, "nbf": now + 60}
    with pytest.raises(AuthenticationError):
        verifier.verify(jwt.encode(future_nbf, private, algorithm="RS256"))
