from types import SimpleNamespace

from clayverse.readiness import claude_readiness


def test_claude_version_probe_never_inherits_service_credentials(monkeypatch):
    monkeypatch.setenv("MISTRAL_API_KEY", "provider-secret")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "generic-provider-secret")
    monkeypatch.setenv("CLERK_SECRET_KEY", "clerk-secret")
    monkeypatch.setenv("GITHUB_READ_TOKEN", "source-secret")

    monkeypatch.setattr(
        "clayverse.readiness.shutil.which",
        lambda name: f"/usr/local/bin/{name}" if name in {"claude", "tmux"} else None,
    )
    seen = {}

    def fake_run(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["env"] = dict(kwargs.get("env") or {})
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("clayverse.readiness.subprocess.run", fake_run)

    status = claude_readiness(required=True)
    assert status.binary_available is True
    assert status.tmux_available is True
    assert status.interactive_cli_version_ok is True
    assert seen["argv"] == ["claude", "--version"]
    assert seen["env"] == {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
    }
    for key in (
        "MISTRAL_API_KEY",
        "CLAYVERSE_LLM_API_TOKEN",
        "CLERK_SECRET_KEY",
        "GITHUB_READ_TOKEN",
    ):
        assert key not in seen["env"]
