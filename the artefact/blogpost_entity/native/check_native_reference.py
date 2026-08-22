#!/usr/bin/env python3
"""Fail-closed provenance gate for the credited native Mini Entity sandbox artifact.

This checker intentionally does not establish runtime correctness. It binds the credited
historical version/hash across canonical records and reports whether current canonical
source is even a compatible rebuild candidate. Source presence alone is never
reproducibility credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from build_native_bound import source_closure_identity


RECEIPT_NAME = "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
REFERENCE_NAME = "MINI_ENTITY_0_6_SANDBOX.md"
SOURCE_NAME = "mini_entity.c"
MINI_VERSION_RE = re.compile(r'^\s*#\s*define\s+MINI_VERSION\s+"([^"]+)"', re.MULTILINE)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def source_version(native_dir: Path, identity: dict) -> str | None:
    versions: set[str] = set()
    for entry in identity.get("files", []):
        path = (native_dir / str(entry["path"])).resolve()
        text = path.read_text(encoding="utf-8")
        versions.update(MINI_VERSION_RE.findall(text))
    if len(versions) > 1:
        raise RuntimeError("MULTIPLE_MINI_VERSION_LABELS:" + ",".join(sorted(versions)))
    return next(iter(versions)) if versions else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, help="Optional mini_entity.clay ELF to byte-verify")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Report missing canonical native source without failing the process",
    )
    args = parser.parse_args()

    here = Path(__file__).resolve()
    root = here.parents[3]
    native_dir = here.parent
    blogpost_dir = native_dir.parent

    state_path = root / "research_entity" / "rooms" / "PROGRAM_STATE.json"
    receipt_path = blogpost_dir / "receipts" / RECEIPT_NAME
    reference_path = native_dir / REFERENCE_NAME
    source_path = native_dir / SOURCE_NAME

    state = json.loads(state_path.read_text(encoding="utf-8"))
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    reference = reference_path.read_text(encoding="utf-8")

    native_state = state["sandbox_evidence"]["native_pipeline"]
    state_version = str(native_state["version"])
    state_hash = str(native_state["binary_sha256"])
    receipt_version = str(receipt["version"])
    receipt_hash = str(receipt["binary_sha256"])

    errors: list[str] = []
    if state_version != receipt_version:
        errors.append(f"VERSION_MISMATCH state={state_version} receipt={receipt_version}")
    if state_hash != receipt_hash:
        errors.append(f"HASH_MISMATCH state={state_hash} receipt={receipt_hash}")
    if receipt_hash not in reference:
        errors.append("REFERENCE_DOES_NOT_BIND_CREDITED_HASH")
    if receipt_version not in reference:
        errors.append("REFERENCE_DOES_NOT_BIND_CREDITED_VERSION")

    source_status = "PRESENT" if source_path.is_file() else "MISSING"
    source_identity = None
    source_label = None
    if source_path.is_file():
        try:
            source_identity = source_closure_identity(source_path)
            source_label = source_version(native_dir, source_identity)
        except (RuntimeError, UnicodeDecodeError, OSError) as exc:
            errors.append("CANONICAL_SOURCE_CLOSURE_INVALID:" + str(exc))
        if source_label is None:
            errors.append("CANONICAL_SOURCE_VERSION_UNBOUND")
        elif source_label != receipt_version:
            errors.append(
                f"CANONICAL_SOURCE_VERSION_DIFFERS_FROM_CREDITED_ARTIFACT "
                f"source={source_label} credited={receipt_version}"
            )
    elif not args.allow_missing_source:
        errors.append("CANONICAL_NATIVE_SOURCE_MISSING")

    binary_status = "NOT_PROVIDED"
    binary_hash = None
    if args.binary is not None:
        binary = args.binary.resolve()
        if not binary.is_file():
            errors.append("BINARY_PATH_MISSING")
            binary_status = "MISSING"
        else:
            binary_hash = sha256_file(binary)
            binary_status = "MATCH" if binary_hash == receipt_hash else "MISMATCH"
            if binary_hash != receipt_hash:
                errors.append(f"BINARY_HASH_MISMATCH expected={receipt_hash} observed={binary_hash}")

    if not source_path.is_file():
        reproducibility = "BLOCKED_SOURCE_MISSING"
    elif source_identity is None:
        reproducibility = "BLOCKED_SOURCE_CLOSURE_INVALID"
    elif source_label != receipt_version:
        reproducibility = "CURRENT_SOURCE_IS_DIFFERENT_VERSION_NOT_CREDITED_REBUILD"
    else:
        reproducibility = "SOURCE_CLOSURE_PRESENT_REBUILD_NOT_YET_CREDITED"

    report = {
        "schema": "mini-entity-native-provenance-check/v2",
        "version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "canonical_source": {
            "path": str(source_path.relative_to(root)),
            "status": source_status,
            "version_label": source_label,
            "root_sha256": source_identity.get("root_sha256") if source_identity else None,
            "closure_sha256": source_identity.get("closure_sha256") if source_identity else None,
            "closure_files": source_identity.get("files", []) if source_identity else [],
        },
        "binary": {
            "status": binary_status,
            "sha256": binary_hash,
        },
        "reproducibility": reproducibility,
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
