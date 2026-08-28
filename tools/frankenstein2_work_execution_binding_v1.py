#!/usr/bin/env python3
"""Frankenstein 2.0 native-child WorkExecutionBinding ledger.

This is the missing causal bridge between a durable workpackage and whatever native child
runtime actually executes it. It deliberately DOES NOT spawn children and DOES NOT assume a
particular Claude/Agent ABI. The caller must provide identity fields that were actually
observed from the installed runtime or from a bounded adapter.

Truth boundary:
  workpackage != spawn
  spawn request != child start
  child start != invocation
  invocation != result
  textual success != completion

Only a current-generation binding with an observed invocation/result and mechanistic
completion evidence can close a workpackage at this layer. Unknown external effect outcomes
stay UNKNOWN and cannot be rewritten into success.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping

SCHEMA = "FRANKENSTEIN2_WORK_EXECUTION_BINDING/v1"
EVENT_SCHEMA = "FRANKENSTEIN2_WORK_EXECUTION_EVENT/v1"
COMPLETION_SCHEMA = "FRANKENSTEIN2_COMPLETION_EVIDENCE/v1"

OUTCOMES = {"SUCCESS", "FAILURE", "REJECTED", "UNKNOWN"}
MECHANISTIC_EVIDENCE_KINDS = {
    "DETERMINISTIC_TEST_RECEIPT",
    "FILE_STATE_DIGEST",
    "DATABASE_STATE_DIGEST",
    "PROCESS_EXIT_AND_OUTPUT_DIGEST",
    "EFFECT_JOURNAL_VERIFIED_OUTCOME",
    "REMOTE_RESOURCE_VERSION_DIGEST",
}


def _canon(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None, timeout=10.0)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=10000")
    con.execute("PRAGMA foreign_keys=ON")
    return con


def _require_text(name: str, value: str) -> str:
    value = str(value or "").strip()
    if not value:
        raise ValueError(f"{name} required")
    return value


def init_schema(db_path: Path) -> None:
    con = _connect(Path(db_path))
    try:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS fr2_work_execution_bindings(
              binding_id TEXT PRIMARY KEY,
              workpackage_id TEXT NOT NULL,
              work_generation TEXT NOT NULL,
              parent_execution_id TEXT,
              child_runtime_kind TEXT NOT NULL,
              child_execution_id TEXT NOT NULL,
              native_agent_id TEXT,
              native_task_id TEXT,
              identity_provenance TEXT NOT NULL,
              identity_observed_at REAL NOT NULL,
              status TEXT NOT NULL,
              created_at REAL NOT NULL,
              UNIQUE(workpackage_id, work_generation, child_execution_id)
            );
            CREATE INDEX IF NOT EXISTS idx_fr2_work_binding_package
              ON fr2_work_execution_bindings(workpackage_id, work_generation, created_at);

            CREATE TABLE IF NOT EXISTS fr2_work_invocations(
              invocation_id TEXT PRIMARY KEY,
              binding_id TEXT NOT NULL REFERENCES fr2_work_execution_bindings(binding_id),
              invocation_kind TEXT NOT NULL,
              native_tool_use_id TEXT,
              request_digest TEXT NOT NULL,
              started_at REAL NOT NULL,
              UNIQUE(binding_id, native_tool_use_id)
            );

            CREATE TABLE IF NOT EXISTS fr2_work_results(
              result_id TEXT PRIMARY KEY,
              binding_id TEXT NOT NULL REFERENCES fr2_work_execution_bindings(binding_id),
              invocation_id TEXT NOT NULL UNIQUE REFERENCES fr2_work_invocations(invocation_id),
              outcome TEXT NOT NULL,
              result_digest TEXT NOT NULL,
              result_provenance TEXT NOT NULL,
              observed_at REAL NOT NULL
            );

            CREATE TABLE IF NOT EXISTS fr2_completion_evidence(
              completion_id TEXT PRIMARY KEY,
              binding_id TEXT NOT NULL REFERENCES fr2_work_execution_bindings(binding_id),
              invocation_id TEXT NOT NULL REFERENCES fr2_work_invocations(invocation_id),
              result_id TEXT NOT NULL REFERENCES fr2_work_results(result_id),
              evidence_kind TEXT NOT NULL,
              evidence_digest TEXT NOT NULL,
              evidence_ref TEXT NOT NULL,
              verified_at REAL NOT NULL,
              UNIQUE(binding_id, invocation_id, result_id)
            );

            CREATE TABLE IF NOT EXISTS fr2_work_execution_events(
              event_id INTEGER PRIMARY KEY AUTOINCREMENT,
              event_schema TEXT NOT NULL,
              binding_id TEXT NOT NULL,
              event_kind TEXT NOT NULL,
              event_json TEXT NOT NULL,
              event_digest TEXT NOT NULL,
              created_at REAL NOT NULL
            );
            """
        )
    finally:
        con.close()


