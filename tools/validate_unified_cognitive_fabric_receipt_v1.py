#!/usr/bin/env python3
"""Fail-closed validator for UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1.

ClayCode owns the semantic entry point. This host-language validator admits only a
bounded evidence envelope. A PASS here is source/mechanism evidence, never proof
that J-Space/GWT/model/runtime behavior actually occurred.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import re
import sys
from typing import Any

SCHEMA = "UNIFIED_COGNITIVE_FABRIC_RUNTIME_RECEIPT/v1"
GIT_OID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ENGINE_CLASSES = {"local_08b", "claude_code", "adaptive_backend"}
JSPACE_MODES = {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY", "COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"}
COST_CLASSES = {"LOCAL", "FREE", "PAID", "SUBSCRIPTION", "UNKNOWN"}
EPISTEMIC_STATUSES = {"MEASURED_SUPPORTED", "UNKNOWN", "ERROR", "REFUTED", "NOT_APPLICABLE"}
VALIDATION_DECISIONS = {"ACCEPT", "REJECT", "BLOCKED"}


class ReceiptError(ValueError):
    pass


def _obj(parent: dict[str, Any], key: str) -> dict[str, Any]:
    value = parent.get(key)
    if type(value) is not dict:
        raise ReceiptError(f"{key}:OBJECT_REQUIRED")
    return value


def _list(parent: dict[str, Any], key: str, *, nonempty: bool = False) -> list[Any]:
    value = parent.get(key)
    if type(value) is not list or (nonempty and not value):
        raise ReceiptError(f"{key}:LIST_REQUIRED")
    return value


def _text(parent: dict[str, Any], key: str) -> str:
    value = parent.get(key)
    if type(value) is not str or not value:
        raise ReceiptError(f"{key}:TEXT_REQUIRED")
    return value


def _bool(parent: dict[str, Any], key: str) -> bool:
    value = parent.get(key)
    if type(value) is not bool:
        raise ReceiptError(f"{key}:BOOL_REQUIRED")
    return value


def _count(parent: dict[str, Any], key: str) -> int:
    value = parent.get(key)
    if type(value) is not int or value < 0:
        raise ReceiptError(f"{key}:NONNEGATIVE_INT_REQUIRED")
    return value


def _is_placeholder_hex(value: str) -> bool:
    return value == ("0" * len(value)) or value == ("f" * len(value))


def _hex(parent: dict[str, Any], key: str, pattern: re.Pattern[str], *, nullable: bool = False) -> str | None:
    value = parent.get(key)
    if value is None and nullable:
        return None
    value = _text(parent, key)
    if pattern.fullmatch(value) is None:
        raise ReceiptError(f"{key}:DIGEST_FORMAT")
    if _is_placeholder_hex(value):
        raise ReceiptError(f"{key}:IDENTITY_PLACEHOLDER")
    return value


def _finite_json(value: Any, path: str = "$") -> None:
    t = type(value)
    if value is None or t in {str, bool, int}:
        return
    if t is float:
        if not math.isfinite(value):
            raise ReceiptError(f"NONFINITE_JSON:{path}")
        return
    if t is list:
        for index, item in enumerate(value):
            _finite_json(item, f"{path}[{index}]")
        return
    if t is dict:
        for key, item in value.items():
            if type(key) is not str:
                raise ReceiptError(f"NONSTRING_JSON_KEY:{path}")
            _finite_json(item, f"{path}.{key}")
        return
    raise ReceiptError(f"UNSUPPORTED_JSON_TYPE:{path}:{t.__name__}")


def canonical_digest(receipt: dict[str, Any]) -> str:
    material = copy.deepcopy(receipt)
    material.pop("receipt_envelope_digest", None)
    _finite_json(material)
    encoded = json.dumps(
        material,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def validate(receipt: dict[str, Any]) -> dict[str, Any]:
    if type(receipt) is not dict:
        raise ReceiptError("ROOT_OBJECT_REQUIRED")
    _finite_json(receipt)
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

    source_commit = _hex(source, "commit", GIT_OID)
    _hex(source, "tree", GIT_OID)
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
    lens_profile_digest = _hex(core, "lens_profile_digest", HEX64, nullable=True)
    _hex(core, "workspace_calibration_digest", HEX64)

    if _hex(binding, "zero_identity_digest", HEX64) != zero_digest:
        raise ReceiptError("STALE_ZERO_IDENTITY_BINDING")
    if _hex(binding, "grf_digest", HEX64) != grf_digest:
        raise ReceiptError("STALE_GRF_BINDING")
    if _hex(binding, "bundled_manifest_digest", HEX64) != manifest_digest:
        raise ReceiptError("STALE_BUNDLED_MANIFEST_BINDING")
    _hex(binding, "boot_binding_receipt_digest", HEX64)

    _hex(workspace, "before_digest", HEX64)
    _hex(workspace, "after_digest", HEX64)
    candidates = _list(workspace, "gwt_candidates", nonempty=True)
    winners = _list(workspace, "gwt_winners")
    if not all(type(x) is str and x for x in candidates + winners):
        raise ReceiptError("GWT_SLOT_ID_INVALID")
    if len(set(candidates)) != len(candidates):
        raise ReceiptError("GWT_CANDIDATE_DUPLICATE")
    if len(set(winners)) != len(winners):
        raise ReceiptError("GWT_WINNER_DUPLICATE")
    if len(winners) > 1:
        raise ReceiptError("GWT_MULTIPLE_WINNERS")
    if not set(winners).issubset(set(candidates)):
        raise ReceiptError("GWT_WINNER_NOT_CANDIDATE")
    _list(workspace, "jspace_observation_refs")
    _list(workspace, "thalamus_gate_decisions", nonempty=True)
    for key in ("epq_ref", "hyperposition_ref", "claycode_ref", "omega_ref"):
        _text(workspace, key)

    engine_class = _text(inference, "engine_class")
    if engine_class not in ENGINE_CLASSES:
        raise ReceiptError("ENGINE_CLASS_UNSUPPORTED")
    executed = _bool(inference, "executed")
    if executed and not winners:
        raise ReceiptError("EXECUTED_INFERENCE_REQUIRES_GWT_WINNER")
    jspace_mode = _text(inference, "jspace_mode")
    if jspace_mode not in JSPACE_MODES:
        raise ReceiptError("JSPACE_MODE_UNSUPPORTED")
    local_activation_access = _bool(inference, "local_activation_access")
    external_hidden_state_claimed = _bool(inference, "external_hidden_state_claimed")
    _text(inference, "adapter_version")
    _hex(inference, "capability_profile_digest", HEX64)
    _hex(inference, "adapter_contract_digest", HEX64)
    _hex(inference, "inference_packet_digest", HEX64)
    candidate_result_digest = _hex(inference, "candidate_result_digest", HEX64, nullable=True)
    epistemic_status = _text(inference, "epistemic_status")
    if epistemic_status not in EPISTEMIC_STATUSES:
        raise ReceiptError("EPISTEMIC_STATUS_UNSUPPORTED")
    if _bool(inference, "candidate_only") is not True:
        raise ReceiptError("INFERENCE_RESULT_NOT_CANDIDATE_ONLY")
    capability_match = _bool(inference, "adapter_capability_match")
    if not capability_match:
        if engine_class == "claude_code":
            raise ReceiptError("CLAUDE_ADAPTER_CAPABILITY_MISMATCH")
        raise ReceiptError("ADAPTER_CAPABILITY_MISMATCH")

    observability_supported = _bool(inference, "provider_observability_claim_supported")
    if not observability_supported:
        raise ReceiptError("UNSUPPORTED_PROVIDER_OBSERVABILITY_CLAIM")

    if engine_class == "claude_code":
        if jspace_mode != "COMPILED_EXTERNAL":
            raise ReceiptError("CLAUDE_MUST_BE_COMPILED_EXTERNAL")
        if local_activation_access:
            raise ReceiptError("CLAUDE_LOCAL_ACTIVATION_CLAIM_FORBIDDEN")
        if external_hidden_state_claimed:
            raise ReceiptError("CLAUDE_HIDDEN_STATE_CLAIM_FORBIDDEN")
    if engine_class == "local_08b" and jspace_mode not in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"}:
        raise ReceiptError("LOCAL_08B_JSPACE_MODE_INVALID")
    if jspace_mode in {"FULL_LOCAL_LATENT", "LOCAL_OBSERVE_ONLY"} and lens_profile_digest is None:
        raise ReceiptError("LOCAL_JSPACE_REQUIRES_LENS_PROFILE")
    if jspace_mode == "FULL_LOCAL_LATENT" and not local_activation_access:
        raise ReceiptError("FULL_LOCAL_LATENT_REQUIRES_ACTIVATION_ACCESS")
    if jspace_mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"} and local_activation_access:
        raise ReceiptError("EXTERNAL_MODE_CANNOT_CLAIM_LOCAL_ACTIVATION_ACCESS")
    if jspace_mode in {"COMPILED_EXTERNAL", "PLAIN_COMPATIBILITY"} and external_hidden_state_claimed:
        raise ReceiptError("EXTERNAL_HIDDEN_STATE_CLAIM_FORBIDDEN")

    intervention = _obj(inference, "jspace_intervention")
    intervention_executed = _bool(intervention, "executed")
    if intervention_executed:
        if not executed:
            raise ReceiptError("INTERVENTION_REQUIRES_EXECUTED_INFERENCE")
        if jspace_mode != "FULL_LOCAL_LATENT":
            raise ReceiptError("INTERVENTION_REQUIRES_FULL_LOCAL_LATENT")
        if not local_activation_access:
            raise ReceiptError("INTERVENTION_REQUIRES_ACTIVATION_ACCESS")
        _hex(intervention, "implementation_digest", HEX64)
        _hex(intervention, "calibration_digest", HEX64)

    if executed:
        if candidate_result_digest is None:
            raise ReceiptError("EXECUTED_INFERENCE_REQUIRES_RESULT_DIGEST")
        if epistemic_status == "NOT_APPLICABLE":
            raise ReceiptError("EXECUTED_INFERENCE_REQUIRES_EPISTEMIC_STATUS")
    else:
        if candidate_result_digest is not None:
            raise ReceiptError("NONEXECUTED_INFERENCE_RESULT_DIGEST_MUST_BE_NULL")
        if epistemic_status != "NOT_APPLICABLE":
            raise ReceiptError("NONEXECUTED_INFERENCE_EPISTEMIC_STATUS_MUST_BE_NOT_APPLICABLE")

    direct_state = _bool(authority, "candidate_requested_direct_state_mutation")
    direct_effect = _bool(authority, "candidate_requested_direct_effect_mutation")
    decision = _text(authority, "validation_decision")
    if decision not in VALIDATION_DECISIONS:
        raise ReceiptError("VALIDATION_DECISION_INVALID")
    canonical_write = _bool(authority, "canonical_write_committed")
    effect_committed = _bool(authority, "effect_committed")
    if direct_state or direct_effect:
        raise ReceiptError("CANDIDATE_AUTHORITY_SMUGGLE")
    if decision == "ACCEPT" and not executed:
        raise ReceiptError("ACCEPT_WITHOUT_EXECUTED_INFERENCE")
    if decision != "ACCEPT" and (canonical_write or effect_committed):
        raise ReceiptError("REJECTED_CANDIDATE_COMMITTED")
    if (canonical_write or effect_committed) and epistemic_status != "MEASURED_SUPPORTED":
        raise ReceiptError("UNSUPPORTED_EPISTEMIC_AUTHORITY")

    free_only = _bool(execution, "free_only")
    cost_class = _text(execution, "lane_cost_class")
    if cost_class not in COST_CLASSES:
        raise ReceiptError("LANE_COST_CLASS_INVALID")
    lane_admitted = _bool(execution, "lane_admitted")
    _hex(execution, "policy_authority_digest", HEX64)
    secret_lookups = _count(execution, "secret_lookup_count")
    network_touches = _count(execution, "network_touch_count")
    if executed and not lane_admitted:
        raise ReceiptError("INFERENCE_EXECUTED_WITHOUT_LANE_ADMISSION")
    if free_only and cost_class in {"PAID", "SUBSCRIPTION", "UNKNOWN"}:
        if lane_admitted:
            raise ReceiptError("FREE_ONLY_NONFREE_LANE_ADMITTED")
        if secret_lookups:
            raise ReceiptError("FREE_ONLY_SECRET_TOUCH")
        if network_touches:
            raise ReceiptError("FREE_ONLY_NETWORK_TOUCH")
        if decision != "BLOCKED":
            raise ReceiptError("FREE_ONLY_NONFREE_LANE_NOT_BLOCKED")
    if not lane_admitted and (canonical_write or effect_committed):
        raise ReceiptError("UNADMITTED_LANE_COMMITTED")

    freshness = _obj(receipt, "freshness")
    stale_zero = _bool(freshness, "stale_zero_identity")
    stale_manifest = _bool(freshness, "stale_bundled_manifest")
    stale_generation = _bool(freshness, "stale_generation")
    if stale_zero or stale_manifest or stale_generation:
        if lane_admitted or executed or decision == "ACCEPT" or canonical_write or effect_committed:
            raise ReceiptError("STALE_INPUT_AUTHORITY_OR_EXECUTION")

    _hex(execution, "terminal_result_digest", HEX64)
    envelope_digest = _hex(receipt, "receipt_envelope_digest", HEX64)
    expected_envelope_digest = canonical_digest(receipt)
    if envelope_digest != expected_envelope_digest:
        raise ReceiptError("RECEIPT_ENVELOPE_DIGEST_MISMATCH")

    return {
        "ok": True,
        "schema": SCHEMA,
        "receipt_digest": envelope_digest,
        "source_commit": source_commit,
        "generation": generation,
        "engine_class": engine_class,
        "jspace_mode": jspace_mode,
        "epistemic_status": epistemic_status,
        "lane_cost_class": cost_class,
        "canonical_write_committed": canonical_write,
        "effect_committed": effect_committed,
    }


def main() -> int:
    try:
        receipt = json.load(
            sys.stdin,
            parse_constant=lambda value: (_ for _ in ()).throw(ReceiptError(f"NONFINITE_JSON_CONSTANT:{value}")),
        )
        result = validate(receipt)
    except (ReceiptError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
