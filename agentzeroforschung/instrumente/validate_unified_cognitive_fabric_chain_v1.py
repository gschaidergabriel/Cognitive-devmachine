#!/usr/bin/env python3
"""Canonical ancestry gate for one Unified Cognitive Fabric runtime cycle.

This is composition, not a second boot or Fabric authority. It reuses the existing
canonical boot validator and the existing UCF structural validator, then requires the
cycle to cryptographically bind the exact boot receipt, bundled manifest and
repository-owned source lock that were admitted upstream.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from validate_unified_cognitive_fabric_receipt_v1 import (  # noqa: E402
    validate_receipt as validate_fabric_receipt,
)

BOOT_SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
HEX64 = re.compile(r"^[0-9a-f]{64}$")


class ChainError(ValueError):
    pass


def _canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _load_boot_validator():
    path = ROOT / "the artefact" / "blogpost_entity" / "jspace_gwt" / "validate_jspace_gwt_boot_binding_v1.py"
    spec = importlib.util.spec_from_file_location("canonical_jspace_gwt_boot_binding_v1", path)
    if spec is None or spec.loader is None:
        raise ChainError("BOOT_VALIDATOR_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _sha64(value: Any, code: str) -> str:
    if not isinstance(value, str) or HEX64.fullmatch(value) is None:
        raise ChainError(code)
    if value in {"0" * 64, "f" * 64}:
        raise ChainError(code + ":PLACEHOLDER_FORBIDDEN")
    return value


def validate_chain(
    cycle: dict[str, Any],
    boot_receipt: dict[str, Any],
    boot_manifest_path: Path,
    boot_source_lock: dict[str, Any],
    *,
    boot_validator: Any | None = None,
) -> list[str]:
    errors = list(validate_fabric_receipt(cycle))

    binding = cycle.get("boot_binding")
    if not isinstance(binding, dict):
        errors.append("BOOT_BINDING_OBJECT_REQUIRED")
        return sorted(set(errors))
    if binding.get("schema") != BOOT_SCHEMA:
        errors.append("BOOT_BINDING_SCHEMA_MISMATCH")
    try:
        expected_receipt = _sha64(binding.get("receipt_sha256"), "BOOT_BINDING_RECEIPT_DIGEST_INVALID")
        expected_manifest = _sha64(binding.get("manifest_file_sha256"), "BOOT_BINDING_MANIFEST_DIGEST_INVALID")
        expected_lock = _sha64(binding.get("source_lock_sha256"), "BOOT_BINDING_SOURCE_LOCK_DIGEST_INVALID")
    except ChainError as exc:
        errors.append(str(exc))
        return sorted(set(errors))

    if not isinstance(boot_receipt, dict):
        errors.append("BOOT_RECEIPT_OBJECT_REQUIRED")
        return sorted(set(errors))
    if not isinstance(boot_source_lock, dict):
        errors.append("BOOT_SOURCE_LOCK_OBJECT_REQUIRED")
        return sorted(set(errors))

    try:
        module = boot_validator if boot_validator is not None else _load_boot_validator()
        module.validate(boot_receipt)
        module.validate_manifest_binding(boot_receipt, boot_manifest_path, boot_source_lock)
    except Exception as exc:
        errors.append(f"BOOT_EVIDENCE_VALIDATION_FAILED:{type(exc).__name__}:{exc}")
        return sorted(set(errors))

    try:
        observed_receipt = _canonical_sha256(boot_receipt)
        observed_manifest = _file_sha256(boot_manifest_path)
        observed_lock = _canonical_sha256(boot_source_lock)
    except (OSError, TypeError, ValueError) as exc:
        errors.append(f"BOOT_EVIDENCE_CANONICALIZATION_FAILED:{type(exc).__name__}")
        return sorted(set(errors))

    if observed_receipt != expected_receipt:
        errors.append("BOOT_RECEIPT_DIGEST_MISMATCH")
    if observed_manifest != expected_manifest:
        errors.append("BOOT_MANIFEST_DIGEST_MISMATCH")
    if observed_lock != expected_lock:
        errors.append("BOOT_SOURCE_LOCK_DIGEST_MISMATCH")

    source = cycle.get("source", {})
    boot_source = boot_receipt.get("source", {})
    if boot_source.get("main_sha") != source.get("commit"):
        errors.append("BOOT_SOURCE_COMMIT_MISMATCH")
    if boot_source.get("tree_sha") != source.get("tree"):
        errors.append("BOOT_SOURCE_TREE_MISMATCH")
    if boot_source.get("dirty") is not False:
        errors.append("BOOT_SOURCE_DIRTY_FOR_CYCLE")

    core = cycle.get("bundled_core", {})
    boot_core = boot_receipt.get("bundled_core", {})
    for cycle_key, boot_key, code in (
        ("manifest_digest", "manifest_sha256", "BOOT_CORE_MANIFEST_MISMATCH"),
        ("checkpoint_digest", "checkpoint_sha256", "BOOT_CORE_CHECKPOINT_MISMATCH"),
        ("tokenizer_digest", "tokenizer_sha256", "BOOT_CORE_TOKENIZER_MISMATCH"),
        ("runtime_digest", "runtime_sha256", "BOOT_CORE_RUNTIME_MISMATCH"),
    ):
        if core.get(cycle_key) != boot_core.get(boot_key):
            errors.append(code)

    identity = cycle.get("identity", {})
    boot_identity = boot_receipt.get("zero_grf", {})
    if identity.get("zero_digest") != boot_identity.get("zero_identity_sha256"):
        errors.append("BOOT_ZERO_IDENTITY_MISMATCH")
    if identity.get("grf_digest") != boot_identity.get("grf_sha256"):
        errors.append("BOOT_GRF_IDENTITY_MISMATCH")

    fabric = cycle.get("fabric", {})
    boot_jspace = boot_receipt.get("jspace", {})
    boot_gwt = boot_receipt.get("gwt", {})
    if fabric.get("jspace_profile_digest") != boot_jspace.get("jspace_profile_sha256"):
        errors.append("BOOT_JSPACE_PROFILE_MISMATCH")
    if fabric.get("lens_profile_digest") is not None and fabric.get("lens_profile_digest") != boot_jspace.get("lens_profile_sha256"):
        errors.append("BOOT_LENS_PROFILE_MISMATCH")
    if fabric.get("workspace_policy_digest") != boot_gwt.get("workspace_policy_sha256"):
        errors.append("BOOT_WORKSPACE_POLICY_MISMATCH")
    if fabric.get("workspace_calibration_digest") != boot_gwt.get("calibration_sha256"):
        errors.append("BOOT_WORKSPACE_CALIBRATION_MISMATCH")

    inference = cycle.get("inference", {})
    if inference.get("engine_class") == "CLAUDE_CODE":
        boot_claude = boot_receipt.get("claude_adapter", {})
        if inference.get("adapter_version") != boot_claude.get("adapter_version"):
            errors.append("BOOT_CLAUDE_ADAPTER_VERSION_MISMATCH")
        if inference.get("capability_profile_digest") != boot_claude.get("capability_profile_sha256"):
            errors.append("BOOT_CLAUDE_CAPABILITY_PROFILE_MISMATCH")

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cycle", type=Path)
    parser.add_argument("boot_receipt", type=Path)
    parser.add_argument("boot_manifest", type=Path)
    parser.add_argument("boot_source_lock", type=Path)
    args = parser.parse_args(argv)
    try:
        cycle = json.loads(args.cycle.read_text(encoding="utf-8"))
        boot_receipt = json.loads(args.boot_receipt.read_text(encoding="utf-8"))
        source_lock = json.loads(args.boot_source_lock.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"READ_ERROR:{exc.__class__.__name__}"]}, sort_keys=True))
        return 2
    if not isinstance(cycle, dict) or not isinstance(boot_receipt, dict) or not isinstance(source_lock, dict):
        print(json.dumps({"ok": False, "errors": ["TOP_LEVEL_OBJECTS_REQUIRED"]}, sort_keys=True))
        return 2
    errors = validate_chain(cycle, boot_receipt, args.boot_manifest, source_lock)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
