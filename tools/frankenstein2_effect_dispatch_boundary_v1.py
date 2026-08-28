#!/usr/bin/env python3
"""Fail-closed pre-dispatch boundary primitive for Frankenstein 2.0 effects.

This is a source-level adapter only. It does not itself prove that every live host/tool
path routes through this boundary, so it cannot mint runtime or EffectGate enforcement
credit. Its job is narrower: make the intended executor ordering executable and testable.

Required ordering for an admitted effect:
  enforcement receipt -> SUBMITTED latch -> real dispatch callback
  -> atomic execution receipt + v2 identity metadata bundle

DENY/UNKNOWN never call the dispatcher. Once SUBMITTED has been latched, any callback or
receipt-persistence failure is classified as outcome-unknown and must not be blindly retried.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol, TypeVar

try:
    from .frankenstein2_execution_receipt_atomicity_v1 import record_execution_bundle_atomic
except ImportError:
    from frankenstein2_execution_receipt_atomicity_v1 import record_execution_bundle_atomic

SCHEMA = "FRANKENSTEIN2_EFFECT_DISPATCH_BOUNDARY/v1"


class EffectDispatchBoundaryError(RuntimeError):
    pass


class EffectSubmittedOutcomeUnknown(EffectDispatchBoundaryError):
    """Submission may have happened; caller must reconcile rather than blind-retry."""


@dataclass(frozen=True)
class ExecutionObservation:
    executable_id: str
    command_digest: str
    environment_id: str
    exit_code: int
    result_digest: str
    source_digest: str
    duplicate_state: str = "UNIQUE"
    status: str | None = None

    def resolved_status(self) -> str:
        if self.status is not None:
            return self.status
        return "SUCCEEDED" if self.exit_code == 0 else "FAILED"


@dataclass(frozen=True)
class DispatchBoundaryDecision:
    schema: str
    invocation_id: str
    admission_decision: str
    dispatched: bool
    terminal_class: str
    result_digest: str | None = None


class EffectLifecyclePort(Protocol):
    def record_enforcement(
        self,
        invocation_id: str,
        *,
        boundary_id: str,
        dispatch_permitted: bool,
        now_ts: float | None = None,
    ) -> None: ...

    def mark_submitted(self, invocation_id: str, *, now_ts: float | None = None) -> None: ...


TStore = TypeVar("TStore", bound=EffectLifecyclePort)


def guarded_dispatch(
    store: TStore,
    *,
    invocation_id: str,
    admission_decision: str,
    boundary_id: str,
    dispatch: Callable[[], ExecutionObservation],
    now_ts: float | None = None,
) -> DispatchBoundaryDecision:
    """Execute exactly one admitted callback behind the lifecycle pre-dispatch gate.

    The lifecycle store remains the identity/policy cross-check. A caller cannot turn a
    stored DENY into an ALLOW merely by passing ``admission_decision='ALLOW'`` because
    ``record_enforcement`` must reject a contradictory decision before the callback runs.
    """
    decision = str(admission_decision).upper()
    if decision not in {"ALLOW", "DENY", "UNKNOWN"}:
        raise EffectDispatchBoundaryError(f"INVALID_ADMISSION_DECISION:{decision}")
    if not invocation_id:
        raise EffectDispatchBoundaryError("MISSING_INVOCATION_ID")
    if not boundary_id:
        raise EffectDispatchBoundaryError("MISSING_BOUNDARY_ID")

    permitted = decision == "ALLOW"
    store.record_enforcement(
        invocation_id,
        boundary_id=boundary_id,
        dispatch_permitted=permitted,
        now_ts=now_ts,
    )

    if not permitted:
        return DispatchBoundaryDecision(
            SCHEMA,
            invocation_id,
            decision,
            False,
            "BLOCKED_PRE_DISPATCH",
            None,
        )

    # Latch SUBMITTED before entering the real callback. From this point onward a failure
    # is not safely replayable without effect-specific reconciliation/idempotency proof.
    store.mark_submitted(invocation_id, now_ts=now_ts)
    try:
        observation = dispatch()
    except BaseException as exc:
        raise EffectSubmittedOutcomeUnknown(
            f"DISPATCH_CALLBACK_FAILED_AFTER_SUBMITTED:{type(exc).__name__}"
        ) from exc

    try:
        if not isinstance(observation, ExecutionObservation):
            raise EffectDispatchBoundaryError("DISPATCH_RETURNED_INVALID_OBSERVATION")
        if not observation.executable_id or not observation.environment_id:
            raise EffectDispatchBoundaryError("MISSING_EXECUTION_PROVENANCE")
        if not observation.command_digest or not observation.result_digest:
            raise EffectDispatchBoundaryError("MISSING_EXECUTION_DIGEST")
        if not observation.source_digest:
            raise EffectDispatchBoundaryError("MISSING_EXECUTION_SOURCE_DIGEST")
        if not observation.duplicate_state:
            raise EffectDispatchBoundaryError("MISSING_DUPLICATE_STATE")

        status = observation.resolved_status()
        if status == "SUCCEEDED" and observation.exit_code != 0:
            raise EffectDispatchBoundaryError("SUCCEEDED_STATUS_CONTRADICTS_NONZERO_EXIT")

        record_execution_bundle_atomic(
            store,
            invocation_id,
            executable_id=observation.executable_id,
            command_digest=observation.command_digest,
            environment_id=observation.environment_id,
            exit_code=observation.exit_code,
            result_digest=observation.result_digest,
            source_digest=observation.source_digest,
            duplicate_state=observation.duplicate_state,
            status=status,
            now_ts=now_ts,
        )
    except BaseException as exc:
        raise EffectSubmittedOutcomeUnknown(
            f"EXECUTION_RECEIPT_PERSISTENCE_FAILED_AFTER_SUBMITTED:{type(exc).__name__}"
        ) from exc

    return DispatchBoundaryDecision(
        SCHEMA,
        invocation_id,
        decision,
        True,
        "EXECUTION_RECORDED",
        observation.result_digest,
    )
