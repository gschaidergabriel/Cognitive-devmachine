#!/usr/bin/env python3
"""Hardening adapter for the converged Trigger-2 Hyperposition labeler v3.

This adapter preserves v3 as the formal-world semantic engine and closes the three
current P0 promotion gaps identified by the exact-current adversarial audit:

1. caller-controlled ``independence_qualified`` is removed from authority;
2. exact event identity is bound to an immutable digest and same-id/different-payload
   replay fails closed rather than becoming a silent idempotent no-op;
3. resolution is exposed only through a combined update+resolve path that requires an
   explicit source-bound synthetic test admissibility/execution receipt.

It also requires the current safe joint-Hyperposition form:
``WHOLE_WORLD_BRANCHES`` with no implicit Cartesian completion. Factorized compatibility
sets remain a successor research lane until a deterministic joint-state transition
semantics exists.

This is synthetic/curriculum reference logic only. It mints no canonical truth, real
external effect, accepted-dataset, training, model/J-Space, HCU or EntityOS credit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any, Iterable

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_LABELER_V3_HARDENING_ADAPTER/v1"
ADAPTER_EVENT_SCHEMA = "XENO_SEMANTIC_HYPERPOSITION_EVENT_HARDENED/v1"
EXECUTION_RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v1"
V3_PATH = Path(__file__).with_name("trigger2_hyperposition_reference_labelers_v3.py")


def _load_v3():
    spec = importlib.util.spec_from_file_location("trigger2_hyperposition_reference_labelers_v3_adapter", V3_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load trigger2_hyperposition_reference_labelers_v3")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V3 = _load_v3()


def _digest(obj: Any) -> str:
    encoded = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _ok(**extra: Any) -> dict[str, Any]:
    out = {
        "schema": SCHEMA,
        "pass": True,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "runtime_credit_minted": False,
        "jspace_model_runtime_credit_minted": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": False,
    }
    out.update(extra)
    return out


def _fail(code: str, **extra: Any) -> dict[str, Any]:
    out = _ok(**extra)
    out["pass"] = False
    out["failure"] = code
    return out


def _joint_state_error(state: Any) -> str | None:
    if not isinstance(state, dict):
        return "STATE_OBJECT_REQUIRED"
    joint = state.get("joint_state")
    if not isinstance(joint, dict):
        return "JOINT_STATE_REQUIRED"
    if joint.get("representation") != "WHOLE_WORLD_BRANCHES":
        return "JOINT_STATE_REQUIRES_WHOLE_WORLD_BRANCHES"
    if joint.get("branch_semantics") != "EACH_BRANCH_IS_COMPLETE_LIVE_WORLD_HYPOTHESIS":
        return "WHOLE_WORLD_BRANCH_SEMANTICS_REQUIRED"
    if joint.get("cartesian_completion_allowed") is not False:
        return "IMPLICIT_CARTESIAN_COMPLETION_FORBIDDEN"
    return None


def _iter_records(state: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for record in branch.get(field, []) or []:
                if isinstance(record, dict):
                    yield record


def _event_identity_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": event.get("event_id"),
        "correlation_ancestry_id": event.get("correlation_ancestry_id"),
        "independence_group": event.get("independence_group"),
        "payload_key": event.get("payload_key"),
        "provenance": event.get("provenance"),
        "epistemic_type": event.get("epistemic_type"),
        "test_id": event.get("test_id"),
        "observed_outcome": event.get("observed_outcome"),
    }


def _record_identity_payload(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": record.get("event_id"),
        "correlation_ancestry_id": record.get("correlation_ancestry_id"),
        "independence_group": record.get("independence_group"),
        "payload_key": record.get("payload_key"),
        "provenance": record.get("provenance"),
        "epistemic_type": record.get("epistemic_type"),
        "test_id": record.get("test_id"),
        "observed_outcome": record.get("observed_outcome"),
    }


def _event_digest(event: dict[str, Any]) -> str:
    return _digest(_event_identity_payload(event))


def _validate_event_identity(state: dict[str, Any], event: dict[str, Any]) -> tuple[bool, str | None]:
    event_id = event.get("event_id")
    if not _nonempty(event_id):
        return False, "EVENT_ID_REQUIRED"
    incoming = _event_digest(event)
    seen_same = [record for record in _iter_records(state) if record.get("event_id") == event_id]
    if not seen_same:
        return False, None
    for record in seen_same:
        if _digest(_record_identity_payload(record)) != incoming:
            return False, "EVENT_ID_MUTATED_IMMUTABLE_PAYLOAD"
    return True, None


def _derive_independence(state: dict[str, Any], event: dict[str, Any]) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    records = list(_iter_records(state))
    if any(record.get("correlation_ancestry_id") == event.get("correlation_ancestry_id") for record in records):
        reasons.append("CORRELATION_ANCESTRY_REUSE")
    if any(record.get("independence_group") == event.get("independence_group") for record in records):
        reasons.append("INDEPENDENCE_GROUP_REUSE")
    if any(record.get("payload_key") == event.get("payload_key") for record in records):
        reasons.append("PAYLOAD_REPACKAGING")
    return not reasons, reasons


def _adapt_event(state: dict[str, Any], event: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    if not isinstance(event, dict) or event.get("schema") != ADAPTER_EVENT_SCHEMA:
        return None, _fail("ADAPTER_EVENT_SCHEMA_MISMATCH")
    if "independence_qualified" in event:
        return None, _fail("CALLER_INDEPENDENCE_QUALIFICATION_FORBIDDEN")
    forbidden = V3.FORBIDDEN_CALLER_LABEL_FIELDS & set(event)
    if forbidden:
        return None, _fail("CALLER_ASSERTED_LABEL_FIELD_FORBIDDEN", fields=sorted(forbidden))

    replay, identity_error = _validate_event_identity(state, event)
    if identity_error:
        return None, _fail(identity_error, event_id=event.get("event_id"))
    independent, reasons = _derive_independence(state, event)

    adapted = deepcopy(event)
    adapted["schema"] = V3.EVENT_SCHEMA
    adapted["independence_qualified"] = independent
    return adapted, _ok(
        event_id=event.get("event_id"),
        event_digest=_event_digest(event),
        exact_replay=replay,
        derived_independence_qualified=independent,
        derived_nonindependence_reasons=sorted(reasons),
    )


def _execution_receipt_error(world: dict[str, Any], event: dict[str, Any], receipt: Any) -> str | None:
    if not isinstance(receipt, dict) or receipt.get("schema") != EXECUTION_RECEIPT_SCHEMA:
        return "SYNTHETIC_EXECUTION_RECEIPT_REQUIRED"
    for field in ("receipt_id", "world_id", "test_id", "event_id", "observed_outcome", "source_digest"):
        if field not in receipt:
            return "SYNTHETIC_EXECUTION_RECEIPT_FIELD_MISSING:" + field
    if receipt.get("world_id") != world.get("world_id"):
        return "SYNTHETIC_EXECUTION_RECEIPT_WORLD_MISMATCH"
    if receipt.get("test_id") != event.get("test_id"):
        return "SYNTHETIC_EXECUTION_RECEIPT_TEST_MISMATCH"
    if receipt.get("event_id") != event.get("event_id"):
        return "SYNTHETIC_EXECUTION_RECEIPT_EVENT_MISMATCH"
    if receipt.get("observed_outcome") != event.get("observed_outcome"):
        return "SYNTHETIC_EXECUTION_RECEIPT_OUTCOME_MISMATCH"
    if receipt.get("executed") is not True:
        return "SYNTHETIC_DISCRIMINATOR_NOT_EXECUTED"
    if receipt.get("admissible") is not True:
        return "SYNTHETIC_DISCRIMINATOR_NOT_ADMISSIBLE"
    if receipt.get("observable") is not True:
        return "SYNTHETIC_DISCRIMINATOR_NOT_OBSERVABLE"
    if not _nonempty(receipt.get("source_digest")):
        return "SYNTHETIC_EXECUTION_RECEIPT_SOURCE_DIGEST_REQUIRED"
    return None


def u_state(world: Any, state: Any, event: Any) -> dict[str, Any]:
    joint_error = _joint_state_error(state)
    if joint_error:
        return _fail(joint_error)
    if not isinstance(world, dict) or not isinstance(state, dict):
        return _fail("WORLD_AND_STATE_OBJECT_REQUIRED")
    adapted, meta = _adapt_event(state, event)
    if adapted is None:
        assert meta is not None
        return meta
    result = V3.u_state(world, state, adapted)
    if not result.get("pass"):
        return _fail("V3_UPDATE_REJECTED", v3_result=result)
    return _ok(
        labeler="u_state_hardened",
        state_after=result["state_after"],
        updates=result.get("updates", []),
        born_branch_ids=result.get("born_branch_ids", []),
        derivation_receipt=result.get("derivation_receipt"),
        event_identity=meta,
        formal_v3_schema=V3.SCHEMA,
    )


def update_and_resolve(world: Any, state: Any, event: Any, execution_receipt: Any) -> dict[str, Any]:
    """Hardened D/E path: update from formal semantics, then resolve only with receipt."""
    if not isinstance(world, dict) or not isinstance(state, dict) or not isinstance(event, dict):
        return _fail("WORLD_STATE_EVENT_OBJECT_REQUIRED")
    receipt_error = _execution_receipt_error(world, event, execution_receipt)
    if receipt_error:
        return _fail(receipt_error)

    updated = u_state(world, state, event)
    if not updated.get("pass"):
        return updated
    state_after = updated["state_after"]
    resolution = V3.d_resolve(world, state_after)
    if not resolution.get("pass"):
        return _fail("V3_RESOLUTION_REJECTED", v3_result=resolution)

    resolution_obj = resolution.get("resolution", {})
    if resolution_obj.get("status") == "RESOLVED":
        resolved_branch = resolution_obj.get("resolved_branch") or resolution_obj.get("resolved_branch_id")
        if not _nonempty(resolved_branch):
            return _fail("RESOLVED_WITHOUT_BRANCH_ID")
        resolution_provenance = {
            "execution_receipt_id": execution_receipt["receipt_id"],
            "execution_receipt_digest": _digest(execution_receipt),
            "event_digest": updated["event_identity"]["event_digest"],
            "formal_v3_schema": V3.SCHEMA,
            "canonical_truth_minted": False,
            "direct_effect_authority_minted": False,
        }
    else:
        resolution_provenance = None

    return _ok(
        labeler="update_and_resolve_hardened",
        state_after=state_after,
        updates=updated.get("updates", []),
        event_identity=updated["event_identity"],
        resolution=resolution_obj,
        resolution_provenance=resolution_provenance,
        retained_branch_ids=resolution.get("retained_branch_ids"),
        formal_v3_schema=V3.SCHEMA,
    )
