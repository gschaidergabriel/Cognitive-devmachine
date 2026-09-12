from __future__ import annotations

import dataclasses
import enum
import hashlib
import json
from typing import Any, Callable


class Decision(str, enum.Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    REQUIRE_CONFIRMATION = "REQUIRE_CONFIRMATION"
    DEGRADE_TO_PROPOSAL = "DEGRADE_TO_PROPOSAL"
    UNKNOWN = "UNKNOWN"


class AlignmentError(RuntimeError):
    pass


class OutcomeUnknown(AlignmentError):
    """The effect may have crossed the boundary; do not replay automatically."""


def _token(name: str, value: str | None) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise AlignmentError(f"INVALID_{name.upper()}")
    if len(value) > 512:
        raise AlignmentError(f"INVALID_{name.upper()}")
    return value


def _sha(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclasses.dataclass(frozen=True, slots=True)
class EffectBinding:
    effect_id: str
    binding_id: str
    invocation_id: str
    tool_use_id: str
    delegation_id: str
    child_identity_sha256: str
    request_sha256: str
    organ_id: str
    owner_id: str | None = None
    machine_id: str | None = None
    runtime_epoch_id: str | None = None

    @classmethod
    def prepare(
        cls,
        *,
        effect_id: str,
        invocation_id: str,
        tool_use_id: str,
        delegation_id: str,
        child_identity_sha256: str,
        request: Any,
        organ_id: str,
        owner_id: str | None = None,
        machine_id: str | None = None,
        runtime_epoch_id: str | None = None,
    ) -> "EffectBinding":
        request_sha256 = _sha(request)
        binding_material = {
            "effect_id": effect_id,
            "invocation_id": invocation_id,
            "tool_use_id": tool_use_id,
            "delegation_id": delegation_id,
            "child_identity_sha256": child_identity_sha256,
            "request_sha256": request_sha256,
            "organ_id": organ_id,
            "owner_id": owner_id,
            "machine_id": machine_id,
            "runtime_epoch_id": runtime_epoch_id,
        }
        binding_id = _sha(binding_material)
        return cls(
            effect_id=_token("effect_id", effect_id),
            binding_id=binding_id,
            invocation_id=_token("invocation_id", invocation_id),
            tool_use_id=_token("tool_use_id", tool_use_id),
            delegation_id=_token("delegation_id", delegation_id),
            child_identity_sha256=_token("child_identity_sha256", child_identity_sha256),
            request_sha256=request_sha256,
            organ_id=_token("organ_id", organ_id),
            owner_id=owner_id,
            machine_id=machine_id,
            runtime_epoch_id=runtime_epoch_id,
        )


@dataclasses.dataclass(frozen=True, slots=True)
class GateEvidence:
    authority_ref: str
    decision_id: str
    decision: Decision
    effect_id: str
    binding_id: str
    invocation_id: str
    tool_use_id: str
    delegation_id: str
    child_identity_sha256: str
    request_sha256: str
    organ_id: str


@dataclasses.dataclass(frozen=True, slots=True)
class ExecutorObservation:
    effect_id: str
    binding_id: str
    invocation_id: str
    tool_use_id: str
    delegation_id: str
    child_identity_sha256: str
    request_sha256: str
    organ_id: str
    result_id: str
    result_sha256: str


@dataclasses.dataclass(frozen=True, slots=True)
class DispatchResult:
    dispatched: bool
    decision: Decision
    decision_id: str
    authority_ref: str
    observation: ExecutorObservation | None
    block_reason: str | None = None


def _assert_same(label: str, actual: str, expected: str) -> None:
    if actual != expected:
        raise AlignmentError(f"{label}_MISMATCH")


def validate_gate(binding: EffectBinding, gate: GateEvidence) -> None:
    pairs = {
        "EFFECT_ID": (gate.effect_id, binding.effect_id),
        "BINDING_ID": (gate.binding_id, binding.binding_id),
        "INVOCATION_ID": (gate.invocation_id, binding.invocation_id),
        "TOOL_USE_ID": (gate.tool_use_id, binding.tool_use_id),
        "DELEGATION_ID": (gate.delegation_id, binding.delegation_id),
        "CHILD_IDENTITY_SHA256": (gate.child_identity_sha256, binding.child_identity_sha256),
        "REQUEST_SHA256": (gate.request_sha256, binding.request_sha256),
        "ORGAN_ID": (gate.organ_id, binding.organ_id),
    }
    for label, (actual, expected) in pairs.items():
        _assert_same(label, actual, expected)


def validate_post(binding: EffectBinding, obs: ExecutorObservation) -> None:
    pairs = {
        "POST_EFFECT_ID": (obs.effect_id, binding.effect_id),
        "POST_BINDING_ID": (obs.binding_id, binding.binding_id),
        "POST_INVOCATION_ID": (obs.invocation_id, binding.invocation_id),
        "POST_TOOL_USE_ID": (obs.tool_use_id, binding.tool_use_id),
        "POST_DELEGATION_ID": (obs.delegation_id, binding.delegation_id),
        "POST_CHILD_IDENTITY_SHA256": (obs.child_identity_sha256, binding.child_identity_sha256),
        "POST_REQUEST_SHA256": (obs.request_sha256, binding.request_sha256),
        "POST_ORGAN_ID": (obs.organ_id, binding.organ_id),
    }
    for label, (actual, expected) in pairs.items():
        _assert_same(label, actual, expected)


def dispatch(
    binding: EffectBinding,
    *,
    authorize: Callable[[EffectBinding], GateEvidence],
    executor: Callable[[EffectBinding], ExecutorObservation],
) -> DispatchResult:
    """Policy-neutral executor interlock.

    The executor never mints ALLOW. Any non-ALLOW decision blocks. Any uncertain
    post-dispatch state becomes OutcomeUnknown and MUST NOT be automatically replayed.
    """
    try:
        gate = authorize(binding)
    except Exception as exc:
        raise AlignmentError("EXTERNAL_EFFECT_AUTHORITY_FAILED") from exc
    if not isinstance(gate, GateEvidence):
        raise AlignmentError("INVALID_GATE_EVIDENCE")
    validate_gate(binding, gate)

    if gate.decision is not Decision.ALLOW:
        return DispatchResult(
            dispatched=False,
            decision=gate.decision,
            decision_id=gate.decision_id,
            authority_ref=gate.authority_ref,
            observation=None,
            block_reason=f"EXTERNAL_GATE_{gate.decision.value}",
        )

    try:
        obs = executor(binding)
    except Exception as exc:
        raise OutcomeUnknown("EXECUTOR_OUTCOME_UNKNOWN_NO_AUTOMATIC_REPLAY") from exc
    if not isinstance(obs, ExecutorObservation):
        raise OutcomeUnknown("INVALID_EXECUTOR_OBSERVATION_NO_AUTOMATIC_REPLAY")
    try:
        validate_post(binding, obs)
    except AlignmentError as exc:
        raise OutcomeUnknown("POST_CORRELATION_FAILED_NO_AUTOMATIC_REPLAY") from exc

    return DispatchResult(
        dispatched=True,
        decision=gate.decision,
        decision_id=gate.decision_id,
        authority_ref=gate.authority_ref,
        observation=obs,
    )
