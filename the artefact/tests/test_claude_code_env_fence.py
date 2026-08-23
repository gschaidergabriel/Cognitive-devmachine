from clayverse.adapters import ClaudeCodeInference


def test_claude_child_env_does_not_inherit_network_route_or_trust_controls(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "allowed-auth")
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "allowed-oauth")
    monkeypatch.setenv("PATH", "/tmp/host-controlled-bin")
    monkeypatch.setenv("HTTP_PROXY", "http://attacker.invalid:8080")
    monkeypatch.setenv("HTTPS_PROXY", "http://attacker.invalid:8443")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://attacker.invalid")
    monkeypatch.setenv("SSL_CERT_FILE", "/tmp/attacker-ca.pem")
    monkeypatch.setenv("SSL_CERT_DIR", "/tmp/attacker-certs")
    monkeypatch.setenv("NODE_EXTRA_CA_CERTS", "/tmp/attacker-node-ca.pem")

    env = ClaudeCodeInference._subprocess_env()

    assert env["ANTHROPIC_API_KEY"] == "allowed-auth"
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "allowed-oauth"
    assert env["PATH"] == ClaudeCodeInference.FIXED_PATH
    assert {
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "ANTHROPIC_BASE_URL",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "NODE_EXTRA_CA_CERTS",
    }.isdisjoint(env)


def test_ambient_claude_code_bin_cannot_retarget_production_cognition(monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_BIN", "/tmp/host-controlled-claude")

    adapter = ClaudeCodeInference()

    assert adapter.binary == ClaudeCodeInference.DEFAULT_BINARY
    assert adapter.binary == "/usr/local/bin/claude"


def test_explicit_binary_override_remains_available_for_bounded_tests():
    adapter = ClaudeCodeInference(binary="/tmp/fake-claude")

    assert adapter.binary == "/tmp/fake-claude"
