#!/usr/bin/env python3
"""Fail-closed consistency gate for the credited native Mini Entity 0.6 artifact.

This checker does not establish runtime correctness or prove that a supplied binary was
built from the current canonical source. It binds the credited historical version/hash
across canonical records and reports whether current canonical source is even a compatible
rebuild candidate. Source presence alone is never reproducibility credit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

from build_native_bound import source_closure


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


def credited_state_identity(native_state: dict) -> tuple[str, str, str]:
    """Read one historical credited identity across native-state schema evolution."""
    if "historical_credited_version" in native_state or "historical_binary_sha256" in native_state:
        version = native_state.get("historical_credited_version")
        digest = native_state.get("historical_binary_sha256")
        schema = "historical_explicit"
    else:
        version = native_state.get("version")
        digest = native_state.get("binary_sha256")
        schema = "legacy_generic"
    missing = []
    if not isinstance(version, str) or not version:
        missing.append("version")
    if not isinstance(digest, str) or not digest:
        missing.append("binary_sha256")
    if missing:
        raise RuntimeError("PROGRAM_STATE_CREDITED_NATIVE_IDENTITY_MISSING:" + ",".join(missing))
    return version, digest, schema


def credited_state_record(state: dict) -> tuple[dict, str]:
    """Locate the historical 0.6 identity without confusing it with current 0.7 evidence.

    Older PROGRAM_STATE schemas stored the credited native record under
    sandbox_evidence.native_pipeline. Current schema 7.9 moved the active line to native_0_7
    and retains a historical_source_bound_evidence object, but that object currently binds a
    different pre-fix 0.7 artifact and does not identify the credited 0.6 receipt. Never reuse
    its elf_sha256 as though it were the 0.6 binary. If future current-state bytes add explicit
    historical_credited_version/historical_binary_sha256 fields, they are safe to consume.
    """
    sandbox = state.get("sandbox_evidence")
    if isinstance(sandbox, dict):
        old = sandbox.get("native_pipeline")
        if isinstance(old, dict):
            return old, "sandbox_evidence.native_pipeline"

    current = state.get("native_0_7")
    if isinstance(current, dict):
        hist = current.get("historical_source_bound_evidence")
        if isinstance(hist, dict):
            if "historical_credited_version" in hist or "historical_binary_sha256" in hist:
                return hist, "native_0_7.historical_source_bound_evidence"
            raise RuntimeError(
                "PROGRAM_STATE_CREDITED_0_6_IDENTITY_UNBOUND_IN_CURRENT_SCHEMA:native_0_7"
            )

    raise RuntimeError("PROGRAM_STATE_NATIVE_IDENTITY_SECTION_MISSING")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--binary", type=Path, help="Optional mini_entity.clay ELF to byte-verify")
    parser.add_argument(
        "--allow-missing-source",
        action="store_true",
        help="Report missing canonical native source without failing the historical consistency check",
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

    errors: list[str] = []
    state_record_path = "UNRESOLVED"
    try:
        native_state, state_record_path = credited_state_record(state)
        state_version, state_hash, state_identity_schema = credited_state_identity(native_state)
    except RuntimeError as exc:
        errors.append(str(exc))
        state_version = "UNRESOLVED"
        state_hash = "UNRESOLVED"
        state_identity_schema = "UNRESOLVED"
    receipt_version = str(receipt["version"])
    receipt_hash = str(receipt["binary_sha256"])

    if state_version != "UNRESOLVED" and state_version != receipt_version:
        errors.append(f"VERSION_MISMATCH state={state_version} receipt={receipt_version}")
    if state_hash != "UNRESOLVED" and state_hash != receipt_hash:
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
            source_identity = source_closure(source_path)
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
        "schema": "mini-entity-native-provenance-check/v3",
        "version": receipt_version,
        "credited_binary_sha256": receipt_hash,
        "program_state_record_path": state_record_path,
        "program_state_identity_schema": state_identity_schema,
        "state_receipt_hash_match": state_hash == receipt_hash,
        "reference_binds_credited_hash": receipt_hash in reference,
        "canonical_source": {
            "path": str(source_path.relative_to(root)),
            "status": source_status,
            "version_label": source_label,
            "entry_sha256": sha256_file(source_path) if source_path.is_file() else None,
            "closure_sha256": source_identity.get("sha256") if source_identity else None,
            "closure_files": source_identity.get("files", []) if source_identity else [],
        },
        "binary": {
            "status": binary_status,
            "sha256": binary_hash,
        },
        "source_build_binding": "NOT_PROVEN_BY_THIS_CHECKER",
        "reproducibility": reproducibility,
        "errors": errors,
        "pass": not errors,
    }
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
