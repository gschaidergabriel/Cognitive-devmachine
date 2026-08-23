#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

This is host-language admission glue for a ClayCode semantic contract. It does not
claim J-Space/GWT behavior exists; it only rejects receipts that would over-credit
or violate the current Mini Entity/EntityOS authority boundaries.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from typing import Any

SCHEMA = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASSES = {"local_08b", "claude_code", "adaptive_backend"}
COST_CLASSES = {"LOCAL", "FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
VALIDATION_DECISIONS = {"ACCEPT", "REJECT", "BLOCKED"}


class ReceiptError(ValueError):
    pass


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise ReceiptError(f"{key}:OBJECT_REQUIRED")
    return value


def _list(parent: dict[str, Any], key: str, *, nonempty: bool = False) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list) or (nonempty and not value):
        raise ReceiptError(f"{key}:LIST_REQUIRED")
    return value


def _text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if not isinstance(value, str) or not value:
        raise ReceiptError(f"{key}:TEXT_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if not isinstance(value, bool):
        raise ReceiptError(f"{key}:BOOL_REQUIRED")
    return value


def _count(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ReceiptError(f"{key}:NONNEGATIVE_INT_REQUIRED")
    return value


def _hex(parent: dict[str, Any], key: str, pattern: re.Pattern[str]) -> str:
    value = _text(parent, key)
    if pattern.fullmatch(value) is None:
        raise ReceiptError(f"{key}:DIGEST_FORMAT")
    return value


def canonical_digest(receipt: dict[str, Any]) -> str:
    encoded = json.dumps(receipt, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return hashlib.sha256(encoded).hexdigest()


def validate(receipt: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(receipt, dict):
        raise ReceiptError("ROOT_OBJECT_REQUIRED")
    if receipt.get("schema") != SCHEMA:
        raise ReceiptError("SCHEMA_MISMATCH")

    source = _obj(receipt, "source")
    runtime = _obj(receipt, "runtime")
    identity = _obj(receipt, "identity")
    core = _obj(receipt, "bundled_core")
    binding = _obj(receipt, "binding")
    workspace = _obj(receipt, "workspace")
    inference = _obj(receipt, "inference")
    authority = _obj(receipt, "authority")
    execution = _obj(receipt, "execution")

    source_commit = _hex(source, "commit", HEX40)
    _hex(source, "tree", HEX40)
    if source.get("dirty") is not False:
        raise ReceiptError("SOURCE_DIRTY_OR_UNKNOWN")

    generation = _count(runtime, "generation")
    _text(runtime, "mini_entity_version")
    _text(runtime, "entityos_version")

    zero_digest = _hex(identity, "zero_identity_digest", HEX64)
    grf_digest = _hex(identity, "grf_digest", HEX64)
    manifest_digest = _hex(core, "manifest_digest", HEX64)
    _hex(core, "checkpoint_digest", HEX64)
    _hex(core, "tokenizer_digest", HEX64)
    _hex(core, "jspace_profile_digest", HEX64)
    _hex(core, "lens_profile_digest", HEX64)
    _hex(core, "workspace_calibration_digest", HEX64)

    if _hex(binding, "zero_identity_digest", HEX64) != zero_digest:
        raise ReceiptError("STALE_ZERO_IDENTITY_BINDING")
    if _hex(binding, "grf_digest", HEX64) != grf_digest:
        raise ReceiptError("STALE_GRF_BINDING")
    if _hex(binding, "bundled_manifest_digest", HEX64) != manifest_digest:
        raise ReceiptError("STALE_BUNDLED_MANIFEST_BINDING")

    _hex(workspace, "before_digest", HEX64)
    _hex(workspace, "after_digest", HEX64)
    candidates = _list(workspace, "gwt_candidates", nonempty=True)
    winners = _list(workspace, "gwt_winners", nonempty=True)
    if not all(isinstance(x, str) and x for x in candidates + winners):
        raise ReceiptError("GWT_SLOT_ID_INVALID")
    if not set(winners).issubset(set(candidates)):
        raise ReceiptError("GWT_WINNER_NOT_CANDIDATE")
    _list(workspace, "jspace_observation_refs", nonempty=True)
    _list(workspace, "thalamus_gate_decisions", nonempty=True)
    for key in ("epq_ref", "hyperposition_ref", "claycode_ref", "omega_ref"):
        _text(workspace, key)

    engine_class = _text(inference, "engine_class")
    if engine_class not in ENGINE_CLASSES:
        raise ReceiptError("ENGINE_CLASS_UNSUPPORTED")
    _hex(inference, "inference_packet_digest", HEX64)
    _hex(inference, "candidate_result_digest", HEX64)
    if _bool(inference, "candidate_only") is not True:
        raise ReceiptError("INFERENCE_RESULT_NOT_CANDIDATE_ONLY")
    capability_match = _bool(inference, "adapter_capability_match")
    if engine_class == "claude_code" and not capability_match:
        raise ReceiptError("CLAUDE_ADAPTER_CAPABILITY_MISMATCH")
    if not _bool(inference, "provider_observability_claim_supported"):
        raise ReceiptError("UNSUPPORTED_PROVIDER_OBSERVABILITY_CLAIM")

    direct_state = _bool(authority, "candidate_requested_direct_state_mutation")
    direct_effect = _bool(authority, "candidate_requested_direct_effect_mutation")
    decision = _text(authority, "validation_decision")
    if decision not in VALIDATION_DECISIONS:
        raise ReceiptError("VALIDATION_DECISION_INVALID")
    canonical_write = _bool(authority, "canonical_write_committed")
    effect_committed = _bool(authority, "effect_committed")
    if direct_state or direct_effect:
        raise ReceiptError("CANDIDATE_AUTHORITY_SMUGGLE")
    if decision != "ACCEPT" and (canonical_write or effect_committed):
        raise ReceiptError("REJECTED_CANDIDATE_COMMITTED")

    free_only = _bool(execution, "free_only")
    cost_class = _text(execution, "lane_cost_class")
    if cost_class not in COST_CLASSES:
        raise ReceiptError("LANE_COST_CLASS_INVALID")
    lane_admitted = _bool(execution, "lane_admitted")
    secret_lookups = _count(execution, "secret_lookup_count")
    network_touches = _count(execution, "network_touch_count")
    if free_only and cost_class in {"PAID", "SUBSCRIPTION", "UNKNOWN"}:
        if lane_admitted:
            raise ReceiptError("FREE_ONLY_NONFREE_LANE_ADMITTED")
        if secret_lookups or network_touches:
            raise ReceiptError("FREE_ONLY_PRESECRET_PRENETWORK_BREACH")
        if decision != "BLOCKED":
            raise ReceiptError("FREE_ONLY_NONFREE_LANE_NOT_BLOCKED")
    if not lane_admitted and (canonical_write or effect_committed):
        raise ReceiptError("UNADMITTED_LANE_COMMITTED")

    _hex(execution, "terminal_result_digest", HEX64)

    return {
        "ok": True,
        "schema": SCHEMA,
        "receipt_digest": canonical_digest(receipt),
        "source_commit": source_commit,
        "generation": generation,
        "engine_class": engine_class,
        "canonical_write_committed": canonical_write,
        "effect_committed": effect_committed,
    }


def main() -> int:
    try:
        receipt = json.load(sys.stdin)
        result = validate(receipt)
    except (ReceiptError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
