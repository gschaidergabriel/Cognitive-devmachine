#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

This validates receipt shape and authority invariants only. A PASS does not create
runtime/model/product credit; provenance still has to show that the receipt came
from the exact admitted executable path.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

RECEIPT_VERSION = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASSES = {"BUNDLED_08B", "CLAUDE_CODE", "ADAPTIVE_BACKEND", "NONE"}
JSPACE_MODES = {
    "FULL_LOCAL_LATENT",
    "LOCAL_OBSERVE_ONLY",
    "COMPILED_EXTERNAL",
    "PLAIN_COMPATIBILITY",
    "NONE",
}
COST_CLASSES = {"LOCAL", "FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
EPISTEMIC_STATUSES = {"MEASURED_SUPPORTED", "UNKNOWN", "ERROR", "REFUTED", "NOT_APPLICABLE"}
VALIDATION_DECISIONS = {"ACCEPT_CANDIDATE", "REJECT_CANDIDATE", "ABSTAIN", "ERROR", "BLOCKED"}


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
    if value is not None and (type(value) is not str or not value.strip()):
        errors.append(f"TYPE_NONEMPTY_STRING:{path}")
    return value


def _digest(receipt: dict[str, Any], path: str, errors: list[str], *, nullable: bool = False) -> Any:
    value = _get(receipt, path, errors)
    if value is None and nullable:
        return value
    if value is not None and not (type(value) is str and HEX64.fullmatch(value)):
        errors.append(f"DIGEST_INVALID:{path}")
    return value


def _list(receipt: dict[str, Any], path: str, errors: list[str]) -> Any:
    value = _get(receipt, path, errors)
    if value is not None and type(value) is not list:
        errors.append(f"TYPE_LIST:{path}")
    return value


def _finite_json(value: Any, errors: list[str], path: str = "$") -> None:
    t = type(value)
    if value is None or t in {str, bool, int}:
        return
    if t is float:
        if not math.isfinite(value):
            errors.append(f"NONFINITE_JSON:{path}")
        return
    if t is list:
        for index, item in enumerate(value):
            _finite_json(item, errors, f"{path}[{index}]")
        return
    if t is dict:
        for key, item in value.items():
            if type(key) is not str:
                errors.append(f"NONSTRING_JSON_KEY:{path}")
                continue
            _finite_json(item, errors, f"{path}.{key}")
        return
    errors.append(f"UNSUPPORTED_JSON_TYPE:{path}:{t.__name__}")


def canonical_receipt_digest(receipt: dict[str, Any]) -> str:
    material = copy.deepcopy(receipt)
    material.pop("receipt_envelope_digest", None)
    payload = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if type(receipt) is not dict:
        return ["RECEIPT_ROOT_NOT_OBJECT"]
    _finite_json(receipt, errors)

    if _get(receipt, "receipt_version", errors) != RECEIPT_VERSION:
        errors.append("BAD_RECEIPT_VERSION")

    commit = _get(receipt, "source.commit", errors)
    tree = _get(receipt, "source.tree", errors)
    dirty = _bool(receipt, "source.dirty", errors)
    if commit is not None and not (type(commit) is str and GIT_OID.fullmatch(commit)):
        errors.append("SOURCE_COMMIT_INVALID")
    if tree is not None and not (type(tree) is str and GIT_OID.fullmatch(tree)):
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
        "validation.reconciliation_digest",
        "execution_policy.policy_authority_digest",
        "terminal_result_digest",
        "receipt_envelope_digest",
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
            if type(candidate) is not dict:
                errors.append(f"GWT_CANDIDATE_NOT_OBJECT:{index}")
                continue
            candidate_id = candidate.get("candidate_id")
            if type(candidate_id) is not str or not candidate_id:
                errors.append(f"GWT_CANDIDATE_ID_INVALID:{index}")
                continue
            if candidate_id in candidate_ids:
                errors.append("GWT_CANDIDATE_ID_DUPLICATE")
            candidate_ids.add(candidate_id)
    if isinstance(winners, list):
        winner_ids: set[str] = set()
        for winner in winners:
            if type(winner) is not str or winner not in candidate_ids:
                errors.append("GWT_WINNER_NOT_CANDIDATE")
                continue
            if winner in winner_ids:
                errors.append("GWT_WINNER_DUPLICATE")
            winner_ids.add(winner)

    engine = _get(receipt, "inference.engine_class", errors)
    mode = _get(receipt, "inference.jspace_mode", errors)
    executed = _bool(receipt, "inference.executed", errors)
    epistemic_status = _get(receipt, "inference.epistemic_status", errors)
    _nonempty_string(receipt, "inference.adapter_version", errors)
    local_activation = _bool(receipt, "inference.local_activation_access", errors)
    hidden_claim = _bool(receipt, "inference.external_hidden_state_claimed", errors)
    result_digest = _digest(receipt, "inference.candidate_result_digest", errors, nullable=True)

    if engine not in ENGINE_CLASSES:
        errors.append("ENGINE_CLASS_INVALID")
    if mode not in JSPACE_MODES:
        errors.append("JSPACE_MODE_INVALID")
    if epistemic_status not in EPISTEMIC_STATUSES:
        errors.append("EPISTEMIC_STATUS_INVALID")

    if engine == "NONE":
        if mode != "NONE":
            errors.append("NONE_ENGINE_REQUIRES_NONE_MODE")
        if executed is True:
            errors.append("NONE_ENGINE_CANNOT_EXECUTE_INFERENCE")
    elif mode == "NONE":
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

    if executed is True:
        if result_digest is None:
            errors.append("EXECUTED_INFERENCE_REQUIRES_RESULT_DIGEST")
        if epistemic_status == "NOT_APPLICABLE":
            errors.append("EXECUTED_INFERENCE_REQUIRES_EPISTEMIC_STATUS")
    elif executed is False:
        if result_digest is not None:
            errors.append("NONEXECUTED_INFERENCE_RESULT_DIGEST_MUST_BE_NULL")
        if epistemic_status != "NOT_APPLICABLE":
            errors.append("NONEXECUTED_INFERENCE_EPISTEMIC_STATUS_MUST_BE_NOT_APPLICABLE")

    intervention = _get(receipt, "fabric.intervention", errors)
    if type(intervention) is not dict:
        if intervention is not None:
            errors.append("TYPE_OBJECT:fabric.intervention")
    else:
        intervention_executed = intervention.get("executed")
        if type(intervention_executed) is not bool:
            errors.append("TYPE_BOOL:fabric.intervention.executed")
        if intervention_executed is True:
            if executed is not True:
                errors.append("INTERVENTION_REQUIRES_EXECUTED_INFERENCE")
            if mode != "FULL_LOCAL_LATENT":
                errors.append("INTERVENTION_REQUIRES_FULL_LOCAL_LATENT")
            if local_activation is not True:
                errors.append("INTERVENTION_REQUIRES_ACTIVATION_ACCESS")
            for key in ("implementation_digest", "calibration_digest"):
                value = intervention.get(key)
                if not (type(value) is str and HEX64.fullmatch(value)):
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
    if decision == "ACCEPT_CANDIDATE" and executed is not True:
        errors.append("ACCEPT_WITHOUT_EXECUTED_INFERENCE")
    if state_write is True and decision != "ACCEPT_CANDIDATE":
        errors.append("STATE_WRITE_WITHOUT_ACCEPT")
    if effect_executed is True and decision != "ACCEPT_CANDIDATE":
        errors.append("EFFECT_WITHOUT_ACCEPT")
    if (state_write is True or effect_executed is True) and epistemic_status != "MEASURED_SUPPORTED":
        errors.append("UNSUPPORTED_EPISTEMIC_AUTHORITY")

    free_only = _bool(receipt, "execution_policy.free_only", errors)
    cost_class = _get(receipt, "execution_policy.cost_class", errors)
    backend_admitted = _bool(receipt, "execution_policy.backend_admitted", errors)
    secret_touches = _nonnegative_int(receipt, "execution_policy.secret_touch_count", errors)
    network_touches = _nonnegative_int(receipt, "execution_policy.network_touch_count", errors)
    if cost_class not in COST_CLASSES:
        errors.append("COST_CLASS_INVALID")

    if executed is True and backend_admitted is not True:
        errors.append("INFERENCE_EXECUTED_WITHOUT_BACKEND_ADMISSION")
    if engine == "NONE" and backend_admitted is True:
        errors.append("NONE_ENGINE_BACKEND_ADMISSION_INVALID")
    if free_only is True and cost_class in {"PAID", "SUBSCRIPTION", "UNKNOWN"}:
        if backend_admitted is True:
            errors.append("FREE_ONLY_NONFREE_BACKEND_ADMITTED")
        if secret_touches != 0:
            errors.append("FREE_ONLY_SECRET_TOUCH")
        if network_touches != 0:
            errors.append("FREE_ONLY_NETWORK_TOUCH")

    stale_values = [
        _bool(receipt, "freshness.stale_zero_identity", errors),
        _bool(receipt, "freshness.stale_bundled_manifest", errors),
        _bool(receipt, "freshness.stale_generation", errors),
    ]
    if any(value is True for value in stale_values):
        if backend_admitted is True or executed is True or decision == "ACCEPT_CANDIDATE" or state_write is True or effect_executed is True:
            errors.append("STALE_INPUT_AUTHORITY_OR_EXECUTION")

    envelope_digest = _get(receipt, "receipt_envelope_digest", errors)
    if type(envelope_digest) is str and HEX64.fullmatch(envelope_digest):
        try:
            expected_digest = canonical_receipt_digest(receipt)
        except (TypeError, ValueError):
            errors.append("RECEIPT_ENVELOPE_CANONICALIZATION_ERROR")
        else:
            if envelope_digest != expected_digest:
                errors.append("RECEIPT_ENVELOPE_DIGEST_MISMATCH")

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.receipt.read_text(encoding="utf-8")
        receipt = json.loads(
            raw,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"NONFINITE_JSON_CONSTANT:{value}")),
        )
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"ok": False, "errors": [f"RECEIPT_READ_ERROR:{exc.__class__.__name__}"]}, sort_keys=True))
        return 2
    if type(receipt) is not dict:
        print(json.dumps({"ok": False, "errors": ["RECEIPT_ROOT_NOT_OBJECT"]}, sort_keys=True))
        return 2

    errors = validate_receipt(receipt)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
