#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

This is host-language validation glue for the ClayCode contract in
research_entity/global/UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT_V1.clay.
It establishes source/mechanism evidence only; it does not mint runtime credit.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASSES = {"BUNDLED_08B", "CLAUDE_CODE", "ADAPTIVE_BACKEND", "NONE"}
JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY", "NONE"}
COST_CLASSES = {"LOCAL", "FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
EPISTEMIC = {"MEASURED_SUPPORTED", "UNKNOWN", "ERROR", "REFUTED"}
DECISIONS = {"ACCEPT", "REJECT", "UNKNOWN"}


class ReceiptError(ValueError):
    pass


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ReceiptError(f"{key}:OBJECT_REQUIRED")
    return value


def _str(parent: dict[str, Any], key: str, *, nonempty: bool = True) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or (nonempty and not value):
        raise ReceiptError(f"{key}:STRING_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise ReceiptError(f"{key}:BOOL_REQUIRED")
    return value


def _int(parent: dict[str, Any], key: str, *, minimum: int = 0) -> int:
    value = parent.get(key)
    if type(value) is not int or value < minimum:
        raise ReceiptError(f"{key}:INT_MIN_{minimum}_REQUIRED")
    return value


def _enum(parent: dict[str, Any], key: str, allowed: set[str]) -> str:
    value = _str(parent, key)
    if value not in allowed:
        raise ReceiptError(f"{key}:ENUM_INVALID:{value}")
    return value


def _hex(parent: dict[str, Any], key: str, regex: re.Pattern[str]) -> str:
    value = _str(parent, key)
    if not regex.fullmatch(value):
        raise ReceiptError(f"{key}:DIGEST_INVALID")
    return value


def _digest_list(parent: dict[str, Any], key: str) -> list[str]:
    value = parent.get(key)
    if not isinstance(value, list):
        raise ReceiptError(f"{key}:LIST_REQUIRED")
    for item in value:
        if not isinstance(item, str) or not HEX64.fullmatch(item):
            raise ReceiptError(f"{key}:DIGEST_LIST_INVALID")
    return value


def validate_receipt(r: dict[str, Any]) -> list[str]:
    if not isinstance(r, dict):
        raise ReceiptError("ROOT_OBJECT_REQUIRED")
    if r.get("schema") != "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1":
        raise ReceiptError("SCHEMA_MISMATCH")

    source = _obj(r, "source")
    _hex(source, "commit_sha", HEX40)
    _hex(source, "tree_sha", HEX40)
    _bool(source, "dirty")
    _str(source, "executor_identity")

    entity = _obj(r, "entity")
    _str(entity, "mini_entity_version")
    _str(entity, "entityos_version")
    _hex(entity, "zero_identity_digest", HEX64)
    _hex(entity, "grf_digest", HEX64)
    _int(entity, "generation", minimum=0)

    core = _obj(r, "bundled_core")
    for key in (
        "manifest_digest", "checkpoint_digest", "tokenizer_digest",
        "jspace_profile_digest", "lens_profile_digest", "workspace_calibration_digest",
    ):
        _hex(core, key, HEX64)

    workspace = _obj(r, "workspace")
    _hex(workspace, "before_digest", HEX64)
    _hex(workspace, "after_digest", HEX64)
    for key in (
        "gwt_admitted_digests", "gwt_winner_digests", "jspace_observation_digests",
        "hyperposition_digests", "claycode_digests", "omega_digests",
    ):
        _digest_list(workspace, key)
    _hex(workspace, "thalamus_decisions_digest", HEX64)
    _hex(workspace, "epq_telemetry_digest", HEX64)
    admitted = set(workspace["gwt_admitted_digests"])
    winners = set(workspace["gwt_winner_digests"])
    if not winners.issubset(admitted):
        raise ReceiptError("GWT_WINNER_NOT_ADMITTED")

    inference = _obj(r, "inference")
    engine = _enum(inference, "engine_class", ENGINE_CLASSES)
    jspace_mode = _enum(inference, "jspace_mode", JSPACE_MODES)
    _hex(inference, "capability_profile_digest", HEX64)
    _hex(inference, "inference_packet_digest", HEX64)
    _hex(inference, "candidate_result_digest", HEX64)
    authority = _str(inference, "candidate_authority")
    epistemic = _enum(inference, "epistemic_status", EPISTEMIC)
    if authority != "CANDIDATE_ONLY":
        raise ReceiptError("INFERENCE_AUTHORITY_ESCALATION")
    if engine == "CLAUDE_CODE" and jspace_mode != "COMPILED_EXTERNAL":
        raise ReceiptError("CLAUDE_JSPACE_MODE_MUST_BE_COMPILED_EXTERNAL")

    admission = _obj(r, "admission")
    free_only = _bool(admission, "free_only")
    cost_class = _enum(admission, "cost_class", COST_CLASSES)
    admitted_exec = _bool(admission, "admitted")
    secret_lookups = _int(admission, "secret_lookup_count", minimum=0)
    network_attempts = _int(admission, "network_attempt_count", minimum=0)
    reasons = admission.get("reason_codes")
    if not isinstance(reasons, list) or not all(isinstance(x, str) and x for x in reasons):
        raise ReceiptError("admission.reason_codes:STRING_LIST_REQUIRED")
    if free_only and cost_class in {"PAID", "SUBSCRIPTION", "UNKNOWN"}:
        if admitted_exec:
            raise ReceiptError("FREE_ONLY_COST_CLASS_ADMITTED")
        if secret_lookups != 0:
            raise ReceiptError("FREE_ONLY_SECRET_TOUCH")
        if network_attempts != 0:
            raise ReceiptError("FREE_ONLY_NETWORK_TOUCH")

    bindings = _obj(r, "bindings")
    zero_match = _bool(bindings, "zero_identity_match")
    manifest_match = _bool(bindings, "bundled_manifest_match")
    capability_match = _bool(bindings, "capability_match")
    stale_generation = _bool(bindings, "stale_generation")

    reconciliation = _obj(r, "reconciliation")
    decision = _enum(reconciliation, "decision", DECISIONS)
    canonical_write = _bool(reconciliation, "canonical_write")
    effect_authorized = _bool(reconciliation, "effect_authorized")
    rec_reasons = reconciliation.get("reason_codes")
    if not isinstance(rec_reasons, list) or not all(isinstance(x, str) and x for x in rec_reasons):
        raise ReceiptError("reconciliation.reason_codes:STRING_LIST_REQUIRED")

    binding_ok = zero_match and manifest_match and capability_match and not stale_generation
    if not binding_ok and (decision == "ACCEPT" or canonical_write or effect_authorized):
        raise ReceiptError("STALE_OR_MISMATCHED_BINDING_AUTHORITY")
    if decision != "ACCEPT" and (canonical_write or effect_authorized):
        raise ReceiptError("NON_ACCEPT_DECISION_HAS_AUTHORITY")
    if (canonical_write or effect_authorized) and epistemic != "MEASURED_SUPPORTED":
        raise ReceiptError("UNSUPPORTED_EPISTEMIC_AUTHORITY")

    replay = _obj(r, "replay")
    stochasticity_disabled = _bool(replay, "stochasticity_disabled")
    replay_performed = _bool(replay, "replay_performed")
    _hex(replay, "scheduler_input_digest", HEX64)
    _hex(replay, "scheduler_decision_digest", HEX64)
    replay_match = _bool(replay, "replay_match")
    if stochasticity_disabled and replay_performed and not replay_match:
        raise ReceiptError("DETERMINISTIC_REPLAY_MISMATCH")

    _hex(r, "terminal_result_digest", HEX64)
    return [
        "SOURCE_BINDING_VALID",
        "AUTHORITY_SPLIT_VALID",
        "FREE_ONLY_BOUNDARY_VALID",
        "RECONCILIATION_VALID",
        "REPLAY_BOUNDARY_VALID",
    ]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.receipt.read_text(encoding="utf-8"))
        checks = validate_receipt(data)
    except (OSError, json.JSONDecodeError, ReceiptError) as exc:
        print(json.dumps({"valid": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps({"valid": True, "checks": checks}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
