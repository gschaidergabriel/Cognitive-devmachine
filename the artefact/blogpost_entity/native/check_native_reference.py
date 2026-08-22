#!/usr/bin/env python3
"""Fail-closed provenance gate for the credited native Mini Entity sandbox artifact.

This checker intentionally does not establish runtime correctness. It binds the credited
artifact identity to canonical state/receipt/reference evidence and refuses source
reproducibility credit unless the credited receipt itself binds the complete local source
closure. A newer source tree merely existing at mini_entity.c is not evidence for an older
credited artifact.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from native_source_closure import (
    declared_mini_version,
    describe_source_closure,
    source_closure_sha256,
)


RECEIPT_NAME = "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
REFERENCE_NAME = "MINI_ENTITY_0_6_SANDBOX.md"
SOURCE_NAME = "mini_entity.c"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def credited_source_closure_sha(receipt: dict[str, Any]) -> str | None:
    direct = receipt.get("source_closure_sha256")
    if isinstance(direct, str) and direct:
        return direct
    build = receipt.get("build_definition")
    if isinstance(build, dict):
        closure = build.get("source_closure")
        if isinstance(closure, dict):
            value = closure.get("sha256")
            if isinstance(value, str) and value:
                return value
    return None


def classify_source(receipt_version: str, receipt: dict[str, Any], source_path: Path) -> dict[str, Any]:
    if not source_path.is_file():
        return {
            "status": "MISSING",
            "entry_sha256": None,
            "declared_version": None,
            "closure_sha256": None,
            "closure_files": [],
            "credited_closure_sha256": credited_source_closure_sha(receipt),
            "reproducibility": "BLOCKED_SOURCE_MISSING",
            "error": "CANONICAL_NATIVE_SOURCE_MISSING",
        }
    try:
        closure = describe_source_closure(source_path)
        closure_sha = source_closure_sha256(closure)
        source_version = declared_mini_version(source_path)
    except (OSError, UnicodeError, ValueError) as exc:
        return {
            "status": "INVALID",
            "entry_sha256": sha256_file(source_path),
            "declared_version": None,
            "closure_sha256": None,
            "closure_files": [],
            "credited_closure_sha256": credited_source_closure_sha(receipt),
            "reproducibility": "BLOCKED_SOURCE_CLOSURE_INVALID",
            "error": "CANONICAL_SOURCE_CLOSURE_INVALID:" + str(exc),
        }

    credited_closure = credited_source_closure_sha(receipt)
    base = {
        "status": "PRESENT",
        "entry_sha256": sha256_file(source_path),
        "declared_version": source_version,
        "closure_sha256": closure_sha,
        "closure_files": closure,
        "credited_closure_sha256": credited_closure,
    }
    if source_version != receipt_version:
        return {
            **base,
            "reproducibility": "BLOCKED_SOURCE_VERSION_MISMATCH",
            "error": f"CANONICAL_SOURCE_VERSION_MISMATCH expected={receipt_version} observed={source_version}",
        }
    if credited_closure is None:
        return {
            **base,
            "reproducibility": "BLOCKED_CREDITED_SOURCE_CLOSURE_UNRECORDED",
            "error": "CREDITED_RECEIPT_HAS_NO_SOURCE_CLOSURE_IDENTITY",
        }
    if credited_closure != closure_sha:
        return {
            **base,
            "reproducibility": "BLOCKED_SOURCE_CLOSURE_MISMATCH",
            "error": f"SOURCE_CLOSURE_HASH_MISMATCH expected={credited_closure} observed={closure_sha}",
        }
    return {**base, "reproducibility": "SOURCE_CLOSURE_BOUND", "error": None}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, help="Optional mini_entity.clay ELF to byte-verify")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Report a genuinely missing canonical native source without failing the process",
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

    source = classify_source(receipt_version, receipt, source_path)
    source_error = source.pop("error")
    if source_error is not None:
        genuinely_missing_and_allowed = (
            source["reproducibility"] == "BLOCKED_SOURCE_MISSING" and args.allow_missing_source
        )
        if not genuinely_missing_and_allowed:
            errors.append(source_error)

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
        "schema": "mini-entity-native-provenance-check/v2",
        "version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "canonical_source": source,
        "binary": {
            "status": binary_status,
            "sha256": binary_hash,
        },
        "reproducibility": source["reproducibility"],
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
