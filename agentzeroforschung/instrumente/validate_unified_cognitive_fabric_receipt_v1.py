#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

The Fabric-cycle receipt is downstream of JSPACE_GWT_BOOT_BINDING_RECEIPT/v1.
Runtime credit requires the exact predecessor boot receipt to be supplied, revalidated
by the canonical boot validator, digest-bound, and identity-consistent with the cycle.
A PASS still does not create model/product credit by itself.
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

RECEIPT_VERSION = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
BOOT_RECEIPT_SCHEMA = "JSPACE_GWT_BOOT_BINDING_RECEIPT/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASSES = {"BUNDLED_08B", "CLAUDE_CODE", "ADAPTIVE_BACKEND", "NONE"}
JSPACE_MODES = {
    "FULL_LOCAL_LATENT",
    "LOCAL_OBSERVE_ONLY",
    "COMPILED_EXTERNAL",
    "PLAIN_COMPATIBILITY",
    "NONE",
}
VALIDATION_DECISIONS = {"ACCEPT_CANDIDATE", "REJECT_CANDIDATE", "ABSTAIN", "ERROR"}


def _get(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    current: Any = receipt
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            errors.append(f"MISSING:{path}")
            return None
        current = current[part]
    return current


def _bool(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    value = _get(receipt, path, errors)
    if value is not None and type(value) is not bool:
        errors.append(f"TYPE_BOOL:{path}")
    return value


def _nonnegative_int(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    value = _get(receipt, path, errors)
    if value is not None and (type(value) is not int or value < 0):
        errors.append(f"TYPE_NONNEGATIVE_INT:{path}")
    return value


def _nonempty_string(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    value = _get(receipt, path, errors)
    if value is not None and (not isinstance(value, str) or not value.strip()):
        errors.append(f"TYPE_NONEMPTY_STRING:{path}")
    return value


def _digest(receipt: dict[str, Any], path: str, errors: list[str], *, nullable: bool = False) -> Any:
    value = _get(receipt, path, errors)
    if value is None and nullable:
        return value
    if value is not None and not (isinstance(value, str) and HEX64.fullmatch(value)):
        errors.append(f"DIGEST_INVALID:{path}")
    return value


def _list(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    value = _get(receipt, path, errors)
    if value is not None and not isinstance(value, list):
        errors.append(f"TYPE_LIST:{path}")
    return value


def canonical_json_sha256(value: Any) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_canonical_boot_validator():
    root = Path(__file__).resolve().parents[2]
    path = root / "the artefact" / "blogpost_entity" / "jspace_gwt" / "validate_jspace_gwt_boot_binding_v1.py"
    spec = importlib.util.spec_from_file_location("canonical_jspace_gwt_boot_binding_v1", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("BOOT_VALIDATOR_IMPORT_SPEC_FAILED")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _validate_boot_chain(
    receipt: dict[str, Any],
    boot_receipt: dict[str, Any] | None,
    errors: list[str],
    *,
    boot_validator: Any | None = None,
) -> None:
    binding = _get(receipt, "boot_binding", errors)
    if not isinstance(binding, dict):
        if binding is not None:
            errors.append("TYPE_OBJECT:boot_binding")
        return

    if binding.get("schema") != BOOT_RECEIPT_SCHEMA:
        errors.append("BOOT_BINDING_SCHEMA_MISMATCH")
    expected_digest = binding.get("receipt_sha256")
    if not (isinstance(expected_digest, str) and HEX64.fullmatch(expected_digest)):
        errors.append("BOOT_BINDING_DIGEST_INVALID")

    if boot_receipt is None:
        errors.append("BOOT_RECEIPT_EVIDENCE_REQUIRED")
        return
    if not isinstance(boot_receipt, dict):
        errors.append("BOOT_RECEIPT_NOT_OBJECT")
        return

    try:
        module = boot_validator if boot_validator is not None else _load_canonical_boot_validator()
        module.validate(boot_receipt)
    except Exception as exc:
        errors.append(f"BOOT_RECEIPT_VALIDATION_FAILED:{type(exc).__name__}:{exc}")
        return

    try:
        observed_digest = canonical_json_sha256(boot_receipt)
    except (TypeError, ValueError) as exc:
        errors.append(f"BOOT_RECEIPT_CANONICALIZATION_FAILED:{type(exc).__name__}")
        return
    if expected_digest != observed_digest:
        errors.append("BOOT_RECEIPT_DIGEST_MISMATCH")

    source = receipt.get("source", {})
    boot_source = boot_receipt.get("source", {})
    if boot_source.get("main_sha") != source.get("commit"):
        errors.append("BOOT_SOURCE_COMMIT_MISMATCH")
    if boot_source.get("tree_sha") != source.get("tree"):
        errors.append("BOOT_SOURCE_TREE_MISMATCH")
    if boot_source.get("dirty") is not False:
        errors.append("BOOT_SOURCE_DIRTY_FOR_CYCLE")

    core = receipt.get("bundled_core", {})
    boot_core = boot_receipt.get("bundled_core", {})
    core_pairs = (
        ("manifest_digest", "manifest_sha256", "BOOT_CORE_MANIFEST_MISMATCH"),
        ("checkpoint_digest", "checkpoint_sha256", "BOOT_CORE_CHECKPOINT_MISMATCH"),
        ("tokenizer_digest", "tokenizer_sha256", "BOOT_CORE_TOKENIZER_MISMATCH"),
        ("runtime_digest", "runtime_sha256", "BOOT_CORE_RUNTIME_MISMATCH"),
    )
    for cycle_key, boot_key, code in core_pairs:
        if core.get(cycle_key) != boot_core.get(boot_key):
            errors.append(code)

    identity = receipt.get("identity", {})
    boot_zero = boot_receipt.get("zero_grf", {})
    if identity.get("zero_digest") != boot_zero.get("zero_identity_sha256"):
        errors.append("BOOT_ZERO_IDENTITY_MISMATCH")
    if identity.get("grf_digest") != boot_zero.get("grf_sha256"):
        errors.append("BOOT_GRF_IDENTITY_MISMATCH")

    fabric = receipt.get("fabric", {})
    boot_jspace = boot_receipt.get("jspace", {})
    boot_gwt = boot_receipt.get("gwt", {})
    if fabric.get("lens_profile_digest") is not None and fabric.get("lens_profile_digest") != boot_jspace.get("lens_profile_sha256"):
        errors.append("BOOT_LENS_PROFILE_MISMATCH")
    if fabric.get("workspace_policy_digest") != boot_gwt.get("workspace_policy_sha256"):
        errors.append("BOOT_WORKSPACE_POLICY_MISMATCH")
    if fabric.get("workspace_calibration_digest") != boot_gwt.get("calibration_sha256"):
        errors.append("BOOT_WORKSPACE_CALIBRATION_MISMATCH")

    inference = receipt.get("inference", {})
    if inference.get("engine_class") == "CLAUDE_CODE":
        boot_claude = boot_receipt.get("claude_adapter", {})
        if inference.get("adapter_version") != boot_claude.get("adapter_version"):
            errors.append("BOOT_CLAUDE_ADAPTER_VERSION_MISMATCH")
        if inference.get("capability_profile_digest") != boot_claude.get("capability_profile_sha256"):
            errors.append("BOOT_CLAUDE_CAPABILITY_PROFILE_MISMATCH")


def validate_receipt(
    receipt: dict[str, Any],
    boot_receipt: dict[str, Any] | None = None,
    *,
    boot_validator: Any | None = None,
) -> list[str]:
    errors: list[str] = []

    if _get(receipt, "receipt_version", errors) != RECEIPT_VERSION:
        errors.append("BAD_RECEIPT_VERSION")

    commit = _get(receipt, "source.commit", errors)
    tree = _get(receipt, "source.tree", errors)
    dirty = _bool(receipt, "source.dirty", errors)
    if commit is not None and not (isinstance(commit, str) and HEX40.fullmatch(commit)):
        errors.append("SOURCE_COMMIT_INVALID")
    if tree is not None and not (isinstance(tree, str) and HEX40.fullmatch(tree)):
        errors.append("SOURCE_TREE_INVALID")
    if dirty is not False:
        errors.append("SOURCE_NOT_CLEAN")

    _nonempty_string(receipt, "runtime.entityos_version", errors)
    _nonempty_string(receipt, "runtime.mini_entity_version", errors)
    _nonnegative_int(receipt, "runtime.entity_generation", errors)

    for path in (
        "identity.zero_digest",
        "identity.grf_digest",
        "bundled_core.manifest_digest",
        "bundled_core.checkpoint_digest",
        "bundled_core.tokenizer_digest",
        "bundled_core.runtime_digest",
        "fabric.jspace_profile_digest",
        "fabric.workspace_policy_digest",
        "fabric.workspace_calibration_digest",
        "workspace.digest_before",
        "workspace.digest_after",
        "inference.capability_profile_digest",
        "inference.adapter_contract_digest",
        "inference.inference_packet_digest",
        "inference.candidate_result_digest",
        "validation.reconciliation_digest",
        "terminal_result_digest",
    ):
        _digest(receipt, path, errors)
    lens_digest = _digest(receipt, "fabric.lens_profile_digest", errors, nullable=True)

    candidates = _list(receipt, "workspace.gwt_candidates", errors)
    winners = _list(receipt, "workspace.gwt_winners", errors)
    for path in (
        "workspace.jspace_observation_refs",
        "workspace.thalamus_decisions",
        "workspace.epq_refs",
        "workspace.hyperposition_refs",
        "workspace.claycode_refs",
        "workspace.omega_refs",
    ):
        _list(receipt, path, errors)

    candidate_ids: set[str] = set()
    if isinstance(candidates, list):
        for index, candidate in enumerate(candidates):
            if not isinstance(candidate, dict):
                errors.append(f"GWT_CANDIDATE_NOT_OBJECT:{index}")
                continue
            candidate_id = candidate.get("candidate_id")
            if not isinstance(candidate_id, str) or not candidate_id:
                errors.append(f"GWT_CANDIDATE_ID_INVALID:{index}")
                continue
            if candidate_id in candidate_ids:
                errors.append("GWT_CANDIDATE_ID_DUPLICATE")
            candidate_ids.add(candidate_id)
    if isinstance(winners, list):
        winner_ids: set[str] = set()
        for winner in winners:
            if not isinstance(winner, str) or winner not in candidate_ids:
                errors.append("GWT_WINNER_NOT_CANDIDATE")
                continue
            if winner in winner_ids:
                errors.append("GWT_WINNER_DUPLICATE")
            winner_ids.add(winner)

    engine = _get(receipt, "inference.engine_class", errors)
    mode = _get(receipt, "inference.jspace_mode", errors)
    _nonempty_string(receipt, "inference.adapter_version", errors)
    local_activation = _bool(receipt, "inference.local_activation_access", errors)
    hidden_claim = _bool(receipt, "inference.external_hidden_state_claimed", errors)
    if engine not in ENGINE_CLASSES:
        errors.append("ENGINE_CLASS_INVALID")
    if mode not in JSPACE_MODES:
        errors.append("JSPACE_MODE_INVALID")
    if engine == "NONE" and mode != "NONE":
        errors.append("NONE_ENGINE_REQUIRES_NONE_MODE")
    if engine != "NONE" and mode == "NONE":
        errors.append("ACTIVE_ENGINE_CANNOT_USE_NONE_MODE")

    if engine == "CLAUDE_CODE" and mode != "COMPILED_EXTERNAL":
        errors.append("CLAUDE_MUST_BE_COMPILED_EXTERNAL")
    if engine == "BUNDLED_08B" and mode not in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}:
        errors.append("BUNDLED_CORE_MODE_INVALID")
    if mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"} and lens_digest is None:
        errors.append("LOCAL_JSPACE_REQUIRES_LENS_PROFILE")
    if mode == "FULL_LOCAL_LATENT" and local_activation is not True:
        errors.append("FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS")
    if mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY", "NONE"}:
        if local_activation is True:
            errors.append("EXTERNAL_MODE_CANNOT_CLAIM_LOCAL_ACTIVATION_ACCESS")
        if hidden_claim is not False:
            errors.append("EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")
    if engine == "CLAUDE_CODE" and hidden_claim is not False:
        errors.append("CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN")

    intervention = _get(receipt, "fabric.intervention", errors)
    if not isinstance(intervention, dict):
        if intervention is not None:
            errors.append("TYPE_OBJECT:fabric.intervention")
    else:
        executed = intervention.get("executed")
        if type(executed) is not bool:
            errors.append("TYPE_BOOL:fabric.intervention.executed")
        if executed is True:
            if mode != "FULL_LOCAL_LATENT":
                errors.append("INTERVENTION_REQUIRES_FULL_LOCAL_LATENT")
            for key in ("implementation_digest", "calibration_digest"):
                value = intervention.get(key)
                if not (isinstance(value, str) and HEX64.fullmatch(value)):
                    errors.append(f"INTERVENTION_{key.upper()}_REQUIRED")

    decision = _get(receipt, "validation.decision", errors)
    if decision not in VALIDATION_DECISIONS:
        errors.append("VALIDATION_DECISION_INVALID")
    attempted_state = _bool(receipt, "validation.candidate_attempted_direct_state_mutation", errors)
    attempted_effect = _bool(receipt, "validation.candidate_attempted_direct_effect", errors)
    state_write = _bool(receipt, "validation.canonical_state_write_committed", errors)
    effect_executed = _bool(receipt, "validation.effect_executed", errors)

    if attempted_state is True and state_write is True:
        errors.append("DIRECT_STATE_MUTATION_BYPASS")
    if attempted_effect is True and effect_executed is True:
        errors.append("DIRECT_EFFECT_BYPASS")
    if (attempted_state is True or attempted_effect is True) and decision == "ACCEPT_CANDIDATE":
        errors.append("DIRECT_AUTHORITY_ATTEMPT_ACCEPTED")
    if state_write is True and decision != "ACCEPT_CANDIDATE":
        errors.append("STATE_WRITE_WITHOUT_ACCEPT")
    if effect_executed is True and decision != "ACCEPT_CANDIDATE":
        errors.append("EFFECT_WITHOUT_ACCEPT")

    free_only = _bool(receipt, "execution_policy.free_only", errors)
    secret_touches = _nonnegative_int(receipt, "execution_policy.secret_touch_count", errors)
    network_touches = _nonnegative_int(receipt, "execution_policy.network_touch_count", errors)
    if free_only is True and (secret_touches != 0 or network_touches != 0):
        errors.append("FREE_ONLY_IO_VIOLATION")

    stale_values = [
        _bool(receipt, "freshness.stale_zero_identity", errors),
        _bool(receipt, "freshness.stale_bundled_manifest", errors),
        _bool(receipt, "freshness.stale_generation", errors),
    ]
    if any(value is True for value in stale_values):
        if decision == "ACCEPT_CANDIDATE" or state_write is True or effect_executed is True:
            errors.append("STALE_INPUT_ACCEPTED")

    _validate_boot_chain(receipt, boot_receipt, errors, boot_validator=boot_validator)
    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    parser.add_argument("--boot-receipt", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        boot_receipt = json.loads(args.boot_receipt.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"RECEIPT_READ_ERROR:{exc.__class__.__name__}"]}, sort_keys=True))
        return 2
    if not isinstance(receipt, dict):
        print(json.dumps({"ok": False, "errors": ["RECEIPT_ROOT_NOT_OBJECT"]}, sort_keys=True))
        return 2

    errors = validate_receipt(receipt, boot_receipt)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
