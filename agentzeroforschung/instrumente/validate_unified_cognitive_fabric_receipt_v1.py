#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

This validates receipt shape and authority invariants only. A PASS does not create
runtime/model/product credit; provenance still has to show that the receipt came
from the exact admitted executable path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

RECEIPT_VERSION = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
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


def validate_receipt(receipt: dict[str, Any]) -> list[str]:
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

    for path in ("runtime.entityos_version", "runtime.mini_entity_version"):
        value = _get(receipt, path, errors)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            errors.append(f"TYPE_NONEMPTY_STRING:{path}")
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
        "workspace.digest_before",
        "workspace.digest_after",
        "inference.inference_packet_digest",
        "inference.candidate_result_digest",
        "terminal_result_digest",
    ):
        _digest(receipt, path, errors)
    _digest(receipt, "fabric.lens_profile_digest", errors, nullable=True)

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
        for winner in winners:
            if not isinstance(winner, str) or winner not in candidate_ids:
                errors.append("GWT_WINNER_NOT_CANDIDATE")

    engine = _get(receipt, "inference.engine_class", errors)
    mode = _get(receipt, "inference.jspace_mode", errors)
    local_activation = _bool(receipt, "inference.local_activation_access", errors)
    hidden_claim = _bool(receipt, "inference.external_hidden_state_claimed", errors)
    if engine not in ENGINE_CLASSES:
        errors.append("ENGINE_CLASS_INVALID")
    if mode not in JSPACE_MODES:
        errors.append("JSPACE_MODE_INVALID")

    if engine == "CLAUDE_CODE":
        if mode != "COMPILED_EXTERNAL":
            errors.append("CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if hidden_claim is not False:
            errors.append("CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN")
    if engine == "BUNDLED_08B" and mode not in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}:
        errors.append("BUNDLED_CORE_MODE_INVALID")
    if mode == "FULL_LOCAL_LATENT" and local_activation is not True:
        errors.append("FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS")
    if mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY", "NONE"} and local_activation is True:
        errors.append("EXTERNAL_MODE_CANNOT_CLAIM_LOCAL_ACTIVATION_ACCESS")

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
    if not isinstance(decision, str) or not decision:
        errors.append("VALIDATION_DECISION_INVALID")
    attempted_state = _bool(receipt, "validation.candidate_attempted_direct_state_mutation", errors)
    attempted_effect = _bool(receipt, "validation.candidate_attempted_direct_effect", errors)
    state_write = _bool(receipt, "validation.canonical_state_write_committed", errors)
    effect_executed = _bool(receipt, "validation.effect_executed", errors)

    if attempted_state is True and state_write is True:
        errors.append("DIRECT_STATE_MUTATION_BYPASS")
    if attempted_effect is True and effect_executed is True:
        errors.append("DIRECT_EFFECT_BYPASS")
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

    return sorted(set(errors))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args(argv)
    try:
        raw = args.receipt.read_text(encoding="utf-8")
        receipt = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "errors": [f"RECEIPT_READ_ERROR:{exc.__class__.__name__}"]}, sort_keys=True))
        return 2
    if not isinstance(receipt, dict):
        print(json.dumps({"ok": False, "errors": ["RECEIPT_ROOT_NOT_OBJECT"]}, sort_keys=True))
        return 2

    errors = validate_receipt(receipt)
    print(json.dumps({"ok": not errors, "errors": errors}, sort_keys=True))
    return 0 if not errors else 2


if __name__ == "__main__":
    sys.exit(main())
