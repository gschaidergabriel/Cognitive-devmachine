from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any, Sequence

from loop_dynamics_reference import LoopDynamicsReadout, decide_recurrence
from posthoc_recurrence_readout import PostHocDecision, decide_posthoc

VERSION = "frank-recurrence-policy-differential/0.1"
DOMAIN = b"FrankRecurrencePolicyDifferential/v1\x00"

TERMINAL_SINGLE = {
    "HALT_CANDIDATE_CONVERGED",
    "ROUTE",
    "ESCALATE_STALLED",
    "ABORT_DIVERGING",
    "ROLLBACK",
}
TERMINAL_POSTHOC = {
    PostHocDecision.HALT_CANDIDATE_CONVERGED.value,
    PostHocDecision.ROUTE.value,
    PostHocDecision.ABORT_DIVERGING.value,
    PostHocDecision.ROLLBACK.value,
}


def _hash(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return hashlib.sha256(DOMAIN + raw.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PolicyDecision:
    policy: str
    prefix_len: int
    state_epoch: int
    decision: str
    reason: str
    authority: str
    terminal: bool


def _validate(readouts: Sequence[LoopDynamicsReadout]) -> None:
    if not readouts:
        raise ValueError("trajectory must not be empty")
    first = readouts[0]
    prior_epoch = -1
    prior_count = -1
    for readout in readouts:
        readout.validate()
        if (readout.loop_id, readout.loop_family, readout.timescale) != (
            first.loop_id,
            first.loop_family,
            first.timescale,
        ):
            raise ValueError("mixed loop trajectory")
        if readout.state_epoch <= prior_epoch:
            raise ValueError("state_epoch must strictly increase")
        if readout.recurrence_count < prior_count:
            raise ValueError("recurrence_count must be monotone")
        prior_epoch = readout.state_epoch
        prior_count = readout.recurrence_count


def _single(prefix: Sequence[LoopDynamicsReadout]) -> PolicyDecision:
    receipt = decide_recurrence(prefix[-1])
    decision = receipt.decision.value
    return PolicyDecision(
        policy="single_state_reference",
        prefix_len=len(prefix),
        state_epoch=prefix[-1].state_epoch,
        decision=decision,
        reason=receipt.reason,
        authority=receipt.authority,
        terminal=decision in TERMINAL_SINGLE,
    )


def _posthoc(prefix: Sequence[LoopDynamicsReadout]) -> PolicyDecision:
    receipt = decide_posthoc(prefix)
    decision = receipt.decision.value
    return PolicyDecision(
        policy="posthoc_trajectory",
        prefix_len=len(prefix),
        state_epoch=prefix[-1].state_epoch,
        decision=decision,
        reason=receipt.reason,
        authority=receipt.authority,
        terminal=decision in TERMINAL_POSTHOC,
    )


def _fixed(prefix: Sequence[LoopDynamicsReadout], fixed_depth: int) -> PolicyDecision:
    if fixed_depth < 1:
        raise ValueError("fixed_depth must be >=1")
    terminal = len(prefix) >= fixed_depth
    return PolicyDecision(
        policy=f"fixed_depth_{fixed_depth}",
        prefix_len=len(prefix),
        state_epoch=prefix[-1].state_epoch,
        decision="HALT_FIXED_DEPTH" if terminal else "CONTINUE",
        reason="fixed_depth_reached" if terminal else "fixed_depth_not_reached",
        authority="PROPOSAL_ONLY",
        terminal=terminal,
    )


def replay_policies(readouts: Sequence[LoopDynamicsReadout], *, fixed_depth: int = 3) -> dict[str, Any]:
    """Replay policy readouts over identical frozen trajectory prefixes.

    This runner never changes the source trajectory. It is a diagnostic differential, not a
    controller. Real policy quality requires outcome/cost labels or receipts supplied by the
    caller; the differential itself never selects a winner and never carries effect authority.
    """
    _validate(readouts)
    rows: dict[str, list[dict[str, Any]]] = {
        "single_state_reference": [],
        "posthoc_trajectory": [],
        f"fixed_depth_{fixed_depth}": [],
    }
    first_terminal: dict[str, dict[str, Any] | None] = {key: None for key in rows}

    for prefix_len in range(1, len(readouts) + 1):
        prefix = readouts[:prefix_len]
        decisions = (_single(prefix), _posthoc(prefix), _fixed(prefix, fixed_depth))
        for decision in decisions:
            row = asdict(decision)
            rows[decision.policy].append(row)
            if decision.terminal and first_terminal[decision.policy] is None:
                first_terminal[decision.policy] = row

    trajectory = [asdict(readout) for readout in readouts]
    payload = {
        "schema_version": "1.0",
        "version": VERSION,
        "trajectory_hash": _hash(trajectory),
        "trajectory_length": len(readouts),
        "policies": rows,
        "first_terminal": first_terminal,
        "authority": "PROPOSAL_ONLY",
        "scope_guard": "Frozen-trajectory policy readout differential only. No policy winner is established without independent outcome/cost labels.",
    }
    payload["receipt_hash"] = _hash(payload)
    return payload
