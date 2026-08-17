"""Deterministic state helpers for live research/worker re-entry delivery.

This module does not perform external effects and is not a state authority. The caller must
serialize manifest writes with the canonical repository CAS mechanism before using an
ALLOW_DELIVERY decision.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Any, Mapping


PENDING = "PENDING"
CLAIMED = "CLAIMED"
UNKNOWN_DELIVERY = "UNKNOWN_DELIVERY"
DELIVERED_ACK_PENDING = "DELIVERED_ACK_PENDING"


class DeliveryStateError(ValueError):
    """Raised when a fail-closed delivery transition is not authorized."""


@dataclass(frozen=True)
class DeliveryState:
    route_id: str
    version: int = 0
    status: str = PENDING
    claim_id: str | None = None
    comment_id: int | None = None


def _canonical_json(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def route_id(
    *,
    run_id: str,
    receiver: str,
    message_kind: str,
    decision: str,
    payload_digest: str,
) -> str:
    required = (run_id, receiver, message_kind, decision, payload_digest)
    if not all(isinstance(item, str) and item for item in required):
        raise DeliveryStateError("route identity fields must be non-empty strings")
    packet = {
        "decision": decision,
        "message_kind": message_kind,
        "payload_digest": payload_digest,
        "receiver": receiver,
        "run_id": run_id,
    }
    return hashlib.sha256(_canonical_json(packet)).hexdigest()


def claim(
    state: DeliveryState,
    *,
    expected_version: int,
    claim_id: str,
) -> DeliveryState:
    """Return the claimed state only when the caller's canonical CAS view is current."""
    if not claim_id:
        raise DeliveryStateError("claim_id required")
    if state.version != expected_version:
        raise DeliveryStateError("stale delivery manifest version")
    if state.status != PENDING or state.claim_id is not None or state.comment_id is not None:
        raise DeliveryStateError("route is not claimable")
    return replace(
        state,
        version=state.version + 1,
        status=CLAIMED,
        claim_id=claim_id,
    )


def authorize_delivery(state: DeliveryState, *, claim_id: str) -> bool:
    """External delivery is allowed only for the exact canonical owner claim."""
    return state.status == CLAIMED and state.claim_id == claim_id and state.comment_id is None


def mark_unknown(state: DeliveryState, *, claim_id: str) -> DeliveryState:
    if state.status != CLAIMED or state.claim_id != claim_id:
        raise DeliveryStateError("only the active claimant may mark delivery unknown")
    return replace(state, version=state.version + 1, status=UNKNOWN_DELIVERY)


def finalize_delivery(
    state: DeliveryState,
    *,
    claim_id: str,
    comment_id: int,
    marker_route_id: str,
) -> DeliveryState:
    """Finalize only a delivery carrying the exact deterministic route marker."""
    if state.status not in {CLAIMED, UNKNOWN_DELIVERY} or state.claim_id != claim_id:
        raise DeliveryStateError("delivery is not owned by this claim")
    if not isinstance(comment_id, int) or comment_id <= 0:
        raise DeliveryStateError("positive comment_id required")
    if marker_route_id != state.route_id:
        raise DeliveryStateError("delivery route marker mismatch")
    return replace(
        state,
        version=state.version + 1,
        status=DELIVERED_ACK_PENDING,
        comment_id=comment_id,
    )


def recovery_decision(
    state: DeliveryState,
    *,
    claim_expired: bool,
    exact_marker_comment_id: int | None,
    target_scan_available: bool,
) -> str:
    """Return a fail-closed recovery action; never authorize a blind retry."""
    if state.status not in {CLAIMED, UNKNOWN_DELIVERY}:
        return "NO_RETRY"
    if exact_marker_comment_id is not None:
        return "FINALIZE_EXISTING_DELIVERY"
    if not target_scan_available:
        return "KEEP_UNKNOWN"
    if not claim_expired:
        return "WAIT_FOR_ACTIVE_CLAIM"
    return "RECLAIM_BY_NEW_CAS"
