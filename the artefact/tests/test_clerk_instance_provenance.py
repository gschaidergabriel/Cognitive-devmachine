from __future__ import annotations

import base64

import pytest

from clayverse.service import _clerk_frontend_api_from_publishable_key, _web_config


def _publishable_key(domain: str, *, live: bool = False) -> str:
    prefix = "pk_live_" if live else "pk_test_"
    encoded = base64.b64encode(f"{domain}$".encode("ascii")).decode("ascii")
    return prefix + encoded


@pytest.mark.parametrize("live", [False, True])
def test_clerk_web_config_binds_publishable_key_frontend_api_and_issuer(monkeypatch, live):
    domain = "clerk.example.com"
    publishable_key = _publishable_key(domain, live=live)
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", publishable_key)
    monkeypatch.setenv("CLERK_FRONTEND_API_URL", f"https://{domain}/")

    assert _clerk_frontend_api_from_publishable_key(publishable_key) == f"https://{domain}"
    assert _web_config(f"https://{domain}/") == (publishable_key, f"https://{domain}")


def test_clerk_web_config_rejects_browser_fapi_from_another_instance(monkeypatch):
    publishable_key = _publishable_key("one.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", publishable_key)
    monkeypatch.setenv("CLERK_FRONTEND_API_URL", "https://two.clerk.accounts.dev")

    with pytest.raises(RuntimeError, match="must match the publishable-key Clerk instance"):
        _web_config("https://one.clerk.accounts.dev")


def test_clerk_web_config_rejects_token_issuer_from_another_instance(monkeypatch):
    publishable_key = _publishable_key("one.clerk.accounts.dev")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", publishable_key)
    monkeypatch.setenv("CLERK_FRONTEND_API_URL", "https://one.clerk.accounts.dev")

    with pytest.raises(RuntimeError, match="CLERK_ISSUER must match"):
        _web_config("https://two.clerk.accounts.dev")


@pytest.mark.parametrize(
    "publishable_key",
    [
        "pk_test_not-base64***",
        "pk_test_" + base64.b64encode(b"clerk.example.com").decode("ascii"),
        _publishable_key("clerk.example.com/other"),
        _publishable_key("user@clerk.example.com"),
        _publishable_key("clerk.example.com:443"),
        "sk_test_" + base64.b64encode(b"clerk.example.com$").decode("ascii"),
    ],
)
def test_clerk_publishable_key_fapi_decode_fails_closed(publishable_key):
    with pytest.raises(RuntimeError):
        _clerk_frontend_api_from_publishable_key(publishable_key)
