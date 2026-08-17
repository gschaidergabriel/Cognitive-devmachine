from pathlib import Path

import clayverse.clerk_auth as auth


ROOT = Path(__file__).resolve().parents[1]


def test_jwks_client_uses_only_finite_set_cache(monkeypatch):
    captured = {}

    class FakePyJWKClient:
        def __init__(self, uri, **kwargs):
            captured["uri"] = uri
            captured.update(kwargs)

    monkeypatch.setattr(auth, "PyJWKClient", FakePyJWKClient)
    verifier = auth.ClerkTokenVerifier(auth.ClerkConfig(
        issuer="https://clerk.example",
        jwks_url="https://clerk.example/.well-known/jwks.json",
        authorized_parties=("https://clay.example",),
    ))

    assert verifier._jwks is not None
    assert captured == {
        "uri": "https://clerk.example/.well-known/jwks.json",
        "cache_keys": False,
        "cache_jwk_set": True,
        "lifespan": auth._JWKS_CACHE_LIFESPAN_SECONDS,
        "timeout": auth._JWKS_FETCH_TIMEOUT_SECONDS,
    }
    assert auth._JWKS_CACHE_LIFESPAN_SECONDS == 300
    assert auth._JWKS_FETCH_TIMEOUT_SECONDS == 5


def test_static_public_key_path_remains_networkless(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("PyJWKClient must not be constructed for CLERK_JWT_KEY mode")

    monkeypatch.setattr(auth, "PyJWKClient", forbidden)
    verifier = auth.ClerkTokenVerifier(auth.ClerkConfig(
        issuer="https://clerk.example",
        jwt_key="test-public-key",
        authorized_parties=("https://clay.example",),
    ))
    assert verifier._jwks is None


def test_websocket_auth_verification_is_off_event_loop():
    source = (ROOT / "clayverse" / "terminal_gateway.py").read_text()
    assert "claims = await asyncio.to_thread(verifier.verify, token)" in source
    assert "claims = verifier.verify(token)" not in source
