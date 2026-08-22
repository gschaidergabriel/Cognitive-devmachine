#!/usr/bin/env python3
"""Fail-closed provenance gate for the credited native Mini Entity 0.6 sandbox artifact.

This checker intentionally does not establish runtime correctness. It binds the
historically credited version/hash across canonical state, the sandbox receipt and the
human-readable native reference, then keeps that historical credit separate from any
newly recreated source line. Source presence or a matching version label alone is never
proof that those bytes produced the credited ELF.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from build_native_bound import sha256_file, source_closure, source_version_label


RECEIPT_NAME = "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
REFERENCE_NAME = "MINI_ENTITY_0_6_SANDBOX.md"
SOURCE_NAME = "mini_entity.c"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, help="Optional historical mini_entity.clay ELF to byte-verify")
    parser.add_argument(
        "--allow-missing-source",
        "--allow-unbound-source",
        dest="allow_unbound_source",
        action="store_true",
        help="Report missing/unbound historical source provenance without failing on that condition alone",
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
    source_entry_hash = sha256_file(source_path) if source_path.is_file() else None
    closure = None
    source_version = None
    source_error = None
    if source_path.is_file():
        try:
            closure = source_closure(source_path)
            source_version = source_version_label(source_path)
        except Exception as exc:
            source_error = f"{type(exc).__name__}:{exc}"
            errors.append("CANONICAL_SOURCE_INVALID:" + source_error)

    source_identity_hash = str(closure["sha256"]) if isinstance(closure, dict) else None
    source_lineage_match = source_version == receipt_version if source_version is not None else False

    credited_source_identity = receipt.get("source_identity_sha256")
    if credited_source_identity is None:
        source_provenance = receipt.get("source_provenance")
        if isinstance(source_provenance, dict):
            credited_source_identity = source_provenance.get("source_identity_sha256")
    if credited_source_identity is not None:
        credited_source_identity = str(credited_source_identity)

    source_identity_match = (
        credited_source_identity is not None
        and source_identity_hash is not None
        and credited_source_identity == source_identity_hash
    )

    provenance_error = None
    if not source_path.is_file():
        reproducibility = "BLOCKED_SOURCE_MISSING"
        provenance_error = "CANONICAL_NATIVE_SOURCE_MISSING"
    elif source_error is not None:
        reproducibility = "BLOCKED_SOURCE_INVALID"
    elif not source_lineage_match:
        reproducibility = "BLOCKED_HISTORICAL_SOURCE_LINEAGE_MISMATCH"
        provenance_error = (
            "CREDITED_BINARY_SOURCE_VERSION_MISMATCH "
            f"credited={receipt_version} canonical_source={source_version}"
        )
    elif credited_source_identity is None:
        reproducibility = "BLOCKED_CREDITED_SOURCE_IDENTITY_MISSING"
        provenance_error = "CREDITED_0_6_SOURCE_IDENTITY_MISSING"
    elif not source_identity_match:
        reproducibility = "BLOCKED_CREDITED_SOURCE_IDENTITY_MISMATCH"
        provenance_error = (
            f"CREDITED_SOURCE_IDENTITY_MISMATCH expected={credited_source_identity} "
            f"observed={source_identity_hash}"
        )
    else:
        reproducibility = "CREDITED_SOURCE_IDENTITY_BOUND"

    if provenance_error is not None and not args.allow_unbound_source:
        errors.append(provenance_error)

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

    report = {
        "schema": "mini-entity-native-provenance-check/v3",
        "credited_version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "credited_source_identity_sha256": credited_source_identity,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "canonical_source": {
            "path": str(source_path.relative_to(root)),
            "status": source_status,
            "entry_sha256": source_entry_hash,
            "identity_sha256": source_identity_hash,
            "version": source_version,
            "lineage_matches_credited_version": source_lineage_match,
            "identity_matches_credited_source": source_identity_match,
            "closure": closure,
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
