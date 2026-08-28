#!/usr/bin/env python3
"""Immutable external-call -> canonical-effect identity binding for Frankenstein 2.0.

This is a deterministic Stage-1 source primitive. It does not execute an effect,
grant EffectGate authority, or mint completion/runtime credit.

The key invariant is a create-once bijection:

    immutable_call_id <-> canonical_effect_id

Session-scoped mutable pointers are context only and are never accepted as correlation
authority. A result can be re-entered only after the exact observed call id resolves to
the exact canonical effect id selected for the lifecycle store.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sqlite3
import time
from typing import Protocol


SCHEMA = "FRANKENSTEIN2_EFFECT_CALL_BIJECTION/v1"


class EffectCallBijectionError(RuntimeError):
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
class CallEffectBinding:
    immutable_call_id: str
    canonical_effect_id: str
    session_id: str
    agent_id: str
    task_id: str
    turn_id: str
    causal_id: str
    generation: int
    bound_ts: float


class EffectCallBijectionStore:
    """SQLite-backed create-once bijection for external call and effect identities."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        con = self._con()
        try:
            con.execute(
                """
                CREATE TABLE IF NOT EXISTS effect_call_bindings(
                  immutable_call_id TEXT PRIMARY KEY,
                  canonical_effect_id TEXT NOT NULL UNIQUE,
                  session_id TEXT NOT NULL,
                  agent_id TEXT NOT NULL,
                  task_id TEXT NOT NULL,
                  turn_id TEXT NOT NULL,
                  causal_id TEXT NOT NULL,
                  generation INTEGER NOT NULL,
                  bound_ts REAL NOT NULL
                )
                """
            )
        finally:
            con.close()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), isolation_level=None, timeout=10.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=10000")
        con.execute("PRAGMA synchronous=NORMAL")
        return con

    @staticmethod
    def _validate_identity(name: str, value: str) -> str:
        value = str(value)
        if not value:
            raise EffectCallBijectionError(f"MISSING_{name}")
        return value

    @staticmethod
    def _row_to_binding(row: sqlite3.Row) -> CallEffectBinding:
        return CallEffectBinding(
            immutable_call_id=str(row["immutable_call_id"]),
            canonical_effect_id=str(row["canonical_effect_id"]),
            session_id=str(row["session_id"]),
            agent_id=str(row["agent_id"]),
            task_id=str(row["task_id"]),
            turn_id=str(row["turn_id"]),
            causal_id=str(row["causal_id"]),
            generation=int(row["generation"]),
            bound_ts=float(row["bound_ts"]),
        )

    def bind_once(
        self,
        *,
        immutable_call_id: str,
        canonical_effect_id: str,
        session_id: str,
        agent_id: str,
        task_id: str,
        turn_id: str,
        causal_id: str,
        generation: int,
        now_ts: float | None = None,
    ) -> CallEffectBinding:
        """Create exactly one immutable call<->effect pair; reassignment always fails closed."""
        immutable_call_id = self._validate_identity("IMMUTABLE_CALL_ID", immutable_call_id)
        canonical_effect_id = self._validate_identity("CANONICAL_EFFECT_ID", canonical_effect_id)
        session_id = self._validate_identity("SESSION_ID", session_id)
        agent_id = self._validate_identity("AGENT_ID", agent_id)
        task_id = self._validate_identity("TASK_ID", task_id)
        turn_id = self._validate_identity("TURN_ID", turn_id)
        causal_id = self._validate_identity("CAUSAL_ID", causal_id)
        generation = int(generation)
        if generation < 0:
            raise EffectCallBijectionError("INVALID_GENERATION")
        ts = time.time() if now_ts is None else float(now_ts)

        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            if con.execute(
                "SELECT 1 FROM effect_call_bindings WHERE immutable_call_id=?",
                (immutable_call_id,),
            ).fetchone() is not None:
                raise EffectCallBijectionError("IMMUTABLE_CALL_ID_ALREADY_BOUND")
            if con.execute(
                "SELECT 1 FROM effect_call_bindings WHERE canonical_effect_id=?",
                (canonical_effect_id,),
            ).fetchone() is not None:
                raise EffectCallBijectionError("CANONICAL_EFFECT_ID_ALREADY_BOUND")
            con.execute(
                "INSERT INTO effect_call_bindings VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    immutable_call_id,
                    canonical_effect_id,
                    session_id,
                    agent_id,
                    task_id,
                    turn_id,
                    causal_id,
                    generation,
                    ts,
                ),
            )
            con.execute("COMMIT")
            return CallEffectBinding(
                immutable_call_id=immutable_call_id,
                canonical_effect_id=canonical_effect_id,
                session_id=session_id,
                agent_id=agent_id,
                task_id=task_id,
                turn_id=turn_id,
                causal_id=causal_id,
                generation=generation,
                bound_ts=ts,
            )
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def resolve_call(self, immutable_call_id: str) -> CallEffectBinding:
        immutable_call_id = self._validate_identity("IMMUTABLE_CALL_ID", immutable_call_id)
        con = self._con()
        try:
            row = con.execute(
                "SELECT * FROM effect_call_bindings WHERE immutable_call_id=?",
                (immutable_call_id,),
            ).fetchone()
            if row is None:
                raise EffectCallBijectionError("UNKNOWN_IMMUTABLE_CALL_ID")
            return self._row_to_binding(row)
        finally:
            con.close()

    def resolve_effect(self, canonical_effect_id: str) -> CallEffectBinding:
        canonical_effect_id = self._validate_identity("CANONICAL_EFFECT_ID", canonical_effect_id)
        con = self._con()
        try:
            row = con.execute(
                "SELECT * FROM effect_call_bindings WHERE canonical_effect_id=?",
                (canonical_effect_id,),
            ).fetchone()
            if row is None:
                raise EffectCallBijectionError("UNKNOWN_CANONICAL_EFFECT_ID")
            return self._row_to_binding(row)
        finally:
            con.close()

    def verify_pair(
        self,
        *,
        immutable_call_id: str,
        canonical_effect_id: str,
    ) -> CallEffectBinding:
        binding = self.resolve_call(immutable_call_id)
        if binding.canonical_effect_id != canonical_effect_id:
            raise EffectCallBijectionError("CALL_EFFECT_BIJECTION_MISMATCH")
        reverse = self.resolve_effect(canonical_effect_id)
        if reverse.immutable_call_id != immutable_call_id:
            raise EffectCallBijectionError("CALL_EFFECT_REVERSE_BIJECTION_MISMATCH")
        return binding


def reenter_bijected_result(
    binding_store: EffectCallBijectionStore,
    lifecycle_store: ResultReentryStore,
    *,
    immutable_call_id: str,
    target_canonical_effect_id: str,
    result_digest: str,
    now_ts: float | None = None,
) -> CallEffectBinding:
    """Resolve the immutable call id before any lifecycle mutation occurs."""
    if not result_digest:
        raise EffectCallBijectionError("MISSING_RESULT_DIGEST")
    binding = binding_store.verify_pair(
        immutable_call_id=immutable_call_id,
        canonical_effect_id=target_canonical_effect_id,
    )
    lifecycle_store.reenter_result(
        binding.canonical_effect_id,
        result_digest=result_digest,
        now_ts=now_ts,
    )
    return binding
