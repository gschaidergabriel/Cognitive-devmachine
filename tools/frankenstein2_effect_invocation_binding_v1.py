#!/usr/bin/env python3
"""Call-scoped effect/result correlation guard for Frankenstein 2.0.

This module is a deterministic source primitive only. It does not execute tools,
grant EffectGate authority, or mint completion/runtime credit.

The purpose is to keep an externally observed tool-use / invocation identifier
separate from session context and from the target row selected by a caller. A
mutable session-scoped router can otherwise mis-attach a result when two calls in
one session interleave; equal result digests make digest-only checks insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


SCHEMA = "FRANKENSTEIN2_EFFECT_INVOCATION_BINDING/v1"


class EffectInvocationBindingError(RuntimeError):
    pass


class ResultReentryStore(Protocol):
    def reenter_result(
        self,
        invocation_id: str,
        *,
        result_digest: str,
        now_ts: float | None = None,
    ) -> None: ...


@dataclass(frozen=True)
class BoundResultIdentity:
    target_invocation_id: str
    observed_invocation_id: str
    result_digest: str


def verify_bound_result_identity(
    *,
    target_invocation_id: str,
    observed_invocation_id: str,
    result_digest: str,
) -> BoundResultIdentity:
    """Fail closed unless the external call-scoped id equals the selected target id."""
    if not target_invocation_id:
        raise EffectInvocationBindingError("MISSING_TARGET_INVOCATION_ID")
    if not observed_invocation_id:
        raise EffectInvocationBindingError("MISSING_OBSERVED_INVOCATION_ID")
    if target_invocation_id != observed_invocation_id:
        raise EffectInvocationBindingError("RESULT_REENTRY_INVOCATION_MISMATCH")
    if not result_digest:
        raise EffectInvocationBindingError("MISSING_RESULT_DIGEST")
    return BoundResultIdentity(
        target_invocation_id=target_invocation_id,
        observed_invocation_id=observed_invocation_id,
        result_digest=result_digest,
    )


def reenter_bound_result(
    store: ResultReentryStore,
    *,
    target_invocation_id: str,
    observed_invocation_id: str,
    result_digest: str,
    now_ts: float | None = None,
) -> BoundResultIdentity:
    """Verify call-scoped identity before delegating to the lifecycle store."""
    bound = verify_bound_result_identity(
        target_invocation_id=target_invocation_id,
        observed_invocation_id=observed_invocation_id,
        result_digest=result_digest,
    )
    store.reenter_result(
        bound.target_invocation_id,
        result_digest=bound.result_digest,
        now_ts=now_ts,
    )
    return bound
