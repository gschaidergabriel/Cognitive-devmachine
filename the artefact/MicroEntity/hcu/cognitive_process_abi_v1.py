#!/usr/bin/env python3
"""Typed size-independent Cognitive Process ABI for EntityOS/HCU.

Source/component scope only. This module defines semantic work, execution claim,
result and integration identities. It does not create canonical truth, effect,
security, capability or coordinator authority.

Identity law:
- work_id = semantic cognitive work identity; independent of physical node,
  grid size, attempt and coordinator topology.
- claim_id = one admitted execution attempt; binds work to route, executor,
  generation, state snapshot and external capability/coordinator authority.
- result_id = one immutable result bound to one claim and payload identity.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence
import hashlib
import importlib
import sys

HCU_DIR = Path(__file__).resolve().parent
if str(HCU_DIR) not in sys.path:
    sys.path.insert(0, str(HCU_DIR))


def _import_exact_repo_module(name: str, expected_path: Path):
    module = importlib.import_module(name)
    raw_path = getattr(module, "__file__", None)
    if not raw_path:
        raise RuntimeError(f"COGNITIVE_ABI_AUTHORITY_MODULE_PATH_MISSING:{name}")
    loaded = Path(raw_path).resolve()
    expected = expected_path.resolve()
    if loaded != expected:
        raise RuntimeError(f"COGNITIVE_ABI_AUTHORITY_MODULE_SHADOWED:{name}:{loaded}:{expected}")
    return module


_canonicalization = _import_exact_repo_module(
    "entry_canonicalization_v1", HCU_DIR / "entry_canonicalization_v1.py"
)
canonicalize = _canonicalization.canonicalize
CanonicalizationError = _canonicalization.CanonicalizationError

WORK_SCHEMA = "COGNITIVE_WORK/v1"
CLAIM_SCHEMA = "COGNITIVE_EXECUTION_CLAIM/v1"
RESULT_SCHEMA = "COGNITIVE_RESULT/v1"
INTEGRATION_SCHEMA = "COGNITIVE_INTEGRATION_DECISION/v1"
EFFECT_REQUEST_SCHEMA = "COGNITIVE_EFFECT_REQUEST/v1"

PROCESS_IDS = tuple(f"AZP{i:02d}" for i in range(1, 21))
DETERMINISTIC_BOUNDARY_PROCESSES = frozenset({"AZP02", "AZP12", "AZP16", "AZP17"})
JSPACE_PROCESS = "AZP09"
EFFECT_PROPOSAL_PROCESS = "AZP11"

EPISTEMIC_CLASSES = frozenset({
    "OBSERVED",
    "INFERRED",
    "CANDIDATE",
    "MEASUREMENT",
    "COUNTEREVIDENCE",
    "UNKNOWN",
})
RESULT_STATUSES = frozenset({"COMPLETED", "BLOCKED", "PARTIAL", "UNKNOWN"})
INTEGRATION_ACTIONS = frozenset({"ADMIT_S1", "REBASE_REQUIRED", "REJECT"})


class CognitiveABIError(ValueError):
    pass


def _canonical_bytes(value: Any) -> bytes:
    try:
        return canonicalize(value)
    except CanonicalizationError as exc:
        raise CognitiveABIError(f"NONCANONICAL_PACKET:{exc}") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CognitiveABIError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha(value: Any, field: str) -> str:
    text = _nonempty(value, field)
    if len(text) != 64 or any(ch not in "0123456789abcdef" for ch in text):
        raise CognitiveABIError(f"{field}:SHA256_HEX_REQUIRED")
    return text


def _strings(values: Sequence[str], field: str, *, allow_empty: bool = True) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise CognitiveABIError(f"{field}:SEQUENCE_REQUIRED")
    out = tuple(_nonempty(v, field) for v in values)
    if not allow_empty and not out:
        raise CognitiveABIError(f"{field}:NONEMPTY_REQUIRED")
    if len(set(out)) != len(out):
        raise CognitiveABIError(f"{field}:DUPLICATE_FORBIDDEN")
    return tuple(sorted(out))


def _process_id(value: Any) -> str:
    p = _nonempty(value, "process_id")
    if p not in PROCESS_IDS:
        raise CognitiveABIError("process_id:UNSUPPORTED")
    return p


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CognitiveABIError("generation:NONNEGATIVE_INT_REQUIRED")
    return value


def _epoch(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise CognitiveABIError(f"{field}:NONNEGATIVE_INT_REQUIRED")
    return value


@dataclass(frozen=True)
class CognitiveWork:
    schema: str
    work_id: str
    causal_event_id: str
    admission_id: str
    workspace_episode_id: str
    process_id: str
    parent_work_id: str | None
    objective_ref: str
    objective_sha256: str
    input_refs: tuple[str, ...]
    precondition_refs: tuple[str, ...]
    completion_criteria_refs: tuple[str, ...]
    semantic_generation: int


@dataclass(frozen=True)
class ExecutionClaim:
    schema: str
    claim_id: str
    work_id: str
    process_id: str
    route_decision_id: str
    executor_id: str
    executor_runtime_sha256: str
    executor_generation: int
    state_epoch: int
    state_digest: str
    capability_authority_sha256: str
    coordinator_lease_id: str
    attempt: int


@dataclass(frozen=True)
class CognitiveResult:
    schema: str
    result_id: str
    work_id: str
    claim_id: str
    process_id: str
    executor_id: str
    base_state_epoch: int
    base_state_digest: str
    payload_ref: str
    payload_sha256: str
    epistemic_class: str
    status: str
    evidence_refs: tuple[str, ...]
    truth_authority: bool
    effect_authority: bool


@dataclass(frozen=True)
class IntegrationDecision:
    schema: str
    decision_id: str
    result_id: str
    action: str
    current_state_epoch: int
    current_state_digest: str
    coordinator_lease_id: str
    reason: str
    s1_only: bool
    s0_truth_authority: bool
    effect_authority: bool


@dataclass(frozen=True)
class EffectRequest:
    schema: str
    effect_request_id: str
    source_result_id: str
    work_id: str
    process_id: str
    effect_type: str
    payload_ref: str
    payload_sha256: str
    capability_scope_ref: str
    generation: int
    effect_authority: bool


def create_work(
    *,
    causal_event_id: str,
    admission_id: str,
    workspace_episode_id: str,
    process_id: str,
    objective_ref: str,
    objective: Any,
    input_refs: Sequence[str] = (),
    precondition_refs: Sequence[str] = (),
    completion_criteria_refs: Sequence[str] = (),
    semantic_generation: int = 0,
    parent_work_id: str | None = None,
) -> CognitiveWork:
    """Create stable semantic work identity.

    Deliberately excludes node id, route, attempt, claim, coordinator, grid size,
    clock time and mutable S1 epoch/digest from work_id.
    """
    causal_event_id = _nonempty(causal_event_id, "causal_event_id")
    admission_id = _nonempty(admission_id, "admission_id")
    workspace_episode_id = _nonempty(workspace_episode_id, "workspace_episode_id")
    process_id = _process_id(process_id)
    objective_ref = _nonempty(objective_ref, "objective_ref")
    objective_sha256 = _sha256(objective)
    input_refs_n = _strings(input_refs, "input_refs")
    precondition_refs_n = _strings(precondition_refs, "precondition_refs")
    completion_refs_n = _strings(completion_criteria_refs, "completion_criteria_refs")
    semantic_generation = _generation(semantic_generation)
    if parent_work_id is not None:
        parent_work_id = _sha(parent_work_id, "parent_work_id")

    identity = {
        "schema": WORK_SCHEMA,
        "causal_event_id": causal_event_id,
        "workspace_episode_id": workspace_episode_id,
        "process_id": process_id,
        "parent_work_id": parent_work_id,
        "objective_ref": objective_ref,
        "objective_sha256": objective_sha256,
        "input_refs": list(input_refs_n),
        "precondition_refs": list(precondition_refs_n),
        "completion_criteria_refs": list(completion_refs_n),
        "semantic_generation": semantic_generation,
    }
    work_id = _sha256(identity)
    return CognitiveWork(
        WORK_SCHEMA,
        work_id,
        causal_event_id,
        admission_id,
        workspace_episode_id,
        process_id,
        parent_work_id,
        objective_ref,
        objective_sha256,
        input_refs_n,
        precondition_refs_n,
        completion_refs_n,
        semantic_generation,
    )


def claim_work(
    work: CognitiveWork,
    *,
    route_decision_id: str,
    executor_id: str,
    executor_runtime_sha256: str,
    executor_generation: int,
    state_epoch: int,
    state_digest: str,
    capability_authority_sha256: str,
    coordinator_lease_id: str,
    attempt: int,
) -> ExecutionClaim:
    if not isinstance(work, CognitiveWork) or work.schema != WORK_SCHEMA:
        raise CognitiveABIError("work:COGNITIVE_WORK_REQUIRED")
    route_decision_id = _nonempty(route_decision_id, "route_decision_id")
    executor_id = _nonempty(executor_id, "executor_id")
    executor_runtime_sha256 = _sha(executor_runtime_sha256, "executor_runtime_sha256")
    executor_generation = _generation(executor_generation)
    state_epoch = _epoch(state_epoch, "state_epoch")
    state_digest = _sha(state_digest, "state_digest")
    capability_authority_sha256 = _sha(capability_authority_sha256, "capability_authority_sha256")
    coordinator_lease_id = _nonempty(coordinator_lease_id, "coordinator_lease_id")
    if isinstance(attempt, bool) or not isinstance(attempt, int) or attempt < 1:
        raise CognitiveABIError("attempt:POSITIVE_INT_REQUIRED")

    identity = {
        "schema": CLAIM_SCHEMA,
        "work_id": work.work_id,
        "process_id": work.process_id,
        "route_decision_id": route_decision_id,
        "executor_id": executor_id,
        "executor_runtime_sha256": executor_runtime_sha256,
        "executor_generation": executor_generation,
        "state_epoch": state_epoch,
        "state_digest": state_digest,
        "capability_authority_sha256": capability_authority_sha256,
        "coordinator_lease_id": coordinator_lease_id,
        "attempt": attempt,
    }
    claim_id = _sha256(identity)
    return ExecutionClaim(
        CLAIM_SCHEMA,
        claim_id,
        work.work_id,
        work.process_id,
        route_decision_id,
        executor_id,
        executor_runtime_sha256,
        executor_generation,
        state_epoch,
        state_digest,
        capability_authority_sha256,
        coordinator_lease_id,
        attempt,
    )


def create_result(
    work: CognitiveWork,
    claim: ExecutionClaim,
    *,
    payload_ref: str,
    payload: Any,
    epistemic_class: str,
    status: str = "COMPLETED",
    evidence_refs: Sequence[str] = (),
    truth_authority: bool = False,
    effect_authority: bool = False,
) -> CognitiveResult:
    if work.work_id != claim.work_id or work.process_id != claim.process_id:
        raise CognitiveABIError("CLAIM_WORK_IDENTITY_MISMATCH")
    if truth_authority is not False:
        raise CognitiveABIError("COGNITIVE_RESULT_CANNOT_SELF_GRANT_TRUTH_AUTHORITY")
    if effect_authority is not False:
        raise CognitiveABIError("COGNITIVE_RESULT_CANNOT_SELF_GRANT_EFFECT_AUTHORITY")
    payload_ref = _nonempty(payload_ref, "payload_ref")
    payload_sha256 = _sha256(payload)
    epistemic_class = _nonempty(epistemic_class, "epistemic_class")
    if epistemic_class not in EPISTEMIC_CLASSES:
        raise CognitiveABIError("epistemic_class:UNSUPPORTED")
    status = _nonempty(status, "status")
    if status not in RESULT_STATUSES:
        raise CognitiveABIError("status:UNSUPPORTED")
    if status == "UNKNOWN" and epistemic_class != "UNKNOWN":
        raise CognitiveABIError("UNKNOWN_STATUS_REQUIRES_UNKNOWN_EPISTEMIC_CLASS")
    if work.process_id == JSPACE_PROCESS and epistemic_class not in {
        "MEASUREMENT",
        "COUNTEREVIDENCE",
        "UNKNOWN",
    }:
        raise CognitiveABIError("JSPACE_RESULT_MUST_REMAIN_MEASUREMENT_COUNTEREVIDENCE_OR_UNKNOWN")
    evidence_refs_n = _strings(evidence_refs, "evidence_refs")

    identity = {
        "schema": RESULT_SCHEMA,
        "work_id": work.work_id,
        "claim_id": claim.claim_id,
        "process_id": work.process_id,
        "executor_id": claim.executor_id,
        "base_state_epoch": claim.state_epoch,
        "base_state_digest": claim.state_digest,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
        "epistemic_class": epistemic_class,
        "status": status,
        "evidence_refs": list(evidence_refs_n),
        "truth_authority": False,
        "effect_authority": False,
    }
    result_id = _sha256(identity)
    return CognitiveResult(
        RESULT_SCHEMA,
        result_id,
        work.work_id,
        claim.claim_id,
        work.process_id,
        claim.executor_id,
        claim.state_epoch,
        claim.state_digest,
        payload_ref,
        payload_sha256,
        epistemic_class,
        status,
        evidence_refs_n,
        False,
        False,
    )


def decide_integration(
    result: CognitiveResult,
    *,
    current_state_epoch: int,
    current_state_digest: str,
    coordinator_lease_id: str,
    lease_valid: bool,
    scope_allows_process: bool,
) -> IntegrationDecision:
    """Return a non-S0 integration decision without rewriting result identity."""
    if not isinstance(result, CognitiveResult) or result.schema != RESULT_SCHEMA:
        raise CognitiveABIError("result:COGNITIVE_RESULT_REQUIRED")
    current_state_epoch = _epoch(current_state_epoch, "current_state_epoch")
    current_state_digest = _sha(current_state_digest, "current_state_digest")
    coordinator_lease_id = _nonempty(coordinator_lease_id, "coordinator_lease_id")
    if not isinstance(lease_valid, bool) or not isinstance(scope_allows_process, bool):
        raise CognitiveABIError("integration_flags:BOOL_REQUIRED")

    if not lease_valid:
        action, reason = "REJECT", "INVALID_OR_STALE_COORDINATOR_LEASE"
    elif not scope_allows_process:
        action, reason = "REJECT", "PROCESS_OUTSIDE_COORDINATOR_SCOPE"
    elif result.base_state_epoch == current_state_epoch and result.base_state_digest == current_state_digest:
        action, reason = "ADMIT_S1", "RESULT_BASE_MATCHES_CURRENT_S1"
    else:
        action, reason = "REBASE_REQUIRED", "RESULT_AUTHENTIC_BUT_BASE_S1_ADVANCED"

    identity = {
        "schema": INTEGRATION_SCHEMA,
        "result_id": result.result_id,
        "action": action,
        "current_state_epoch": current_state_epoch,
        "current_state_digest": current_state_digest,
        "coordinator_lease_id": coordinator_lease_id,
        "reason": reason,
        "s1_only": True,
        "s0_truth_authority": False,
        "effect_authority": False,
    }
    return IntegrationDecision(
        INTEGRATION_SCHEMA,
        _sha256(identity),
        result.result_id,
        action,
        current_state_epoch,
        current_state_digest,
        coordinator_lease_id,
        reason,
        True,
        False,
        False,
    )


def create_effect_request(
    work: CognitiveWork,
    result: CognitiveResult,
    *,
    effect_type: str,
    payload_ref: str,
    payload: Any,
    capability_scope_ref: str,
    generation: int,
) -> EffectRequest:
    """Create a PROPOSE_ONLY typed request for deterministic EffectGate/Journal."""
    if work.process_id != EFFECT_PROPOSAL_PROCESS or result.process_id != EFFECT_PROPOSAL_PROCESS:
        raise CognitiveABIError("EFFECT_REQUEST_REQUIRES_AZP11_PLAN_ACTION_CANDIDATE")
    if work.work_id != result.work_id:
        raise CognitiveABIError("EFFECT_REQUEST_WORK_RESULT_MISMATCH")
    effect_type = _nonempty(effect_type, "effect_type")
    payload_ref = _nonempty(payload_ref, "payload_ref")
    payload_sha256 = _sha256(payload)
    capability_scope_ref = _nonempty(capability_scope_ref, "capability_scope_ref")
    generation = _generation(generation)

    identity = {
        "schema": EFFECT_REQUEST_SCHEMA,
        "source_result_id": result.result_id,
        "work_id": work.work_id,
        "process_id": EFFECT_PROPOSAL_PROCESS,
        "effect_type": effect_type,
        "payload_ref": payload_ref,
        "payload_sha256": payload_sha256,
        "capability_scope_ref": capability_scope_ref,
        "generation": generation,
        "effect_authority": False,
    }
    return EffectRequest(
        EFFECT_REQUEST_SCHEMA,
        _sha256(identity),
        result.result_id,
        work.work_id,
        EFFECT_PROPOSAL_PROCESS,
        effect_type,
        payload_ref,
        payload_sha256,
        capability_scope_ref,
        generation,
        False,
    )
