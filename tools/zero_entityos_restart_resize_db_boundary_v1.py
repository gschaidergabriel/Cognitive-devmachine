#!/usr/bin/env python3
"""Executable DB-vs-simulation restart/resize boundary smoke for EntityOS/HCU.

Component/reference-fixture scope only. This module does not implement trained
cognition, Claude Code, canonical production DB admission, EffectGate, or a
Global J-Space runtime. It exists to falsify persistence/authority mistakes.

S0 = persistent exact state in SQLite.
S1 = rebuildable noncanonical workspace projection held in process memory.
S2 = disposable process-local scratch held in process memory.

No model/grid/Claude/J-Space path can directly mutate S0 here. Durable writes
must be proposed then admitted by the deterministic test boundary at the
current runtime generation. Effects are proposal-only; no EffectJournal write
exists in this fixture.
"""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from zero_entityos_variable_grid_fixture_v1 import canonical_json, digest

SMOKE_SCHEMA = "RESTART_RESIZE_DB_BOUNDARY_SMOKE/v1"
S1_SCHEMA = "ZERO_ENTITYOS_S1_REBUILD_PROJECTION/v1"
DB_PROPOSAL_SCHEMA = "ZERO_ENTITYOS_DB_WRITE_PROPOSAL/v1"
EFFECT_PROPOSAL_SCHEMA = "ZERO_ENTITYOS_EFFECT_PROPOSAL/v1"


class BoundaryError(ValueError):
    pass


@dataclass(frozen=True)
class RuntimeIdentity:
    runtime_generation: int
    grid_n: int


