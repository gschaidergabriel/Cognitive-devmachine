#!/usr/bin/env python3
"""Install the exact digest-pinned xterm browser package.

Build-only helper. It verifies the repository-owned SHA-512 lock before opening
an npm tarball, validates package identity, rejects links/path traversal and
extracts only regular files beneath the canonical `package/` root.
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
TARGET = Path(os.environ.get("CLAYVERSE_XTERM_TARGET", "/opt/clayverse/vendor/xterm"))


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
        data = response.read()
    verify_digest(data, expected_sha512)
    return data


def safe_members(tf: tarfile.TarFile) -> list[tarfile.TarInfo]:
    members = tf.getmembers()
    for member in members:
        path = Path(member.name)
        if path.is_absolute() or ".." in path.parts:
            raise SystemExit(f"unsafe xterm archive path: {member.name}")
        if not path.parts or path.parts[0] != "package":
            raise SystemExit(f"unexpected xterm archive root: {member.name}")
        if member.issym() or member.islnk() or not (member.isdir() or member.isfile()):
            raise SystemExit(f"unsafe xterm archive member type: {member.name}")
    return members


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
        members = safe_members(tf)
        manifests = [m for m in members if m.isfile() and m.name == "package/package.json"]
        if len(manifests) != 1:
            raise SystemExit(f"expected exactly one xterm package.json, got {len(manifests)}")
        try:
            metadata = json.loads(_read_member(tf, manifests[0]).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit("invalid xterm package.json") from exc
        if metadata.get("name") != expected_package or str(metadata.get("version")) != expected_version:
            raise SystemExit("xterm package identity mismatch")

        if target.exists():
            raise SystemExit(f"xterm target already exists: {target}")
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_name(target.name + f".tmp-{os.getpid()}")
        if tmp.exists():
            shutil.rmtree(tmp)
        tmp.mkdir(mode=0o755)
        try:
            for member in members:
                rel_parts = Path(member.name).parts[1:]
                if not rel_parts:
                    continue
                dest = tmp.joinpath(*rel_parts)
                if member.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                payload = _read_member(tf, member)
                with dest.open("wb") as out:
                    out.write(payload)
                    out.flush()
                    os.fsync(out.fileno())
                dest.chmod(0o444)
            required = [tmp / "package.json", tmp / "lib" / "xterm.js", tmp / "css" / "xterm.css"]
            missing = [str(path.relative_to(tmp)) for path in required if not path.is_file()]
            if missing:
                raise SystemExit(f"xterm archive missing required files: {','.join(missing)}")
            for directory in sorted((p for p in tmp.rglob("*") if p.is_dir()), reverse=True):
                directory.chmod(0o555)
            tmp.chmod(0o555)
            os.replace(tmp, target)
        except BaseException:
            shutil.rmtree(tmp, ignore_errors=True)
            raise


def main() -> None:
    package, version, url, digest = load_config()
    data = fetch_verified(url, digest)
    install_archive(data, TARGET, package, version)


if __name__ == "__main__":
    main()
