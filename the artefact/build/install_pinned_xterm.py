#!/usr/bin/env python3
"""Install the exact digest-pinned xterm browser runtime assets.

Build-only helper. It verifies the repository-owned SHA-512 lock before opening
an npm tarball, validates package identity and archive shape, bounds downloaded
and unpacked input, and installs only the three files ClayVerse serves/needs.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.request

LOCK_PATH = Path(os.environ.get("CLAYVERSE_SOURCE_LOCK", "/opt/clayverse-build/SOURCE_LOCK.json"))
TARGET = Path(os.environ.get("CLAYVERSE_XTERM_TARGET", "/opt/clayverse/vendor/xterm"))
MAX_ARCHIVE_BYTES = 20 * 1024 * 1024
MAX_MEMBERS = 4096
MAX_UNPACKED_BYTES = 64 * 1024 * 1024
_REQUIRED_FILES = {
    "package/package.json": "package.json",
    "package/lib/xterm.js": "lib/xterm.js",
    "package/css/xterm.css": "css/xterm.css",
}


def load_config() -> tuple[str, str, str, str]:
    lock = json.loads(LOCK_PATH.read_text("utf-8"))
    item = lock["xterm"]
    package = str(item["package"])
    version = str(item["version"])
    url = str(item["tarball_url"])
    digest = str(item["sha512"]).lower()
    expected_url = f"https://registry.npmjs.org/@xterm/xterm/-/xterm-{version}.tgz"
    if package != "@xterm/xterm" or url != expected_url:
        raise SystemExit("invalid xterm package identity lock")
    if len(digest) != 128 or any(c not in "0123456789abcdef" for c in digest):
        raise SystemExit("invalid xterm SHA-512 lock")
    return package, version, url, digest


def verify_digest(data: bytes, expected_sha512: str) -> None:
    actual = hashlib.sha512(data).hexdigest()
    if actual != expected_sha512:
        raise SystemExit(f"xterm archive digest mismatch: expected {expected_sha512}, got {actual}")


def fetch_verified(url: str, expected_sha512: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ClayVerse-build/1"})
    with urllib.request.urlopen(req, timeout=180) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise SystemExit("xterm archive exceeds download size limit")
    verify_digest(data, expected_sha512)
    return data


def safe_members(tf: tarfile.TarFile) -> dict[str, tarfile.TarInfo]:
    members = tf.getmembers()
    if len(members) > MAX_MEMBERS:
        raise SystemExit("xterm archive has too many members")

    regular: dict[str, tarfile.TarInfo] = {}
    seen: set[str] = set()
    unpacked_bytes = 0
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"unsafe xterm archive path: {member.name}")
        if not path.parts or path.parts[0] != "package":
            raise SystemExit(f"unexpected xterm archive root: {member.name}")
        if member.name in seen:
            raise SystemExit(f"duplicate xterm archive member: {member.name}")
        seen.add(member.name)
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise SystemExit(f"unsafe xterm archive member type: {member.name}")
        if member.isdir():
            continue
        if not member.isfile():
            raise SystemExit(f"unsafe xterm archive member type: {member.name}")
        if member.size < 0:
            raise SystemExit(f"invalid xterm archive member size: {member.name}")
        unpacked_bytes += member.size
        if unpacked_bytes > MAX_UNPACKED_BYTES:
            raise SystemExit("xterm archive exceeds unpacked size limit")
        regular[member.name] = member

    missing = sorted(set(_REQUIRED_FILES) - set(regular))
    if missing:
        raise SystemExit(f"xterm archive missing required files: {','.join(missing)}")
    return regular


def _read_member(tf: tarfile.TarFile, member: tarfile.TarInfo) -> bytes:
    src = tf.extractfile(member)
    if src is None:
        raise SystemExit(f"unreadable xterm archive member: {member.name}")
    return src.read()


def install_archive(
    data: bytes,
    target: Path,
    expected_package: str,
    expected_version: str,
) -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        regular = safe_members(tf)
        try:
            metadata = json.loads(_read_member(tf, regular["package/package.json"]).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit("invalid xterm package.json") from exc
        if metadata.get("name") != expected_package or str(metadata.get("version")) != expected_version:
            raise SystemExit("xterm package identity mismatch")

        if target.exists():
            raise SystemExit(f"xterm target already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".xterm-", dir=target.parent) as temp_name:
            temp = Path(temp_name)
            for archive_name, relative_name in _REQUIRED_FILES.items():
                payload = _read_member(tf, regular[archive_name])
                dest = temp / relative_name
                dest.parent.mkdir(parents=True, exist_ok=True)
                with dest.open("wb") as out:
                    out.write(payload)
                    out.flush()
                    os.fsync(out.fileno())
                dest.chmod(0o444)
            for directory in (temp / "lib", temp / "css", temp):
                directory.chmod(0o555)
            os.replace(temp, target)


def main() -> None:
    package, version, url, digest = load_config()
    data = fetch_verified(url, digest)
    install_archive(data, TARGET, package, version)


if __name__ == "__main__":
    main()
