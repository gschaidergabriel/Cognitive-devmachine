#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

FIXED_ZIP_DT = (1980, 1, 1, 0, 0, 0)
RECEIPT_SCHEMA = "PACKAGE_ARTIFACT_RECEIPT/v1"

class SnapshotError(RuntimeError):
    pass

def _git_blob_sha(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("ascii")
    return hashlib.sha1(header + data).hexdigest()

def _validate_member_name(name: str) -> PurePosixPath:
    p = PurePosixPath(name)
    if not name or p.is_absolute() or ".." in p.parts or "." in p.parts:
        raise SnapshotError(f"UNSAFE_MEMBER_PATH:{name}")
    if "\\" in name:
        raise SnapshotError(f"NON_POSIX_MEMBER_PATH:{name}")
    return p

def _load_manifest(root: Path) -> tuple[dict, list[str]]:
    path = root / "PACKAGE_MANIFEST.json"
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SnapshotError(f"BAD_MANIFEST:{type(exc).__name__}:{exc}") from exc
    members = manifest.get("archive_members_required")
    if not isinstance(members, list) or not members or not all(isinstance(x, str) for x in members):
        raise SnapshotError("BAD_ARCHIVE_MEMBER_LIST")
    if len(members) != len(set(members)):
        raise SnapshotError("DUPLICATE_ARCHIVE_MEMBER")
    for member in members:
        _validate_member_name(member)
    return manifest, members

def _member_bytes(root: Path, member: str) -> bytes:
    base = root.resolve()
    path = (root / Path(*PurePosixPath(member).parts)).resolve()
    try:
        path.relative_to(base)
    except ValueError as exc:
        raise SnapshotError(f"MEMBER_ESCAPES_ROOT:{member}") from exc
    if not path.is_file():
        raise SnapshotError(f"MISSING_MEMBER:{member}")
    return path.read_bytes()

def _build_bytes(root: Path, members: list[str]) -> bytes:
    fd, tmp_name = tempfile.mkstemp(prefix="microentity-snapshot-", suffix=".zip")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for member in members:
                data = _member_bytes(root, member)
                info = zipfile.ZipInfo(member, date_time=FIXED_ZIP_DT)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                info.create_system = 3
                zf.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
        return tmp.read_bytes()
    finally:
        tmp.unlink(missing_ok=True)

def verify_bytes(data: bytes, expected_members: list[str]) -> dict:
    fd, tmp_name = tempfile.mkstemp(prefix="microentity-verify-", suffix=".zip")
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_bytes(data)
        with zipfile.ZipFile(tmp, "r") as zf:
            names = zf.namelist()
            if names != expected_members:
                raise SnapshotError(f"MEMBER_ORDER_OR_SET_MISMATCH:{names!r}")
            bad = zf.testzip()
            if bad is not None:
                raise SnapshotError(f"ZIP_CRC_FAIL:{bad}")
            entries = []
            for name in names:
                raw = zf.read(name)
                entries.append({
                    "name": name,
                    "size": len(raw),
                    "sha256": hashlib.sha256(raw).hexdigest(),
                })
    except zipfile.BadZipFile as exc:
        raise SnapshotError(f"BAD_ZIP:{exc}") from exc
    finally:
        tmp.unlink(missing_ok=True)
    return {
        "member_count": len(expected_members),
        "members": entries,
        "archive_size": len(data),
        "archive_sha256": hashlib.sha256(data).hexdigest(),
        "archive_git_blob_sha": _git_blob_sha(data),
    }

def rebuild(root: Path, output: Path, receipt_path: Path | None, source_head: str | None, source_tree: str | None) -> dict:
    manifest, members = _load_manifest(root)
    data = _build_bytes(root, members)
    verified = verify_bytes(data, members)
    output.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=output.name + ".", dir=str(output.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        tmp.write_bytes(data)
        os.replace(tmp, output)
    finally:
        tmp.unlink(missing_ok=True)
    receipt = {
        "schema": RECEIPT_SCHEMA,
        "package": manifest.get("package"),
        "snapshot": output.name,
        "manifest_sha256": hashlib.sha256((root / "PACKAGE_MANIFEST.json").read_bytes()).hexdigest(),
        "source_head": source_head,
        "source_tree": source_tree,
        **verified,
        "claim_class": "ARTIFACT_INTEGRITY_ONLY_NOT_RUNTIME_ACCEPTANCE",
    }
    if receipt_path is not None:
        receipt_path.parent.mkdir(parents=True, exist_ok=True)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt

def main() -> int:
    ap = argparse.ArgumentParser(description="Deterministically rebuild and verify MICROENTITY_CURRENT.zip")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
    ap.add_argument("--output", type=Path)
    ap.add_argument("--receipt", type=Path)
    ap.add_argument("--source-head")
    ap.add_argument("--source-tree")
    args = ap.parse_args()
    root = args.root.resolve()
    output = args.output or (root / "MICROENTITY_CURRENT.zip")
    receipt = args.receipt or (root / "PACKAGE_ARTIFACT_RECEIPT.json")
    result = rebuild(root, output, receipt, args.source_head, args.source_tree)
    print(json.dumps(result, sort_keys=True))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
