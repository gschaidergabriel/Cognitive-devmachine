#!/usr/bin/env python3
"""Frankenstein 2.0 WorkExecutionBinding v2 terminal-state hardening.

Successor to v1.  It preserves the v1 storage model but closes two truth-boundary
failures that matter for Stage-1 coordination correctness:

1. a result from an invocation that was already in flight must not regress a binding
   after CompletionGate has marked it COMPLETED;
2. a binding must not be completed while any invocation is still unresolved, and a
   binding may have at most one completion record.

The module is intentionally narrow.  It does not spawn workers, grant effect authority,
or infer native agent/task identity.  Existing v1 databases are admitted only when they
contain no legacy multiple-completion ambiguity.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sqlite3
import sys
import time
from typing import Any, Mapping


_V1_PATH = Path(__file__).with_name("frankenstein2_work_execution_binding_v1.py")
_SPEC = importlib.util.spec_from_file_location("frankenstein2_work_execution_binding_v1", _V1_PATH)
if _SPEC is None or _SPEC.loader is None:
    raise RuntimeError("FR2_WORK_EXECUTION_BINDING_V1_IMPORT_FAILED")
v1 = importlib.util.module_from_spec(_SPEC)
sys.modules.setdefault(_SPEC.name, v1)
_SPEC.loader.exec_module(v1)

SCHEMA = "FRANKENSTEIN2_WORK_EXECUTION_BINDING/v2"
TERMINAL_BINDING_STATES = {"COMPLETED", "ABANDONED"}


def init_hardened_schema(db_path: Path) -> None:
    """Install v1 schema plus the v2 one-completion-per-binding invariant.

    A legacy database with multiple completions is ambiguous and therefore cannot be
    silently normalized.  It must be reconciled explicitly before v2 is admitted.
    """
    v1.init_schema(Path(db_path))
    con = v1._connect(Path(db_path))
    try:
        con.execute("BEGIN IMMEDIATE")
        duplicate = con.execute(
            """SELECT binding_id,COUNT(*) AS n
               FROM fr2_completion_evidence
               GROUP BY binding_id
               HAVING COUNT(*) > 1
               ORDER BY binding_id
               LIMIT 1"""
        ).fetchone()
        if duplicate is not None:
            raise ValueError(
                f"LEGACY_MULTIPLE_COMPLETIONS_REQUIRE_RECONCILIATION:"
                f"{duplicate['binding_id']}:{duplicate['n']}"
            )
        con.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_fr2_single_completion_per_binding "
            "ON fr2_completion_evidence(binding_id)"
        )
        con.execute("COMMIT")
    except Exception:
        try:
            con.execute("ROLLBACK")
        except sqlite3.Error:
            pass
        raise
    finally:
        con.close()


class WorkExecutionLedger(v1.WorkExecutionLedger):
    """v2 ledger with monotonic terminal-state and completion closure semantics."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)
        init_hardened_schema(self.db_path)

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
        if outcome not in v1.OUTCOMES:
            raise ValueError(f"outcome must be one of {sorted(v1.OUTCOMES)}")
        result_id = v1._require_text("result_id", result_id)
        binding_id = v1._require_text("binding_id", binding_id)
        invocation_id = v1._require_text("invocation_id", invocation_id)
        provenance = v1._require_text("result_provenance", result_provenance)
        result_digest = v1._digest(dict(result))

        con = v1._connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            binding = con.execute(
                "SELECT status FROM fr2_work_execution_bindings WHERE binding_id=?",
                (binding_id,),
            ).fetchone()
            if binding is None:
                raise ValueError("unknown binding_id")
            if str(binding["status"]) in TERMINAL_BINDING_STATES:
                raise ValueError(f"binding is terminal: {binding['status']}")

            inv = con.execute(
                "SELECT binding_id FROM fr2_work_invocations WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if inv is None or inv["binding_id"] != binding_id:
                raise ValueError("result does not bind to this invocation/binding")

            con.execute(
                """INSERT INTO fr2_work_results
                   (result_id,binding_id,invocation_id,outcome,result_digest,result_provenance,observed_at)
                   VALUES(?,?,?,?,?,?,?)""",
                (
                    result_id,
                    binding_id,
                    invocation_id,
                    outcome,
                    result_digest,
                    provenance,
                    float(observed_at if observed_at is not None else time.time()),
                ),
            )
            next_status = "RESULT_OBSERVED" if outcome != "UNKNOWN" else "UNKNOWN_OUTCOME"
            cur = con.execute(
                """UPDATE fr2_work_execution_bindings
                   SET status=?
                   WHERE binding_id=? AND status NOT IN ('COMPLETED','ABANDONED')""",
                (next_status, binding_id),
            )
            if cur.rowcount != 1:
                raise ValueError("TERMINAL_BINDING_STATUS_REGRESSION_FORBIDDEN")
            v1._append_event(
                con,
                binding_id,
                "RESULT_OBSERVED",
                {
                    "result_id": result_id,
                    "invocation_id": invocation_id,
                    "outcome": outcome,
                    "result_digest": result_digest,
                    "result_provenance": provenance,
                    "binding_schema": SCHEMA,
                },
            )
            con.execute("COMMIT")
            return result_digest
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
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
        """Mint one completion only after every observed invocation has a known result."""
        evidence_kind = str(evidence_kind).upper().strip()
        if evidence_kind not in v1.MECHANISTIC_EVIDENCE_KINDS:
            raise ValueError(
                "completion requires mechanistic evidence kind; textual/model claim is insufficient"
            )
        completion_id = v1._require_text("completion_id", completion_id)
        binding_id = v1._require_text("binding_id", binding_id)
        invocation_id = v1._require_text("invocation_id", invocation_id)
        result_id = v1._require_text("result_id", result_id)
        evidence_ref = v1._require_text("evidence_ref", evidence_ref)
        expected_work_generation = v1._require_text(
            "expected_work_generation", expected_work_generation
        )
        evidence_digest = v1._digest(dict(evidence_payload))

        con = v1._connect(self.db_path)
        try:
            con.execute("BEGIN IMMEDIATE")
            row = con.execute(
                """SELECT b.work_generation,b.status,r.outcome,r.binding_id,r.invocation_id
                   FROM fr2_work_execution_bindings b
                   JOIN fr2_work_results r ON r.binding_id=b.binding_id
                   WHERE b.binding_id=? AND r.result_id=?""",
                (binding_id, result_id),
            ).fetchone()
            if row is None:
                raise ValueError("missing bound result")
            if str(row["status"]) in TERMINAL_BINDING_STATES:
                raise ValueError(f"binding is terminal: {row['status']}")
            if row["work_generation"] != expected_work_generation:
                raise ValueError("STALE_WORK_GENERATION")
            if row["invocation_id"] != invocation_id or row["binding_id"] != binding_id:
                raise ValueError("completion identity mismatch")
            if row["outcome"] != "SUCCESS":
                raise ValueError(f"completion forbidden for outcome={row['outcome']}")

            unresolved = con.execute(
                """SELECT COUNT(*) AS n
                   FROM fr2_work_invocations i
                   LEFT JOIN fr2_work_results r ON r.invocation_id=i.invocation_id
                   WHERE i.binding_id=? AND r.result_id IS NULL""",
                (binding_id,),
            ).fetchone()
            unresolved_n = int(unresolved["n"])
            if unresolved_n:
                raise ValueError(f"UNRESOLVED_INVOCATIONS:{unresolved_n}")

            unknown = con.execute(
                "SELECT COUNT(*) AS n FROM fr2_work_results WHERE binding_id=? AND outcome='UNKNOWN'",
                (binding_id,),
            ).fetchone()
            unknown_n = int(unknown["n"])
            if unknown_n:
                raise ValueError(f"UNKNOWN_INVOCATION_OUTCOME:{unknown_n}")

            existing = con.execute(
                "SELECT completion_id FROM fr2_completion_evidence WHERE binding_id=?",
                (binding_id,),
            ).fetchone()
            if existing is not None:
                raise ValueError(
                    f"BINDING_ALREADY_HAS_COMPLETION:{existing['completion_id']}"
                )

            con.execute(
                """INSERT INTO fr2_completion_evidence
                   (completion_id,binding_id,invocation_id,result_id,evidence_kind,evidence_digest,evidence_ref,verified_at)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (
                    completion_id,
                    binding_id,
                    invocation_id,
                    result_id,
                    evidence_kind,
                    evidence_digest,
                    evidence_ref,
                    time.time(),
                ),
            )
            cur = con.execute(
                """UPDATE fr2_work_execution_bindings
                   SET status='COMPLETED'
                   WHERE binding_id=? AND status NOT IN ('COMPLETED','ABANDONED')""",
                (binding_id,),
            )
            if cur.rowcount != 1:
                raise ValueError("COMPLETION_TERMINAL_CAS_FAILED")
            v1._append_event(
                con,
                binding_id,
                "COMPLETION_VERIFIED",
                {
                    "completion_id": completion_id,
                    "invocation_id": invocation_id,
                    "result_id": result_id,
                    "work_generation": expected_work_generation,
                    "evidence_kind": evidence_kind,
                    "evidence_digest": evidence_digest,
                    "evidence_ref": evidence_ref,
                    "binding_schema": SCHEMA,
                    "all_observed_invocations_resolved": True,
                    "unknown_outcome_count": 0,
                },
            )
            con.execute("COMMIT")
            return evidence_digest
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()


__all__ = [
    "SCHEMA",
    "TERMINAL_BINDING_STATES",
    "WorkExecutionLedger",
    "init_hardened_schema",
]
