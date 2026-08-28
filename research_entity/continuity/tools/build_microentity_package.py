#!/usr/bin/env python3
"""Deterministic STORE-only builder for the canonical MicroEntity package snapshot.

The builder intentionally avoids DEFLATE so identical admitted member bytes produce
identical archive bytes without depending on a zlib implementation/version. It is
an artifact builder only: it does not mint runtime/model/HCU credit or state authority.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import os
import struct
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

LOCAL_SIG = 0x04034B50
CENTRAL_SIG = 0x02014B50
EOCD_SIG = 0x06054B50
VERSION_NEEDED = 20
VERSION_MADE_BY_UNIX = (3 << 8) | 20
FIXED_DOS_TIME = 0
FIXED_DOS_DATE = (1 << 5) | 1  # 1980-01-01
FILE_MODE = 0o100644
MAX_U16 = 0xFFFF
MAX_U32 = 0xFFFFFFFF


class PackageBuildError(ValueError):
    pass


@dataclass(frozen=True)
class BuildResult:
    data: bytes
    members: tuple[str, ...]
    zip_sha256: str
    zip_git_blob_sha1: str


def _git_blob_sha1(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode("ascii") + data).hexdigest()


def _load_manifest(package_root: Path, manifest_path: Path | None = None) -> dict[str, Any]:
    path = (manifest_path or package_root / "PACKAGE_MANIFEST.json").resolve()
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageBuildError(f"MANIFEST_UNREADABLE:{exc.__class__.__name__}") from exc
    if not isinstance(manifest, dict):
        raise PackageBuildError("MANIFEST_OBJECT_REQUIRED")
    members = manifest.get("archive_members_required")
    if not isinstance(members, list) or not members:
        raise PackageBuildError("MANIFEST_REQUIRED_MEMBERS_NONEMPTY_LIST_REQUIRED")
    seen: set[str] = set()
    for member in members:
        if not isinstance(member, str) or not member:
            raise PackageBuildError("MANIFEST_MEMBER_NONEMPTY_STRING_REQUIRED")
        posix = PurePosixPath(member)
        if posix.is_absolute() or ".." in posix.parts or member.endswith("/"):
            raise PackageBuildError(f"MANIFEST_MEMBER_PATH_FORBIDDEN:{member}")
        if member in seen:
            raise PackageBuildError(f"MANIFEST_DUPLICATE_MEMBER:{member}")
        seen.add(member)
    snapshot = manifest.get("snapshot")
    if not isinstance(snapshot, str) or not snapshot or PurePosixPath(snapshot).name != snapshot:
        raise PackageBuildError("MANIFEST_SNAPSHOT_BASENAME_REQUIRED")
    return manifest


def _read_members(package_root: Path, members: tuple[str, ...]) -> list[tuple[str, bytes]]:
    package_root = package_root.resolve()
    out: list[tuple[str, bytes]] = []
    for member in members:
        source = (package_root / PurePosixPath(member)).resolve()
        try:
            source.relative_to(package_root)
        except ValueError as exc:
            raise PackageBuildError(f"MEMBER_PATH_ESCAPES_ROOT:{member}") from exc
        if not source.is_file():
            raise PackageBuildError(f"MEMBER_SOURCE_REGULAR_FILE_REQUIRED:{member}")
        try:
            data = source.read_bytes()
        except OSError as exc:
            raise PackageBuildError(f"MEMBER_SOURCE_UNREADABLE:{member}:{exc.__class__.__name__}") from exc
        if len(data) > MAX_U32:
            raise PackageBuildError(f"MEMBER_TOO_LARGE_FOR_NON_ZIP64:{member}")
        out.append((member, data))
    return out


def build_bytes(package_root: Path, manifest_path: Path | None = None) -> BuildResult:
    package_root = package_root.resolve()
    manifest = _load_manifest(package_root, manifest_path)
    members = tuple(manifest["archive_members_required"])
    if len(members) > MAX_U16:
        raise PackageBuildError("TOO_MANY_MEMBERS_FOR_NON_ZIP64")
    files = _read_members(package_root, members)

    body = bytearray()
    central = bytearray()
    for member, data in files:
        name = member.encode("utf-8")
        if len(name) > MAX_U16:
            raise PackageBuildError(f"MEMBER_NAME_TOO_LONG:{member}")
        crc = binascii.crc32(data) & MAX_U32
        offset = len(body)
        if offset > MAX_U32:
            raise PackageBuildError("ARCHIVE_OFFSET_TOO_LARGE_FOR_NON_ZIP64")
        body.extend(struct.pack(
            "<IHHHHHIIIHH",
            LOCAL_SIG, VERSION_NEEDED, 0, 0, FIXED_DOS_TIME, FIXED_DOS_DATE,
            crc, len(data), len(data), len(name), 0,
        ))
        body.extend(name)
        body.extend(data)
        central.extend(struct.pack(
            "<IHHHHHHIIIHHHHHII",
            CENTRAL_SIG, VERSION_MADE_BY_UNIX, VERSION_NEEDED, 0, 0,
            FIXED_DOS_TIME, FIXED_DOS_DATE, crc, len(data), len(data), len(name),
            0, 0, 0, 0, FILE_MODE << 16, offset,
        ))
        central.extend(name)

    central_offset = len(body)
    central_size = len(central)
    if central_offset > MAX_U32 or central_size > MAX_U32:
        raise PackageBuildError("ARCHIVE_TOO_LARGE_FOR_NON_ZIP64")
    body.extend(central)
    body.extend(struct.pack(
        "<IHHHHIIH",
        EOCD_SIG, 0, 0, len(members), len(members), central_size, central_offset, 0,
    ))
    data = bytes(body)
    return BuildResult(
        data=data,
        members=members,
        zip_sha256=hashlib.sha256(data).hexdigest(),
        zip_git_blob_sha1=_git_blob_sha1(data),
    )


def write_snapshot(package_root: Path, manifest_path: Path | None = None) -> BuildResult:
    package_root = package_root.resolve()
    manifest = _load_manifest(package_root, manifest_path)
    result = build_bytes(package_root, manifest_path)
    target = (package_root / manifest["snapshot"]).resolve()
    if target.parent != package_root:
        raise PackageBuildError("SNAPSHOT_PATH_MUST_BE_PACKAGE_ROOT_BASENAME")
    fd, tmp_name = tempfile.mkstemp(prefix=f".{target.name}.", dir=package_root)
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(result.data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, target)
    finally:
        if tmp.exists():
            tmp.unlink()
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package_root", type=Path)
    parser.add_argument("--write", action="store_true", help="atomically replace the manifest-declared snapshot")
    args = parser.parse_args()
    result = write_snapshot(args.package_root) if args.write else build_bytes(args.package_root)
    print(json.dumps({
        "schema": "MICROENTITY_DETERMINISTIC_PACKAGE_BUILD/v1",
        "compression": "STORE",
        "fixed_dos_timestamp": "1980-01-01T00:00:00",
        "member_count": len(result.members),
        "members": list(result.members),
        "zip_size": len(result.data),
        "zip_sha256": result.zip_sha256,
        "zip_git_blob_sha1": result.zip_git_blob_sha1,
        "runtime_credit": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
