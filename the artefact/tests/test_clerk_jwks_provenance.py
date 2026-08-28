import pytest

import clayverse.clerk_auth as auth


def _base_env(monkeypatch):
    monkeypatch.setenv("CLERK_ISSUER", "https://one.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "https://clay.example")
    monkeypatch.delenv("CLERK_JWT_KEY", raising=False)
    monkeypatch.delenv("CLERK_AUDIENCE", raising=False)


def test_network_jwks_defaults_to_exact_issuer_endpoint(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.delenv("CLERK_JWKS_URL", raising=False)
    cfg = auth.ClerkConfig.from_env()
    assert cfg.jwks_url == "https://one.clerk.accounts.dev/.well-known/jwks.json"


def test_network_jwks_rejects_cross_instance_override(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("CLERK_JWKS_URL", "https://attacker.example/.well-known/jwks.json")
    with pytest.raises(RuntimeError, match="JWKS"):
        auth.ClerkConfig.from_env()


def test_network_jwks_rejects_same_host_wrong_path(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("CLERK_JWKS_URL", "https://one.clerk.accounts.dev/alternate-keys.json")
    with pytest.raises(RuntimeError, match="JWKS"):
        auth.ClerkConfig.from_env()


def test_direct_config_cannot_bypass_network_jwks_binding(monkeypatch):
    class ForbiddenPyJWKClient:
        def __init__(self, *args, **kwargs):
            raise AssertionError("unbound JWKS URL reached network client")

    monkeypatch.setattr(auth, "PyJWKClient", ForbiddenPyJWKClient)
    with pytest.raises(RuntimeError, match="JWKS"):
        auth.ClerkTokenVerifier(auth.ClerkConfig(
            issuer="https://one.clerk.accounts.dev",
            jwks_url="https://attacker.example/.well-known/jwks.json",
            authorized_parties=("https://clay.example",),
        ))


def test_static_key_mode_remains_networkless_even_with_no_jwks_url(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("PyJWKClient must not be constructed for static-key mode")

    monkeypatch.setattr(auth, "PyJWKClient", forbidden)
    verifier = auth.ClerkTokenVerifier(auth.ClerkConfig(
        issuer="https://one.clerk.accounts.dev",
        jwt_key="test-public-key",
        authorized_parties=("https://clay.example",),
    ))
    assert verifier._jwks is None


def test_exact_network_jwks_override_is_accepted(monkeypatch):
    _base_env(monkeypatch)
    monkeypatch.setenv("CLERK_JWKS_URL", "https://one.clerk.accounts.dev/.well-known/jwks.json")
    cfg = auth.ClerkConfig.from_env()
    assert cfg.jwks_url == "https://one.clerk.accounts.dev/.well-known/jwks.json"


def test_static_key_env_discards_network_jwks_override(monkeypatch):
    monkeypatch.setenv("CLERK_ISSUER", "https://one.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_AUTHORIZED_PARTIES", "https://clay.example")
    monkeypatch.setenv("CLERK_JWT_KEY", "test-public-key")
    monkeypatch.setenv("CLERK_JWKS_URL", "https://attacker.example/ignored.json")
    cfg = auth.ClerkConfig.from_env()
    assert cfg.jwt_key == "test-public-key"
    assert cfg.jwks_url is None
