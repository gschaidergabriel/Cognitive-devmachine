#!/usr/bin/env python3
"""Executable restart/resize discriminator for the EntityOS/HCU DB boundary.

This fixture intentionally separates durable S0 and cognitive S1/S2 storage:
- S0 is a file-backed SQLite DB owned by deterministic CanonicalStateAuthority.
- grid cognition gets an SQLite engine-level read-only S0 connection.
- S1/S2 live in an in-memory DB and disappear on module/grid restart.
- DB_WRITE_PROPOSAL/v2 binds the S0 object epoch observed by cognition.
- canonical admission uses BEGIN IMMEDIATE + compare-and-admit, so a same-generation
  stale proposal cannot overwrite a newer S0 value.

No model, Claude Code, provider, tool, network or real-effect execution occurs.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import tempfile
from typing import Any

SMOKE_SCHEMA = "RESTART_RESIZE_DB_BOUNDARY_SMOKE/v2"


class BoundaryError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class CanonicalStateAuthority:
    """Sole deterministic S0 writer used by this component fixture."""

    def __init__(self, path: Path):
        self.path = Path(path)
        # Autocommit permits an explicit BEGIN IMMEDIATE around the compare+commit section.
        self.con = sqlite3.connect(self.path, isolation_level=None)
        self.con.row_factory = sqlite3.Row
        self.con.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS canonical_state(
              object_key TEXT PRIMARY KEY,
              value_json TEXT NOT NULL,
              value_digest TEXT NOT NULL,
              provenance TEXT NOT NULL,
              generation INTEGER NOT NULL,
              epoch INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS admission_log(
              admission_id TEXT PRIMARY KEY,
              proposal_id TEXT NOT NULL,
              source_result_id TEXT NOT NULL,
              generation INTEGER NOT NULL,
              object_key TEXT NOT NULL,
              expected_s0_epoch INTEGER NOT NULL,
              committed_s0_epoch INTEGER NOT NULL,
              value_digest TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.con.close()

    def seed(self, key: str, value: Any, *, provenance: str, generation: int, epoch: int) -> str:
        text = canonical_json(value)
        value_digest = digest(value)
        self.con.execute(
            "INSERT OR REPLACE INTO canonical_state VALUES(?,?,?,?,?,?)",
            (key, text, value_digest, provenance, generation, epoch),
        )
        return value_digest

    def get(self, key: str) -> dict[str, Any] | None:
        row = self.con.execute("SELECT * FROM canonical_state WHERE object_key=?", (key,)).fetchone()
        if row is None:
            return None
        return {
            "object_key": row["object_key"],
            "value": json.loads(row["value_json"]),
            "value_digest": row["value_digest"],
            "provenance": row["provenance"],
            "generation": row["generation"],
            "epoch": row["epoch"],
        }

    def snapshot_digest(self) -> str:
        rows = self.con.execute(
            "SELECT object_key,value_json,value_digest,provenance,generation,epoch "
            "FROM canonical_state ORDER BY object_key"
        ).fetchall()
        return digest([dict(row) for row in rows])

    def admit_proposal(self, proposal: dict[str, Any], *, current_generation: int, epoch: int) -> str:
        if proposal.get("schema") != "DB_WRITE_PROPOSAL/v2":
            raise BoundaryError("PROPOSAL_SCHEMA_INVALID")
        if proposal.get("canonical_commit") is not False:
            raise BoundaryError("PROPOSAL_SELF_COMMIT_FORBIDDEN")
        if proposal.get("generation") != current_generation:
            raise BoundaryError("STALE_GENERATION_WRITE_PROPOSAL_REJECTED")

        value_digest = digest(proposal["value"])
        if proposal.get("value_digest") != value_digest:
            raise BoundaryError("PROPOSAL_VALUE_DIGEST_MISMATCH")

        expected_s0_epoch = proposal.get("expected_s0_epoch")
        if (
            isinstance(expected_s0_epoch, bool)
            or not isinstance(expected_s0_epoch, int)
            or expected_s0_epoch < 0
        ):
            raise BoundaryError("EXPECTED_S0_EPOCH_INVALID")

        self.con.execute("BEGIN IMMEDIATE")
        try:
            row = self.con.execute(
                "SELECT epoch FROM canonical_state WHERE object_key=?",
                (proposal["object_key"],),
            ).fetchone()
            current_s0_epoch = 0 if row is None else int(row["epoch"])
            if current_s0_epoch != expected_s0_epoch:
                raise BoundaryError("STALE_S0_EPOCH_WRITE_PROPOSAL_REJECTED")
            if isinstance(epoch, bool) or not isinstance(epoch, int) or epoch <= current_s0_epoch:
                raise BoundaryError("NEW_S0_EPOCH_NOT_MONOTONIC")

            admission_id = "dba-" + digest(
                {
                    "proposal_id": proposal["proposal_id"],
                    "generation": current_generation,
                    "expected_s0_epoch": expected_s0_epoch,
                    "committed_s0_epoch": epoch,
                    "value_digest": value_digest,
                }
            )[:24]

            self.con.execute(
                "INSERT OR REPLACE INTO canonical_state VALUES(?,?,?,?,?,?)",
                (
                    proposal["object_key"],
                    canonical_json(proposal["value"]),
                    value_digest,
                    f"proposal:{proposal['proposal_id']}",
                    current_generation,
                    epoch,
                ),
            )
            self.con.execute(
                "INSERT INTO admission_log VALUES(?,?,?,?,?,?,?,?)",
                (
                    admission_id,
                    proposal["proposal_id"],
                    proposal["source_result_id"],
                    current_generation,
                    proposal["object_key"],
                    expected_s0_epoch,
                    epoch,
                    value_digest,
                ),
            )
            self.con.execute("COMMIT")
            return admission_id
        except Exception:
            self.con.execute("ROLLBACK")
            raise


@dataclass(frozen=True)
class GridConfig:
    n: int
    generation: int

    def __post_init__(self):
        if isinstance(self.n, bool) or not isinstance(self.n, int) or self.n < 1:
            raise BoundaryError("N_MUST_BE_POSITIVE")
        if isinstance(self.generation, bool) or not isinstance(self.generation, int) or self.generation < 0:
            raise BoundaryError("GENERATION_INVALID")


class CognitiveGridRuntime:
    """Variable-N cognitive side with engine-level read-only S0 and disposable S1/S2."""

    def __init__(self, canonical_db: Path, config: GridConfig):
        self.config = config
        uri = f"file:{Path(canonical_db).resolve()}?mode=ro"
        self.s0 = sqlite3.connect(uri, uri=True)
        self.s0.row_factory = sqlite3.Row
        self.s1 = sqlite3.connect(":memory:")
        self.s1.row_factory = sqlite3.Row
        self.s1.executescript(
            """
            CREATE TABLE work_queue(
              work_id TEXT PRIMARY KEY,
              process_id TEXT NOT NULL,
              payload_json TEXT NOT NULL,
              semantic_identity TEXT NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE result_log(
              result_id TEXT PRIMARY KEY,
              work_id TEXT NOT NULL,
              process_id TEXT NOT NULL,
              executor_id TEXT NOT NULL,
              semantic_identity TEXT NOT NULL,
              result_class TEXT NOT NULL
            );
            CREATE TABLE db_write_proposals(
              proposal_id TEXT PRIMARY KEY,
              proposal_json TEXT NOT NULL
            );
            CREATE TABLE effect_candidates(
              candidate_id TEXT PRIMARY KEY,
              request_json TEXT NOT NULL,
              status TEXT NOT NULL
            );
            CREATE TABLE workspace_reentry(
              reentry_id TEXT PRIMARY KEY,
              source_result_id TEXT NOT NULL,
              process_id TEXT NOT NULL,
              payload_digest TEXT NOT NULL
            );
            """
        )

    def close(self) -> None:
        self.s1.close()
        self.s0.close()

    def read_s0(self, key: str) -> Any | None:
        row = self.s0.execute("SELECT value_json FROM canonical_state WHERE object_key=?", (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def read_s0_epoch(self, key: str) -> int:
        row = self.s0.execute("SELECT epoch FROM canonical_state WHERE object_key=?", (key,)).fetchone()
        return 0 if row is None else int(row["epoch"])

    def attempt_direct_s0_write(self, key: str, value: Any) -> bool:
        """Return True only when SQLite itself rejects cognitive direct S0 mutation."""
        try:
            text = canonical_json(value)
            self.s0.execute(
                "INSERT OR REPLACE INTO canonical_state VALUES(?,?,?,?,?,?)",
                (key, text, digest(value), "ILLEGAL_COGNITIVE_PATH", self.config.generation, 999),
            )
            self.s0.commit()
        except sqlite3.OperationalError as exc:
            if "readonly" in str(exc).lower() or "read-only" in str(exc).lower():
                # A failed DML statement still opens an implicit transaction (python
                # sqlite3 legacy transaction handling begins one before any DML, even
                # one that then raises). Without an explicit rollback, this read-only
                # connection stays pinned to its pre-attempt snapshot and silently
                # stops observing subsequent committed writes from the S0 writer
                # connection -- rollback releases that stale snapshot immediately.
                self.s0.rollback()
                return True
            raise
        return False

    def enqueue(self, process_id: str, payload: Any) -> dict[str, Any]:
        payload_digest = digest(payload)
        semantic_identity = digest(
            {
                "schema": "COGNITIVE_WORK_SEMANTIC_IDENTITY/v1",
                "generation": self.config.generation,
                "process_id": process_id,
                "payload_digest": payload_digest,
            }
        )
        work_id = "work-" + semantic_identity[:24]
        self.s1.execute(
            "INSERT OR IGNORE INTO work_queue VALUES(?,?,?,?,?)",
            (work_id, process_id, canonical_json(payload), semantic_identity, "READY"),
        )
        self.s1.commit()
        return {"work_id": work_id, "process_id": process_id, "semantic_identity": semantic_identity}

    def execute(self, work: dict[str, Any]) -> dict[str, Any]:
        row = self.s1.execute("SELECT * FROM work_queue WHERE work_id=?", (work["work_id"],)).fetchone()
        if row is None or row["status"] != "READY":
            raise BoundaryError("WORK_NOT_READY")
        slot = int(hashlib.sha256(row["work_id"].encode()).hexdigest(), 16) % self.config.n
        executor_id = f"node-{slot:04d}"
        result_id = "res-" + digest(
            {
                "semantic_identity": row["semantic_identity"],
                "executor_id": executor_id,
                "N": self.config.n,
            }
        )[:24]
        self.s1.execute(
            "INSERT INTO result_log VALUES(?,?,?,?,?,?)",
            (result_id, row["work_id"], row["process_id"], executor_id, row["semantic_identity"], "CANDIDATE"),
        )
        self.s1.execute("UPDATE work_queue SET status='DONE' WHERE work_id=?", (row["work_id"],))
        self.s1.commit()
        return {
            "result_id": result_id,
            "work_id": row["work_id"],
            "process_id": row["process_id"],
            "executor_id": executor_id,
            "semantic_identity": row["semantic_identity"],
            "result_class": "CANDIDATE",
            "canonical_truth": False,
            "effect_authority": False,
        }

    def propose_db_write(self, result: dict[str, Any], key: str, value: Any) -> dict[str, Any]:
        proposal = {
            "schema": "DB_WRITE_PROPOSAL/v2",
            "source_result_id": result["result_id"],
            "generation": self.config.generation,
            "object_key": key,
            "expected_s0_epoch": self.read_s0_epoch(key),
            "value": value,
            "value_digest": digest(value),
            "canonical_commit": False,
        }
        proposal_id = "dbp-" + digest(proposal)[:24]
        proposal["proposal_id"] = proposal_id
        self.s1.execute(
            "INSERT INTO db_write_proposals VALUES(?,?)", (proposal_id, canonical_json(proposal))
        )
        self.s1.commit()
        return proposal

    def propose_effect(self, result: dict[str, Any], request: Any) -> str:
        candidate_id = "efp-" + digest({"result_id": result["result_id"], "request": request})[:24]
        self.s1.execute(
            "INSERT INTO effect_candidates VALUES(?,?,?)",
            (candidate_id, canonical_json(request), "PROPOSED_NOT_EXECUTED"),
        )
        self.s1.commit()
        return candidate_id

    def stub_claude_reentry(self, result: dict[str, Any], payload: Any) -> dict[str, Any]:
        """Observable bridge-shape fixture only; there is no Claude/model call."""
        payload_digest = digest(payload)
        reentry = {
            "schema": "WORKSPACE_REENTRY/v1",
            "source_result_id": result["result_id"],
            "source_process_id": "ZECP14",
            "payload_digest": payload_digest,
            "model_execution_observed": False,
            "activation_access_claimed": False,
            "global_jspace_causal_credit": False,
        }
        reentry_id = "re-" + digest(reentry)[:24]
        self.s1.execute(
            "INSERT INTO workspace_reentry VALUES(?,?,?,?)",
            (reentry_id, result["result_id"], "ZECP14", payload_digest),
        )
        self.s1.commit()
        return {**reentry, "reentry_id": reentry_id}

    def s1_counts(self) -> dict[str, int]:
        out = {}
        for table in ("work_queue", "result_log", "db_write_proposals", "effect_candidates", "workspace_reentry"):
            out[table] = int(self.s1.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
        return out


def _rebased_copy(proposal: dict[str, Any], *, proposal_id: str, expected_s0_epoch: int) -> dict[str, Any]:
    fresh = dict(proposal)
    fresh["proposal_id"] = proposal_id
    fresh["expected_s0_epoch"] = expected_s0_epoch
    return fresh


def run_restart_resize_smoke(db_path: Path) -> dict[str, Any]:
    authority = CanonicalStateAuthority(db_path)
    try:
        generation = 3
        authority.seed("task/id", "task-001", provenance="fixture:admitted", generation=generation, epoch=1)
        authority.seed("goal", {"goal": "restart-resize"}, provenance="fixture:admitted", generation=generation, epoch=1)
        authority.seed("evidence/ref", "ev-001", provenance="fixture:observed", generation=generation, epoch=1)
        s0_before = authority.snapshot_digest()

        grid1 = CognitiveGridRuntime(db_path, GridConfig(n=1, generation=generation))
        try:
            if not grid1.attempt_direct_s0_write("illegal/model-write", {"x": 1}):
                raise BoundaryError("DIRECT_COGNITIVE_S0_WRITE_NOT_REJECTED")
            work1 = grid1.enqueue("ZECP03", {"goal_ref": "goal", "evidence_ref": "evidence/ref"})
            result1 = grid1.execute(work1)
            proposal = grid1.propose_db_write(result1, "memory/admitted", {"summary": "bounded"})
            if proposal["expected_s0_epoch"] != 0:
                raise BoundaryError("NEW_OBJECT_EXPECTED_EPOCH_NOT_ZERO")

            # A and B intentionally observe the same object epoch. A may win; B must fail
            # even though its generation remains current.
            authority.seed("memory/race", {"winner": "base"}, provenance="fixture:race", generation=generation, epoch=7)
            race_a = grid1.propose_db_write(result1, "memory/race", {"winner": "A"})
            race_b = grid1.propose_db_write(result1, "memory/race", {"winner": "B"})
            if race_a["expected_s0_epoch"] != 7 or race_b["expected_s0_epoch"] != 7:
                raise BoundaryError("RACE_PROPOSALS_DID_NOT_BIND_SHARED_OBSERVED_EPOCH")

            if authority.get("memory/admitted") is not None:
                raise BoundaryError("PROPOSAL_MUTATED_S0_BEFORE_ADMISSION")
            effect_candidate = grid1.propose_effect(result1, {"kind": "fixture-noop"})
            claude_stub = grid1.stub_claude_reentry(result1, {"candidate": "no-model-call"})
            s1_pre_restart = grid1.s1_counts()
        finally:
            grid1.close()

        admission_id = authority.admit_proposal(proposal, current_generation=generation, epoch=2)
        race_a_admission_id = authority.admit_proposal(race_a, current_generation=generation, epoch=8)

        same_generation_stale_rejected = False
        try:
            authority.admit_proposal(race_b, current_generation=generation, epoch=9)
        except BoundaryError as exc:
            same_generation_stale_rejected = str(exc) == "STALE_S0_EPOCH_WRITE_PROPOSAL_REJECTED"
        if not same_generation_stale_rejected:
            raise BoundaryError("SAME_GENERATION_STALE_EPOCH_NOT_REJECTED")
        race_after_a = authority.get("memory/race")
        if race_after_a is None or race_after_a["value"] != {"winner": "A"} or race_after_a["epoch"] != 8:
            raise BoundaryError("STALE_REJECTION_DID_NOT_PRESERVE_WINNER")

        # Once B explicitly rebases to the observed winner epoch, it may commit at a newer epoch.
        race_b_rebased = _rebased_copy(race_b, proposal_id="dbp-race-b-rebased", expected_s0_epoch=8)
        race_b_rebased_admission_id = authority.admit_proposal(
            race_b_rebased, current_generation=generation, epoch=9
        )
        race_after_rebase = authority.get("memory/race")
        if race_after_rebase is None or race_after_rebase["value"] != {"winner": "B"} or race_after_rebase["epoch"] != 9:
            raise BoundaryError("FRESH_REBASE_DID_NOT_COMMIT")

        s0_after_admission = authority.snapshot_digest()
        if s0_before == s0_after_admission:
            raise BoundaryError("ADMITTED_DURABLE_PROPOSAL_DID_NOT_CHANGE_S0")

        stale = dict(proposal)
        stale["proposal_id"] = "dbp-stale-generation"
        stale["generation"] = generation - 1
        stale_rejected = False
        try:
            authority.admit_proposal(stale, current_generation=generation, epoch=3)
        except BoundaryError as exc:
            stale_rejected = str(exc) == "STALE_GENERATION_WRITE_PROPOSAL_REJECTED"
        if not stale_rejected:
            raise BoundaryError("STALE_GENERATION_NOT_REJECTED")

        grid20 = CognitiveGridRuntime(db_path, GridConfig(n=20, generation=generation))
        try:
            s1_after_restart = grid20.s1_counts()
            if any(s1_after_restart.values()):
                raise BoundaryError("S1_S2_SURVIVED_RESTART")
            if grid20.read_s0("goal") != {"goal": "restart-resize"}:
                raise BoundaryError("S0_GOAL_NOT_REBUILT")
            if grid20.read_s0("memory/admitted") != {"summary": "bounded"}:
                raise BoundaryError("ADMITTED_MEMORY_NOT_PERSISTENT")
            if grid20.read_s0("memory/race") != {"winner": "B"}:
                raise BoundaryError("REBASING_RESULT_NOT_PERSISTENT")
            if authority.snapshot_digest() != s0_after_admission:
                raise BoundaryError("S0_CHANGED_DURING_RESTART_RESIZE")
            work20 = grid20.enqueue("ZECP18", {"resume_from": "memory/admitted"})
            result20 = grid20.execute(work20)
            if result20["process_id"] == result1["process_id"]:
                raise BoundaryError("RESTART_DID_NOT_ROUTE_DIFFERENT_PROCESS")
            if not grid20.attempt_direct_s0_write("illegal/after-resize", {"x": 2}):
                raise BoundaryError("POST_RESIZE_DIRECT_S0_WRITE_NOT_REJECTED")
        finally:
            grid20.close()

        return {
            "schema": SMOKE_SCHEMA,
            "N_before": 1,
            "N_after": 20,
            "network_or_provider_io": False,
            "model_execution_observed": False,
            "claude_code_execution_observed": False,
            "real_effect_execution_observed": False,
            "checks": {
                "S0_ENGINE_LEVEL_READONLY_FROM_COGNITION": True,
                "DB_PROPOSAL_DOES_NOT_SELF_COMMIT": True,
                "DB_PROPOSAL_BINDS_EXPECTED_S0_EPOCH": True,
                "DETERMINISTIC_PROPOSAL_ADMISSION_SUCCEEDS": True,
                "STALE_GENERATION_WRITE_REJECTED": True,
                "SAME_GENERATION_STALE_S0_EPOCH_WRITE_REJECTED": True,
                "FRESH_S0_EPOCH_REBASE_SUCCEEDS": True,
                "S1_S2_DISCARDED_ON_RESTART": True,
                "S0_PERSISTS_ACROSS_RESTART_AND_N_RESIZE": True,
                "DIFFERENT_PROCESS_ROUTES_AFTER_RESTART": True,
                "EFFECT_REMAINS_CANDIDATE_ONLY": bool(effect_candidate),
                "CLAUDE_REENTRY_STUB_NONAUTHORITATIVE": claude_stub["global_jspace_causal_credit"] is False,
            },
            "evidence": {
                "s0_before_digest": s0_before,
                "s0_after_admission_digest": s0_after_admission,
                "admission_id": admission_id,
                "race_a_admission_id": race_a_admission_id,
                "race_b_same_generation_stale_rejected": same_generation_stale_rejected,
                "race_b_rebased_admission_id": race_b_rebased_admission_id,
                "race_final_epoch": race_after_rebase["epoch"],
                "s1_pre_restart": s1_pre_restart,
                "s1_after_restart": s1_after_restart,
                "process_before": result1["process_id"],
                "process_after": result20["process_id"],
                "executor_before": result1["executor_id"],
                "executor_after": result20["executor_id"],
            },
            "credit_boundary": {
                "db_simulation_boundary_component_runtime": 1,
                "s0_epoch_cas_component_runtime": 1,
                "variable_grid_model_runtime": 0,
                "claude_code_bridge_runtime": 0,
                "global_jspace_causal_runtime": 0,
                "whole_entityos_hcu_runtime": 0,
                "training": 0,
            },
        }
    finally:
        authority.close()


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="entityos-db-smoke-") as td:
        receipt = run_restart_resize_smoke(Path(td) / "canonical.sqlite3")
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
