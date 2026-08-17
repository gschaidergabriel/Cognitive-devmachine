import pytest

from clayverse.clerk_auth import AuthenticationError, ClerkConfig, ClerkTokenVerifier


def _verifier() -> ClerkTokenVerifier:
    return ClerkTokenVerifier(
        ClerkConfig(
            issuer="https://example.clerk.accounts.dev",
            jwt_key="test-public-key",
            authorized_parties=("https://app.example",),
        )
    )


def _claims(**extra):
    claims = {
        "iss": "https://example.clerk.accounts.dev",
        "sub": "user_gabriel",
        "sid": "sess_1",
        "azp": "https://app.example",
        "nbf": 1,
        "exp": 4_000_000_000,
    }
    claims.update(extra)
    return claims


def test_regular_canonical_session_claims_are_admitted(monkeypatch):
    monkeypatch.setattr("clayverse.clerk_auth.jwt.decode", lambda *args, **kwargs: _claims())
    assert _verifier().verify("signed-token")["sub"] == "user_gabriel"


def test_impersonated_clerk_session_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "clayverse.clerk_auth.jwt.decode",
        lambda *args, **kwargs: _claims(
            act={
                "iss": "https://dashboard.clerk.com",
                "sid": "sess_impersonated",
                "sub": "user_admin",
            }
        ),
    )
    with pytest.raises(AuthenticationError, match="impersonated"):
        _verifier().verify("signed-token")


def test_pending_clerk_session_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "clayverse.clerk_auth.jwt.decode",
        lambda *args, **kwargs: _claims(sts="pending"),
    )
    with pytest.raises(AuthenticationError, match="pending"):
        _verifier().verify("signed-token")
