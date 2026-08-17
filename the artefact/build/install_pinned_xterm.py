#!/usr/bin/env python3
from __future__ import annotations

import base64
import hashlib
import hmac
import io
import json
import os
from pathlib import Path, PurePosixPath
import tarfile
import tempfile
import urllib.parse
import urllib.request

LOCK_PATH = Path("/opt/clayverse-build/SOURCE_LOCK.json")
DESTINATION = Path("/opt/clayverse/vendor/xterm")
MAX_ARCHIVE_BYTES = 16 * 1024 * 1024
MAX_ASSET_BYTES = 8 * 1024 * 1024
REQUIRED_ASSETS = {
    "package/lib/xterm.js": Path("lib/xterm.js"),
    "package/css/xterm.css": Path("css/xterm.css"),
}


def _parse_sha512_sri(value: str) -> bytes:
    prefix = "sha512-"
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError("xterm integrity must be a sha512 SRI value")
    try:
        digest = base64.b64decode(value[len(prefix) :], validate=True)
    except Exception as exc:  # noqa: BLE001 - fail closed on malformed lock data
        raise ValueError("xterm integrity is not valid base64") from exc
    if len(digest) != hashlib.sha512().digest_size:
        raise ValueError("xterm sha512 integrity has the wrong digest length")
    return digest


def _safe_archive_name(name: str) -> bool:
    if not isinstance(name, str) or not name or "\x00" in name:
        return False
    path = PurePosixPath(name)
    return not path.is_absolute() and all(part not in {"", ".", ".."} for part in path.parts)


def _verify_archive(blob: bytes, integrity: str) -> None:
    if len(blob) > MAX_ARCHIVE_BYTES:
        raise ValueError("xterm archive exceeds the configured size limit")
    expected = _parse_sha512_sri(integrity)
    actual = hashlib.sha512(blob).digest()
    if not hmac.compare_digest(actual, expected):
        raise ValueError("xterm archive sha512 mismatch")


def _extract_required_assets(blob: bytes, destination: Path) -> None:
    selected: dict[str, bytes] = {}
    with tarfile.open(fileobj=io.BytesIO(blob), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not _safe_archive_name(member.name):
                raise ValueError(f"unsafe xterm archive member: {member.name!r}")
            if member.name not in REQUIRED_ASSETS:
                continue
            if member.name in selected:
                raise ValueError(f"duplicate required xterm asset: {member.name}")
            if not member.isfile():
                raise ValueError(f"required xterm asset is not a regular file: {member.name}")
            if member.size < 0 or member.size > MAX_ASSET_BYTES:
                raise ValueError(f"required xterm asset exceeds size limit: {member.name}")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError(f"required xterm asset cannot be read: {member.name}")
            data = stream.read(MAX_ASSET_BYTES + 1)
            if len(data) != member.size or len(data) > MAX_ASSET_BYTES:
                raise ValueError(f"required xterm asset length mismatch: {member.name}")
            selected[member.name] = data

    missing = set(REQUIRED_ASSETS) - set(selected)
    if missing:
        raise ValueError(f"xterm archive is missing required assets: {sorted(missing)!r}")

    destination.mkdir(parents=True, exist_ok=True)
    for member_name, relative_target in REQUIRED_ASSETS.items():
        target = destination / relative_target
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=target.parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                handle.write(selected[member_name])
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temp_name, 0o444)
            os.replace(temp_name, target)
        finally:
            if os.path.exists(temp_name):
                os.unlink(temp_name)


def _download_bounded(url: str) -> bytes:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("xterm source URL must be credential-free HTTPS")
    request = urllib.request.Request(url, headers={"User-Agent": "ClayVerse-build/1"})
    with urllib.request.urlopen(request, timeout=45) as response:
        blob = response.read(MAX_ARCHIVE_BYTES + 1)
    if len(blob) > MAX_ARCHIVE_BYTES:
        raise ValueError("xterm archive exceeds the configured size limit")
    return blob


def install(lock_path: Path = LOCK_PATH, destination: Path = DESTINATION) -> None:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    xterm = lock.get("xterm_web")
    if not isinstance(xterm, dict):
        raise ValueError("SOURCE_LOCK.json is missing xterm_web")
    url = xterm.get("tarball_url")
    integrity = xterm.get("integrity")
    if not isinstance(url, str) or not isinstance(integrity, str):
        raise ValueError("xterm_web lock requires tarball_url and integrity")
    blob = _download_bounded(url)
    _verify_archive(blob, integrity)
    _extract_required_assets(blob, destination)


if __name__ == "__main__":
    install()
