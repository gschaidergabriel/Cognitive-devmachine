#!/usr/bin/env python3
"""Frankenstein 2.0 Stage-1 deterministic effect lifecycle substrate.

Source-level implementation of the Triggerword-4 forensic fusion contract. This module
models and persists immutable per-invocation effect identity and its typed receipts. It
does NOT itself execute tools or grant runtime/EffectGate authority.

Required chain:
    EffectRequest -> AdmissionDecision -> EnforcementReceipt -> ExecutionReceipt
    -> WorldEffectVerification -> ResultReentry -> CompletionEvidence

The critical safety property is that session_id is context only. invocation_id is the
correlation authority for every state transition, including parallel/reordered calls.

CompletionEvidence is minted only at issue_completion_evidence(). That method is wired to
the source-bound Frankenstein-2 Completion Verifier v2. The v1 completion_status() remains
a diagnostic/precondition view and can no longer mint completion by itself.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Any, Mapping

try:  # package import when tests import tools.frankenstein2_effect_lifecycle_v1
    from .frankenstein2_completion_verifier_v2 import (
        ADMISSION_SCHEMA as V2_ADMISSION_SCHEMA,
        ENFORCEMENT_SCHEMA as V2_ENFORCEMENT_SCHEMA,
        EXECUTION_SCHEMA as V2_EXECUTION_SCHEMA,
        REENTRY_SCHEMA as V2_REENTRY_SCHEMA,
        WORLD_SCHEMA as V2_WORLD_SCHEMA,
        AdmissionReceipt as V2AdmissionReceipt,
        EnforcementReceipt as V2EnforcementReceipt,
        ExecutionReceipt as V2ExecutionReceipt,
        ExpectedInvocation as V2ExpectedInvocation,
        ResultReentryReceipt as V2ResultReentryReceipt,
        WorldVerificationReceipt as V2WorldVerificationReceipt,
        verify_completion as verify_completion_v2,
    )
except ImportError:  # direct script/tools-PYTHONPATH execution
    from frankenstein2_completion_verifier_v2 import (
        ADMISSION_SCHEMA as V2_ADMISSION_SCHEMA,
        ENFORCEMENT_SCHEMA as V2_ENFORCEMENT_SCHEMA,
        EXECUTION_SCHEMA as V2_EXECUTION_SCHEMA,
        REENTRY_SCHEMA as V2_REENTRY_SCHEMA,
        WORLD_SCHEMA as V2_WORLD_SCHEMA,
        AdmissionReceipt as V2AdmissionReceipt,
        EnforcementReceipt as V2EnforcementReceipt,
        ExecutionReceipt as V2ExecutionReceipt,
        ExpectedInvocation as V2ExpectedInvocation,
        ResultReentryReceipt as V2ResultReentryReceipt,
        WorldVerificationReceipt as V2WorldVerificationReceipt,
        verify_completion as verify_completion_v2,
    )

SCHEMA = "FRANKENSTEIN2_EFFECT_LIFECYCLE/v1"
V2_COMPLETION_EVIDENCE_CLASS = "VERIFIED_EFFECT_COMPLETION_V2"


class EffectLifecycleError(RuntimeError):
    pass


class AdmissionDecision(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    UNKNOWN = "UNKNOWN"


class PendingEffectState(str, Enum):
    PENDING = "PENDING"
    CANCELLED_BEFORE_SUBMISSION = "CANCELLED_BEFORE_SUBMISSION"
    SUBMITTED = "SUBMITTED"


class WorldOutcome(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class EffectRequest:
    invocation_id: str
    session_id: str
    agent_id: str
    task_id: str
    turn_id: str
    causal_id: str
    generation: int
    tool_name: str
    normalized_arguments: Mapping[str, Any]
    effect_scope: str
    request_digest: str
    parent_candidate_id: str | None = None


@dataclass(frozen=True)
class CompletionStatus:
    closable: bool
    reasons: tuple[str, ...]


class EffectLifecycleStore:
    """SQLite-backed source substrate for exact per-invocation effect correlation.

    This store intentionally has no executor callback. A real executor boundary must
    independently honor an EnforcementReceipt before runtime enforcement credit exists.
    """

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _con(self) -> sqlite3.Connection:
        con = sqlite3.connect(str(self.path), isolation_level=None, timeout=10.0)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA busy_timeout=10000")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def _init_schema(self) -> None:
        con = self._con()
        try:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS effect_requests(
                  invocation_id TEXT PRIMARY KEY,
                  session_id TEXT NOT NULL,
                  agent_id TEXT NOT NULL,
                  task_id TEXT NOT NULL,
                  turn_id TEXT NOT NULL,
                  causal_id TEXT NOT NULL,
                  generation INTEGER NOT NULL,
                  tool_name TEXT NOT NULL,
                  arguments_json TEXT NOT NULL,
                  effect_scope TEXT NOT NULL,
                  request_digest TEXT NOT NULL,
                  parent_candidate_id TEXT,
                  pending_state TEXT NOT NULL,
                  created_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS admission_decisions(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  decision TEXT NOT NULL,
                  reason TEXT NOT NULL,
                  decided_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS enforcement_receipts(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  decision TEXT NOT NULL,
                  request_digest TEXT NOT NULL,
                  dispatch_permitted INTEGER NOT NULL,
                  boundary_id TEXT NOT NULL,
                  enforced_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS execution_receipts(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  request_digest TEXT NOT NULL,
                  executable_id TEXT NOT NULL,
                  command_digest TEXT NOT NULL,
                  environment_id TEXT NOT NULL,
                  exit_code INTEGER NOT NULL,
                  result_digest TEXT NOT NULL,
                  executed_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS world_effect_verifications(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  outcome TEXT NOT NULL,
                  evidence_digest TEXT,
                  verified_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS result_reentries(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  result_digest TEXT NOT NULL,
                  task_id TEXT NOT NULL,
                  turn_id TEXT NOT NULL,
                  causal_id TEXT NOT NULL,
                  generation INTEGER NOT NULL,
                  reentered_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS completion_evidence(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  evidence_class TEXT NOT NULL,
                  receipt_digest TEXT NOT NULL,
                  created_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS completion_v2_source_bindings(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  expected_source_digest TEXT NOT NULL,
                  bound_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS execution_v2_metadata(
                  invocation_id TEXT PRIMARY KEY REFERENCES effect_requests(invocation_id),
                  source_digest TEXT NOT NULL,
                  duplicate_state TEXT NOT NULL,
                  status TEXT NOT NULL,
                  recorded_ts REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS effect_lifecycle_events(
                  seq INTEGER PRIMARY KEY AUTOINCREMENT,
                  invocation_id TEXT NOT NULL,
                  event_type TEXT NOT NULL,
                  payload_json TEXT NOT NULL,
                  created_ts REAL NOT NULL
                );
                """
            )
        finally:
            con.close()

    @staticmethod
    def build_request(
        *,
        invocation_id: str,
        session_id: str,
        agent_id: str,
        task_id: str,
        turn_id: str,
        causal_id: str,
        generation: int,
        tool_name: str,
        normalized_arguments: Mapping[str, Any],
        effect_scope: str,
        parent_candidate_id: str | None = None,
    ) -> EffectRequest:
        if not invocation_id or not tool_name or generation < 0:
            raise EffectLifecycleError("INVALID_EFFECT_REQUEST_IDENTITY")
        args = dict(normalized_arguments)
        digest = digest_json(
            {
                "invocation_id": invocation_id,
                "session_id": session_id,
                "agent_id": agent_id,
                "task_id": task_id,
                "turn_id": turn_id,
                "causal_id": causal_id,
                "generation": int(generation),
                "tool_name": tool_name,
                "normalized_arguments": args,
                "effect_scope": effect_scope,
                "parent_candidate_id": parent_candidate_id,
            }
        )
        return EffectRequest(
            invocation_id=invocation_id,
            session_id=session_id,
            agent_id=agent_id,
            task_id=task_id,
            turn_id=turn_id,
            causal_id=causal_id,
            generation=int(generation),
            tool_name=tool_name,
            normalized_arguments=args,
            effect_scope=effect_scope,
            request_digest=digest,
            parent_candidate_id=parent_candidate_id,
        )

    def _event(self, con: sqlite3.Connection, invocation_id: str, event_type: str, payload: Mapping[str, Any], ts: float) -> None:
        con.execute(
            "INSERT INTO effect_lifecycle_events(invocation_id,event_type,payload_json,created_ts) VALUES(?,?,?,?)",
            (invocation_id, event_type, canonical_json(dict(payload)), float(ts)),
        )

    def create_request(self, req: EffectRequest, *, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            con.execute(
                "INSERT INTO effect_requests VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    req.invocation_id, req.session_id, req.agent_id, req.task_id,
                    req.turn_id, req.causal_id, req.generation, req.tool_name,
                    canonical_json(dict(req.normalized_arguments)), req.effect_scope,
                    req.request_digest, req.parent_candidate_id,
                    PendingEffectState.PENDING.value, ts,
                ),
            )
            self._event(con, req.invocation_id, "EFFECT_REQUEST_CREATED", {"request_digest": req.request_digest}, ts)
            con.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            con.execute("ROLLBACK")
            raise EffectLifecycleError(f"DUPLICATE_INVOCATION_ID:{req.invocation_id}") from exc
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def bind_completion_source(
        self,
        invocation_id: str,
        *,
        source_digest: str,
        now_ts: float | None = None,
    ) -> None:
        """Create-once expected source identity before any submission can occur."""
        ts = time.time() if now_ts is None else float(now_ts)
        if not source_digest:
            raise EffectLifecycleError("MISSING_EXPECTED_SOURCE_DIGEST")
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            if req["pending_state"] != PendingEffectState.PENDING.value:
                raise EffectLifecycleError("SOURCE_BINDING_REQUIRES_PRE_SUBMISSION_PENDING")
            con.execute(
                "INSERT INTO completion_v2_source_bindings VALUES(?,?,?)",
                (invocation_id, str(source_digest), ts),
            )
            self._event(
                con,
                invocation_id,
                "COMPLETION_V2_SOURCE_BOUND",
                {"expected_source_digest": str(source_digest)},
                ts,
            )
            con.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise EffectLifecycleError("COMPLETION_V2_SOURCE_ALREADY_BOUND") from exc
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def decide(self, invocation_id: str, decision: AdmissionDecision | str, *, reason: str, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        decision = AdmissionDecision(decision)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._require_request(con, invocation_id)
            if con.execute("SELECT 1 FROM admission_decisions WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("ADMISSION_DECISION_ALREADY_FINAL")
            con.execute("INSERT INTO admission_decisions VALUES(?,?,?,?)", (invocation_id, decision.value, reason, ts))
            self._event(con, invocation_id, "ADMISSION_DECIDED", {"decision": decision.value, "reason": reason}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def record_enforcement(self, invocation_id: str, *, boundary_id: str, dispatch_permitted: bool, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            adm = con.execute("SELECT decision FROM admission_decisions WHERE invocation_id=?", (invocation_id,)).fetchone()
            if adm is None:
                raise EffectLifecycleError("ENFORCEMENT_WITHOUT_ADMISSION")
            decision = AdmissionDecision(adm["decision"])
            expected_dispatch = decision is AdmissionDecision.ALLOW
            if bool(dispatch_permitted) != expected_dispatch:
                raise EffectLifecycleError(f"ENFORCEMENT_CONTRADICTS_ADMISSION:{decision.value}:{int(bool(dispatch_permitted))}")
            if con.execute("SELECT 1 FROM enforcement_receipts WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("ENFORCEMENT_RECEIPT_ALREADY_FINAL")
            con.execute(
                "INSERT INTO enforcement_receipts VALUES(?,?,?,?,?,?)",
                (invocation_id, decision.value, req["request_digest"], int(bool(dispatch_permitted)), boundary_id, ts),
            )
            self._event(con, invocation_id, "ENFORCEMENT_RECORDED", {"decision": decision.value, "dispatch_permitted": bool(dispatch_permitted), "boundary_id": boundary_id}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def cancel_before_submission(self, invocation_id: str, *, reason: str, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            if req["pending_state"] != PendingEffectState.PENDING.value:
                raise EffectLifecycleError(f"CANNOT_CANCEL_STATE:{req['pending_state']}")
            changed = con.execute(
                "UPDATE effect_requests SET pending_state=? WHERE invocation_id=? AND pending_state=?",
                (PendingEffectState.CANCELLED_BEFORE_SUBMISSION.value, invocation_id, PendingEffectState.PENDING.value),
            ).rowcount
            if changed != 1:
                raise EffectLifecycleError("CANCELLATION_CAS_FAILED")
            self._event(con, invocation_id, "CANCELLED_BEFORE_SUBMISSION", {"reason": reason}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def mark_submitted(self, invocation_id: str, *, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            if req["pending_state"] != PendingEffectState.PENDING.value:
                raise EffectLifecycleError(f"SUBMIT_REQUIRES_PENDING:{req['pending_state']}")
            adm = con.execute("SELECT decision FROM admission_decisions WHERE invocation_id=?", (invocation_id,)).fetchone()
            enf = con.execute("SELECT decision,request_digest,dispatch_permitted FROM enforcement_receipts WHERE invocation_id=?", (invocation_id,)).fetchone()
            if adm is None or adm["decision"] != AdmissionDecision.ALLOW.value:
                raise EffectLifecycleError("SUBMIT_REQUIRES_ALLOW")
            if enf is None or int(enf["dispatch_permitted"]) != 1:
                raise EffectLifecycleError("SUBMIT_REQUIRES_ENFORCEMENT_ALLOW")
            if enf["decision"] != AdmissionDecision.ALLOW.value or enf["request_digest"] != req["request_digest"]:
                raise EffectLifecycleError("SUBMIT_IDENTITY_MISMATCH")
            source_binding = con.execute(
                "SELECT expected_source_digest FROM completion_v2_source_bindings WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if source_binding is None or not str(source_binding["expected_source_digest"]):
                raise EffectLifecycleError("SUBMIT_REQUIRES_SOURCE_BINDING")
            changed = con.execute(
                "UPDATE effect_requests SET pending_state=? WHERE invocation_id=? AND pending_state=?",
                (PendingEffectState.SUBMITTED.value, invocation_id, PendingEffectState.PENDING.value),
            ).rowcount
            if changed != 1:
                raise EffectLifecycleError("SUBMIT_CAS_FAILED")
            self._event(con, invocation_id, "EFFECT_SUBMITTED", {"request_digest": req["request_digest"]}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def record_execution(self, invocation_id: str, *, executable_id: str, command_digest: str, environment_id: str, exit_code: int, result_digest: str, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            if req["pending_state"] != PendingEffectState.SUBMITTED.value:
                raise EffectLifecycleError("EXECUTION_RECEIPT_REQUIRES_SUBMITTED")
            if con.execute("SELECT 1 FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("EXECUTION_RECEIPT_ALREADY_FINAL")
            con.execute(
                "INSERT INTO execution_receipts VALUES(?,?,?,?,?,?,?,?)",
                (invocation_id, req["request_digest"], executable_id, command_digest, environment_id, int(exit_code), result_digest, ts),
            )
            self._event(con, invocation_id, "EXECUTION_RECORDED", {"exit_code": int(exit_code), "result_digest": result_digest}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def record_execution_v2_metadata(
        self,
        invocation_id: str,
        *,
        source_digest: str,
        duplicate_state: str,
        status: str,
        now_ts: float | None = None,
    ) -> None:
        """Persist the v2-only execution identity fields after the base execution receipt."""
        ts = time.time() if now_ts is None else float(now_ts)
        if not source_digest:
            raise EffectLifecycleError("MISSING_EXECUTION_SOURCE_DIGEST")
        if not duplicate_state:
            raise EffectLifecycleError("MISSING_EXECUTION_DUPLICATE_STATE")
        if not status:
            raise EffectLifecycleError("MISSING_EXECUTION_STATUS")
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._require_request(con, invocation_id)
            exe = con.execute(
                "SELECT exit_code FROM execution_receipts WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if exe is None:
                raise EffectLifecycleError("V2_EXECUTION_METADATA_REQUIRES_EXECUTION_RECEIPT")
            if str(status) == "SUCCEEDED" and int(exe["exit_code"]) != 0:
                raise EffectLifecycleError("SUCCEEDED_STATUS_CONTRADICTS_NONZERO_EXIT")
            con.execute(
                "INSERT INTO execution_v2_metadata VALUES(?,?,?,?,?)",
                (invocation_id, str(source_digest), str(duplicate_state), str(status), ts),
            )
            self._event(
                con,
                invocation_id,
                "EXECUTION_V2_METADATA_RECORDED",
                {
                    "source_digest": str(source_digest),
                    "duplicate_state": str(duplicate_state),
                    "status": str(status),
                },
                ts,
            )
            con.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise EffectLifecycleError("EXECUTION_V2_METADATA_ALREADY_FINAL") from exc
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def record_execution_bundle(
        self,
        invocation_id: str,
        *,
        executable_id: str,
        command_digest: str,
        environment_id: str,
        exit_code: int,
        result_digest: str,
        source_digest: str,
        duplicate_state: str,
        status: str,
        now_ts: float | None = None,
    ) -> None:
        """Atomically persist the base execution receipt and its v2 identity metadata.

        The external dispatch has already returned by this point. Because SUBMITTED means
        the real-world outcome may exist, a persistence failure must roll back both local
        execution rows so recovery never observes a half-bundle and callers can classify
        the post-submission state as UNKNOWN rather than treating a partial receipt as fact.
        """
        ts = time.time() if now_ts is None else float(now_ts)
        if not source_digest:
            raise EffectLifecycleError("MISSING_EXECUTION_SOURCE_DIGEST")
        if not duplicate_state:
            raise EffectLifecycleError("MISSING_EXECUTION_DUPLICATE_STATE")
        if not status:
            raise EffectLifecycleError("MISSING_EXECUTION_STATUS")
        status = str(status)
        if status == "SUCCEEDED" and int(exit_code) != 0:
            raise EffectLifecycleError("SUCCEEDED_STATUS_CONTRADICTS_NONZERO_EXIT")

        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            if req["pending_state"] != PendingEffectState.SUBMITTED.value:
                raise EffectLifecycleError("EXECUTION_RECEIPT_REQUIRES_SUBMITTED")
            if con.execute("SELECT 1 FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("EXECUTION_RECEIPT_ALREADY_FINAL")
            if con.execute("SELECT 1 FROM execution_v2_metadata WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("EXECUTION_V2_METADATA_ALREADY_FINAL")

            source_binding = con.execute(
                "SELECT expected_source_digest FROM completion_v2_source_bindings WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            if source_binding is None:
                raise EffectLifecycleError("EXECUTION_BUNDLE_REQUIRES_SOURCE_BINDING")
            if str(source_binding["expected_source_digest"]) != str(source_digest):
                raise EffectLifecycleError("EXECUTION_SOURCE_DIGEST_MISMATCH")

            con.execute(
                "INSERT INTO execution_receipts VALUES(?,?,?,?,?,?,?,?)",
                (
                    invocation_id,
                    req["request_digest"],
                    executable_id,
                    command_digest,
                    environment_id,
                    int(exit_code),
                    result_digest,
                    ts,
                ),
            )
            con.execute(
                "INSERT INTO execution_v2_metadata VALUES(?,?,?,?,?)",
                (invocation_id, str(source_digest), str(duplicate_state), status, ts),
            )
            self._event(
                con,
                invocation_id,
                "EXECUTION_RECORDED",
                {"exit_code": int(exit_code), "result_digest": result_digest},
                ts,
            )
            self._event(
                con,
                invocation_id,
                "EXECUTION_V2_METADATA_RECORDED",
                {
                    "source_digest": str(source_digest),
                    "duplicate_state": str(duplicate_state),
                    "status": status,
                },
                ts,
            )
            con.execute("COMMIT")
        except sqlite3.IntegrityError as exc:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise EffectLifecycleError("EXECUTION_BUNDLE_PERSISTENCE_CONFLICT") from exc
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def verify_world_effect(self, invocation_id: str, outcome: WorldOutcome | str, *, evidence_digest: str | None, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        outcome = WorldOutcome(outcome)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            self._require_request(con, invocation_id)
            if con.execute("SELECT 1 FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone() is None:
                raise EffectLifecycleError("WORLD_VERIFICATION_REQUIRES_EXECUTION_RECEIPT")
            if con.execute("SELECT 1 FROM world_effect_verifications WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("WORLD_VERIFICATION_ALREADY_FINAL")
            con.execute("INSERT INTO world_effect_verifications VALUES(?,?,?,?)", (invocation_id, outcome.value, evidence_digest, ts))
            self._event(con, invocation_id, "WORLD_EFFECT_VERIFIED", {"outcome": outcome.value, "evidence_digest": evidence_digest}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def reenter_result(self, invocation_id: str, *, result_digest: str, now_ts: float | None = None) -> None:
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            exe = con.execute("SELECT result_digest FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone()
            if exe is None:
                raise EffectLifecycleError("RESULT_REENTRY_REQUIRES_EXECUTION_RECEIPT")
            if exe["result_digest"] != result_digest:
                raise EffectLifecycleError("RESULT_REENTRY_DIGEST_MISMATCH")
            if con.execute("SELECT 1 FROM result_reentries WHERE invocation_id=?", (invocation_id,)).fetchone():
                raise EffectLifecycleError("RESULT_REENTRY_ALREADY_FINAL")
            con.execute(
                "INSERT INTO result_reentries VALUES(?,?,?,?,?,?,?)",
                (invocation_id, result_digest, req["task_id"], req["turn_id"], req["causal_id"], int(req["generation"]), ts),
            )
            self._event(con, invocation_id, "RESULT_REENTERED", {"result_digest": result_digest}, ts)
            con.execute("COMMIT")
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def completion_status(self, invocation_id: str) -> CompletionStatus:
        con = self._con()
        try:
            req = self._require_request(con, invocation_id)
            reasons: list[str] = []
            adm = con.execute("SELECT decision FROM admission_decisions WHERE invocation_id=?", (invocation_id,)).fetchone()
            enf = con.execute("SELECT decision,request_digest,dispatch_permitted FROM enforcement_receipts WHERE invocation_id=?", (invocation_id,)).fetchone()
            exe = con.execute("SELECT request_digest,exit_code,result_digest FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone()
            world = con.execute("SELECT outcome FROM world_effect_verifications WHERE invocation_id=?", (invocation_id,)).fetchone()
            reentry = con.execute("SELECT result_digest,task_id,turn_id,causal_id,generation FROM result_reentries WHERE invocation_id=?", (invocation_id,)).fetchone()
            if adm is None or adm["decision"] != AdmissionDecision.ALLOW.value:
                reasons.append("ADMISSION_NOT_ALLOW")
            if enf is None or int(enf["dispatch_permitted"]) != 1:
                reasons.append("ENFORCEMENT_NOT_ALLOW")
            elif enf["request_digest"] != req["request_digest"]:
                reasons.append("ENFORCEMENT_REQUEST_MISMATCH")
            if req["pending_state"] != PendingEffectState.SUBMITTED.value:
                reasons.append("NOT_SUBMITTED")
            if exe is None:
                reasons.append("MISSING_EXECUTION_RECEIPT")
            else:
                if exe["request_digest"] != req["request_digest"]:
                    reasons.append("EXECUTION_REQUEST_MISMATCH")
                if int(exe["exit_code"]) != 0:
                    reasons.append("EXECUTION_FAILED")
            if world is None:
                reasons.append("MISSING_WORLD_VERIFICATION")
            elif world["outcome"] != WorldOutcome.SUCCEEDED.value:
                reasons.append(f"WORLD_{world['outcome']}")
            if reentry is None:
                reasons.append("MISSING_RESULT_REENTRY")
            else:
                if exe is not None and reentry["result_digest"] != exe["result_digest"]:
                    reasons.append("REENTRY_RESULT_MISMATCH")
                if reentry["task_id"] != req["task_id"] or reentry["turn_id"] != req["turn_id"] or reentry["causal_id"] != req["causal_id"] or int(reentry["generation"]) != int(req["generation"]):
                    reasons.append("REENTRY_LINEAGE_MISMATCH")
            return CompletionStatus(not reasons, tuple(reasons))
        finally:
            con.close()

    def issue_completion_evidence(self, invocation_id: str, *, now_ts: float | None = None) -> str:
        """Validate bound receipts and mint completion in one writer transaction."""
        ts = time.time() if now_ts is None else float(now_ts)
        con = self._con()
        try:
            # Completion is a state transition. Acquire the writer snapshot before the
            # first bound-receipt read so validation and mint cannot be interleaved.
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            reasons: list[str] = []
            adm = con.execute(
                "SELECT decision FROM admission_decisions WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            enf = con.execute(
                "SELECT decision,request_digest,dispatch_permitted,boundary_id FROM enforcement_receipts WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            exe = con.execute(
                "SELECT request_digest,executable_id,environment_id,exit_code,result_digest FROM execution_receipts WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            world = con.execute(
                "SELECT outcome,evidence_digest FROM world_effect_verifications WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            reentry = con.execute(
                "SELECT result_digest,task_id,turn_id,causal_id,generation FROM result_reentries WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()

            if adm is None or adm["decision"] != AdmissionDecision.ALLOW.value:
                reasons.append("ADMISSION_NOT_ALLOW")
            if enf is None or int(enf["dispatch_permitted"]) != 1:
                reasons.append("ENFORCEMENT_NOT_ALLOW")
            elif enf["request_digest"] != req["request_digest"]:
                reasons.append("ENFORCEMENT_REQUEST_MISMATCH")
            if req["pending_state"] != PendingEffectState.SUBMITTED.value:
                reasons.append("NOT_SUBMITTED")
            if exe is None:
                reasons.append("MISSING_EXECUTION_RECEIPT")
            else:
                if exe["request_digest"] != req["request_digest"]:
                    reasons.append("EXECUTION_REQUEST_MISMATCH")
                if int(exe["exit_code"]) != 0:
                    reasons.append("EXECUTION_FAILED")
            if world is None:
                reasons.append("MISSING_WORLD_VERIFICATION")
            elif world["outcome"] != WorldOutcome.SUCCEEDED.value:
                reasons.append(f"WORLD_{world['outcome']}")
            if reentry is None:
                reasons.append("MISSING_RESULT_REENTRY")
            else:
                if exe is not None and reentry["result_digest"] != exe["result_digest"]:
                    reasons.append("REENTRY_RESULT_MISMATCH")
                if reentry["task_id"] != req["task_id"] or reentry["turn_id"] != req["turn_id"] or reentry["causal_id"] != req["causal_id"] or int(reentry["generation"]) != int(req["generation"]):
                    reasons.append("REENTRY_LINEAGE_MISMATCH")
            if reasons:
                raise EffectLifecycleError("COMPLETION_GATE_OPEN:" + ",".join(reasons))

            source_binding = con.execute(
                "SELECT expected_source_digest FROM completion_v2_source_bindings WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()
            execution_v2 = con.execute(
                "SELECT source_digest,duplicate_state,status FROM execution_v2_metadata WHERE invocation_id=?",
                (invocation_id,),
            ).fetchone()

            expected_source = "" if source_binding is None else str(source_binding["expected_source_digest"])
            execution_source = "" if execution_v2 is None else str(execution_v2["source_digest"])
            duplicate_state = "UNKNOWN" if execution_v2 is None else str(execution_v2["duplicate_state"])
            execution_status = "UNKNOWN" if execution_v2 is None else str(execution_v2["status"])

            expected = V2ExpectedInvocation(
                invocation_id=invocation_id,
                request_digest=str(req["request_digest"]),
                task_id=str(req["task_id"]),
                turn_id=str(req["turn_id"]),
                causal_id=str(req["causal_id"]),
                generation=int(req["generation"]),
                source_digest=expected_source,
            )
            decision = verify_completion_v2(
                expected,
                admission=V2AdmissionReceipt(
                    V2_ADMISSION_SCHEMA,
                    invocation_id,
                    str(req["request_digest"]),
                    int(req["generation"]),
                    str(adm["decision"]),
                ),
                enforcement=V2EnforcementReceipt(
                    V2_ENFORCEMENT_SCHEMA,
                    invocation_id,
                    str(enf["request_digest"]),
                    int(req["generation"]),
                    str(enf["decision"]),
                    bool(enf["dispatch_permitted"]),
                    str(enf["boundary_id"]),
                ),
                execution=V2ExecutionReceipt(
                    V2_EXECUTION_SCHEMA,
                    invocation_id,
                    str(exe["request_digest"]),
                    int(req["generation"]),
                    execution_source,
                    str(exe["executable_id"]),
                    str(exe["environment_id"]),
                    execution_status,
                    int(exe["exit_code"]),
                    str(exe["result_digest"]),
                    duplicate_state,
                ),
                world=V2WorldVerificationReceipt(
                    V2_WORLD_SCHEMA,
                    invocation_id,
                    int(req["generation"]),
                    str(exe["result_digest"]),
                    str(world["outcome"]),
                    None if world["evidence_digest"] is None else str(world["evidence_digest"]),
                ),
                reentry=V2ResultReentryReceipt(
                    V2_REENTRY_SCHEMA,
                    invocation_id,
                    int(reentry["generation"]),
                    str(reentry["result_digest"]),
                    str(reentry["task_id"]),
                    str(reentry["turn_id"]),
                    str(reentry["causal_id"]),
                ),
                require_test_receipt=False,
                require_world_evidence=True,
            )
            if not decision.closable or not decision.validation_digest:
                raise EffectLifecycleError("COMPLETION_V2_GATE_OPEN:" + ",".join(decision.reasons))

            receipt_digest = str(decision.validation_digest)
            con.execute(
                "INSERT INTO completion_evidence VALUES(?,?,?,?)",
                (invocation_id, V2_COMPLETION_EVIDENCE_CLASS, receipt_digest, ts),
            )
            self._event(
                con,
                invocation_id,
                "COMPLETION_EVIDENCE_ISSUED",
                {
                    "receipt_digest": receipt_digest,
                    "validator_schema": decision.schema,
                    "evidence_class": V2_COMPLETION_EVIDENCE_CLASS,
                },
                ts,
            )
            con.execute("COMMIT")
            return receipt_digest
        except sqlite3.IntegrityError as exc:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise EffectLifecycleError("COMPLETION_EVIDENCE_ALREADY_FINAL") from exc
        except Exception:
            try:
                con.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
        finally:
            con.close()

    def snapshot(self, invocation_id: str) -> dict[str, Any]:
        con = self._con()
        try:
            req = dict(self._require_request(con, invocation_id))
            out: dict[str, Any] = {"request": req}
            for table, key in (
                ("admission_decisions", "admission"),
                ("enforcement_receipts", "enforcement"),
                ("execution_receipts", "execution"),
                ("completion_v2_source_bindings", "completion_v2_source"),
                ("execution_v2_metadata", "execution_v2"),
                ("world_effect_verifications", "world"),
                ("result_reentries", "reentry"),
                ("completion_evidence", "completion"),
            ):
                row = con.execute(f"SELECT * FROM {table} WHERE invocation_id=?", (invocation_id,)).fetchone()
                out[key] = None if row is None else dict(row)
            return out
        finally:
            con.close()

    @staticmethod
    def _require_request(con: sqlite3.Connection, invocation_id: str) -> sqlite3.Row:
        row = con.execute("SELECT * FROM effect_requests WHERE invocation_id=?", (invocation_id,)).fetchone()
        if row is None:
            raise EffectLifecycleError(f"UNKNOWN_INVOCATION:{invocation_id}")
        return row
