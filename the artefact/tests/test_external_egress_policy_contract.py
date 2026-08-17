from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "deployment" / "EXTERNAL_EGRESS_POLICY_CONTRACT.md"


def test_external_egress_contract_keeps_default_deny_as_baseline():
    text = CONTRACT.read_text()
    assert "clayverse-default-deny" in text
    assert "does **not** authorize any network flow" in text
    assert "0.0.0.0/0" in text
    assert "::/0" in text
    assert "unrestricted HTTPS" in text
    assert "unrestricted DNS" in text


def test_external_egress_requires_one_explicit_strategy():
    text = CONTRACT.read_text()
    assert "Exactly one deployment-specific external-egress strategy MUST be selected" in text
    assert "Strategy A — FQDN-capable CNI policy" in text
    assert "Strategy B — dedicated egress proxy boundary" in text
    assert "toFQDNs" in text
    assert "direct pod egress to the public network remains denied" in text


def test_provider_domains_are_runtime_bound_not_guessed_in_source():
    text = CONTRACT.read_text()
    assert "MUST NOT guess a permanent provider-domain list" in text
    assert "Clerk issuer/JWKS/frontend/browser authentication paths" in text
    assert "interactive Claude Code login/runtime provider paths" in text
    assert "optional GLM API endpoint" in text
    assert "GLM remains inference-only" in text


def test_acceptance_proves_allowed_and_denied_flows_on_real_target():
    text = CONTRACT.read_text()
    assert "enumerate the full additive policy set selecting the ClayVerse pod" in text
    assert "prove representative undeclared external domains/IPs" in text
    assert "arbitrary DNS resolvers" in text
    assert "rotate/re-resolve provider DNS" in text
    assert "Tier-2 replacement" in text
    assert "before ingress reopens" in text


def test_static_success_never_becomes_runtime_credit():
    text = CONTRACT.read_text()
    assert "static YAML policy" in text
    assert "does not establish whole ClayVerse PASS" in text
    assert "Final acceptance MUST refresh" in text
    assert "execute the real target tests" in text
