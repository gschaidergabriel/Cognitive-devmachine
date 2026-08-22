#!/usr/bin/env python3
"""Fail-closed provenance gate for the historically credited native Mini Entity artifact.

This checker intentionally does not establish runtime correctness. It binds the historical
credited version/hash across canonical state, the sandbox receipt and the human-readable
reference. A newer canonical source line is reported explicitly and must never be mistaken
for the source that produced the historical credited ELF.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_native_bound import sha256_file, source_closure, source_version_label


RECEIPT_NAME = "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
REFERENCE_NAME = "MINI_ENTITY_0_6_SANDBOX.md"
SOURCE_NAME = "mini_entity.c"


def _historical_state_identity(native_state: dict) -> tuple[str | None, str | None]:
    """Support the current explicit historical fields and the bounded older state schema."""
    version = native_state.get("historical_credited_version", native_state.get("version"))
    digest = native_state.get("historical_binary_sha256", native_state.get("binary_sha256"))
    return (str(version) if version is not None else None, str(digest) if digest is not None else None)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, help="Optional historical mini_entity.clay ELF to byte-verify")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Report missing canonical native source without adding a missing-source error",
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
    state_version, state_hash = _historical_state_identity(native_state)
    receipt_version = str(receipt["version"])
    receipt_hash = str(receipt["binary_sha256"])

    errors: list[str] = []
    if state_version is None:
        errors.append("STATE_HISTORICAL_VERSION_MISSING")
    elif state_version != receipt_version:
        errors.append(f"VERSION_MISMATCH state={state_version} receipt={receipt_version}")
    if state_hash is None:
        errors.append("STATE_HISTORICAL_HASH_MISSING")
    elif state_hash != receipt_hash:
        errors.append(f"HASH_MISMATCH state={state_hash} receipt={receipt_hash}")
    if receipt_hash not in reference:
        errors.append("REFERENCE_DOES_NOT_BIND_CREDITED_HASH")
    if receipt_version not in reference:
        errors.append("REFERENCE_DOES_NOT_BIND_CREDITED_VERSION")

    source_status = "PRESENT" if source_path.is_file() else "MISSING"
    source_entry_hash = sha256_file(source_path) if source_path.is_file() else None
    closure = None
    current_source_version = None
    source_error = None
    if source_path.is_file():
        try:
            closure = source_closure(source_path)
            current_source_version = source_version_label(source_path, closure)
        except Exception as exc:
            source_error = f"{type(exc).__name__}:{exc}"
            errors.append("CANONICAL_SOURCE_INVALID:" + source_error)

    source_lineage_matches = current_source_version == receipt_version if current_source_version is not None else False
    if current_source_version is not None and not source_lineage_matches:
        errors.append(
            "CREDITED_BINARY_SOURCE_VERSION_MISMATCH "
            f"credited={receipt_version} canonical_source={current_source_version}"
        )

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
        if not args.allow_missing_source:
            errors.append("CANONICAL_NATIVE_SOURCE_MISSING")
    elif source_error is not None:
        reproducibility = "BLOCKED_SOURCE_INVALID"
    elif not source_lineage_matches:
        reproducibility = "BLOCKED_HISTORICAL_SOURCE_LINEAGE_MISMATCH"
    elif binary_status == "MATCH":
        reproducibility = "SOURCE_LINEAGE_AND_CREDITED_BINARY_MATCH"
    else:
        reproducibility = "SOURCE_LINEAGE_MATCH_BUILD_NOT_BYTE_VERIFIED"

    report = {
        "schema": "mini-entity-native-provenance-check/v2",
        "credited_version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "state_receipt_version_match": state_version == receipt_version,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "reference_binds_credited_version": receipt_version in reference,
        "canonical_source": {
            "path": str(source_path.relative_to(root)),
            "status": source_status,
            "entry_sha256": source_entry_hash,
            "version": current_source_version,
            "lineage_matches_credited_version": source_lineage_matches,
            "source_identity_sha256": closure.get("sha256") if closure else None,
            "closure_file_count": len(closure.get("files", [])) if closure else 0,
            "error": source_error,
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
