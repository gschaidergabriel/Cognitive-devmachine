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

SCHEMA = "FRANKENSTEIN2_EFFECT_LIFECYCLE/v1"


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
        ts = time.time() if now_ts is None else float(now_ts)
        status = self.completion_status(invocation_id)
        if not status.closable:
            raise EffectLifecycleError("COMPLETION_GATE_OPEN:" + ",".join(status.reasons))
        con = self._con()
        try:
            con.execute("BEGIN IMMEDIATE")
            req = self._require_request(con, invocation_id)
            exe = con.execute("SELECT result_digest FROM execution_receipts WHERE invocation_id=?", (invocation_id,)).fetchone()
            world = con.execute("SELECT outcome,evidence_digest FROM world_effect_verifications WHERE invocation_id=?", (invocation_id,)).fetchone()
            receipt_digest = digest_json({
                "schema": SCHEMA,
                "invocation_id": invocation_id,
                "request_digest": req["request_digest"],
                "result_digest": exe["result_digest"],
                "world_outcome": world["outcome"],
                "world_evidence_digest": world["evidence_digest"],
                "task_id": req["task_id"],
                "turn_id": req["turn_id"],
                "causal_id": req["causal_id"],
                "generation": int(req["generation"]),
            })
            con.execute("INSERT INTO completion_evidence VALUES(?,?,?,?)", (invocation_id, "VERIFIED_EFFECT_COMPLETION", receipt_digest, ts))
            self._event(con, invocation_id, "COMPLETION_EVIDENCE_ISSUED", {"receipt_digest": receipt_digest}, ts)
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
