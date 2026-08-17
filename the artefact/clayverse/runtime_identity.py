from __future__ import annotations

import hashlib
import os
import re
import shutil
import subprocess
from pathlib import Path


class RuntimeIdentityError(RuntimeError):
    pass


_HEX40 = re.compile(r"^[0-9a-fA-F]{40}$")
_HEX64 = re.compile(r"^[0-9a-fA-F]{64}$")
_SAFE_COMMAND_ENV = {
    "PATH": "/usr/local/bin:/usr/bin:/bin",
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
}


def _sha256_file(path: Path, label: str) -> str:
    if path.is_symlink() or not path.is_file():
        raise RuntimeIdentityError(f"{label} must be a real file")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as fh:
            while True:
                chunk = fh.read(1024 * 1024)
                if not chunk:
                    return digest.hexdigest()
                digest.update(chunk)
    except OSError as exc:
        raise RuntimeIdentityError(f"{label} unreadable") from exc


def _required_source_revision() -> str:
    value = os.environ.get("CLAYVERSE_SOURCE_REVISION", "").strip()
    if _HEX40.fullmatch(value) is None:
        raise RuntimeIdentityError("CLAYVERSE_SOURCE_REVISION must be an exact 40-hex revision")
    return value.lower()


def _required_image_digest() -> str:
    value = os.environ.get("CLAYVERSE_IMAGE_DIGEST", "").strip()
    if not value.startswith("sha256:") or _HEX64.fullmatch(value[7:]) is None:
        raise RuntimeIdentityError("CLAYVERSE_IMAGE_DIGEST must be an exact sha256 digest")
    return "sha256:" + value[7:].lower()


def _required_entityos_pin() -> tuple[Path, str]:
    path = Path(os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip())
    expected = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
    if not path.is_absolute():
        raise RuntimeIdentityError("CLAYVERSE_ENTITYOS_PATH must be absolute")
    if _HEX64.fullmatch(expected) is None:
        raise RuntimeIdentityError("CLAYVERSE_ENTITYOS_SHA256 must be an exact SHA-256")
    actual = _sha256_file(path, "EntityOS")
    if actual != expected.lower():
        raise RuntimeIdentityError("EntityOS runtime digest does not match configured pin")
    return path, actual


def _command_identity(binary_name: str, argv_tail: list[str], label: str) -> str:
    binary = shutil.which(binary_name, path=_SAFE_COMMAND_ENV["PATH"])
    if not binary or not os.path.isabs(binary):
        raise RuntimeIdentityError(f"{label} binary unavailable")
    try:
        result = subprocess.run(
            [binary, *argv_tail], shell=False, capture_output=True, text=False,
            timeout=5, check=False, env=dict(_SAFE_COMMAND_ENV),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeIdentityError(f"{label} identity probe failed") from exc
    if result.returncode != 0 or result.stderr not in {b"", None}:
        raise RuntimeIdentityError(f"{label} identity probe failed")
    output = bytes(result.stdout or b"")
    if not output or len(output) > 512:
        raise RuntimeIdentityError(f"{label} identity output invalid")
    try:
        value = output.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise RuntimeIdentityError(f"{label} identity output is not UTF-8") from exc
    if not value or len(value) > 256 or any(ord(ch) < 0x20 or ord(ch) > 0x7E for ch in value):
        raise RuntimeIdentityError(f"{label} identity output is not one visible ASCII line")
    return value


def collect_runtime_identity() -> dict[str, str]:
    source_revision = _required_source_revision()
    image_digest = _required_image_digest()
    _entityos_path, entityos_sha256 = _required_entityos_pin()
    managed_settings = Path(os.environ.get("CLAYVERSE_MANAGED_SETTINGS_PATH", "/etc/claude-code/managed-settings.json"))
    managed_mcp = Path(os.environ.get("CLAYVERSE_MANAGED_MCP_PATH", "/etc/claude-code/managed-mcp.json"))
    runtime_claude_md = Path(os.environ.get("CLAYVERSE_RUNTIME_CLAUDE_MD_PATH", "/opt/clayverse/runtime/CLAUDE.md"))
    return {
        "source_revision": source_revision,
        "image_digest": image_digest,
        "entityos_sha256": entityos_sha256,
        "managed_settings_sha256": _sha256_file(managed_settings, "managed Claude settings"),
        "managed_mcp_sha256": _sha256_file(managed_mcp, "managed MCP policy"),
        "runtime_claude_md_sha256": _sha256_file(runtime_claude_md, "runtime CLAUDE.md"),
        "claude_identity": _command_identity("claude", ["--version"], "Claude Code"),
        "tmux_identity": _command_identity("tmux", ["-V"], "tmux"),
    }
