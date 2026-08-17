#!/usr/bin/env python3
"""Install exactly the repository-locked xterm browser assets without npm/Node.

Build-only helper. It downloads one exact npm registry tarball, verifies the
locked SHA-512 before opening it, validates package identity and archive shape,
and installs only the browser assets ClayVerse serves at runtime.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import tarfile
import tempfile
import urllib.parse
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


def load_config() -> tuple[str, str, str, bytes]:
    lock = json.loads(LOCK_PATH.read_text("utf-8"))
    item = lock["xterm"]
    package = str(item["package"])
    version = str(item["version"])
    url = str(item["tarball"])
    integrity = str(item["integrity"])
    if package != "@xterm/xterm" or version != "6.0.0":
        raise SystemExit("unexpected xterm package identity")
    expected_url = f"https://registry.npmjs.org/@xterm/xterm/-/xterm-{version}.tgz"
    if url != expected_url:
        raise SystemExit("unexpected xterm tarball URL")
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != "registry.npmjs.org" or parsed.username or parsed.password:
        raise SystemExit("unsafe xterm tarball origin")
    if not integrity.startswith("sha512-"):
        raise SystemExit("xterm integrity must be sha512 SRI")
    try:
        digest = base64.b64decode(integrity[7:], validate=True)
    except Exception as exc:
        raise SystemExit("invalid xterm SHA-512 SRI") from exc
    if len(digest) != hashlib.sha512().digest_size:
        raise SystemExit("invalid xterm SHA-512 digest length")
    return package, version, url, digest


def fetch_verified(url: str, expected_sha512: bytes) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": "ClayVerse-build/1"})
    with urllib.request.urlopen(req, timeout=180) as response:
        data = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(data) > MAX_ARCHIVE_BYTES:
        raise SystemExit("xterm archive exceeds size limit")
    actual = hashlib.sha512(data).digest()
    if actual != expected_sha512:
        raise SystemExit("xterm archive digest mismatch")
    return data


def _validated_regular_members(tf: tarfile.TarFile) -> dict[str, tarfile.TarInfo]:
    members = tf.getmembers()
    if len(members) > MAX_MEMBERS:
        raise SystemExit("xterm archive has too many members")
    regular: dict[str, tarfile.TarInfo] = {}
    total = 0
    for member in members:
        path = PurePosixPath(member.name)
        if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != "package":
            raise SystemExit(f"unsafe xterm archive member: {member.name}")
        if member.issym() or member.islnk() or member.isdev() or member.isfifo():
            raise SystemExit(f"unsafe xterm archive member type: {member.name}")
        if member.isdir():
            continue
        if not member.isfile():
            raise SystemExit(f"unsupported xterm archive member type: {member.name}")
        if member.name in regular:
            raise SystemExit(f"duplicate xterm archive member: {member.name}")
        total += member.size
        if total > MAX_UNPACKED_BYTES:
            raise SystemExit("xterm archive exceeds unpacked size limit")
        regular[member.name] = member
    missing = sorted(set(_REQUIRED_FILES) - set(regular))
    if missing:
        raise SystemExit(f"xterm archive missing required files: {','.join(missing)}")
    return regular


def install_archive(data: bytes, target: Path = TARGET, *, package: str = "@xterm/xterm", version: str = "6.0.0") -> None:
    with tarfile.open(fileobj=io.BytesIO(data), mode="r:gz") as tf:
        regular = _validated_regular_members(tf)
        package_src = tf.extractfile(regular["package/package.json"])
        if package_src is None:
            raise SystemExit("xterm package.json unreadable")
        try:
            metadata = json.loads(package_src.read().decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise SystemExit("invalid xterm package.json") from exc
        if metadata.get("name") != package or metadata.get("version") != version:
            raise SystemExit("xterm archive package identity mismatch")

        target.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".xterm-", dir=target.parent) as temp_name:
            temp = Path(temp_name)
            for archive_name, relative_name in _REQUIRED_FILES.items():
                src = tf.extractfile(regular[archive_name])
                if src is None:
                    raise SystemExit(f"xterm asset unreadable: {archive_name}")
                dst = temp / relative_name
                dst.parent.mkdir(parents=True, exist_ok=True)
                with dst.open("wb") as out:
                    shutil.copyfileobj(src, out)
                    out.flush()
                    os.fsync(out.fileno())
                dst.chmod(0o444)
            for directory in (temp / "lib", temp / "css", temp):
                directory.chmod(0o555)
            old = target.with_name(target.name + ".old")
            if old.exists():
                shutil.rmtree(old)
            if target.exists():
                os.replace(target, old)
            os.replace(temp, target)
            if old.exists():
                shutil.rmtree(old)


def main() -> None:
    package, version, url, digest = load_config()
    data = fetch_verified(url, digest)
    install_archive(data, TARGET, package=package, version=version)


if __name__ == "__main__":
    main()
