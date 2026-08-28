#!/usr/bin/env python3
"""GRID10 unified cognitive runtime v4: causal heartbeat <-> persistent-agency coupling.

v3 proved that Fabric, heartbeat telemetry and PersistentAgencyStore can share one physical
SQLite authority. v4 closes the next bounded Triggerword-4 gap by coupling the deterministic
runtime cycle to the durable AgencyState scheduler:

    due/wake -> live ControlSnapshot -> heartbeat -> GRID action gate
    -> continuation checkpoint -> next-tick schedule

The ControlSnapshot is latched exactly once at the cognitive pulse boundary. Pulse cadence
uses the live control plane unless an explicit compatibility/test override is supplied.
Material action paths consume the corresponding GRID cell mode/gain controls before the
runtime publishes its next-action candidate. Control writes remain owner-mediated and apply
to later ticks; this module never mutates controls during a tick.

The cycle commit is generation-like CAS guarded by the AgencyState epoch and lands in the
same SQLite/WAL file. This module never grants canonical truth or external-effect authority.
GRID/model output remains candidate cognition; EffectGate/EffectJournal remain authoritative
for real effects outside this runtime.

Triggerword-4 convergence note: persistent service wrappers may pre-evaluate wake conditions
only when they pass the exact awakened goal IDs back into ``tick_once``. That keeps one v4
state-transition core instead of allowing a scheduler adapter to retain its own heartbeat /
checkpoint / schedule write semantics.
"""
from __future__ import annotations

from dataclasses import dataclass
import argparse
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Iterable, Mapping

from frankenstein2_cognitive_control_plane_v1 import (
    CognitiveControlPlane,
    ControlMode,
    ControlSnapshot,
)
from grid10_cognitive_heartbeat_v1 import _trusted_normal_axes, append_frame_jsonl
from grid10_cognitive_unified_runtime_v3 import (
    build_unified_agency_runtime,
    runtime_authority_receipt,
)
from grid10_persistent_agency_v1 import PersistentAgencyStore

SCHEMA = "GRID10_UNIFIED_COGNITIVE_RUNTIME/v4"
CHECKPOINT_SCHEMA = "GRID10_COGNITIVE_CYCLE_CHECKPOINT/v1"
IDLE_CHECKPOINT_SCHEMA = "GRID10_IDLE_HOLD_CHECKPOINT/v1"

# These are routing requirements, not claims that the cells themselves are canonical truth.
# The live control plane can attenuate or disable the compute/output path that would otherwise
# publish the heartbeat's cognitive action candidate.
ACTION_GRID_CELLS: Mapping[str, tuple[str, ...]] = {
    "OBSERVE": ("orientation",),
    "SEARCH": ("epistemic", "retrieval"),
    "SIMULATE": ("hypothesis", "world"),
    "ACT_CANDIDATE": ("planning", "critic"),
}


class RuntimeCycleError(RuntimeError):
    pass


class RuntimeCycleNotDue(RuntimeCycleError):
    pass


class RuntimeCycleConflict(RuntimeCycleError):
    pass


