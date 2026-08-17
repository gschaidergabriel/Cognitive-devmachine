import hashlib
from types import SimpleNamespace

import pytest

from clayverse.runtime_identity import RuntimeIdentityError, collect_runtime_identity


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _seed_runtime_files(tmp_path, monkeypatch):
    entityos = tmp_path / "EntityOS"
    settings = tmp_path / "managed-settings.json"
    mcp = tmp_path / "managed-mcp.json"
    runtime_md = tmp_path / "CLAUDE.md"
    entityos.write_bytes(b"entityos-exact")
    settings.write_bytes(b'{"settings":true}\n')
    mcp.write_bytes(b'{"mcp":true}\n')
    runtime_md.write_bytes(b"runtime policy\n")
    monkeypatch.setenv("CLAYVERSE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("CLAYVERSE_IMAGE_DIGEST", "sha256:" + "b" * 64)
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_PATH", str(entityos))
    monkeypatch.setenv("CLAYVERSE_ENTITYOS_SHA256", _sha(entityos))
    monkeypatch.setenv("CLAYVERSE_MANAGED_SETTINGS_PATH", str(settings))
    monkeypatch.setenv("CLAYVERSE_MANAGED_MCP_PATH", str(mcp))
    monkeypatch.setenv("CLAYVERSE_RUNTIME_CLAUDE_MD_PATH", str(runtime_md))
    return entityos, settings, mcp, runtime_md


def _fake_commands(monkeypatch):
    monkeypatch.setattr(
        "clayverse.runtime_identity.shutil.which",
        lambda name, path=None: f"/usr/local/bin/{name}",
    )

    def fake_run(argv, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["capture_output"] is True
        assert kwargs["text"] is False
        assert kwargs["check"] is False
        assert kwargs["timeout"] == 5
        assert "MISTRAL_API_KEY" not in kwargs["env"]
        assert "CLAYVERSE_LLM_API_TOKEN" not in kwargs["env"]
        assert "GITHUB_READ_TOKEN" not in kwargs["env"]
        output = b"2.1.0\n" if argv[-1] == "--version" else b"tmux 3.5a\n"
        return SimpleNamespace(returncode=0, stdout=output, stderr=b"")

    monkeypatch.setattr("clayverse.runtime_identity.subprocess.run", fake_run)


def test_collect_runtime_identity_binds_injected_oci_and_measured_runtime_bytes(tmp_path, monkeypatch):
    entityos, settings, mcp, runtime_md = _seed_runtime_files(tmp_path, monkeypatch)
    monkeypatch.setenv("MISTRAL_API_KEY", "must-not-enter-version-child")
    monkeypatch.setenv("CLAYVERSE_LLM_API_TOKEN", "must-not-enter-version-child-either")
    monkeypatch.setenv("GITHUB_READ_TOKEN", "must-not-enter-version-child")
    _fake_commands(monkeypatch)

    identity = collect_runtime_identity()

    assert identity == {
        "source_revision": "a" * 40,
        "image_digest": "sha256:" + "b" * 64,
        "entityos_sha256": _sha(entityos),
        "managed_settings_sha256": _sha(settings),
        "managed_mcp_sha256": _sha(mcp),
        "runtime_claude_md_sha256": _sha(runtime_md),
        "claude_identity": "2.1.0",
        "tmux_identity": "tmux 3.5a",
    }


def test_runtime_identity_rejects_unbound_source_or_image(tmp_path, monkeypatch):
    _seed_runtime_files(tmp_path, monkeypatch)
    _fake_commands(monkeypatch)
    monkeypatch.setenv("CLAYVERSE_SOURCE_REVISION", "main")
    with pytest.raises(RuntimeIdentityError, match="SOURCE_REVISION"):
        collect_runtime_identity()

    monkeypatch.setenv("CLAYVERSE_SOURCE_REVISION", "a" * 40)
    monkeypatch.setenv("CLAYVERSE_IMAGE_DIGEST", "latest")
    with pytest.raises(RuntimeIdentityError, match="IMAGE_DIGEST"):
        collect_runtime_identity()


def test_runtime_identity_rejects_entityos_substitution(tmp_path, monkeypatch):
    entityos, *_ = _seed_runtime_files(tmp_path, monkeypatch)
    _fake_commands(monkeypatch)
    entityos.write_bytes(b"substituted")

    with pytest.raises(RuntimeIdentityError, match="EntityOS runtime digest"):
        collect_runtime_identity()


def test_runtime_identity_rejects_symlinked_policy_file(tmp_path, monkeypatch):
    _, settings, *_ = _seed_runtime_files(tmp_path, monkeypatch)
    _fake_commands(monkeypatch)
    real = tmp_path / "settings.real"
    settings.rename(real)
    settings.symlink_to(real.name)

    with pytest.raises(RuntimeIdentityError, match="real file"):
        collect_runtime_identity()


def test_runtime_identity_rejects_multiline_or_stderr_command_identity(tmp_path, monkeypatch):
    _seed_runtime_files(tmp_path, monkeypatch)
    monkeypatch.setattr(
        "clayverse.runtime_identity.shutil.which",
        lambda name, path=None: f"/usr/local/bin/{name}",
    )
    monkeypatch.setattr(
        "clayverse.runtime_identity.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(returncode=0, stdout=b"version\nsecond\n", stderr=b""),
    )

    with pytest.raises(RuntimeIdentityError, match="visible ASCII line"):
        collect_runtime_identity()
