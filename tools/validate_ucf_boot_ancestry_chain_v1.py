#!/usr/bin/env python3
"""Compose canonical UCF v1 with exact admitted J-Space/GWT boot ancestry.

This tool adds no receipt/state/truth authority. It first executes the current canonical
UCF validator and the current canonical boot+manifest+source-lock validator, then checks
that the UCF cycle actually descends from that admitted boot evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UCF_VALIDATOR = ROOT / "tools" / "validate_unified_cognitive_fabric_receipt_v1.py"
BOOT_VALIDATOR = ROOT / "the artefact" / "blogpost_entity" / "jspace_gwt" / "validate_jspace_gwt_boot_binding_v1.py"


class ChainError(ValueError):
    pass


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ChainError(f"IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate_chain(
    cycle: dict[str, Any],
    boot_receipt: dict[str, Any],
    boot_manifest: Path,
    boot_source_lock: dict[str, Any],
    *,
    ucf_validator: Any | None = None,
    boot_validator: Any | None = None,
) -> list[str]:
    errors: list[str] = []

    try:
        ucf = ucf_validator if ucf_validator is not None else _load(UCF_VALIDATOR, "canonical_ucf_v1")
        ucf.validate(cycle)
    except Exception as exc:
        return [f"UCF_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]

    try:
        boot = boot_validator if boot_validator is not None else _load(BOOT_VALIDATOR, "canonical_boot_v1")
        boot.validate(boot_receipt)
        boot.validate_manifest_binding(boot_receipt, boot_manifest, boot_source_lock)
    except Exception as exc:
        return [f"BOOT_VALIDATION_FAILED:{type(exc).__name__}:{exc}"]

    binding = cycle.get("binding", {})
    observed_boot_digest = canonical_sha256(boot_receipt)
    if binding.get("boot_binding_receipt_digest") != observed_boot_digest:
        errors.append("BOOT_RECEIPT_ANCESTRY_MISMATCH")

    source = cycle.get("source", {})
    boot_source = boot_receipt.get("source", {})
    if source.get("commit") != boot_source.get("main_sha"):
        errors.append("BOOT_SOURCE_COMMIT_MISMATCH")
    if source.get("tree") != boot_source.get("tree_sha"):
        errors.append("BOOT_SOURCE_TREE_MISMATCH")
    if boot_source.get("dirty") is not False:
        errors.append("BOOT_SOURCE_DIRTY_FOR_CYCLE")

    identity = cycle.get("identity", {})
    boot_identity = boot_receipt.get("zero_grf", {})
    if identity.get("zero_identity_digest") != boot_identity.get("zero_identity_sha256"):
        errors.append("BOOT_ZERO_IDENTITY_MISMATCH")
    if identity.get("grf_digest") != boot_identity.get("grf_sha256"):
        errors.append("BOOT_GRF_IDENTITY_MISMATCH")

    core = cycle.get("bundled_core", {})
    boot_core = boot_receipt.get("bundled_core", {})
    if core.get("manifest_digest") != boot_core.get("manifest_sha256"):
        errors.append("BOOT_CORE_MANIFEST_MISMATCH")
    if core.get("checkpoint_digest") != boot_core.get("checkpoint_sha256"):
        errors.append("BOOT_CORE_CHECKPOINT_MISMATCH")
    if core.get("tokenizer_digest") != boot_core.get("tokenizer_sha256"):
        errors.append("BOOT_CORE_TOKENIZER_MISMATCH")

    boot_jspace = boot_receipt.get("jspace", {})
    boot_gwt = boot_receipt.get("gwt", {})
    if core.get("jspace_profile_digest") != boot_jspace.get("jspace_profile_sha256"):
        errors.append("BOOT_JSPACE_PROFILE_MISMATCH")
    cycle_lens = core.get("lens_profile_digest")
    if cycle_lens is not None and cycle_lens != boot_jspace.get("lens_profile_sha256"):
        errors.append("BOOT_LENS_PROFILE_MISMATCH")
    if core.get("workspace_calibration_digest") != boot_gwt.get("calibration_sha256"):
        errors.append("BOOT_WORKSPACE_CALIBRATION_MISMATCH")

    # Runtime-byte identity is transitive here: current UCF v1 binds the exact bundled
    # manifest digest, while current boot admission requires manifest.runtime_digest ==
    # bundled_core.runtime_sha256. We deliberately do not invent a second runtime field.
    inference = cycle.get("inference", {})
    if inference.get("engine_class") == "claude_code":
        boot_claude = boot_receipt.get("claude_adapter", {})
        if boot_claude.get("enabled") is not True:
            errors.append("BOOT_CLAUDE_ADAPTER_DISABLED")
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
        print(json.dumps({"ok": False, "errors": [f"READ_ERROR:{type(exc).__name__}"]}, sort_keys=True))
        return 2
    if type(cycle) is not dict or type(boot_receipt) is not dict or type(source_lock) is not dict:
        print(json.dumps({"ok": False, "errors": ["TOP_LEVEL_OBJECTS_REQUIRED"]}, sort_keys=True))
        return 2

    errors = validate_chain(cycle, boot_receipt, args.boot_manifest, source_lock)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