@dataclass(frozen=True)
class UnifiedCycleResult:
    tick_id: str
    heartbeat_result: Any
    woken_goal_ids: tuple[str, ...]
    agency_epoch_before: int
    agency_epoch_after: int
    assurance_mode: str
    next_action: str
    next_tick_not_before: float
    checkpoint: Mapping[str, Any]


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def _init_cycle_schema(path: Path) -> None:
    con = _connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS grid10_cognitive_cycles(
              tick_id TEXT PRIMARY KEY,
              agency_epoch_before INTEGER NOT NULL,
              agency_epoch_after INTEGER NOT NULL,
              source_state_epoch INTEGER NOT NULL,
              assurance_mode TEXT NOT NULL,
              next_action TEXT NOT NULL,
              woken_goal_ids_json TEXT NOT NULL,
              checkpoint_json TEXT NOT NULL,
              next_tick_not_before REAL NOT NULL,
              created_ts REAL NOT NULL
            )
            """
        )
    finally:
        con.close()


def _grid_control_view(snapshot: ControlSnapshot, action: str) -> tuple[Mapping[str, Any], ...]:
    rows: list[Mapping[str, Any]] = []
    for cell in ACTION_GRID_CELLS.get(action, ()):
        mode = snapshot.mode(f"grid.{cell}.mode")
        gain = snapshot.float(f"grid.{cell}.gain")
        rows.append(
            {
                "cell": cell,
                "mode": mode.value,
                "gain": gain,
                "compute_enabled": mode != ControlMode.COMPUTE_OFF and gain > 0.0,
                "output_enabled": mode not in {ControlMode.COMPUTE_OFF, ControlMode.OUTPUT_OFF} and gain > 0.0,
                "memory_enabled": mode != ControlMode.MEMORY_OFF,
            }
        )
    return tuple(rows)


def _apply_grid_action_controls(
    snapshot: ControlSnapshot,
    raw_action: str,
) -> tuple[str, tuple[str, ...], tuple[Mapping[str, Any], ...]]:
    """Consume live GRID modes/gains before publishing a cognitive action candidate.

    A cell that is COMPUTE_OFF/OUTPUT_OFF cannot support an action requiring that cell.
    Gain is a live admission weight: the weakest required cell must meet the live pulse
    salience threshold. This is deliberately bounded and deterministic; it does not invent
    world facts or execute an effect.
    """
    cells = _grid_control_view(snapshot, raw_action)
    if not cells or raw_action == "HOLD":
        return raw_action, (), cells

    reasons: list[str] = []
    blocked = [r["cell"] for r in cells if not r["compute_enabled"] or not r["output_enabled"]]
    threshold = snapshot.float("pulse.salience_threshold")
    min_gain = min(float(r["gain"]) for r in cells)
    if blocked:
        reasons.append("GRID_MODE_BLOCK:" + ",".join(str(x) for x in blocked))
    if min_gain < threshold:
        reasons.append(f"GRID_GAIN_BELOW_SALIENCE:{min_gain:.6f}<{threshold:.6f}")

    if not reasons:
        return raw_action, (), cells

    # Fail toward a lower-authority observation candidate. If even orientation is disabled,
    # hold rather than silently bypassing the live control frame.
    orientation = _grid_control_view(snapshot, "OBSERVE")
    orientation_ok = bool(orientation) and all(
        bool(r["compute_enabled"]) and bool(r["output_enabled"])
        and float(r["gain"]) >= threshold
        for r in orientation
    )
    fallback = "OBSERVE" if raw_action != "OBSERVE" and orientation_ok else "HOLD"
    return fallback, tuple(reasons), cells


def _atomic_commit_cycle(
    agency: PersistentAgencyStore,
    *,
    expected_agency_epoch: int,
    tick_id: str,
    source_state_epoch: int,
    assurance_mode: str,
    next_action: str,
    woken_goal_ids: tuple[str, ...],
    checkpoint: Mapping[str, Any],
    next_tick_not_before: float,
    now_ts: float,
) -> int:
    """Commit checkpoint + scheduler mode as one AgencyState epoch transition.

    Heartbeat telemetry is written by the existing heartbeat store before this function.
    If another agency writer moves the epoch in between, this commit fails closed rather
    than silently overwriting the newer continuation state.
    """
    encoded_checkpoint = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"))
    encoded_woken = json.dumps(list(woken_goal_ids), sort_keys=True, separators=(",", ":"))
    event_id = f"cognitive-cycle:{tick_id}"
    con = _connect(Path(agency.path))
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT state_epoch FROM agency_meta WHERE singleton=1"
        ).fetchone()
        if row is None:
            raise RuntimeCycleConflict("MISSING_AGENCY_META")
        observed_epoch = int(row["state_epoch"])
        if observed_epoch != int(expected_agency_epoch):
            raise RuntimeCycleConflict(
                f"STALE_AGENCY_EPOCH:{expected_agency_epoch}!={observed_epoch}"
            )
        new_epoch = observed_epoch + 1
        changed = con.execute(
            """UPDATE agency_meta
               SET state_epoch=?,mode=?,next_tick_not_before=?,continuation_checkpoint=?,updated_ts=?
               WHERE singleton=1 AND state_epoch=?""",
            (
                new_epoch,
                assurance_mode,
                float(next_tick_not_before),
                encoded_checkpoint,
                float(now_ts),
                observed_epoch,
            ),
        ).rowcount
        if changed != 1:
            raise RuntimeCycleConflict("AGENCY_CYCLE_CAS_FAILED")
        try:
            con.execute(
                """INSERT INTO grid10_cognitive_cycles VALUES(?,?,?,?,?,?,?,?,?,?)""",
                (
                    tick_id,
                    observed_epoch,
                    new_epoch,
                    int(source_state_epoch),
                    assurance_mode,
                    next_action,
                    encoded_woken,
                    encoded_checkpoint,
                    float(next_tick_not_before),
                    float(now_ts),
                ),
            )
            con.execute(
                """INSERT INTO agency_events(
                     event_id,event_type,goal_id,intent_id,state_epoch,generation,payload_json,created_ts
                   ) VALUES(?,?,NULL,NULL,?,NULL,?,?)""",
                (
                    event_id,
                    "COGNITIVE_CYCLE_COMMITTED",
                    new_epoch,
                    json.dumps(
                        {
                            "tick_id": tick_id,
                            "source_state_epoch": int(source_state_epoch),
                            "assurance_mode": assurance_mode,
                            "next_action": next_action,
                            "woken_goal_ids": list(woken_goal_ids),
                            "next_tick_not_before": float(next_tick_not_before),
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    float(now_ts),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise RuntimeCycleConflict(f"DUPLICATE_OR_CONFLICTING_TICK:{tick_id}") from exc
        con.execute("COMMIT")
        return new_epoch
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


def _atomic_commit_idle_hold(
    agency: PersistentAgencyStore,
    *,
    expected_agency_epoch: int,
    cycle_id: str,
    awakened_goal_ids: tuple[str, ...],
    next_tick_not_before: float,
    now_ts: float,
    reason: str = "NO_ACTIVE_OR_TRIAL_GOAL",
) -> tuple[int, Mapping[str, Any]]:
    """Persist an idle/HOLD scheduler decision with one AgencyState CAS transaction.

    No heartbeat/model cycle ran, so this deliberately does *not* mint a row in
    ``grid10_cognitive_cycles``. It only advances the durable AgencyState schedule/checkpoint
    and appends a typed agency event. This replaces the older scheduler adapter's two separate
    ``set_continuation_checkpoint`` + ``schedule_next_tick`` writes.
    """
    checkpoint: Mapping[str, Any] = {
        "schema": IDLE_CHECKPOINT_SCHEMA,
        "cycle_id": cycle_id,
        "mode": "HOLD",
        "reason": reason,
        "awakened_goal_ids": list(awakened_goal_ids),
        "next_tick_not_before": float(next_tick_not_before),
        "external_effect_executed": False,
    }
    encoded_checkpoint = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"))
    event_id = f"cognitive-idle:{cycle_id}"
    con = _connect(Path(agency.path))
    try:
        con.execute("BEGIN IMMEDIATE")
        row = con.execute(
            "SELECT state_epoch FROM agency_meta WHERE singleton=1"
        ).fetchone()
        if row is None:
            raise RuntimeCycleConflict("MISSING_AGENCY_META")
        observed_epoch = int(row["state_epoch"])
        if observed_epoch != int(expected_agency_epoch):
            raise RuntimeCycleConflict(
                f"STALE_AGENCY_EPOCH:{expected_agency_epoch}!={observed_epoch}"
            )
        new_epoch = observed_epoch + 1
        changed = con.execute(
            """UPDATE agency_meta
               SET state_epoch=?,mode='HOLD',next_tick_not_before=?,continuation_checkpoint=?,updated_ts=?
               WHERE singleton=1 AND state_epoch=?""",
            (
                new_epoch,
                float(next_tick_not_before),
                encoded_checkpoint,
                float(now_ts),
                observed_epoch,
            ),
        ).rowcount
        if changed != 1:
            raise RuntimeCycleConflict("AGENCY_IDLE_CAS_FAILED")
        try:
            con.execute(
                """INSERT INTO agency_events(
                     event_id,event_type,goal_id,intent_id,state_epoch,generation,payload_json,created_ts
                   ) VALUES(?,?,NULL,NULL,?,NULL,?,?)""",
                (
                    event_id,
                    "COGNITIVE_IDLE_HOLD_COMMITTED",
                    new_epoch,
                    json.dumps(
                        {
                            "cycle_id": cycle_id,
                            "reason": reason,
                            "awakened_goal_ids": list(awakened_goal_ids),
                            "next_tick_not_before": float(next_tick_not_before),
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    float(now_ts),
                ),
            )
        except sqlite3.IntegrityError as exc:
            raise RuntimeCycleConflict(f"DUPLICATE_OR_CONFLICTING_IDLE:{cycle_id}") from exc
        con.execute("COMMIT")
        return new_epoch, checkpoint
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


class UnifiedCognitiveRuntimeV4:
    """One-cycle deterministic bridge between PersistentAgencyStore and the v3 heartbeat."""

    def __init__(
        self,
        heartbeat_runtime: Any,
        agency: PersistentAgencyStore,
        *,
        control_plane: CognitiveControlPlane | None = None,
    ):
        self.heartbeat_runtime = heartbeat_runtime
        self.agency = agency
        self.control_plane = control_plane or CognitiveControlPlane(Path(agency.path))
        _init_cycle_schema(Path(agency.path))

    def tick_once(
        self,
        *,
        tick_id: str,
        interval: float | None = None,
        hold_interval: float | None = None,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        prewoken_goal_ids: Iterable[str] | None = None,
        trusted_axes: Mapping[str, Any] | None = None,
        extra_variables: Mapping[str, Any] | None = None,
    ) -> UnifiedCycleResult:
        now = time.time() if now_ts is None else float(now_ts)
        if prewoken_goal_ids is not None:
            if tuple(observed_events):
                raise RuntimeCycleError(
                    "AMBIGUOUS_WAKE_INPUT:prewoken_goal_ids_and_observed_events"
                )
            woken = tuple(str(goal_id) for goal_id in prewoken_goal_ids)
        else:
            woken = self.agency.wake_due(
                now_ts=now,
                observed_events=tuple(observed_events),
                event_id_prefix=f"{tick_id}:wake",
            )
        before = self.agency.snapshot()
        if not woken and not self.agency.due_for_tick(now_ts=now):
            raise RuntimeCycleNotDue(
                f"NEXT_TICK_NOT_DUE:{before.next_tick_not_before}"
            )

        # Exactly one immutable dynamic-frame snapshot is latched for this cognitive tick.
        # No control mutation occurs below; later commits become visible on a later tick.
        control = self.control_plane.snapshot()

        heartbeat = self.heartbeat_runtime.tick_once(
            tick_id=tick_id,
            trusted_axes=trusted_axes,
            extra_variables=extra_variables,
        )
        assurance_mode = getattr(heartbeat.assurance_mode, "value", str(heartbeat.assurance_mode))
        raw_next_action = str(heartbeat.next_action)
        next_action, control_reasons, grid_controls = _apply_grid_action_controls(
            control,
            raw_next_action,
        )

        if raw_next_action == "HOLD":
            selected_interval = (
                float(hold_interval)
                if hold_interval is not None
                else control.float("pulse.hold_interval_seconds")
            )
        else:
            selected_interval = (
                float(interval)
                if interval is not None
                else control.float("pulse.active_interval_seconds")
            )
        next_tick_not_before = now + max(0.05, selected_interval)
        checkpoint = {
            "schema": CHECKPOINT_SCHEMA,
            "tick_id": tick_id,
            "source_state_epoch": int(heartbeat.state_epoch),
            "assurance_mode": assurance_mode,
            "raw_next_action": raw_next_action,
            "next_action": next_action,
            "woken_goal_ids": list(woken),
            "heartbeat_reasons": list(getattr(heartbeat, "reasons", ())),
            "control_snapshot": {
                "schema": control.schema,
                "control_epoch": int(control.control_epoch),
                "snapshot_digest": control.snapshot_digest,
            },
            "pulse_interval_seconds_consumed": float(selected_interval),
            "grid_controls_consumed": list(grid_controls),
            "control_reasons": list(control_reasons),
        }
        after_epoch = _atomic_commit_cycle(
            self.agency,
            expected_agency_epoch=before.state_epoch,
            tick_id=tick_id,
            source_state_epoch=int(heartbeat.state_epoch),
            assurance_mode=assurance_mode,
            next_action=next_action,
            woken_goal_ids=tuple(woken),
            checkpoint=checkpoint,
            next_tick_not_before=next_tick_not_before,
            now_ts=now,
        )
        return UnifiedCycleResult(
            tick_id=tick_id,
            heartbeat_result=heartbeat,
            woken_goal_ids=tuple(woken),
            agency_epoch_before=before.state_epoch,
            agency_epoch_after=after_epoch,
            assurance_mode=assurance_mode,
            next_action=next_action,
            next_tick_not_before=next_tick_not_before,
            checkpoint=checkpoint,
        )


def build_unified_cognitive_runtime_v4(
    unified_db: Path,
    *,
    allow_regulator_writes: bool = False,
) -> tuple[Any, Any, PersistentAgencyStore, UnifiedCognitiveRuntimeV4, Any]:
    fabric, heartbeat, agency, base_runtime, fingerprint = build_unified_agency_runtime(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )
    control_plane = CognitiveControlPlane(Path(unified_db))
    runtime = UnifiedCognitiveRuntimeV4(base_runtime, agency, control_plane=control_plane)
    return fabric, heartbeat, agency, runtime, fingerprint


def run_bounded(
    *,
    unified_db: Path,
    frames_jsonl: Path,
    ticks: int,
    interval: float | None,
    allow_regulator_writes: bool = False,
    trusted_normal_test_fixture: bool = False,
) -> list[dict[str, Any]]:
    fabric, heartbeat, agency, runtime, _fingerprint = build_unified_cognitive_runtime_v4(
        unified_db,
        allow_regulator_writes=allow_regulator_writes,
    )
    authority = runtime_authority_receipt(fabric, heartbeat, agency)
    authority["runtime_schema"] = SCHEMA
    print(json.dumps(authority, sort_keys=True))

    trusted = _trusted_normal_axes() if trusted_normal_test_fixture else None
    rows: list[dict[str, Any]] = []
    for i in range(max(0, int(ticks))):
        now = time.time()
        tick_id = f"unified-v4-{time.time_ns()}-{i}"
        cycle = runtime.tick_once(
            tick_id=tick_id,
            interval=interval,
            now_ts=now,
            trusted_axes=trusted,
        )
        append_frame_jsonl(Path(frames_jsonl), cycle.heartbeat_result.frame_json)
        row = {
            "schema": SCHEMA,
            "tick_id": cycle.tick_id,
            "agency_epoch_before": cycle.agency_epoch_before,
            "agency_epoch_after": cycle.agency_epoch_after,
            "assurance_mode": cycle.assurance_mode,
            "next_action": cycle.next_action,
            "woken_goal_ids": list(cycle.woken_goal_ids),
            "next_tick_not_before": cycle.next_tick_not_before,
            "control_snapshot": cycle.checkpoint.get("control_snapshot"),
            "pulse_interval_seconds_consumed": cycle.checkpoint.get("pulse_interval_seconds_consumed"),
        }
        rows.append(row)
        print(json.dumps(row, sort_keys=True))
        if i + 1 < ticks:
            sleep_interval = interval
            if sleep_interval is None:
                sleep_interval = float(cycle.checkpoint["pulse_interval_seconds_consumed"])
            time.sleep(max(0.05, float(sleep_interval)))
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--unified-db", required=True)
    p.add_argument("--frames-jsonl", required=True)
    p.add_argument("--ticks", type=int, default=1)
    p.add_argument("--interval", type=float, default=None)
    p.add_argument("--allow-regulator-writes", action="store_true")
    p.add_argument("--trusted-normal-test-fixture", action="store_true")
    args = p.parse_args()
    run_bounded(
        unified_db=Path(args.unified_db),
        frames_jsonl=Path(args.frames_jsonl),
        ticks=args.ticks,
        interval=args.interval,
        allow_regulator_writes=bool(args.allow_regulator_writes),
        trusted_normal_test_fixture=bool(args.trusted_normal_test_fixture),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())