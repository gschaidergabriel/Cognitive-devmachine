#!/usr/bin/env python3
"""Trigger-2 Hyperposition derivation-bound pre-admission gate v3.

This is a narrow successor of ``trigger2_hyperposition_derivation_bound_gate_v2``.
It deliberately reuses the same v3 formal Hyperposition reference labeler and adds no
second semantic authority.  The v3 gate closes two provenance roots before a synthetic
positive D/E/epistemic candidate can pass pre-admission:

1. ``event_id`` is bound to a deterministic immutable event-content digest.  Reusing an
   event id with different content is a hard failure, not an idempotent replay.
2. the event's discriminator must have a typed, digest-bound evaluator-only receipt that
   proves admissibility, execution identity, exact observed outcome, and complete coverage
   of the formal target branches.  OBSERVED events additionally require the typed receipt
   to carry ``observation_qualified=true``; a naked boolean argument is never accepted.

The gate remains SOURCE/CANDIDATE PRE-ADMISSION ONLY.  PASS cannot write the canonical
training dataset and cannot mint truth, effect, runtime, J-Space, HCU, EntityOS, provider,
or training credit.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_DERIVATION_BOUND_GATE/v3"
DEPENDENCE_SCHEMA = "XENO_SYNTHETIC_EVENT_DEPENDENCE_REGISTRY/v2"
DISCRIMINATOR_SCHEMA = "XENO_SYNTHETIC_DISCRIMINATOR_RECEIPT/v1"
BASE_FILENAME = "trigger2_hyperposition_derivation_bound_gate_v2.py"
BASE_REPO_PATH = "tools/" + BASE_FILENAME
SELF_REPO_PATH = "tools/trigger2_hyperposition_derivation_bound_gate_v3.py"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


base = _load_sibling(BASE_FILENAME, "trigger2_derivation_bound_gate_v2_for_v3")
lab = base.lab


def _digest(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _records(state: Any) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(state, dict):
        return out
    for branch in state.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for item in branch.get(field, []) or []:
                if isinstance(item, dict):
                    out.append(item)
    return out


def event_content_projection(event: Any) -> dict[str, Any] | None:
    """Return the immutable semantic event projection used for event identity.

    ``independence_qualified`` is excluded because the predecessor gate explicitly derives
    that value and treats the caller boolean as non-authoritative.  The digest field itself
    is excluded to avoid self-reference.  Every other caller-provided event field is bound,
    including unknown future extension fields, so semantic extensions cannot hide outside
    the identity preimage.
    """
    if not isinstance(event, dict):
        return None
    excluded = {"independence_qualified", "event_content_sha256"}
    return {k: deepcopy(event[k]) for k in sorted(event) if k not in excluded}


def event_content_sha256(event: Any) -> str | None:
    projection = event_content_projection(event)
    return _digest(projection) if projection is not None else None


def discriminator_receipt_sha256(receipt: Any) -> str | None:
    if not isinstance(receipt, dict):
        return None
    payload = {k: deepcopy(v) for k, v in receipt.items() if k != "receipt_sha256"}
    return _digest(payload)


def current_source_binding(generator_repo_path: Any) -> dict[str, Any]:
    inherited = base.current_source_binding(generator_repo_path)
    if not inherited.get("pass"):
        return inherited
    here = Path(__file__).resolve().parent
    return {
        **inherited,
        "base_gate_path": BASE_REPO_PATH,
        "base_gate_sha256": _sha256(here / BASE_FILENAME),
        "base_gate_schema": base.SCHEMA,
        "gate_path": SELF_REPO_PATH,
        "gate_sha256": _sha256(Path(__file__).resolve()),
        "gate_schema": SCHEMA,
    }


def _base_source_binding(binding: dict[str, Any]) -> dict[str, Any]:
    keys = (
        "labeler_path",
        "labeler_sha256",
        "labeler_schema",
        "generator_path",
        "generator_sha256",
    )
    return {k: binding[k] for k in keys if k in binding}


def _world_for_base(world: Any) -> Any:
    out = deepcopy(world)
    if isinstance(out, dict) and isinstance(out.get("event_dependence_registry"), dict):
        out["event_dependence_registry"]["schema"] = base.DEPENDENCE_SCHEMA
    return out


def _validate_event_identity(world: Any, state: Any, event: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(world, dict):
        return {"pass": False, "failures": ["FORMAL_WORLD_OBJECT_REQUIRED"]}
    registry = world.get("event_dependence_registry")
    if not isinstance(registry, dict) or registry.get("schema") != DEPENDENCE_SCHEMA:
        return {"pass": False, "failures": ["EVENT_DEPENDENCE_REGISTRY_V2_REQUIRED"]}
    events = registry.get("events")
    if not isinstance(events, dict):
        return {"pass": False, "failures": ["EVENT_DEPENDENCE_REGISTRY_EVENTS_REQUIRED"]}
    if not isinstance(event, dict) or not _nonempty(event.get("event_id")):
        return {"pass": False, "failures": ["EVENT_ID_REQUIRED_FOR_CONTENT_BINDING"]}

    event_id = event["event_id"]
    entry = events.get(event_id)
    if not isinstance(entry, dict):
        return {"pass": False, "failures": ["EVENT_NOT_IN_FORMAL_DEPENDENCE_REGISTRY"]}
    actual_digest = event_content_sha256(event)
    if not _nonempty(entry.get("event_content_sha256")):
        failures.append("REGISTRY_EVENT_CONTENT_DIGEST_REQUIRED")
    elif entry.get("event_content_sha256") != actual_digest:
        failures.append("EVENT_CONTENT_DIGEST_MISMATCH")

    # The predecessor also rechecks these values; keeping the check here makes the v2->v3
    # schema downgrade an internal implementation detail rather than a weaker proof path.
    for key in (
        "correlation_ancestry_id",
        "independence_group",
        "payload_key",
        "provenance",
        "test_id",
        "observed_outcome",
    ):
        if entry.get(key) != event.get(key):
            failures.append("EVENT_REGISTRY_BINDING_MISMATCH:" + key)

    prior = _records(state)
    same_id = [r for r in prior if r.get("event_id") == event_id]
    for record in same_id:
        prior_digest = record.get("event_content_sha256")
        if not _nonempty(prior_digest):
            failures.append("PRIOR_EVENT_DIGEST_MISSING_FOR_SAME_ID")
        elif prior_digest != actual_digest:
            failures.append("EVENT_ID_REBOUND_TO_DIFFERENT_CONTENT")

    depends = entry.get("depends_on_event_ids")
    if not isinstance(depends, list) or not all(_nonempty(x) for x in depends):
        failures.append("DEPENDENCY_EVENT_IDS_LIST_REQUIRED")
        depends = []
    for dependency_id in depends:
        dep_records = [r for r in prior if r.get("event_id") == dependency_id]
        if not dep_records:
            # The predecessor will also reject this; retain a v3-local reason.
            failures.append("DEPENDENCY_REFERENCE_NOT_IN_PRIOR_STATE:" + dependency_id)
            continue
        dep_digests = {r.get("event_content_sha256") for r in dep_records if _nonempty(r.get("event_content_sha256"))}
        if len(dep_digests) != len({r.get("event_content_sha256") for r in dep_records}):
            failures.append("DEPENDENCY_PRIOR_EVENT_DIGEST_MISSING:" + dependency_id)
            continue
        if len(dep_digests) != 1:
            failures.append("DEPENDENCY_EVENT_IDENTITY_AMBIGUOUS:" + dependency_id)
            continue
        dep_entry = events.get(dependency_id)
        if not isinstance(dep_entry, dict) or dep_entry.get("event_content_sha256") not in dep_digests:
            failures.append("DEPENDENCY_REGISTRY_DIGEST_MISMATCH:" + dependency_id)

    return {
        "pass": not failures,
        "failures": sorted(set(failures)),
        "event_id": event_id,
        "event_content_sha256": actual_digest,
        "caller_independence_flag_in_digest": False,
        "identity_rule": "EVENT_ID_PLUS_IMMUTABLE_CONTENT_DIGEST; SAME_ID_DIFFERENT_CONTENT_FAILS_CLOSED",
    }


def _validate_discriminator(world: Any, state: Any, event: Any, event_digest: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(world, dict) or not isinstance(state, dict) or not isinstance(event, dict):
        return {"pass": False, "failures": ["DISCRIMINATOR_CONTEXT_REQUIRED"]}
    receipts = world.get("discriminator_receipts")
    if not isinstance(receipts, dict):
        return {"pass": False, "failures": ["DISCRIMINATOR_RECEIPTS_REQUIRED"]}
    receipt = receipts.get(event.get("test_id"))
    if not isinstance(receipt, dict):
        return {"pass": False, "failures": ["DISCRIMINATOR_RECEIPT_FOR_EVENT_TEST_REQUIRED"]}
    if receipt.get("schema") != DISCRIMINATOR_SCHEMA:
        failures.append("DISCRIMINATOR_RECEIPT_SCHEMA_MISMATCH")
    if not _nonempty(receipt.get("receipt_id")):
        failures.append("DISCRIMINATOR_RECEIPT_ID_REQUIRED")
    if receipt.get("test_id") != event.get("test_id"):
        failures.append("DISCRIMINATOR_TEST_ID_MISMATCH")
    if receipt.get("world_id") != world.get("world_id"):
        failures.append("DISCRIMINATOR_WORLD_ID_MISMATCH")
    if receipt.get("event_id") != event.get("event_id"):
        failures.append("DISCRIMINATOR_EVENT_ID_MISMATCH")
    if receipt.get("event_content_sha256") != event_digest:
        failures.append("DISCRIMINATOR_EVENT_DIGEST_MISMATCH")
    if receipt.get("observed_outcome") != event.get("observed_outcome"):
        failures.append("DISCRIMINATOR_OUTCOME_MISMATCH")
    if receipt.get("admissible") is not True:
        failures.append("DISCRIMINATOR_NOT_ADMISSIBLE")
    if receipt.get("executed") is not True:
        failures.append("DISCRIMINATOR_NOT_EXECUTED")
    if receipt.get("coverage_complete") is not True:
        failures.append("DISCRIMINATOR_COVERAGE_NOT_DECLARED_COMPLETE")
    if receipt.get("canonical_truth_allowed") is not False:
        failures.append("DISCRIMINATOR_CANONICAL_TRUTH_MUST_BE_FALSE")
    if receipt.get("direct_effect_authority") is not False:
        failures.append("DISCRIMINATOR_DIRECT_EFFECT_AUTHORITY_MUST_BE_FALSE")
    if not isinstance(receipt.get("observation_qualified"), bool):
        failures.append("DISCRIMINATOR_OBSERVATION_QUALIFIED_BOOL_REQUIRED")
    if event.get("epistemic_type") == "OBSERVED" and receipt.get("observation_qualified") is not True:
        failures.append("OBSERVED_EVENT_REQUIRES_TYPED_OBSERVATION_RECEIPT")

    identity = receipt.get("execution_identity")
    if not isinstance(identity, dict):
        failures.append("DISCRIMINATOR_EXECUTION_IDENTITY_REQUIRED")
    else:
        for key in ("executor_id", "execution_id", "source_sha256"):
            if not _nonempty(identity.get(key)):
                failures.append("DISCRIMINATOR_EXECUTION_IDENTITY_FIELD_REQUIRED:" + key)

    # Coverage is derived from formal branch predictions, not caller claims.
    probe_event = deepcopy(event)
    if not isinstance(probe_event.get("independence_qualified"), bool):
        probe_event["independence_qualified"] = False
    derived = lab.derive_relations(world, state, probe_event)
    target_ids: list[str] = []
    if not derived.get("pass"):
        failures.append("DISCRIMINATOR_TARGET_DERIVATION_FAILED:" + str(derived.get("failure")))
    else:
        target_ids = sorted(derived.get("target_branch_ids", []))
        covered = receipt.get("covered_branch_ids")
        if not isinstance(covered, list) or sorted(covered) != target_ids:
            failures.append("DISCRIMINATOR_BRANCH_COVERAGE_MISMATCH")

    expected_receipt_sha = discriminator_receipt_sha256(receipt)
    if not _nonempty(receipt.get("receipt_sha256")):
        failures.append("DISCRIMINATOR_RECEIPT_DIGEST_REQUIRED")
    elif receipt.get("receipt_sha256") != expected_receipt_sha:
        failures.append("DISCRIMINATOR_RECEIPT_DIGEST_MISMATCH")

    return {
        "pass": not failures,
        "failures": sorted(set(failures)),
        "receipt_id": receipt.get("receipt_id"),
        "receipt_sha256": expected_receipt_sha,
        "target_branch_ids": target_ids,
        "observation_qualified": receipt.get("observation_qualified") is True,
        "typed_execution_proof": True,
    }


def _identity_bound_state(state_after: Any, event_id: Any, event_digest: Any, receipt_digest: Any) -> Any:
    out = deepcopy(state_after)
    if not isinstance(out, dict):
        return out
    for branch in out.get("branches", []) or []:
        if not isinstance(branch, dict):
            continue
        for field in ("E_plus", "E_minus", "F", "correlated_observations"):
            for record in branch.get(field, []) or []:
                if isinstance(record, dict) and record.get("event_id") == event_id:
                    record["event_content_sha256"] = event_digest
                    record["discriminator_receipt_sha256"] = receipt_digest
    return out


def _result(
    failures: list[str],
    *,
    source_binding: Any = None,
    event_identity: Any = None,
    discriminator: Any = None,
    base_result: Any = None,
) -> dict[str, Any]:
    failures = sorted(set(failures))
    recomputed = base_result.get("recomputed_target") if isinstance(base_result, dict) else None
    identity_state = None
    if not failures and isinstance(recomputed, dict):
        identity_state = _identity_bound_state(
            recomputed.get("state_after"),
            event_identity.get("event_id") if isinstance(event_identity, dict) else None,
            event_identity.get("event_content_sha256") if isinstance(event_identity, dict) else None,
            discriminator.get("receipt_sha256") if isinstance(discriminator, dict) else None,
        )
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "source_binding": source_binding,
        "event_identity_binding": event_identity,
        "discriminator_evidence_binding": discriminator,
        "recomputed_target": recomputed,
        "identity_bound_state_after": identity_state,
        "base_gate_schema": base.SCHEMA,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "evidence_boundary": "v3 synthetic candidate pre-admission only; typed proof is evaluator evidence, never canonical truth or runtime/training credit.",
    }


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    requested_binding = row.get("source_binding")
    generator_path = requested_binding.get("generator_path") if isinstance(requested_binding, dict) else None
    actual_binding = current_source_binding(generator_path)
    if not actual_binding.get("pass"):
        failures.append(str(actual_binding.get("failure")))
    else:
        expected_binding = {k: v for k, v in actual_binding.items() if k != "pass"}
        if requested_binding != expected_binding:
            failures.append("SOURCE_BINDING_MISMATCH_ACTUAL_LOCAL_BYTES")

    world = row.get("formal_task_world_evaluator_only")
    state = row.get("hyperposition_state_before_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    for value, code in (
        (world, "FORMAL_TASK_WORLD_REQUIRED"),
        (state, "HYPERPOSITION_STATE_BEFORE_REQUIRED"),
        (event, "SYNTHETIC_TEST_EVENT_REQUIRED"),
    ):
        if value is None:
            failures.append(code)

    event_identity = None
    discriminator = None
    if world is not None and state is not None and event is not None:
        event_identity = _validate_event_identity(world, state, event)
        if not event_identity.get("pass"):
            failures.extend("EVENT_IDENTITY:" + x for x in event_identity.get("failures", []))
        discriminator = _validate_discriminator(
            world,
            state,
            event,
            event_identity.get("event_content_sha256") if isinstance(event_identity, dict) else None,
        )
        if not discriminator.get("pass"):
            failures.extend("DISCRIMINATOR:" + x for x in discriminator.get("failures", []))

    if failures:
        return _result(
            failures,
            source_binding={k: v for k, v in actual_binding.items() if k != "pass"} if isinstance(actual_binding, dict) else None,
            event_identity=event_identity,
            discriminator=discriminator,
        )

    # Delegate all semantic relation/update/resolution rules to the existing v2 gate, after
    # an internal schema downgrade of the already-v3-validated dependence registry.
    delegated = deepcopy(row)
    delegated["formal_task_world_evaluator_only"] = _world_for_base(world)
    delegated["source_binding"] = _base_source_binding({k: v for k, v in actual_binding.items() if k != "pass"})
    base_result = base.adjudicate(delegated)
    if not base_result.get("pass"):
        failures.extend("BASE_GATE:" + x for x in base_result.get("failures", []))

    return _result(
        failures,
        source_binding={k: v for k, v in actual_binding.items() if k != "pass"},
        event_identity=event_identity,
        discriminator=discriminator,
        base_result=base_result,
    )
