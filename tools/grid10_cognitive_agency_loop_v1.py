#!/usr/bin/env python3
"""Persistent AgencyState -> cognitive heartbeat scheduling bridge for GRID10.

The bridge makes stored HOLD/WAKE and next-tick state causally control whether a heartbeat
runs. It is deterministic and model/provider-free. It never executes external effects and
never upgrades a cognitive result into verified world truth.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Any

from grid10_cognitive_heartbeat_v1 import CognitiveHeartbeatRuntime, CognitiveTickResult
from grid10_cognitive_fabric_adapter_v1 import TrustedAxisEvidence
from grid10_persistent_agency_v1 import GoalState, PersistentAgencyStore


@dataclass(frozen=True)
class AgencyLoopReceipt:
    tick_id: str
    disposition: str
    awakened_goal_ids: tuple[str, ...]
    active_goal_ids: tuple[str, ...]
    agency_epoch_before: int
    agency_epoch_after: int
    heartbeat: CognitiveTickResult | None
    next_tick_not_before: float | None


class PersistentAgencyHeartbeatLoop:
    def __init__(
        self,
        agency: PersistentAgencyStore,
        heartbeat: CognitiveHeartbeatRuntime,
        *,
        tick_interval_seconds: float = 1.0,
    ) -> None:
        self.agency = agency
        self.heartbeat = heartbeat
        self.tick_interval_seconds = max(0.05, float(tick_interval_seconds))

    def tick_if_due(
        self,
        *,
        tick_id: str,
        now_ts: float,
        observed_events: Iterable[str] = (),
        trusted_axes: Mapping[str, TrustedAxisEvidence] | None = None,
    ) -> AgencyLoopReceipt:
        before = self.agency.snapshot()
        awakened = self.agency.wake_due(
            now_ts=now_ts,
            observed_events=observed_events,
            event_id_prefix=f"{tick_id}:wake",
        )

        # A concrete wake is itself a reason to re-enter cognition immediately even when a
        # previously scheduled idle review lies farther in the future.
        if not awakened and not self.agency.due_for_tick(now_ts=now_ts):
            after = self.agency.snapshot()
            return AgencyLoopReceipt(
                tick_id=tick_id,
                disposition="NOT_DUE",
                awakened_goal_ids=(),
                active_goal_ids=tuple(g.goal_id for g in after.goals if g.state == GoalState.ACTIVE),
                agency_epoch_before=before.state_epoch,
                agency_epoch_after=after.state_epoch,
                heartbeat=None,
                next_tick_not_before=after.next_tick_not_before,
            )

        agency_for_tick = self.agency.snapshot()
        active = tuple(g.goal_id for g in agency_for_tick.goals if g.state == GoalState.ACTIVE)
        result = self.heartbeat.tick_once(tick_id=tick_id, trusted_axes=trusted_axes)

        checkpoint: dict[str, Any] = {
            "tick_id": tick_id,
            "active_goal_ids": list(active),
            "awakened_goal_ids": list(awakened),
            "heartbeat_state_epoch": result.state_epoch,
            "assurance_mode": result.assurance_mode.value,
            "next_action": result.next_action,
        }
        self.agency.set_continuation_checkpoint(
            checkpoint,
            event_id=f"{tick_id}:checkpoint",
            now_ts=now_ts,
        )
        self.agency.schedule_next_tick(
            not_before=now_ts + self.tick_interval_seconds,
            mode=result.assurance_mode.value,
            event_id=f"{tick_id}:schedule",
            now_ts=now_ts,
        )
        after = self.agency.snapshot()
        return AgencyLoopReceipt(
            tick_id=tick_id,
            disposition="TICKED",
            awakened_goal_ids=tuple(awakened),
            active_goal_ids=active,
            agency_epoch_before=before.state_epoch,
            agency_epoch_after=after.state_epoch,
            heartbeat=result,
            next_tick_not_before=after.next_tick_not_before,
        )


__all__ = ["AgencyLoopReceipt", "PersistentAgencyHeartbeatLoop"]
