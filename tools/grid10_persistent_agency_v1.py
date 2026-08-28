#!/usr/bin/env python3
"""Durable AgencyState / GoalContract / HOLD-WAKE substrate for GRID10.

This module is intentionally deterministic and model-free. It persists only control-plane
agency state; it does not grant effect authority, mint world facts, or execute actions.
All material transitions use generation checks inside one SQLite transaction so restart,
stale-writer, and deferred-wake behavior can be falsified independently of an LLM.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import sqlite3
import time
from typing import Iterable, Mapping, Sequence


class AgencyError(RuntimeError):
    pass


class StaleGeneration(AgencyError):
    pass


class InvalidTransition(AgencyError):
    pass


class GoalState(str, Enum):
    CANDIDATE = "CANDIDATE"
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    RETIRED = "RETIRED"
    REJECTED = "REJECTED"


class WakeKind(str, Enum):
    TIME_AT = "TIME_AT"
    EVENT = "EVENT"
    PERIODIC_REVIEW = "PERIODIC_REVIEW"


class DeferredIntentState(str, Enum):
    PENDING = "PENDING"
    FIRED = "FIRED"
    STALE = "STALE"
    CANCELLED = "CANCELLED"


_ALLOWED_TRANSITIONS: Mapping[GoalState, frozenset[GoalState]] = {
    GoalState.CANDIDATE: frozenset({GoalState.TRIAL, GoalState.ACTIVE, GoalState.REJECTED, GoalState.RETIRED}),
    GoalState.TRIAL: frozenset({GoalState.ACTIVE, GoalState.DORMANT, GoalState.BLOCKED, GoalState.REJECTED, GoalState.RETIRED}),
    GoalState.ACTIVE: frozenset({GoalState.DORMANT, GoalState.BLOCKED, GoalState.COMPLETED, GoalState.RETIRED}),
    GoalState.DORMANT: frozenset({GoalState.ACTIVE, GoalState.BLOCKED, GoalState.RETIRED}),
    GoalState.BLOCKED: frozenset({GoalState.ACTIVE, GoalState.DORMANT, GoalState.RETIRED}),
    GoalState.COMPLETED: frozenset({GoalState.RETIRED}),
    GoalState.RETIRED: frozenset(),
    GoalState.REJECTED: frozenset({GoalState.RETIRED}),
}


@dataclass(frozen=True)
class GoalContract:
    goal_id: str
    origin: str
    semantic_goal: str
    state: GoalState
    generation: int
    parent_goal_ids: tuple[str, ...]
    success_criteria: tuple[str, ...]
    wake_conditions: tuple[str, ...]
    uncertainty: float
    priority: int
    created_ts: float
    updated_ts: float


@dataclass(frozen=True)
class DeferredIntent:
    intent_id: str
    goal_id: str
    goal_generation: int
    wake_kind: WakeKind
    wake_value: str
    state: DeferredIntentState
    created_ts: float
    updated_ts: float


@dataclass(frozen=True)
class AgencySnapshot:
    state_epoch: int
    mode: str
    next_tick_not_before: float | None
    continuation_checkpoint: str | None
    goals: tuple[GoalContract, ...]
    deferred_intents: tuple[DeferredIntent, ...]


class PersistentAgencyStore:
    """Single-file durable agency control state.

    Canonical reality/effect authority stays elsewhere. This store is a deterministic
    continuation/control substrate and therefore stores explicit provenance/event rows rather
    than treating model prose as verified completion.
    """

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), timeout=5.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_schema(self) -> None:
        con = self._connect()
        try:
            con.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS agency_meta(
                  singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                  state_epoch INTEGER NOT NULL,
                  mode TEXT NOT NULL,
                  next_tick_not_before REAL,
                  continuation_checkpoint TEXT,
                  updated_ts REAL NOT NULL
                );
                INSERT OR IGNORE INTO agency_meta(singleton,state_epoch,mode,updated_ts)
                  VALUES(1,0,'NORMAL',0);

                CREATE TABLE IF NOT EXISTS goals(
                  goal_id TEXT PRIMARY KEY,
                  origin TEXT NOT NULL,
                  semantic_goal TEXT NOT NULL,
                  state TEXT NOT NULL,
                  generation INTEGER NOT NULL,
                  parent_goal_ids_json TEXT NOT NULL,
                  success_criteria_json TEXT NOT NULL,
                  wake_conditions_json TEXT NOT NULL,
                  uncertainty REAL NOT NULL CHECK(uncertainty>=0.0 AND uncertainty<=1.0),
                  priority INTEGER NOT NULL,
                  created_ts REAL NOT NULL,
                  updated_ts REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS deferred_intents(
                  intent_id TEXT PRIMARY KEY,
                  goal_id TEXT NOT NULL REFERENCES goals(goal_id),
                  goal_generation INTEGER NOT NULL,
                  wake_kind TEXT NOT NULL,
                  wake_value TEXT NOT NULL,
                  state TEXT NOT NULL,
                  created_ts REAL NOT NULL,
                  updated_ts REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS deferred_pending_idx
                  ON deferred_intents(state,wake_kind,wake_value);

                CREATE TABLE IF NOT EXISTS agency_events(
                  event_seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  event_id TEXT UNIQUE NOT NULL,
                  event_type TEXT NOT NULL,
                  goal_id TEXT,
                  intent_id TEXT,
                  state_epoch INTEGER NOT NULL,
                  generation INTEGER,
                  payload_json TEXT NOT NULL,
                  created_ts REAL NOT NULL
                );
                """
            )
            con.commit()
        finally:
            con.close()

    @staticmethod
    def _goal_from_row(row: sqlite3.Row) -> GoalContract:
        return GoalContract(
            goal_id=row["goal_id"],
            origin=row["origin"],
            semantic_goal=row["semantic_goal"],
            state=GoalState(row["state"]),
            generation=int(row["generation"]),
            parent_goal_ids=tuple(json.loads(row["parent_goal_ids_json"])),
            success_criteria=tuple(json.loads(row["success_criteria_json"])),
            wake_conditions=tuple(json.loads(row["wake_conditions_json"])),
            uncertainty=float(row["uncertainty"]),
            priority=int(row["priority"]),
            created_ts=float(row["created_ts"]),
            updated_ts=float(row["updated_ts"]),
        )

    @staticmethod
    def _intent_from_row(row: sqlite3.Row) -> DeferredIntent:
        return DeferredIntent(
            intent_id=row["intent_id"],
            goal_id=row["goal_id"],
            goal_generation=int(row["goal_generation"]),
            wake_kind=WakeKind(row["wake_kind"]),
            wake_value=row["wake_value"],
            state=DeferredIntentState(row["state"]),
            created_ts=float(row["created_ts"]),
            updated_ts=float(row["updated_ts"]),
        )

    @staticmethod
    def _next_epoch(con: sqlite3.Connection, now_ts: float) -> int:
        row = con.execute("SELECT state_epoch FROM agency_meta WHERE singleton=1").fetchone()
        epoch = int(row[0]) + 1
        con.execute(
            "UPDATE agency_meta SET state_epoch=?, updated_ts=? WHERE singleton=1",
            (epoch, now_ts),
        )
        return epoch

    @staticmethod
    def _event(
        con: sqlite3.Connection,
        *,
        event_id: str,
        event_type: str,
        state_epoch: int,
        now_ts: float,
        goal_id: str | None = None,
        intent_id: str | None = None,
        generation: int | None = None,
        payload: Mapping[str, object] | None = None,
    ) -> None:
        con.execute(
            "INSERT INTO agency_events(event_id,event_type,goal_id,intent_id,state_epoch,generation,payload_json,created_ts) VALUES(?,?,?,?,?,?,?,?)",
            (event_id, event_type, goal_id, intent_id, state_epoch, generation,
             json.dumps(payload or {}, sort_keys=True, separators=(",", ":")), now_ts),
        )

    def create_goal(
        self,
        *,
        goal_id: str,
        origin: str,
        semantic_goal: str,
        state: GoalState = GoalState.CANDIDATE,
        parent_goal_ids: Sequence[str] = (),
        success_criteria: Sequence[str] = (),
        wake_conditions: Sequence[str] = (),
        uncertainty: float = 1.0,
        priority: int = 0,
        event_id: str,
        now_ts: float | None = None,
    ) -> GoalContract:
        if not 0.0 <= uncertainty <= 1.0:
            raise ValueError("uncertainty must be in [0,1]")
        now = time.time() if now_ts is None else float(now_ts)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO goals VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (goal_id, origin, semantic_goal, state.value, 0,
                 json.dumps(list(parent_goal_ids)), json.dumps(list(success_criteria)),
                 json.dumps(list(wake_conditions)), float(uncertainty), int(priority), now, now),
            )
            epoch = self._next_epoch(con, now)
            self._event(con, event_id=event_id, event_type="GOAL_CREATED", goal_id=goal_id,
                        state_epoch=epoch, generation=0, now_ts=now,
                        payload={"state": state.value, "origin": origin})
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return self.get_goal(goal_id)

    def get_goal(self, goal_id: str) -> GoalContract:
        con = self._connect()
        try:
            row = con.execute("SELECT * FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
        finally:
            con.close()
        if row is None:
            raise KeyError(goal_id)
        return self._goal_from_row(row)

    def transition_goal(
        self,
        goal_id: str,
        *,
        expected_generation: int,
        new_state: GoalState,
        event_id: str,
        reason: str,
        now_ts: float | None = None,
    ) -> GoalContract:
        now = time.time() if now_ts is None else float(now_ts)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state,generation FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if row is None:
                raise KeyError(goal_id)
            current = GoalState(row["state"])
            generation = int(row["generation"])
            if generation != expected_generation:
                raise StaleGeneration(f"{goal_id}: expected {expected_generation}, observed {generation}")
            if new_state not in _ALLOWED_TRANSITIONS[current]:
                raise InvalidTransition(f"{current.value}->{new_state.value}")
            new_generation = generation + 1
            cur = con.execute(
                "UPDATE goals SET state=?,generation=?,updated_ts=? WHERE goal_id=? AND generation=?",
                (new_state.value, new_generation, now, goal_id, expected_generation),
            )
            if cur.rowcount != 1:
                raise StaleGeneration(goal_id)
            epoch = self._next_epoch(con, now)
            self._event(con, event_id=event_id, event_type="GOAL_TRANSITION", goal_id=goal_id,
                        state_epoch=epoch, generation=new_generation, now_ts=now,
                        payload={"from": current.value, "to": new_state.value, "reason": reason})
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return self.get_goal(goal_id)

    def defer_goal(
        self,
        goal_id: str,
        *,
        expected_generation: int,
        intent_id: str,
        wake_kind: WakeKind,
        wake_value: str,
        event_id: str,
        reason: str,
        now_ts: float | None = None,
    ) -> DeferredIntent:
        now = time.time() if now_ts is None else float(now_ts)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT state,generation FROM goals WHERE goal_id=?", (goal_id,)).fetchone()
            if row is None:
                raise KeyError(goal_id)
            current = GoalState(row["state"])
            generation = int(row["generation"])
            if generation != expected_generation:
                raise StaleGeneration(f"{goal_id}: expected {expected_generation}, observed {generation}")
            if GoalState.DORMANT not in _ALLOWED_TRANSITIONS[current]:
                raise InvalidTransition(f"{current.value}->DORMANT")
            new_generation = generation + 1
            cur = con.execute(
                "UPDATE goals SET state=?,generation=?,updated_ts=? WHERE goal_id=? AND generation=?",
                (GoalState.DORMANT.value, new_generation, now, goal_id, expected_generation),
            )
            if cur.rowcount != 1:
                raise StaleGeneration(goal_id)
            con.execute(
                "INSERT INTO deferred_intents VALUES(?,?,?,?,?,?,?,?)",
                (intent_id, goal_id, new_generation, wake_kind.value, wake_value,
                 DeferredIntentState.PENDING.value, now, now),
            )
            epoch = self._next_epoch(con, now)
            self._event(con, event_id=event_id, event_type="GOAL_DEFERRED", goal_id=goal_id,
                        intent_id=intent_id, state_epoch=epoch, generation=new_generation,
                        now_ts=now, payload={"reason": reason, "wake_kind": wake_kind.value, "wake_value": wake_value})
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return self.get_intent(intent_id)

    def get_intent(self, intent_id: str) -> DeferredIntent:
        con = self._connect()
        try:
            row = con.execute("SELECT * FROM deferred_intents WHERE intent_id=?", (intent_id,)).fetchone()
        finally:
            con.close()
        if row is None:
            raise KeyError(intent_id)
        return self._intent_from_row(row)

    @staticmethod
    def _intent_due(intent: DeferredIntent, *, now_ts: float, observed_events: frozenset[str]) -> bool:
        if intent.wake_kind in {WakeKind.TIME_AT, WakeKind.PERIODIC_REVIEW}:
            try:
                return now_ts >= float(intent.wake_value)
            except ValueError:
                return False
        if intent.wake_kind == WakeKind.EVENT:
            return intent.wake_value in observed_events
        return False

    def wake_due(
        self,
        *,
        now_ts: float | None = None,
        observed_events: Iterable[str] = (),
        event_id_prefix: str = "wake",
    ) -> tuple[str, ...]:
        now = time.time() if now_ts is None else float(now_ts)
        observed = frozenset(observed_events)
        con = self._connect()
        fired: list[str] = []
        try:
            con.execute("BEGIN IMMEDIATE")
            rows = con.execute(
                "SELECT * FROM deferred_intents WHERE state=? ORDER BY created_ts,intent_id",
                (DeferredIntentState.PENDING.value,),
            ).fetchall()
            for row in rows:
                intent = self._intent_from_row(row)
                if not self._intent_due(intent, now_ts=now, observed_events=observed):
                    continue
                grow = con.execute("SELECT state,generation FROM goals WHERE goal_id=?", (intent.goal_id,)).fetchone()
                if grow is None:
                    con.execute(
                        "UPDATE deferred_intents SET state=?,updated_ts=? WHERE intent_id=?",
                        (DeferredIntentState.STALE.value, now, intent.intent_id),
                    )
                    continue
                current_state = GoalState(grow["state"])
                generation = int(grow["generation"])
                if generation != intent.goal_generation or current_state != GoalState.DORMANT:
                    con.execute(
                        "UPDATE deferred_intents SET state=?,updated_ts=? WHERE intent_id=?",
                        (DeferredIntentState.STALE.value, now, intent.intent_id),
                    )
                    continue
                new_generation = generation + 1
                cur = con.execute(
                    "UPDATE goals SET state=?,generation=?,updated_ts=? WHERE goal_id=? AND generation=?",
                    (GoalState.ACTIVE.value, new_generation, now, intent.goal_id, generation),
                )
                if cur.rowcount != 1:
                    con.execute(
                        "UPDATE deferred_intents SET state=?,updated_ts=? WHERE intent_id=?",
                        (DeferredIntentState.STALE.value, now, intent.intent_id),
                    )
                    continue
                con.execute(
                    "UPDATE deferred_intents SET state=?,updated_ts=? WHERE intent_id=?",
                    (DeferredIntentState.FIRED.value, now, intent.intent_id),
                )
                epoch = self._next_epoch(con, now)
                self._event(
                    con,
                    event_id=f"{event_id_prefix}:{intent.intent_id}",
                    event_type="DEFERRED_INTENT_FIRED",
                    goal_id=intent.goal_id,
                    intent_id=intent.intent_id,
                    state_epoch=epoch,
                    generation=new_generation,
                    now_ts=now,
                    payload={"wake_kind": intent.wake_kind.value, "wake_value": intent.wake_value},
                )
                fired.append(intent.goal_id)
            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()
        return tuple(fired)

    def set_continuation_checkpoint(
        self,
        checkpoint: Mapping[str, object],
        *,
        event_id: str,
        now_ts: float | None = None,
    ) -> int:
        now = time.time() if now_ts is None else float(now_ts)
        encoded = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"))
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            epoch = self._next_epoch(con, now)
            con.execute(
                "UPDATE agency_meta SET continuation_checkpoint=?,updated_ts=? WHERE singleton=1",
                (encoded, now),
            )
            self._event(con, event_id=event_id, event_type="CHECKPOINT_WRITTEN",
                        state_epoch=epoch, now_ts=now, payload={"checkpoint_digest_material": encoded})
            con.commit()
            return epoch
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def schedule_next_tick(
        self,
        *,
        not_before: float,
        mode: str,
        event_id: str,
        now_ts: float | None = None,
    ) -> int:
        now = time.time() if now_ts is None else float(now_ts)
        con = self._connect()
        try:
            con.execute("BEGIN IMMEDIATE")
            epoch = self._next_epoch(con, now)
            con.execute(
                "UPDATE agency_meta SET mode=?,next_tick_not_before=?,updated_ts=? WHERE singleton=1",
                (mode, float(not_before), now),
            )
            self._event(con, event_id=event_id, event_type="NEXT_TICK_SCHEDULED",
                        state_epoch=epoch, now_ts=now,
                        payload={"not_before": float(not_before), "mode": mode})
            con.commit()
            return epoch
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

    def due_for_tick(self, *, now_ts: float | None = None) -> bool:
        now = time.time() if now_ts is None else float(now_ts)
        con = self._connect()
        try:
            row = con.execute("SELECT next_tick_not_before FROM agency_meta WHERE singleton=1").fetchone()
        finally:
            con.close()
        return row[0] is None or now >= float(row[0])

    def snapshot(self) -> AgencySnapshot:
        con = self._connect()
        try:
            meta = con.execute("SELECT * FROM agency_meta WHERE singleton=1").fetchone()
            goals = tuple(self._goal_from_row(r) for r in con.execute("SELECT * FROM goals ORDER BY priority DESC,created_ts,goal_id"))
            intents = tuple(self._intent_from_row(r) for r in con.execute("SELECT * FROM deferred_intents ORDER BY created_ts,intent_id"))
        finally:
            con.close()
        return AgencySnapshot(
            state_epoch=int(meta["state_epoch"]),
            mode=str(meta["mode"]),
            next_tick_not_before=None if meta["next_tick_not_before"] is None else float(meta["next_tick_not_before"]),
            continuation_checkpoint=meta["continuation_checkpoint"],
            goals=goals,
            deferred_intents=intents,
        )


__all__ = [
    "AgencyError", "AgencySnapshot", "DeferredIntent", "DeferredIntentState",
    "GoalContract", "GoalState", "InvalidTransition", "PersistentAgencyStore",
    "StaleGeneration", "WakeKind",
]