def _append_event(con: sqlite3.Connection, binding_id: str, kind: str, payload: Mapping[str, Any]) -> str:
    body = {"schema": EVENT_SCHEMA, "binding_id": binding_id, "event_kind": kind, "payload": dict(payload)}
    digest = _digest(body)
    con.execute(
        "INSERT INTO fr2_work_execution_events(event_schema,binding_id,event_kind,event_json,event_digest,created_at) VALUES(?,?,?,?,?,?)",
        (EVENT_SCHEMA, binding_id, kind, _canon(body), digest, time.time()),
    )
    return digest


@dataclass(frozen=True)
class WorkExecutionBinding:
    binding_id: str
    workpackage_id: str
    work_generation: str
    child_runtime_kind: str
    child_execution_id: str
    native_agent_id: str | None
    native_task_id: str | None
    identity_provenance: str
    status: str


class WorkExecutionLedger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        init_schema(self.db_path)

    def bind_child(
        self,
        *,
        binding_id: str,
        workpackage_id: str,
        work_generation: str,
        child_runtime_kind: str,
        child_execution_id: str,
        identity_provenance: str,
        identity_observed_at: float | None = None,
        native_agent_id: str | None = None,
        native_task_id: str | None = None,
        parent_execution_id: str | None = None,
    ) -> WorkExecutionBinding:
        """Bind an OBSERVED child identity; never invent missing native IDs.

        `child_execution_id` is the adapter-neutral stable identity for this execution.
        Native IDs remain nullable because installed-runtime ABI is not yet proven. A caller
        may populate them only when actually observed.
        """
        vals = {
            "binding_id": _require_text("binding_id", binding_id),
            "workpackage_id": _require_text("workpackage_id", workpackage_id),
            "work_generation": _require_text("work_generation", work_generation),
            "child_runtime_kind": _require_text("child_runtime_kind", child_runtime_kind),
            "child_execution_id": _require_text("child_execution_id", child_execution_id),
            "identity_provenance": _require_text("identity_provenance", identity_provenance),
        }
        observed_at = float(identity_observed_at if identity_observed_at is not None else time.time())
        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                """INSERT INTO fr2_work_execution_bindings
                   (binding_id,workpackage_id,work_generation,parent_execution_id,child_runtime_kind,
                    child_execution_id,native_agent_id,native_task_id,identity_provenance,
                    identity_observed_at,status,created_at)
                   VALUES(?,?,?,?,?,?,?,?,?,?,'BOUND',?)""",
                (
                    vals["binding_id"], vals["workpackage_id"], vals["work_generation"],
                    parent_execution_id, vals["child_runtime_kind"], vals["child_execution_id"],
                    native_agent_id, native_task_id, vals["identity_provenance"], observed_at, time.time(),
                ),
            )
            _append_event(con, vals["binding_id"], "CHILD_IDENTITY_BOUND", {
                "workpackage_id": vals["workpackage_id"],
                "work_generation": vals["work_generation"],
                "child_runtime_kind": vals["child_runtime_kind"],
                "child_execution_id": vals["child_execution_id"],
                "native_agent_id": native_agent_id,
                "native_task_id": native_task_id,
                "identity_provenance": vals["identity_provenance"],
            })
            con.execute("COMMIT")
        except Exception:
            try: con.execute("ROLLBACK")
            except sqlite3.Error: pass
            raise
        finally:
            con.close()
        return WorkExecutionBinding(
            vals["binding_id"], vals["workpackage_id"], vals["work_generation"],
            vals["child_runtime_kind"], vals["child_execution_id"], native_agent_id,
            native_task_id, vals["identity_provenance"], "BOUND",
        )

    def record_invocation(
        self,
        *,
        binding_id: str,
        invocation_id: str,
        invocation_kind: str,
        request: Mapping[str, Any],
        native_tool_use_id: str | None = None,
        started_at: float | None = None,
    ) -> str:
        binding_id = _require_text("binding_id", binding_id)
        invocation_id = _require_text("invocation_id", invocation_id)
        invocation_kind = _require_text("invocation_kind", invocation_kind)
        request_digest = _digest(dict(request))
        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute("SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?", (binding_id,)).fetchone()
            if row is None:
                raise ValueError("unknown binding_id")
            if row["status"] in {"COMPLETED", "ABANDONED"}:
                raise ValueError(f"binding is terminal: {row['status']}")
            con.execute(
                "INSERT INTO fr2_work_invocations(invocation_id,binding_id,invocation_kind,native_tool_use_id,request_digest,started_at) VALUES(?,?,?,?,?,?)",
                (invocation_id, binding_id, invocation_kind, native_tool_use_id, request_digest, float(started_at or time.time())),
            )
            con.execute("UPDATE fr2_work_execution_bindings SET status='RUNNING' WHERE binding_id=?", (binding_id,))
            _append_event(con, binding_id, "INVOCATION_OBSERVED", {
                "invocation_id": invocation_id,
                "invocation_kind": invocation_kind,
                "native_tool_use_id": native_tool_use_id,
                "request_digest": request_digest,
            })
            con.execute("COMMIT")
            return request_digest
        except Exception:
            try: con.execute("ROLLBACK")
            except sqlite3.Error: pass
            raise
        finally:
            con.close()

    def record_result(
        self,
        *,
        result_id: str,
        binding_id: str,
        invocation_id: str,
        outcome: str,
        result: Mapping[str, Any],
        result_provenance: str,
        observed_at: float | None = None,
    ) -> str:
        outcome = str(outcome).upper().strip()
        if outcome not in OUTCOMES:
            raise ValueError(f"outcome must be one of {sorted(OUTCOMES)}")
        result_id = _require_text("result_id", result_id)
        binding_id = _require_text("binding_id", binding_id)
        invocation_id = _require_text("invocation_id", invocation_id)
        provenance = _require_text("result_provenance", result_provenance)
        result_digest = _digest(dict(result))
        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            inv = con.execute(
                "SELECT binding_id FROM fr2_work_invocations WHERE invocation_id=?", (invocation_id,)
            ).fetchone()
            if inv is None or inv["binding_id"] != binding_id:
                raise ValueError("result does not bind to this invocation/binding")
            con.execute(
                "INSERT INTO fr2_work_results(result_id,binding_id,invocation_id,outcome,result_digest,result_provenance,observed_at) VALUES(?,?,?,?,?,?,?)",
                (result_id, binding_id, invocation_id, outcome, result_digest, provenance, float(observed_at or time.time())),
            )
            # UNKNOWN remains explicitly nonterminal. FAILURE/REJECTED are terminal for this
            # invocation but not silently converted into workpackage completion.
            next_status = "RESULT_OBSERVED" if outcome != "UNKNOWN" else "UNKNOWN_OUTCOME"
            con.execute("UPDATE fr2_work_execution_bindings SET status=? WHERE binding_id=?", (next_status, binding_id))
            _append_event(con, binding_id, "RESULT_OBSERVED", {
                "result_id": result_id,
                "invocation_id": invocation_id,
                "outcome": outcome,
                "result_digest": result_digest,
                "result_provenance": provenance,
            })
            con.execute("COMMIT")
            return result_digest
        except Exception:
            try: con.execute("ROLLBACK")
            except sqlite3.Error: pass
            raise
        finally:
            con.close()

    def verify_completion(
        self,
        *,
        completion_id: str,
        binding_id: str,
        invocation_id: str,
        result_id: str,
        expected_work_generation: str,
        evidence_kind: str,
        evidence_ref: str,
        evidence_payload: Mapping[str, Any],
    ) -> str:
        """Close only a SUCCESS result at the exact current generation with typed evidence."""
        evidence_kind = str(evidence_kind).upper().strip()
        if evidence_kind not in MECHANISTIC_EVIDENCE_KINDS:
            raise ValueError("completion requires mechanistic evidence kind; textual/model claim is insufficient")
        completion_id = _require_text("completion_id", completion_id)
        evidence_ref = _require_text("evidence_ref", evidence_ref)
        expected_work_generation = _require_text("expected_work_generation", expected_work_generation)
        evidence_digest = _digest(dict(evidence_payload))
        con = _connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                """SELECT b.work_generation,r.outcome,r.binding_id,r.invocation_id
                   FROM fr2_work_execution_bindings b
                   JOIN fr2_work_results r ON r.binding_id=b.binding_id
                   WHERE b.binding_id=? AND r.result_id=?""",
                (binding_id, result_id),
            ).fetchone()
            if row is None:
                raise ValueError("missing bound result")
            if row["work_generation"] != expected_work_generation:
                raise ValueError("STALE_WORK_GENERATION")
            if row["invocation_id"] != invocation_id or row["binding_id"] != binding_id:
                raise ValueError("completion identity mismatch")
            if row["outcome"] != "SUCCESS":
                raise ValueError(f"completion forbidden for outcome={row['outcome']}")
            con.execute(
                "INSERT INTO fr2_completion_evidence(completion_id,binding_id,invocation_id,result_id,evidence_kind,evidence_digest,evidence_ref,verified_at) VALUES(?,?,?,?,?,?,?,?)",
                (completion_id, binding_id, invocation_id, result_id, evidence_kind, evidence_digest, evidence_ref, time.time()),
            )
            con.execute("UPDATE fr2_work_execution_bindings SET status='COMPLETED' WHERE binding_id=?", (binding_id,))
            _append_event(con, binding_id, "COMPLETION_VERIFIED", {
                "completion_id": completion_id,
                "invocation_id": invocation_id,
                "result_id": result_id,
                "work_generation": expected_work_generation,
                "evidence_kind": evidence_kind,
                "evidence_digest": evidence_digest,
                "evidence_ref": evidence_ref,
            })
            con.execute("COMMIT")
            return evidence_digest
        except Exception:
            try: con.execute("ROLLBACK")
            except sqlite3.Error: pass
            raise
        finally:
            con.close()

    def binding_snapshot(self, binding_id: str) -> dict[str, Any]:
        con = _connect(self.db_path)
        try:
            binding = con.execute("SELECT * FROM fr2_work_execution_bindings WHERE binding_id=?", (binding_id,)).fetchone()
            if binding is None:
                raise ValueError("unknown binding_id")
            invocations = [dict(x) for x in con.execute("SELECT * FROM fr2_work_invocations WHERE binding_id=? ORDER BY started_at,invocation_id", (binding_id,))]
            results = [dict(x) for x in con.execute("SELECT * FROM fr2_work_results WHERE binding_id=? ORDER BY observed_at,result_id", (binding_id,))]
            completions = [dict(x) for x in con.execute("SELECT * FROM fr2_completion_evidence WHERE binding_id=? ORDER BY verified_at,completion_id", (binding_id,))]
            return {
                "schema": SCHEMA,
                "binding": dict(binding),
                "invocations": invocations,
                "results": results,
                "completions": completions,
            }
        finally:
            con.close()
