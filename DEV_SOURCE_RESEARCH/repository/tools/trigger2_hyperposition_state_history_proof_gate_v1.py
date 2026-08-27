#!/usr/bin/env python3
"""Replay-bound Trigger-2 Hyperposition state-history proof gate v1.

This successor proof lane hardens the current v3 reference semantics without creating a
second semantic authority. It treats the existing v3 labeler as the transition oracle, but
requires positive D/E candidate state to be reconstructed from a clean genesis plus an
immutable event history. Every history/current event is bound to a semantic digest and an
explicit discriminator execution receipt. Caller ``independence_qualified`` is ignored and
re-derived from the retained derivation-bound gate v2.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints no canonical dataset, truth, effect,
provider, runtime, J-Space, HCU, EntityOS or training credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_PROOF_GATE/v1"
DIGEST_REGISTRY_SCHEMA = "XENO_SYNTHETIC_EVENT_DIGEST_REGISTRY/v1"
DISCRIMINATOR_RECEIPT_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_EXECUTION_RECEIPT/v1"
OBSERVATION_RECEIPT_SCHEMA = "ENTITYOS_TYPED_OBSERVATION_EVIDENCE_RECEIPT/v1"
BASE_GATE_FILENAME = "trigger2_hyperposition_derivation_bound_gate_v2.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


OBSERVED_PRODUCER_AUTH_GATE_FILENAME = "trigger2_observed_evidence_producer_auth_gate_v1.py"

base = _load_sibling(BASE_GATE_FILENAME, "trigger2_hp_derivation_gate_v2_for_history")
lab = base.lab
observed_producer_auth = _load_sibling(
    OBSERVED_PRODUCER_AUTH_GATE_FILENAME, "trigger2_observed_producer_auth_for_history"
)


def _digest(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _event_semantic_payload(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    keys = (
        "schema", "event_id", "correlation_ancestry_id", "independence_group",
        "payload_key", "provenance", "epistemic_type", "test_id", "observed_outcome",
        "canonical_truth_allowed", "direct_effect_authority",
    )
    if any(k not in event for k in keys):
        return None
    return {k: deepcopy(event[k]) for k in keys}


def event_semantic_sha256(event: Any) -> str | None:
    payload = _event_semantic_payload(event)
    return None if payload is None else _digest(payload)


def _world_sha256(world: Any) -> str | None:
    return _digest(world) if isinstance(world, dict) else None


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "deterministic replay/state-proof candidate gate only",
    }
    out.update(extra)
    return out


def _records(state: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(state, dict):
        return out
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for rec in branch.get(field, []) or []:
                if isinstance(rec, dict):
                    out.append(rec)
    return out


def _genesis_is_clean(genesis: Any) -> tuple[bool, list[str]]:
    failures: list[str] = []
    if not isinstance(genesis, dict):
        return False, ["GENESIS_STATE_OBJECT_REQUIRED"]
    for branch in genesis.get("branches", []) or []:
        if not isinstance(branch, dict):
            failures.append("GENESIS_BRANCH_OBJECT_REQUIRED")
            continue
        if branch.get("sigma") != "LIVE_UNRESOLVED":
            failures.append("GENESIS_SIGMA_MUST_BE_LIVE_UNRESOLVED")
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            if branch.get(field, []) not in ([], None):
                failures.append("GENESIS_PRESEEDED_EVIDENCE_FORBIDDEN:" + field)
    return not failures, sorted(set(failures))


def _digest_registry_map(registry: Any) -> tuple[dict[str, str], list[str]]:
    if not isinstance(registry, dict) or registry.get("schema") != DIGEST_REGISTRY_SCHEMA:
        return {}, ["EVENT_DIGEST_REGISTRY_REQUIRED"]
    events = registry.get("events")
    if not isinstance(events, dict):
        return {}, ["EVENT_DIGEST_REGISTRY_EVENTS_REQUIRED"]
    out: dict[str, str] = {}
    failures: list[str] = []
    for event_id, digest in events.items():
        if not isinstance(event_id, str) or not event_id or not isinstance(digest, str) or len(digest) != 64:
            failures.append("EVENT_DIGEST_REGISTRY_ENTRY_INVALID")
            continue
        out[event_id] = digest
    return out, sorted(set(failures))


def _receipt_index(receipts: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    if not isinstance(receipts, list):
        return {}, ["DISCRIMINATOR_RECEIPTS_LIST_REQUIRED"]
    out: dict[str, dict[str, Any]] = {}
    failures: list[str] = []
    for receipt in receipts:
        if not isinstance(receipt, dict) or receipt.get("schema") != DISCRIMINATOR_RECEIPT_SCHEMA:
            failures.append("DISCRIMINATOR_RECEIPT_SCHEMA_INVALID")
            continue
        event_id = receipt.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            failures.append("DISCRIMINATOR_RECEIPT_EVENT_ID_REQUIRED")
            continue
        if event_id in out:
            failures.append("DUPLICATE_DISCRIMINATOR_RECEIPT_EVENT_ID:" + event_id)
            continue
        out[event_id] = receipt
    return out, sorted(set(failures))


def _validate_discriminator_receipt(world: Any, state: Any, event: Any, receipt: Any, event_digest: str) -> list[str]:
    failures: list[str] = []
    if not isinstance(receipt, dict) or receipt.get("schema") != DISCRIMINATOR_RECEIPT_SCHEMA:
        return ["DISCRIMINATOR_EXECUTION_RECEIPT_REQUIRED"]
    if receipt.get("event_id") != event.get("event_id"):
        failures.append("DISCRIMINATOR_EVENT_ID_MISMATCH")
    if receipt.get("test_id") != event.get("test_id"):
        failures.append("DISCRIMINATOR_TEST_ID_MISMATCH")
    if receipt.get("observed_outcome") != event.get("observed_outcome"):
        failures.append("DISCRIMINATOR_OUTCOME_MISMATCH")
    if receipt.get("event_semantic_sha256") != event_digest:
        failures.append("DISCRIMINATOR_EVENT_DIGEST_MISMATCH")
    if receipt.get("world_sha256") != _world_sha256(world):
        failures.append("DISCRIMINATOR_WORLD_DIGEST_MISMATCH")
    if receipt.get("admissible") is not True:
        failures.append("DISCRIMINATOR_NOT_ADMISSIBLE")
    if receipt.get("executed") is not True:
        failures.append("DISCRIMINATOR_NOT_EXECUTED")
    if not isinstance(receipt.get("execution_receipt_id"), str) or not receipt.get("execution_receipt_id"):
        failures.append("DISCRIMINATOR_EXECUTION_RECEIPT_ID_REQUIRED")
    try:
        ordering = lab.u_test_order(world, state, [event.get("test_id")])
    except Exception as exc:
        failures.append("DISCRIMINATOR_ORDER_RECOMPUTE_EXCEPTION:" + type(exc).__name__)
    else:
        if not ordering.get("pass"):
            failures.append("DISCRIMINATOR_ORDER_RECOMPUTE_REJECTED:" + str(ordering.get("failure")))
        else:
            row = ordering.get("ordering", [{}])[0]
            if receipt.get("separated_live_pairs") != row.get("separated_live_pairs"):
                failures.append("DISCRIMINATOR_COVERAGE_COUNT_MISMATCH")
            if receipt.get("separates_all_live_pairs") is not row.get("separates_all_live_pairs"):
                failures.append("DISCRIMINATOR_FULL_COVERAGE_FLAG_MISMATCH")
            if not isinstance(receipt.get("separated_live_pairs"), int) or receipt.get("separated_live_pairs", 0) <= 0:
                failures.append("DISCRIMINATOR_MUST_SEPARATE_AT_LEAST_ONE_LIVE_PAIR")
    return sorted(set(failures))


def _validate_observation_receipt(
    event: Any, receipts: Any, event_digest: str,
    source_payloads: Any = None, admissions: Any = None,
) -> list[str]:
    if event.get("epistemic_type") != "OBSERVED":
        return []
    if not isinstance(receipts, list):
        return ["OBSERVED_EVENT_TYPED_EVIDENCE_RECEIPTS_REQUIRED"]
    matches = [r for r in receipts if isinstance(r, dict) and r.get("event_id") == event.get("event_id")]
    if len(matches) != 1:
        return ["OBSERVED_EVENT_REQUIRES_EXACTLY_ONE_TYPED_EVIDENCE_RECEIPT"]
    rec = matches[0]
    failures: list[str] = []
    if rec.get("schema") != OBSERVATION_RECEIPT_SCHEMA:
        failures.append("OBSERVATION_RECEIPT_SCHEMA_INVALID")
    if rec.get("event_semantic_sha256") != event_digest:
        failures.append("OBSERVATION_RECEIPT_EVENT_DIGEST_MISMATCH")
    if rec.get("canonical_truth_allowed") is not False:
        failures.append("OBSERVATION_RECEIPT_CANNOT_MINT_CANONICAL_TRUTH")
    if rec.get("direct_effect_authority") is not False:
        failures.append("OBSERVATION_RECEIPT_CANNOT_MINT_DIRECT_EFFECT_AUTHORITY")
    for key in ("source", "provenance", "observed_time", "receipt_id"):
        if not isinstance(rec.get(key), str) or not rec.get(key):
            failures.append("OBSERVATION_RECEIPT_FIELD_REQUIRED:" + key)

    # Producer authentication: schema/digest/fences alone were confirmed accepted for a fully
    # caller-forged receipt (arbitrary source/provenance/receipt_id). Require independent
    # recomputation against the one authorized producer/policy/admission scope instead of
    # trusting these caller strings.
    event_id = event.get("event_id")
    source_payload_map = source_payloads if isinstance(source_payloads, dict) else {}
    admission_map = admissions if isinstance(admissions, dict) else {}
    if event_id not in source_payload_map:
        failures.append("OBSERVED_EVIDENCE_SOURCE_PAYLOAD_REQUIRED")
    if event_id not in admission_map:
        failures.append("OBSERVED_EVIDENCE_ADMISSION_REQUIRED")
    if event_id in source_payload_map and event_id in admission_map:
        auth_result = observed_producer_auth.adjudicate(
            claimed_receipt=rec,
            causal_event_id=event_id,
            event_semantic_sha256=event_digest,
            observed_value=event.get("observed_outcome"),
            source_payload=source_payload_map.get(event_id),
            admission=admission_map.get(event_id),
            observed_time=rec.get("observed_time"),
        )
        if not auth_result.get("pass"):
            failures.extend("OBSERVED_PRODUCER_AUTH:" + x for x in auth_result.get("failures", []))

    return sorted(set(failures))


def _bind_event_digest(event: Any, digest_map: dict[str, str], seen: dict[str, str]) -> tuple[str | None, list[str]]:
    event_id = event.get("event_id") if isinstance(event, dict) else None
    digest = event_semantic_sha256(event)
    if not isinstance(event_id, str) or not event_id or digest is None:
        return digest, ["EVENT_SEMANTIC_IDENTITY_INVALID"]
    failures: list[str] = []
    if digest_map.get(event_id) != digest:
        failures.append("EVENT_DIGEST_REGISTRY_MISMATCH:" + event_id)
    if event_id in seen and seen[event_id] != digest:
        failures.append("EVENT_ID_REUSED_WITH_DIFFERENT_SEMANTIC_DIGEST:" + event_id)
    seen.setdefault(event_id, digest)
    return digest, sorted(set(failures))


def _decorate_event_records(state: Any, event_id: str, event_digest: str) -> None:
    if not isinstance(state, dict):
        return
    for rec in _records(state):
        if rec.get("event_id") == event_id:
            existing = rec.get("event_sha256")
            if existing is not None and existing != event_digest:
                raise ValueError("EVENT_RECORD_DIGEST_CONFLICT")
            rec["event_sha256"] = event_digest


def _derive_and_apply(world: Any, state: Any, event: Any) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[str]]:
    try:
        independence = base.derive_independence(world, state, event)
    except Exception as exc:
        return None, None, ["INDEPENDENCE_DERIVATION_EXCEPTION:" + type(exc).__name__]
    substantive = [x for x in independence.get("failures", []) if x != "CALLER_INDEPENDENCE_FLAG_MISMATCH_DERIVED_VALUE"]
    if substantive:
        return independence, None, sorted("INDEPENDENCE:" + x for x in substantive)
    event_for_lab = deepcopy(event)
    event_for_lab["independence_qualified"] = bool(independence.get("derived_independence_qualified", False))
    try:
        update = lab.u_state(world, state, event_for_lab)
    except Exception as exc:
        return independence, None, ["V3_UPDATE_EXCEPTION:" + type(exc).__name__]
    if not update.get("pass"):
        return independence, update, ["V3_UPDATE_REJECTED:" + str(update.get("failure"))]
    return independence, update, []


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    world = row.get("formal_task_world_evaluator_only")
    supplied_before = row.get("hyperposition_state_before_evaluator_only")
    genesis = row.get("hyperposition_genesis_state_evaluator_only")
    history = row.get("synthetic_event_history_evaluator_only")
    current_event = row.get("synthetic_test_event_evaluator_only")
    digest_registry = row.get("event_digest_registry_evaluator_only")
    disc_receipts = row.get("discriminator_execution_receipts_evaluator_only")
    obs_receipts = row.get("typed_observation_evidence_receipts_evaluator_only", [])
    obs_source_payloads = row.get("observed_evidence_source_payloads_evaluator_only", {})
    obs_admissions = row.get("observed_evidence_admissions_evaluator_only", {})

    ok, genesis_failures = _genesis_is_clean(genesis)
    if not ok:
        failures.extend(genesis_failures)
    if not isinstance(history, list):
        failures.append("SYNTHETIC_EVENT_HISTORY_LIST_REQUIRED")
        history = []
    digest_map, digest_failures = _digest_registry_map(digest_registry)
    failures.extend(digest_failures)
    receipt_map, receipt_failures = _receipt_index(disc_receipts)
    failures.extend(receipt_failures)

    replay_state = deepcopy(genesis) if isinstance(genesis, dict) else None
    seen_digests: dict[str, str] = {}
    replay_steps: list[dict[str, Any]] = []
    if isinstance(world, dict) and isinstance(replay_state, dict):
        for idx, event in enumerate(history):
            if not isinstance(event, dict):
                failures.append(f"HISTORY_EVENT_OBJECT_REQUIRED:{idx}")
                continue
            digest, ds = _bind_event_digest(event, digest_map, seen_digests)
            failures.extend(ds)
            if digest is None:
                continue
            failures.extend(_validate_discriminator_receipt(world, replay_state, event, receipt_map.get(event.get("event_id")), digest))
            failures.extend(_validate_observation_receipt(event, obs_receipts, digest, obs_source_payloads, obs_admissions))
            independence, update, step_failures = _derive_and_apply(world, replay_state, event)
            failures.extend(step_failures)
            if update is None or not update.get("pass"):
                continue
            replay_state = deepcopy(update["state_after"])
            try:
                _decorate_event_records(replay_state, event["event_id"], digest)
            except ValueError:
                failures.append("EVENT_RECORD_DIGEST_CONFLICT:" + event["event_id"])
            replay_steps.append({
                "index": idx,
                "event_id": event["event_id"],
                "event_sha256": digest,
                "derived_independence_qualified": independence.get("derived_independence_qualified") if isinstance(independence, dict) else None,
                "state_sha256": _digest(replay_state),
            })

    replay_matches_supplied = isinstance(replay_state, dict) and isinstance(supplied_before, dict) and replay_state == supplied_before
    if not replay_matches_supplied:
        failures.append("SUPPLIED_STATE_BEFORE_NOT_EXACT_REPLAY_OF_GENESIS_HISTORY")

    current_digest = None
    current_update = None
    current_resolution = None
    current_independence = None
    if isinstance(world, dict) and isinstance(supplied_before, dict) and isinstance(current_event, dict):
        current_digest, ds = _bind_event_digest(current_event, digest_map, seen_digests)
        failures.extend(ds)
        if current_digest is not None:
            failures.extend(_validate_discriminator_receipt(world, supplied_before, current_event, receipt_map.get(current_event.get("event_id")), current_digest))
            failures.extend(_validate_observation_receipt(current_event, obs_receipts, current_digest, obs_source_payloads, obs_admissions))
            independence, update, step_failures = _derive_and_apply(world, supplied_before, current_event)
            current_independence = independence
            failures.extend(step_failures)
            if update is not None and update.get("pass"):
                current_update = deepcopy(update["state_after"])
                try:
                    _decorate_event_records(current_update, current_event["event_id"], current_digest)
                except ValueError:
                    failures.append("CURRENT_EVENT_RECORD_DIGEST_CONFLICT")
                try:
                    resolution = lab.d_resolve(world, current_update)
                except Exception as exc:
                    failures.append("CURRENT_RESOLUTION_EXCEPTION:" + type(exc).__name__)
                else:
                    if not resolution.get("pass"):
                        failures.append("CURRENT_RESOLUTION_REJECTED:" + str(resolution.get("failure")))
                    else:
                        current_resolution = resolution.get("resolution")

    elimination_proof: dict[str, list[str]] = {}
    if isinstance(current_update, dict) and isinstance(current_resolution, dict) and current_resolution.get("status") == "RESOLVED_WITHIN_SYNTHETIC_WORLD":
        winner = current_resolution.get("resolved_branch")
        for branch in current_update.get("branches", []) or []:
            if not isinstance(branch, dict) or branch.get("branch_id") == winner or branch.get("sigma") != "FALSIFIED":
                continue
            ids = []
            for rec in branch.get("F", []) or []:
                if not isinstance(rec, dict):
                    continue
                eid = rec.get("event_id")
                if isinstance(eid, str) and rec.get("event_sha256") == digest_map.get(eid) and eid in receipt_map:
                    ids.append(eid)
            if not ids:
                failures.append("RESOLVED_COMPETITOR_LACKS_DIGEST_BOUND_EXECUTED_DISCRIMINATOR_PROOF:" + str(branch.get("branch_id")))
            elimination_proof[str(branch.get("branch_id"))] = sorted(set(ids))

    base_gate_result = None
    if isinstance(current_event, dict):
        sanitized_row = deepcopy(row)
        sanitized_event = deepcopy(current_event)
        if isinstance(current_independence, dict):
            sanitized_event["independence_qualified"] = bool(current_independence.get("derived_independence_qualified", False))
        sanitized_row["synthetic_test_event_evaluator_only"] = sanitized_event
        try:
            base_gate_result = base.adjudicate(sanitized_row)
        except Exception as exc:
            failures.append("BASE_DERIVATION_GATE_V2_EXCEPTION:" + type(exc).__name__)
        else:
            if not base_gate_result.get("pass"):
                failures.extend("BASE_GATE_V2:" + str(x) for x in base_gate_result.get("failures", []))
    else:
        failures.append("CURRENT_EVENT_REQUIRED_FOR_BASE_GATE_V2")

    claimed = row.get("state_history_reference_target_evaluator_only")
    recomputed = {
        "state_after": current_update,
        "task_resolution": current_resolution,
        "event_sha256": current_digest,
        "eliminated_competitor_event_ids": elimination_proof,
    }
    if claimed is None:
        failures.append("STATE_HISTORY_REFERENCE_TARGET_REQUIRED")
    elif claimed != recomputed:
        failures.append("CLAIMED_STATE_HISTORY_TARGET_DOES_NOT_MATCH_RECOMPUTED_PROOF")

    return _result(
        failures,
        replay_matches_supplied_state=replay_matches_supplied,
        replayed_state_sha256=_digest(replay_state) if isinstance(replay_state, dict) else None,
        supplied_state_sha256=_digest(supplied_before) if isinstance(supplied_before, dict) else None,
        replay_steps=replay_steps,
        recomputed_target=recomputed,
        base_derivation_gate_v2_result=base_gate_result,
        caller_independence_boolean_authoritative=False,
        event_id_digest_binding_required=True,
        discriminator_admissibility_execution_coverage_required=True,
        observed_promotion_typed_receipt_required=True,
    )
