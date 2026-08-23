#!/usr/bin/env python3
"""Deterministically rebuild MICROENTITY_CURRENT.zip from the MicroEntity package tree."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

BLOCKED_NAMES = {".env", "id_rsa", "id_ed25519", "credentials.json", "secrets.json"}
BLOCKED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
CONTENTS_NAME = "SNAPSHOT_CONTENTS.json"


def blocked(path: Path) -> bool:
    name = path.name.lower()
    return name in BLOCKED_NAMES or path.suffix.lower() in BLOCKED_SUFFIXES


def collect(root: Path, output: Path):
    files = []
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if p.resolve() == output.resolve():
            continue
        if p.name == CONTENTS_NAME and p.parent.resolve() == root.resolve():
            continue
        if blocked(p):
            raise SystemExit(f"blocked secret-like package path: {p.relative_to(root)}")
        files.append(p)
    return files


def _zip_write(z: ZipFile, rel: str, data: bytes) -> None:
    zi = ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
    zi.compress_type = ZIP_DEFLATED
    zi.external_attr = (0o100644 & 0xFFFF) << 16
    z.writestr(zi, data)


def build(root: Path, output: Path):
    files = collect(root, output)
    hashes = {}
    payloads = []
    for p in files:
        rel = p.relative_to(root).as_posix()
        data = p.read_bytes()
        hashes[rel] = hashlib.sha256(data).hexdigest()
        payloads.append((rel, data))
    contents = {
        "schema": "MICROENTITY_SNAPSHOT_CONTENTS/v2",
        "policy": "RECURSIVE_ALL_NON_SECRET_FILES_UNDER_ROOT",
        "payload_file_count": len(payloads),
        "files": hashes,
    }
    contents_bytes = (json.dumps(contents, indent=2, sort_keys=True) + "\n").encode()
    (root / CONTENTS_NAME).write_bytes(contents_bytes)

    output.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(output, "w", compression=ZIP_DEFLATED, compresslevel=9) as z:
        for rel, data in payloads:
            _zip_write(z, rel, data)
        _zip_write(z, CONTENTS_NAME, contents_bytes)
    return {
        **contents,
        "archive_file_count": len(payloads) + 1,
        "snapshot_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path("the artefact/MicroEntity"))
    ap.add_argument("--output", type=Path)
    args = ap.parse_args()
    output = args.output or (args.root / "MICROENTITY_CURRENT.zip")
    print(json.dumps(build(args.root, output), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
