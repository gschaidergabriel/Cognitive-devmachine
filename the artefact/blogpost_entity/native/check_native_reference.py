#!/usr/bin/env python3
"""Fail-closed provenance gate for the credited native Mini Entity sandbox artifact.

This checker intentionally does not establish runtime correctness. It only binds the
currently credited version/hash across canonical state, the sandbox receipt and the
human-readable native reference, and refuses reproducibility credit while the native
source bytes are absent from the canonical repository.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


RECEIPT_NAME = "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
REFERENCE_NAME = "MINI_ENTITY_0_6_SANDBOX.md"
SOURCE_NAME = "mini_entity.c"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    source_hash = sha256_file(source_path) if source_path.is_file() else None

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

    reproducibility = "SOURCE_PRESENT" if source_path.is_file() else "BLOCKED_SOURCE_MISSING"
    if not source_path.is_file() and not args.allow_missing_source:
        errors.append("CANONICAL_NATIVE_SOURCE_MISSING")

    report = {
        "schema": "mini-entity-native-provenance-check/v1",
        "version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "canonical_source": {
            "path": str(source_path.relative_to(root)),
            "status": source_status,
            "sha256": source_hash,
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
