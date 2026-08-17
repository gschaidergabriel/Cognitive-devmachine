#!/usr/bin/env python3
"""Install the exact digest-pinned native Claude Code release asset.

Build-only helper. It accepts only the two glibc Linux architectures admitted by
SOURCE_LOCK.json, bounds the download to the exact locked release-asset size,
verifies the whole downloaded archive before opening it, then extracts exactly
one regular file named `claude` to /usr/local/bin/claude.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import tarfile
import urllib.request

LOCK_PATH = Path(os.environ.get("CLAYVERSE_SOURCE_LOCK", "/opt/clayverse-build/SOURCE_LOCK.json"))
TARGET = Path(os.environ.get("CLAYVERSE_CLAUDE_TARGET", "/usr/local/bin/claude"))
MAX_ARCHIVE_BYTES = 128 * 1024 * 1024


def load_config() -> tuple[str, str, str, int]:
    arch = os.environ.get("TARGETARCH", "").strip()
    if arch not in {"amd64", "arm64"}:
        raise SystemExit(f"unsupported TARGETARCH {arch!r}; supported=amd64,arm64")
    lock = json.loads(LOCK_PATH.read_text("utf-8"))
    release = lock["claude_code"]
    item = release[f"linux_{arch}"]
    version = str(release["version"])
    asset = str(item["asset"])
    digest = str(item["sha256"]).lower()
    size = item.get("size_bytes")
    if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise SystemExit("invalid Claude Code SHA-256 lock")
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0 or size > MAX_ARCHIVE_BYTES:
        raise SystemExit("invalid Claude Code archive size lock")
    return version, asset, digest, size


def fetch_verified(url: str, expected_sha256: str, expected_size: int) -> bytes:
    if isinstance(expected_size, bool) or not isinstance(expected_size, int) or expected_size <= 0 or expected_size > MAX_ARCHIVE_BYTES:
        raise SystemExit("invalid Claude Code archive size lock")
    req = urllib.request.Request(url, headers={"User-Agent": "ClayVerse-build/1"})
    with urllib.request.urlopen(req, timeout=180) as response:
        data = response.read(expected_size + 1)
    if len(data) != expected_size:
        raise SystemExit(
            f"Claude Code archive size mismatch: expected {expected_size}, got {len(data)}"
        )
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected_sha256:
        raise SystemExit(f"Claude Code archive digest mismatch: expected {expected_sha256}, got {actual}")
    return data


def safe_members(tf: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = tf.getmembers()
    for member in members:
        path = Path(member.name)
        if path.is_absolute() or ".." in path.parts or member.issym() or member.islnk():
            raise SystemExit(f"unsafe Claude Code archive member: {member.name}")
    return members


def install_archive(data: bytes, target: Path = TARGET) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        members = safe_members(tf)
        candidates = [m for m in members if m.isfile() and Path(m.name).name == "claude"]
        if len(candidates) != 1:
            raise SystemExit(f"expected exactly one Claude binary, got {len(candidates)}")
        src = tf.extractfile(candidates[0])
        if src is None:
            raise SystemExit("Claude binary unreadable")
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + ".tmp")
        with tmp.open("wb") as out:
            shutil.copyfileobj(src, out)
            out.flush()
            os.fsync(out.fileno())
        tmp.chmod(0o555)
        os.replace(tmp, target)


def main() -> None:
    version, asset, digest, size = load_config()
    url = f"https://github.com/anthropics/claude-code/releases/download/v{version}/{asset}"
    data = fetch_verified(url, digest, size)
    install_archive(data)


if __name__ == "__main__":
    main()
