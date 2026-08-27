#!/usr/bin/env python3
"""Fail-closed verifier for the canonical MicroEntity package snapshot.

This tool verifies the existing package contract without becoming a second package
builder or state authority. It checks that MICROENTITY_CURRENT.zip is exactly the
ordered set declared by PACKAGE_MANIFEST.json and that each decompressed member is
byte-identical to the versioned source file under the MicroEntity package root.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

RECEIPT_SCHEMA = "PACKAGE_ARTIFACT_RECEIPT/v1"
SHA1_RE = re.compile(r"^[0-9a-f]{40}$")


class PackageVerificationError(ValueError):
    """Typed fail-closed package verification error."""


@dataclass(frozen=True)
class PackageVerification:
    zip_size: int
    zip_sha256: str
    zip_git_blob_sha1: str
    members: tuple[str, ...]
    member_sha256: dict[str, str]


def _load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PackageVerificationError(f"MANIFEST_UNREADABLE:{exc.__class__.__name__}") from exc
    if not isinstance(value, dict):
        raise PackageVerificationError("MANIFEST_OBJECT_REQUIRED")
    required = value.get("archive_members_required")
    if not isinstance(required, list) or not required:
        raise PackageVerificationError("MANIFEST_REQUIRED_MEMBERS_NONEMPTY_LIST_REQUIRED")
    seen: set[str] = set()
    for member in required:
        if not isinstance(member, str) or not member:
            raise PackageVerificationError("MANIFEST_MEMBER_NONEMPTY_STRING_REQUIRED")
        posix = PurePosixPath(member)
        if posix.is_absolute() or ".." in posix.parts or member.endswith("/"):
            raise PackageVerificationError(f"MANIFEST_MEMBER_PATH_FORBIDDEN:{member}")
        if member in seen:
            raise PackageVerificationError(f"MANIFEST_DUPLICATE_MEMBER:{member}")
        seen.add(member)
    snapshot = value.get("snapshot")
    if not isinstance(snapshot, str) or not snapshot or PurePosixPath(snapshot).name != snapshot:
        raise PackageVerificationError("MANIFEST_SNAPSHOT_BASENAME_REQUIRED")
    return value


def _git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()


def verify_package(package_root: Path, manifest_path: Path | None = None, snapshot_path: Path | None = None) -> PackageVerification:
    package_root = package_root.resolve()
    manifest_path = (manifest_path or package_root / "PACKAGE_MANIFEST.json").resolve()
    manifest = _load_manifest(manifest_path)
    snapshot_path = (snapshot_path or package_root / manifest["snapshot"]).resolve()
    expected_snapshot = (package_root / manifest["snapshot"]).resolve()
    if snapshot_path != expected_snapshot:
        raise PackageVerificationError("SNAPSHOT_PATH_MUST_MATCH_MANIFEST")
    try:
        zip_bytes = snapshot_path.read_bytes()
    except OSError as exc:
        raise PackageVerificationError(f"SNAPSHOT_UNREADABLE:{exc.__class__.__name__}") from exc
    if not zip_bytes:
        raise PackageVerificationError("SNAPSHOT_EMPTY")

    required = tuple(manifest["archive_members_required"])
    try:
        with zipfile.ZipFile(snapshot_path, "r") as archive:
            infos = archive.infolist()
            names = tuple(info.filename for info in infos)
            if len(names) != len(set(names)):
                raise PackageVerificationError("ZIP_DUPLICATE_MEMBER")
            if names != required:
                raise PackageVerificationError(
                    "ZIP_MEMBER_SET_OR_ORDER_MISMATCH:"
                    + json.dumps({"expected": required, "observed": names}, separators=(",", ":"))
                )
            for info in infos:
                if info.is_dir():
                    raise PackageVerificationError(f"ZIP_DIRECTORY_MEMBER_FORBIDDEN:{info.filename}")
                posix = PurePosixPath(info.filename)
                if posix.is_absolute() or ".." in posix.parts:
                    raise PackageVerificationError(f"ZIP_MEMBER_PATH_FORBIDDEN:{info.filename}")
                if info.flag_bits & 0x1:
                    raise PackageVerificationError(f"ZIP_ENCRYPTED_MEMBER_FORBIDDEN:{info.filename}")
                unix_mode = (info.external_attr >> 16) & 0xFFFF
                if unix_mode and stat.S_IFMT(unix_mode) not in (0, stat.S_IFREG):
                    raise PackageVerificationError(f"ZIP_NONREGULAR_MEMBER_FORBIDDEN:{info.filename}")
            bad = archive.testzip()
            if bad is not None:
                raise PackageVerificationError(f"ZIP_CRC_FAILURE:{bad}")

            member_sha256: dict[str, str] = {}
            for member in required:
                source = (package_root / PurePosixPath(member)).resolve()
                try:
                    source.relative_to(package_root)
                except ValueError as exc:
                    raise PackageVerificationError(f"SOURCE_ESCAPES_PACKAGE_ROOT:{member}") from exc
                try:
                    source_bytes = source.read_bytes()
                except OSError as exc:
                    raise PackageVerificationError(f"SOURCE_MEMBER_UNREADABLE:{member}:{exc.__class__.__name__}") from exc
                archive_bytes = archive.read(member)
                if archive_bytes != source_bytes:
                    raise PackageVerificationError(f"ZIP_MEMBER_BYTES_MISMATCH:{member}")
                member_sha256[member] = hashlib.sha256(source_bytes).hexdigest()
    except PackageVerificationError:
        raise
    except (zipfile.BadZipFile, EOFError, OSError) as exc:
        raise PackageVerificationError(f"ZIP_BAD_OR_TRUNCATED:{exc.__class__.__name__}") from exc

    return PackageVerification(
        zip_size=len(zip_bytes),
        zip_sha256=hashlib.sha256(zip_bytes).hexdigest(),
        zip_git_blob_sha1=_git_blob_sha1(zip_bytes),
        members=required,
        member_sha256=member_sha256,
    )


def make_receipt(result: PackageVerification, *, source_commit: str, source_tree: str, package_path: str) -> dict[str, Any]:
    for label, value in (("source_commit", source_commit), ("source_tree", source_tree)):
        if not isinstance(value, str) or not SHA1_RE.fullmatch(value):
            raise PackageVerificationError(f"{label.upper()}_GIT_SHA1_REQUIRED")
    return {
        "schema": RECEIPT_SCHEMA,
        "classification": "PACKAGE_ARTIFACT_INTEGRITY_ONLY",
        "package_path": package_path,
        "source_commit": source_commit,
        "source_tree": source_tree,
        "zip_size": result.zip_size,
        "zip_sha256": result.zip_sha256,
        "zip_git_blob_sha1": result.zip_git_blob_sha1,
        "archive_members_ordered": list(result.members),
        "member_sha256": result.member_sha256,
        "runtime_credit": 0,
        "model_credit": 0,
        "hcu_capacity_credit": 0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--package-root", type=Path, required=True)
    parser.add_argument("--source-commit", required=True)
    parser.add_argument("--source-tree", required=True)
    args = parser.parse_args(argv)
    try:
        result = verify_package(args.package_root)
        receipt = make_receipt(
            result,
            source_commit=args.source_commit,
            source_tree=args.source_tree,
            package_path=str(args.package_root),
        )
    except PackageVerificationError as exc:
        print(json.dumps({"status": "FAIL_CLOSED", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