class RestartResizeDBBoundary:
    def __init__(self, db_path: str | Path, *, grid_n: int):
        if isinstance(grid_n, bool) or not isinstance(grid_n, int) or grid_n < 1:
            raise BoundaryError("grid_n:MUST_BE_POSITIVE_INT")
        self.db_path = str(db_path)
        self.grid_n = grid_n
        self.con = sqlite3.connect(self.db_path)
        self.con.row_factory = sqlite3.Row
        self._schema()
        self.runtime_generation = self._next_runtime_generation()
        self.s1: dict[str, dict[str, Any]] = {}
        self.s2: dict[str, Any] = {}

    def _schema(self) -> None:
        self.con.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_metadata(
              key TEXT PRIMARY KEY,
              value INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS s0_state(
              object_key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL,
              epoch INTEGER NOT NULL,
              digest TEXT NOT NULL,
              admitted_generation INTEGER NOT NULL,
              provenance TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS db_write_proposals(
              proposal_id TEXT PRIMARY KEY,
              schema TEXT NOT NULL,
              work_id TEXT NOT NULL,
              object_key TEXT NOT NULL,
              value_json TEXT NOT NULL,
              value_digest TEXT NOT NULL,
              source_generation INTEGER NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS effect_proposals(
              proposal_id TEXT PRIMARY KEY,
              schema TEXT NOT NULL,
              work_id TEXT NOT NULL,
              request_json TEXT NOT NULL,
              request_digest TEXT NOT NULL,
              source_generation INTEGER NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS effect_journal(
              effect_id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL,
              outcome TEXT NOT NULL
            );
            """
        )
        self.con.commit()

    def _next_runtime_generation(self) -> int:
        row = self.con.execute(
            "SELECT value FROM runtime_metadata WHERE key='runtime_generation'"
        ).fetchone()
        generation = 1 if row is None else int(row[0]) + 1
        self.con.execute(
            """INSERT INTO runtime_metadata(key,value) VALUES('runtime_generation',?)
               ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
            (generation,),
        )
        self.con.commit()
        return generation

    @property
    def identity(self) -> RuntimeIdentity:
        return RuntimeIdentity(self.runtime_generation, self.grid_n)

    def close(self) -> None:
        self.con.close()

    def seed_s0_fixture(self, object_key: str, value: Any, *, provenance: str = "TEST_FIXTURE") -> None:
        """Test-only deterministic seed. Never callable as a model/result admission."""
        if not object_key:
            raise BoundaryError("object_key:REQUIRED")
        value_json = canonical_json(value)
        value_digest = digest(value)
        existing = self.con.execute(
            "SELECT 1 FROM s0_state WHERE object_key=?", (object_key,)
        ).fetchone()
        if existing:
            raise BoundaryError("S0_FIXTURE_SEED_ALREADY_EXISTS")
        self.con.execute(
            """INSERT INTO s0_state
               (object_key,value_json,epoch,digest,admitted_generation,provenance)
               VALUES(?,?,?,?,?,?)""",
            (
                object_key,
                value_json,
                1,
                value_digest,
                self.runtime_generation,
                provenance,
            ),
        )
        self.con.commit()

    def read_s0(self, object_key: str) -> dict[str, Any] | None:
        row = self.con.execute(
            """SELECT object_key,value_json,epoch,digest,admitted_generation,provenance
               FROM s0_state WHERE object_key=?""",
            (object_key,),
        ).fetchone()
        if row is None:
            return None
        return {
            "object_key": row["object_key"],
            "value": json.loads(row["value_json"]),
            "epoch": int(row["epoch"]),
            "digest": row["digest"],
            "admitted_generation": int(row["admitted_generation"]),
            "provenance": row["provenance"],
        }

    def s0_snapshot(self) -> list[dict[str, Any]]:
        rows = self.con.execute(
            """SELECT object_key,value_json,epoch,digest,admitted_generation,provenance
               FROM s0_state ORDER BY object_key"""
        ).fetchall()
        return [
            {
                "object_key": row["object_key"],
                "value": json.loads(row["value_json"]),
                "epoch": int(row["epoch"]),
                "digest": row["digest"],
                "admitted_generation": int(row["admitted_generation"]),
                "provenance": row["provenance"],
            }
            for row in rows
        ]

    def s0_fingerprint(self) -> str:
        """Canonical-state fingerprint intentionally excludes runtime generation and grid N."""
        return digest({"schema": "ZERO_ENTITYOS_S0_FIXTURE/v1", "state": self.s0_snapshot()})

    def rebuild_s1_from_s0(self, object_keys: Iterable[str]) -> dict[str, dict[str, Any]]:
        projection: dict[str, dict[str, Any]] = {}
        for key in sorted(set(object_keys)):
            state = self.read_s0(key)
            if state is None:
                projection[key] = {
                    "schema": S1_SCHEMA,
                    "object_key": key,
                    "status": "UNKNOWN",
                    "source_s0_digest": None,
                    "source_s0_epoch": None,
                    "runtime_generation": self.runtime_generation,
                    "truth_authority": False,
                    "effect_authority": False,
                }
            else:
                projection[key] = {
                    "schema": S1_SCHEMA,
                    "object_key": key,
                    "status": "PROJECTED_FROM_S0",
                    "value": state["value"],
                    "source_s0_digest": state["digest"],
                    "source_s0_epoch": state["epoch"],
                    "runtime_generation": self.runtime_generation,
                    "truth_authority": False,
                    "effect_authority": False,
                }
        self.s1 = projection
        return json.loads(canonical_json(projection))

    def write_s2(self, key: str, value: Any) -> None:
        if not key:
            raise BoundaryError("s2.key:REQUIRED")
        self.s2[key] = json.loads(canonical_json(value))

    def propose_db_write(
        self,
        *,
        work_id: str,
        object_key: str,
        value: Any,
        source_generation: int | None = None,
    ) -> str:
        if not work_id or not object_key:
            raise BoundaryError("DB_PROPOSAL_IDENTITY_REQUIRED")
        if source_generation is None:
            source_generation = self.runtime_generation
        if isinstance(source_generation, bool) or not isinstance(source_generation, int) or source_generation < 1:
            raise BoundaryError("source_generation:MUST_BE_POSITIVE_INT")
        value_json = canonical_json(value)
        value_digest = digest(value)
        proposal_id = "dbp-" + digest(
            {
                "schema": DB_PROPOSAL_SCHEMA,
                "work_id": work_id,
                "object_key": object_key,
                "value_digest": value_digest,
                "source_generation": source_generation,
            }
        )[:24]
        self.con.execute(
            """INSERT INTO db_write_proposals
               (proposal_id,schema,work_id,object_key,value_json,value_digest,source_generation,status)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                proposal_id,
                DB_PROPOSAL_SCHEMA,
                work_id,
                object_key,
                value_json,
                value_digest,
                source_generation,
                "PROPOSED_NOT_COMMITTED",
            ),
        )
        self.con.commit()
        return proposal_id

    def admit_db_write(self, proposal_id: str, *, expected_generation: int) -> dict[str, Any]:
        if expected_generation != self.runtime_generation:
            raise BoundaryError("ADMISSION_EXPECTED_GENERATION_STALE")
        row = self.con.execute(
            "SELECT * FROM db_write_proposals WHERE proposal_id=?", (proposal_id,)
        ).fetchone()
        if row is None:
            raise BoundaryError("DB_PROPOSAL_NOT_FOUND")
        if row["status"] != "PROPOSED_NOT_COMMITTED":
            raise BoundaryError("DB_PROPOSAL_NOT_PENDING")
        if int(row["source_generation"]) != self.runtime_generation:
            self.con.execute(
                "UPDATE db_write_proposals SET status='REJECTED_STALE_GENERATION' WHERE proposal_id=?",
                (proposal_id,),
            )
            self.con.commit()
            raise BoundaryError("DB_PROPOSAL_SOURCE_GENERATION_STALE")

        current = self.con.execute(
            "SELECT epoch FROM s0_state WHERE object_key=?", (row["object_key"],)
        ).fetchone()
        next_epoch = 1 if current is None else int(current[0]) + 1
        self.con.execute(
            """INSERT INTO s0_state
               (object_key,value_json,epoch,digest,admitted_generation,provenance)
               VALUES(?,?,?,?,?,?)
               ON CONFLICT(object_key) DO UPDATE SET
                 value_json=excluded.value_json,
                 epoch=excluded.epoch,
                 digest=excluded.digest,
                 admitted_generation=excluded.admitted_generation,
                 provenance=excluded.provenance""",
            (
                row["object_key"],
                row["value_json"],
                next_epoch,
                row["value_digest"],
                self.runtime_generation,
                f"ADMITTED_PROPOSAL:{proposal_id}",
            ),
        )
        self.con.execute(
            "UPDATE db_write_proposals SET status='ADMITTED_TO_S0' WHERE proposal_id=?",
            (proposal_id,),
        )
        self.con.commit()
        return self.read_s0(row["object_key"])  # type: ignore[return-value]

    def model_direct_s0_write(self, *_: Any, **__: Any) -> None:
        raise BoundaryError("DIRECT_MODEL_GRID_CLAUDE_JSPACE_TO_S0_FORBIDDEN")

    def recover_s0_from_s1_cache(self, *_: Any, **__: Any) -> None:
        raise BoundaryError("S1_CACHE_IS_NOT_S0_RECOVERY_AUTHORITY")

    def propose_effect(self, *, work_id: str, request: Any) -> str:
        if not work_id:
            raise BoundaryError("effect.work_id:REQUIRED")
        request_json = canonical_json(request)
        request_digest = digest(request)
        proposal_id = "efp-" + digest(
            {
                "schema": EFFECT_PROPOSAL_SCHEMA,
                "work_id": work_id,
                "request_digest": request_digest,
                "source_generation": self.runtime_generation,
            }
        )[:24]
        self.con.execute(
            """INSERT INTO effect_proposals
               (proposal_id,schema,work_id,request_json,request_digest,source_generation,status)
               VALUES(?,?,?,?,?,?,?)""",
            (
                proposal_id,
                EFFECT_PROPOSAL_SCHEMA,
                work_id,
                request_json,
                request_digest,
                self.runtime_generation,
                "PROPOSED_NOT_EXECUTED",
            ),
        )
        self.con.commit()
        return proposal_id

    def direct_effect(self, *_: Any, **__: Any) -> None:
        raise BoundaryError("DIRECT_EFFECT_EXECUTION_FORBIDDEN_EFFECTGATE_REQUIRED")

    def count(self, table: str) -> int:
        allowed = {"s0_state", "db_write_proposals", "effect_proposals", "effect_journal"}
        if table not in allowed:
            raise BoundaryError("table:NOT_ALLOWED")
        return int(self.con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
