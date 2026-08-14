from __future__ import annotations

"""FRANK Database Pulse execution plane V6 research candidate.

V6 is deliberately narrower than semantic Runtime V5:

* StateLedger remains the only semantic/provenance authority and its event table is the only
  authoritative semantic change stream.
* Pulse bookkeeping does NOT write ``pulse:*`` rows or DATABASE_PULSE events into StateLedger.
* A separate physical execution plane stores only Pulse cursor/state/receipts/checkpoints.
* Source progress advances only across whole StateLedger events.  ``source_epoch`` and
  ``source_semantic_state_hash`` are always the boundary of the last fully consumed event.
* Candidate ranking reuses the current-main two-phase AdaptiveAuthoritativeRankPathV5.  Read
  Pulses never CREATE/DROP the expression index; physical maintenance remains a separately
  receipted CAS operation.
* Every selected focus row is verified at the causal use boundary by AuthShadowFocusGuard.
* Model output is context-only receipt data.  There is no tool/effect API.

The candidate exists to falsify the remaining semantic self-churn in current semantic Pulse
Runtime V5 while preserving its newer rank-lifecycle and integrity work.  It is not a promoted
Harness component and makes no universal database-superiority claim.
"""

from dataclasses import asdict, dataclass
import json
import sqlite3
from typing import Any, Callable, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.runtime.auth_shadow_focus_guard import AuthShadowFocusGuard
from research_entity.runtime.database_pulse_rank_path_v5 import (
    AdaptiveAuthoritativeRankPathV5,
    RankLifecyclePlan,
    RankMaintenanceReceipt,
)
from research_entity.runtime.database_pulse_runtime_v4 import PulseRankPolicyV4
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics


IMPLEMENTATION_ID = "database_pulse_execution_plane_v6_direct_stateledger_events"
MAX_MODEL_OUTPUT_BYTES = 65536
REENTRY_MODES = {
    "TRUTHFUL",
    "NO_REENTRY",
    "SHUFFLED_CONTROL",
    "PROVENANCE_BROKEN_CONTROL",
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS pulse_execution_state_v6(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  entity_id TEXT NOT NULL,
  lineage_id TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PULSING','PAUSED','STOPPED','QUARANTINED')),
  pulse_count INTEGER NOT NULL CHECK(pulse_count>=0),
  source_event_count INTEGER NOT NULL CHECK(source_event_count>=0),
  last_source_event_seq INTEGER NOT NULL CHECK(last_source_event_seq>=0),
  source_epoch INTEGER NOT NULL CHECK(source_epoch>=0),
  source_semantic_state_hash TEXT NOT NULL,
  last_focus_json TEXT NOT NULL,
  last_assembly_hash TEXT,
  state_hash TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pulse_execution_receipts_v6(
  invocation_id TEXT PRIMARY KEY,
  pulse_index INTEGER NOT NULL UNIQUE CHECK(pulse_index>0),
  mode TEXT NOT NULL CHECK(mode IN ('COGNITIVE','CATCH_UP')),
  spec_hash TEXT NOT NULL,
  pre_state_hash TEXT NOT NULL,
  post_state_hash TEXT NOT NULL,
  basis_epoch INTEGER NOT NULL,
  basis_semantic_state_hash TEXT NOT NULL,
  source_event_seq_before INTEGER NOT NULL,
  source_event_seq_after INTEGER NOT NULL,
  source_epoch_after INTEGER NOT NULL,
  source_semantic_state_hash_after TEXT NOT NULL,
  source_event_count INTEGER NOT NULL,
  backlog_events_after INTEGER NOT NULL,
  focus_json TEXT NOT NULL,
  candidate_json TEXT NOT NULL,
  assembly_hash TEXT NOT NULL,
  selection_hash TEXT,
  physical_rank_mode TEXT NOT NULL,
  integrity_mode TEXT NOT NULL,
  focus_guard_passed INTEGER NOT NULL CHECK(focus_guard_passed IN (0,1)),
  conflicts_present INTEGER NOT NULL,
  unknown_present INTEGER NOT NULL,
  reentry_count INTEGER NOT NULL,
  memory_update_observed_count INTEGER NOT NULL,
  model_candidate_json TEXT,
  model_candidate_hash TEXT,
  model_call_count INTEGER NOT NULL,
  tool_call_count INTEGER NOT NULL,
  effect_count INTEGER NOT NULL,
  receipt_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pulse_execution_receipts_v6_index
ON pulse_execution_receipts_v6(pulse_index DESC);

CREATE TABLE IF NOT EXISTS pulse_execution_checkpoints_v6(
  checkpoint_id TEXT PRIMARY KEY,
  pulse_index INTEGER NOT NULL CHECK(pulse_index>=0),
  snapshot_json TEXT NOT NULL,
  state_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pulse_execution_checkpoints_v6_latest
ON pulse_execution_checkpoints_v6(pulse_index DESC);
"""


class PulseV6Error(RuntimeError):
    pass


class PulseV6IntegrityError(PulseV6Error):
    pass


class PulseV6ControlError(PulseV6Error):
    pass


class PulseV6Backlog(PulseV6Error):
    pass


class PulseV6InvocationConflict(PulseV6Error):
    pass


class PulseV6ExecutionStateStale(PulseV6Error):
    pass


@dataclass(frozen=True)
class PulseSpecV6:
    invocation_id: str
    basis_epoch: int
    source_domains: tuple[str, ...] = (
        "self", "world", "memory", "goal", "task", "semantic", "capability", "percept"
    )
    max_candidates: int = 128
    max_focus: int = 12
    max_source_events: int = 32
    reentry_mode: str = "TRUTHFUL"
    full_audit_every: int = 32


@dataclass(frozen=True)
class PulseReceiptV6:
    status: str
    invocation_id: str
    pulse_index: int
    mode: str
    basis_epoch: int
    semantic_state_hash: str
    source_event_count: int
    source_event_seq_before: int
    source_event_seq_after: int
    source_epoch_after: int
    source_semantic_state_hash_after: str
    backlog_events_after: int
    focus_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    assembly_hash: str
    selection_hash: str | None
    physical_rank_mode: str
    integrity_mode: str
    focus_guard_passed: bool
    conflicts_present: int
    unknown_present: int
    reentry_count: int
    memory_update_observed_count: int
    model_call_count: int
    tool_call_count: int
    effect_count: int
    receipt_hash: str
    authority: str = "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


@dataclass(frozen=True)
class PulseRankMaintenanceV6:
    actor: str
    policy_provenance_ref: str
    plan: RankLifecyclePlan
    receipt: RankMaintenanceReceipt
    authority: str = "PHYSICAL_MAINTENANCE_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY"


def _decode_json_object(text: str, *, label: str) -> dict[str, Any]:
    try:
        value = json.loads(text)
    except Exception as exc:
        raise PulseV6IntegrityError(f"unreadable {label}") from exc
    if not isinstance(value, dict):
        raise PulseV6IntegrityError(f"{label} must be an object")
    return value


class DatabasePulseExecutionPlaneV6:
    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64
    MAX_SOURCE_EVENTS_HARD = 65536

    def __init__(
        self,
        ledger: StateLedger,
        *,
        entity_id: str = "dr-unterweger-frank-personal-entity",
        lineage_id: str = "frank-v0.1-database-pulse-v6",
        rank_policy_provider: Callable[[PulseSpecV6], PulseRankPolicyV4] | None = None,
        now: str = "V6_INIT",
    ):
        self.ledger = ledger
        self.con = ledger.conn
        self.con.executescript(SCHEMA)
        self.con.commit()
        self.rank_path = AdaptiveAuthoritativeRankPathV5(ledger)
        self.rank_policy_provider = rank_policy_provider
        self.focus_guard = AuthShadowFocusGuard(ledger)
        self._bootstrap(entity_id=entity_id, lineage_id=lineage_id, now=now)

    # --------------------------------------------------------------- canonical execution state
    @staticmethod
    def _state_material(row: Any) -> dict[str, Any]:
        return {
            "entity_id": str(row["entity_id"]),
            "lineage_id": str(row["lineage_id"]),
            "status": str(row["status"]),
            "pulse_count": int(row["pulse_count"]),
            "source_event_count": int(row["source_event_count"]),
            "last_source_event_seq": int(row["last_source_event_seq"]),
            "source_epoch": int(row["source_epoch"]),
            "source_semantic_state_hash": str(row["source_semantic_state_hash"]),
            "last_focus_json": str(row["last_focus_json"]),
            "last_assembly_hash": row["last_assembly_hash"],
        }

    @classmethod
    def _state_hash(cls, row: Any) -> str:
        return h(cls._state_material(row))

    def _state(self):
        row = self.con.execute(
            "SELECT * FROM pulse_execution_state_v6 WHERE singleton_id=1"
        ).fetchone()
        if row is None:
            raise PulseV6IntegrityError("V6 execution state missing")
        return row

    def _max_event_seq(self) -> int:
        return int(self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def _event_at_seq(self, seq: int):
        if seq <= 0:
            return None
        return self.con.execute(
            "SELECT seq,epoch,event_id,ops_json,semantic_state_hash FROM events WHERE seq=?", (seq,)
        ).fetchone()

    def _verify_state(self, row=None):
        row = row or self._state()
        actual = self._state_hash(row)
        if actual != str(row["state_hash"]):
            raise PulseV6IntegrityError("V6 execution state hash mismatch")
        cursor = int(row["last_source_event_seq"])
        max_seq = self._max_event_seq()
        if cursor > max_seq:
            raise PulseV6IntegrityError("V6 source cursor is ahead of StateLedger")
        if int(row["source_epoch"]) > self.ledger.epoch:
            raise PulseV6IntegrityError("V6 source epoch is ahead of StateLedger")
        if cursor > 0:
            event = self._event_at_seq(cursor)
            if event is None:
                raise PulseV6IntegrityError("V6 source cursor event is missing")
            if int(event["epoch"]) != int(row["source_epoch"]):
                raise PulseV6IntegrityError("V6 source epoch does not match cursor event")
            if str(event["semantic_state_hash"]) != str(row["source_semantic_state_hash"]):
                raise PulseV6IntegrityError("V6 source semantic hash does not match cursor event")
        if cursor == max_seq:
            if int(row["source_epoch"]) != self.ledger.epoch:
                raise PulseV6IntegrityError("V6 head cursor does not match ledger epoch")
            if str(row["source_semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise PulseV6IntegrityError("V6 head cursor does not match ledger semantic hash")
        try:
            focus = json.loads(str(row["last_focus_json"]))
        except Exception as exc:
            raise PulseV6IntegrityError("V6 last_focus_json unreadable") from exc
        if not isinstance(focus, list) or any(not isinstance(x, str) for x in focus):
            raise PulseV6IntegrityError("V6 last_focus_json invalid")
        return row

    def _bootstrap(self, *, entity_id: str, lineage_id: str, now: str) -> None:
        if self.con.execute(
            "SELECT 1 FROM pulse_execution_state_v6 WHERE singleton_id=1"
        ).fetchone() is not None:
            self._verify_state()
            return
        self._full_integrity()
        max_seq = self._max_event_seq()
        material = {
            "entity_id": entity_id,
            "lineage_id": lineage_id,
            "status": "PULSING",
            "pulse_count": 0,
            "source_event_count": 0,
            "last_source_event_seq": max_seq,
            "source_epoch": self.ledger.epoch,
            "source_semantic_state_hash": self.ledger.semantic_state_hash,
            "last_focus_json": "[]",
            "last_assembly_hash": None,
        }
        state_hash = h(material)
        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self.con.execute(
                "SELECT 1 FROM pulse_execution_state_v6 WHERE singleton_id=1"
            ).fetchone() is None:
                self.con.execute(
                    """INSERT INTO pulse_execution_state_v6(
                       singleton_id,entity_id,lineage_id,status,pulse_count,source_event_count,
                       last_source_event_seq,source_epoch,source_semantic_state_hash,last_focus_json,
                       last_assembly_hash,state_hash,updated_at
                    ) VALUES(1,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        entity_id, lineage_id, "PULSING", 0, 0, max_seq, self.ledger.epoch,
                        self.ledger.semantic_state_hash, "[]", None, state_hash, now,
                    ),
                )
                self.con.execute(
                    """INSERT INTO pulse_execution_checkpoints_v6(
                       checkpoint_id,pulse_index,snapshot_json,state_hash,created_at
                    ) VALUES(?,?,?,?,?)""",
                    ("bootstrap", 0, cjson(material), state_hash, now),
                )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        self._verify_state()

    # --------------------------------------------------------------------- integrity / control
    def _full_integrity(self) -> tuple[str, str]:
        try:
            semantic, trace = self.ledger._roots()
        except Exception as exc:
            raise PulseV6IntegrityError(f"cannot recompute StateLedger roots: {exc}") from exc
        if semantic != self.ledger.semantic_state_hash:
            raise PulseV6IntegrityError("StateLedger semantic root mismatch")
        if trace != self.ledger.trace_root_hash:
            raise PulseV6IntegrityError("StateLedger trace root mismatch")
        return semantic, trace

    def _scheduler_enabled(self) -> bool:
        row = self.ledger.get("pulse_control", "scheduler")
        if row is None:
            raise PulseV6ControlError("pulse scheduler has no explicit persisted state")
        if row["status"] != "CURRENT" or row["epistemic"] != "KNOWN":
            raise PulseV6ControlError("pulse scheduler is not KNOWN/CURRENT")
        value = row.get("value")
        if not isinstance(value, dict) or not isinstance(value.get("enabled"), bool):
            raise PulseV6ControlError("pulse scheduler is malformed")
        return bool(value["enabled"])

    @staticmethod
    def sqlite_wal_multiwriter_safety() -> dict[str, Any]:
        v = tuple(int(x) for x in sqlite3.sqlite_version_info)
        safe = (
            v >= (3, 51, 3)
            or (v[:2] == (3, 50) and v >= (3, 50, 7))
            or (v[:2] == (3, 44) and v >= (3, 44, 6))
        )
        return {
            "sqlite_version": sqlite3.sqlite_version,
            "wal_reset_bug_fixed_family": bool(safe),
            "required_for_multi_connection_wal_release_gate": True,
        }

    # --------------------------------------------------------------------------- source stream
    def pending_event_count(self) -> int:
        state = self._verify_state()
        cursor = int(state["last_source_event_seq"])
        return int(self.con.execute("SELECT COUNT(*) FROM events WHERE seq>?", (cursor,)).fetchone()[0])

    def _pending_events(self, *, cursor: int, limit: int):
        return list(self.con.execute(
            """SELECT seq,epoch,event_id,ops_json,semantic_state_hash
               FROM events WHERE seq>? ORDER BY seq LIMIT ?""",
            (cursor, limit),
        ))

    @staticmethod
    def _changed_refs(events: Iterable[Any]) -> tuple[list[str], int]:
        refs: list[str] = []
        seen: set[str] = set()
        memory: set[str] = set()
        for event in events:
            try:
                ops = json.loads(str(event["ops_json"]))
            except Exception as exc:
                raise PulseV6IntegrityError(
                    f"unreadable StateLedger ops at seq={event['seq']}"
                ) from exc
            if not isinstance(ops, list):
                raise PulseV6IntegrityError("StateLedger ops_json is not a list")
            for op in ops:
                if not isinstance(op, dict):
                    raise PulseV6IntegrityError("StateLedger op is not an object")
                domain = str(op.get("domain") or "")
                key = str(op.get("key") or "")
                if not domain or not key or domain in {"pulse", "pulse_control"}:
                    continue
                ref = f"{domain}:{key}"
                if ref not in seen:
                    refs.append(ref); seen.add(ref)
                if domain == "memory":
                    memory.add(ref)
        return refs, len(memory)

    # ----------------------------------------------------------------------------- rank policy
    @staticmethod
    def _safe_unmeasured_policy() -> PulseRankPolicyV4:
        return PulseRankPolicyV4(
            economics_without_horizon=CompileEconomics(
                build_cost_us=0.0,
                online_query_us=0.0,
                compiled_query_us=0.0,
                online_quality=1.0,
                compiled_quality=1.0,
                expected_reads_before_invalidation=0.0,
                safety_factor=1.2,
            ),
            pulse_history=(),
            provenance_ref="UNMEASURED_FAIL_ONLINE",
        )

    def _policy(self, spec: PulseSpecV6) -> PulseRankPolicyV4:
        policy = self.rank_policy_provider(spec) if self.rank_policy_provider else self._safe_unmeasured_policy()
        if not isinstance(policy, PulseRankPolicyV4):
            raise TypeError("rank_policy_provider must return PulseRankPolicyV4")
        policy.validate()
        return policy

    def maintain_rank_index(
        self,
        *,
        basis_epoch: int,
        policy: PulseRankPolicyV4,
        actor: str,
    ) -> PulseRankMaintenanceV6:
        if not isinstance(actor, str) or not actor.strip():
            raise ValueError("maintenance actor required")
        policy.validate()
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"rank maintenance basis {basis_epoch}!={self.ledger.epoch}")
        before = (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
        plan = self.rank_path.plan_lifecycle(
            basis_epoch=basis_epoch,
            economics_without_horizon=policy.economics_without_horizon,
            pulse_history=policy.pulse_history,
        )
        receipt = self.rank_path.apply_maintenance(plan)
        after = (self.ledger.epoch, self.ledger.semantic_state_hash, self.ledger.trace_root_hash)
        if before != after:
            raise PulseV6IntegrityError("rank physical maintenance changed semantic StateLedger roots")
        return PulseRankMaintenanceV6(
            actor=actor,
            policy_provenance_ref=policy.provenance_ref,
            plan=plan,
            receipt=receipt,
        )

    # ---------------------------------------------------------------------- receipts/idempotency
    @staticmethod
    def _spec_hash(spec: PulseSpecV6) -> str:
        return h(asdict(spec))

    def _receipt_row(self, invocation_id: str):
        return self.con.execute(
            "SELECT * FROM pulse_execution_receipts_v6 WHERE invocation_id=?", (invocation_id,)
        ).fetchone()

    @staticmethod
    def _receipt_from_row(row, *, status: str) -> PulseReceiptV6:
        return PulseReceiptV6(
            status=status,
            invocation_id=str(row["invocation_id"]),
            pulse_index=int(row["pulse_index"]),
            mode=str(row["mode"]),
            basis_epoch=int(row["basis_epoch"]),
            semantic_state_hash=str(row["basis_semantic_state_hash"]),
            source_event_count=int(row["source_event_count"]),
            source_event_seq_before=int(row["source_event_seq_before"]),
            source_event_seq_after=int(row["source_event_seq_after"]),
            source_epoch_after=int(row["source_epoch_after"]),
            source_semantic_state_hash_after=str(row["source_semantic_state_hash_after"]),
            backlog_events_after=int(row["backlog_events_after"]),
            focus_refs=tuple(json.loads(str(row["focus_json"]))),
            candidate_refs=tuple(json.loads(str(row["candidate_json"]))),
            assembly_hash=str(row["assembly_hash"]),
            selection_hash=row["selection_hash"],
            physical_rank_mode=str(row["physical_rank_mode"]),
            integrity_mode=str(row["integrity_mode"]),
            focus_guard_passed=bool(row["focus_guard_passed"]),
            conflicts_present=int(row["conflicts_present"]),
            unknown_present=int(row["unknown_present"]),
            reentry_count=int(row["reentry_count"]),
            memory_update_observed_count=int(row["memory_update_observed_count"]),
            model_call_count=int(row["model_call_count"]),
            tool_call_count=int(row["tool_call_count"]),
            effect_count=int(row["effect_count"]),
            receipt_hash=str(row["receipt_hash"]),
        )

    def _existing(self, invocation_id: str, spec_hash: str) -> PulseReceiptV6 | None:
        row = self._receipt_row(invocation_id)
        if row is None:
            return None
        if str(row["spec_hash"]) != spec_hash:
            raise PulseV6InvocationConflict("invocation_id reused with different V6 spec")
        body = {
            k: row[k]
            for k in row.keys()
            if k not in {"receipt_hash", "created_at"}
        }
        if h(body) != str(row["receipt_hash"]):
            raise PulseV6IntegrityError("persisted V6 receipt hash mismatch")
        return self._receipt_from_row(row, status="ALREADY_COMMITTED")

    def _commit(
        self,
        *,
        invocation_id: str,
        spec_hash: str,
        mode: str,
        pre_state_hash: str,
        basis_epoch: int,
        basis_semantic_state_hash: str,
        observed_head_seq: int,
        source_seq_before: int,
        source_seq_after: int,
        source_epoch_after: int,
        source_hash_after: str,
        source_event_count: int,
        backlog_after: int,
        focus_refs: tuple[str, ...],
        candidate_refs: tuple[str, ...],
        assembly_hash: str,
        selection_hash: str | None,
        physical_rank_mode: str,
        integrity_mode: str,
        focus_guard_passed: bool,
        conflicts_present: int,
        unknown_present: int,
        reentry_count: int,
        memory_update_observed_count: int,
        model_candidate: Any,
        model_candidate_hash: str | None,
        model_call_count: int,
        now: str,
    ) -> PulseReceiptV6:
        self.con.execute("BEGIN IMMEDIATE")
        try:
            already = self._receipt_row(invocation_id)
            if already is not None:
                self.con.rollback()
                if str(already["spec_hash"]) != spec_hash:
                    raise PulseV6InvocationConflict("concurrent invocation_id spec mismatch")
                return self._receipt_from_row(already, status="ALREADY_COMMITTED")

            if self.ledger.epoch != basis_epoch:
                raise StaleEpoch(f"V6 commit basis {basis_epoch}!={self.ledger.epoch}")
            if self.ledger.semantic_state_hash != basis_semantic_state_hash:
                raise StaleEpoch("V6 semantic root changed before execution commit")
            if self._max_event_seq() != observed_head_seq:
                raise StaleEpoch("V6 StateLedger event head changed before execution commit")

            current = self._verify_state()
            if str(current["state_hash"]) != pre_state_hash:
                raise PulseV6ExecutionStateStale("V6 execution state advanced concurrently")

            pulse_index = int(current["pulse_count"]) + 1
            state_material = self._state_material(current)
            state_material.update({
                "pulse_count": pulse_index,
                "source_event_count": int(current["source_event_count"]) + source_event_count,
                "last_source_event_seq": source_seq_after,
                "source_epoch": source_epoch_after,
                "source_semantic_state_hash": source_hash_after,
                "last_focus_json": cjson(list(focus_refs)),
                "last_assembly_hash": assembly_hash,
            })
            post_state_hash = h(state_material)

            model_json = None if model_candidate is None else cjson(model_candidate)
            receipt_body = {
                "invocation_id": invocation_id,
                "pulse_index": pulse_index,
                "mode": mode,
                "spec_hash": spec_hash,
                "pre_state_hash": pre_state_hash,
                "post_state_hash": post_state_hash,
                "basis_epoch": basis_epoch,
                "basis_semantic_state_hash": basis_semantic_state_hash,
                "source_event_seq_before": source_seq_before,
                "source_event_seq_after": source_seq_after,
                "source_epoch_after": source_epoch_after,
                "source_semantic_state_hash_after": source_hash_after,
                "source_event_count": source_event_count,
                "backlog_events_after": backlog_after,
                "focus_json": cjson(list(focus_refs)),
                "candidate_json": cjson(list(candidate_refs)),
                "assembly_hash": assembly_hash,
                "selection_hash": selection_hash,
                "physical_rank_mode": physical_rank_mode,
                "integrity_mode": integrity_mode,
                "focus_guard_passed": int(focus_guard_passed),
                "conflicts_present": conflicts_present,
                "unknown_present": unknown_present,
                "reentry_count": reentry_count,
                "memory_update_observed_count": memory_update_observed_count,
                "model_candidate_json": model_json,
                "model_candidate_hash": model_candidate_hash,
                "model_call_count": model_call_count,
                "tool_call_count": 0,
                "effect_count": 0,
            }
            receipt_hash = h(receipt_body)

            self.con.execute(
                """UPDATE pulse_execution_state_v6 SET
                   pulse_count=?,source_event_count=?,last_source_event_seq=?,source_epoch=?,
                   source_semantic_state_hash=?,last_focus_json=?,last_assembly_hash=?,state_hash=?,
                   updated_at=? WHERE singleton_id=1""",
                (
                    state_material["pulse_count"], state_material["source_event_count"],
                    source_seq_after, source_epoch_after, source_hash_after,
                    state_material["last_focus_json"], assembly_hash, post_state_hash, now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_receipts_v6(
                   invocation_id,pulse_index,mode,spec_hash,pre_state_hash,post_state_hash,
                   basis_epoch,basis_semantic_state_hash,source_event_seq_before,source_event_seq_after,
                   source_epoch_after,source_semantic_state_hash_after,source_event_count,
                   backlog_events_after,focus_json,candidate_json,assembly_hash,selection_hash,
                   physical_rank_mode,integrity_mode,focus_guard_passed,conflicts_present,
                   unknown_present,reentry_count,memory_update_observed_count,model_candidate_json,
                   model_candidate_hash,model_call_count,tool_call_count,effect_count,receipt_hash,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    invocation_id, pulse_index, mode, spec_hash, pre_state_hash, post_state_hash,
                    basis_epoch, basis_semantic_state_hash, source_seq_before, source_seq_after,
                    source_epoch_after, source_hash_after, source_event_count, backlog_after,
                    receipt_body["focus_json"], receipt_body["candidate_json"], assembly_hash,
                    selection_hash, physical_rank_mode, integrity_mode, int(focus_guard_passed),
                    conflicts_present, unknown_present, reentry_count, memory_update_observed_count,
                    model_json, model_candidate_hash, model_call_count, 0, 0, receipt_hash, now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_checkpoints_v6(
                   checkpoint_id,pulse_index,snapshot_json,state_hash,created_at
                ) VALUES(?,?,?,?,?)""",
                (
                    f"pulse-v6:{pulse_index}:{post_state_hash[:16]}", pulse_index,
                    cjson(state_material), post_state_hash, now,
                ),
            )
            self.con.commit()
            row = self._receipt_row(invocation_id)
            if row is None:
                raise PulseV6IntegrityError("V6 receipt disappeared after commit")
            return self._receipt_from_row(row, status="COMMITTED")
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise

    # -------------------------------------------------------------------------------- cognition
    def run_pulse(
        self,
        spec: PulseSpecV6,
        *,
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        now: str = "V6_PULSE",
    ) -> PulseReceiptV6:
        if not spec.invocation_id.strip():
            raise ValueError("invocation_id required")
        if spec.basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"V6 pulse basis {spec.basis_epoch}!={self.ledger.epoch}")
        if not spec.source_domains or any(d in {"pulse", "pulse_control"} for d in spec.source_domains):
            raise ValueError("source_domains must be explicit and exclude Pulse output/control")
        if not 1 <= spec.max_candidates <= self.MAX_CANDIDATES_HARD:
            raise ValueError("max_candidates out of bounds")
        if not 1 <= spec.max_focus <= min(spec.max_candidates, self.MAX_FOCUS_HARD):
            raise ValueError("max_focus out of bounds")
        if not 1 <= spec.max_source_events <= self.MAX_SOURCE_EVENTS_HARD:
            raise ValueError("max_source_events out of bounds")
        if not 1 <= spec.full_audit_every <= 1000000:
            raise ValueError("full_audit_every out of bounds")
        mode = spec.reentry_mode.upper()
        if mode not in REENTRY_MODES:
            raise ValueError(f"unsupported reentry mode: {spec.reentry_mode}")

        spec_hash = self._spec_hash(spec)
        existing = self._existing(spec.invocation_id, spec_hash)
        if existing is not None:
            return existing
        if not self._scheduler_enabled():
            raise PulseV6ControlError("pulse scheduler is paused")

        state = self._verify_state()
        if str(state["status"]) != "PULSING":
            raise PulseV6ControlError(f"V6 execution state={state['status']}")
        pre_state_hash = str(state["state_hash"])
        cursor = int(state["last_source_event_seq"])
        observed_head_seq = self._max_event_seq()
        pending = int(self.con.execute(
            "SELECT COUNT(*) FROM events WHERE seq>?", (cursor,)
        ).fetchone()[0])
        if pending > spec.max_source_events:
            raise PulseV6Backlog(
                f"{pending} source events exceed cognitive budget {spec.max_source_events}; catch up first"
            )
        events = self._pending_events(cursor=cursor, limit=spec.max_source_events)
        if len(events) != pending:
            raise PulseV6IntegrityError("V6 pending-event census changed during read")

        integrity_mode = "FOCUS_USE_BOUNDARY_ONLY"
        if pending > 0 or int(state["pulse_count"]) == 0 or (
            (int(state["pulse_count"]) + 1) % spec.full_audit_every == 0
        ):
            self._full_integrity()
            integrity_mode = "FULL_CANONICAL_PLUS_FOCUS"

        previous_focus = tuple(json.loads(str(state["last_focus_json"])))
        policy = self._policy(spec)
        semantic_before = self.ledger.semantic_state_hash
        epoch_before = self.ledger.epoch
        index_before = self.rank_path.index_exists()
        selection = self.rank_path.select(
            source_domains=tuple(dict.fromkeys(spec.source_domains)),
            basis_epoch=spec.basis_epoch,
            max_candidates=spec.max_candidates,
            max_focus=spec.max_focus,
            economics_without_horizon=policy.economics_without_horizon,
            pulse_history=policy.pulse_history,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
        )
        if self.rank_path.index_exists() != index_before:
            raise PulseV6IntegrityError("V6 cognition read mutated rank index lifecycle")
        if (self.ledger.epoch, self.ledger.semantic_state_hash) != (epoch_before, semantic_before):
            raise PulseV6IntegrityError("V6 rank read mutated semantic StateLedger")

        guard = self.focus_guard.refresh_and_verify_refs(selection.focus_refs, now=now)
        if not guard.passed:
            raise PulseV6IntegrityError("V6 focus use-boundary verification failed")
        if (self.ledger.epoch, self.ledger.semantic_state_hash) != (epoch_before, semantic_before):
            raise PulseV6IntegrityError("V6 focus guard mutated semantic StateLedger")

        changed_refs, memory_updates = self._changed_refs(events)
        if events:
            last = events[-1]
            source_seq_after = int(last["seq"])
            source_epoch_after = int(last["epoch"])
            source_hash_after = str(last["semantic_state_hash"])
            if source_seq_after != observed_head_seq:
                raise PulseV6IntegrityError("V6 cognitive pulse did not consume complete observed event head")
            if source_epoch_after != self.ledger.epoch or source_hash_after != self.ledger.semantic_state_hash:
                raise PulseV6IntegrityError("V6 consumed event head is not current semantic boundary")
        else:
            source_seq_after = cursor
            source_epoch_after = int(state["source_epoch"])
            source_hash_after = str(state["source_semantic_state_hash"])
            if source_seq_after != observed_head_seq:
                raise PulseV6IntegrityError("V6 idle cursor is not current event head")

        focus_hashes: list[str] = []
        focus_context: list[dict[str, Any]] = []
        score_by_ref = dict(zip(selection.candidate_refs, selection.candidate_scores))
        for ref in selection.focus_refs:
            domain, key = ref.split(":", 1)
            row = self.ledger.get(domain, key)
            if row is None or row["epistemic"] != "KNOWN" or row["status"] != "CURRENT":
                raise PulseV6IntegrityError(f"selected ref invalid after focus guard: {ref}")
            focus_hashes.append(str(row["semantic_hash"]))
            focus_context.append({
                "ref": ref,
                "score": score_by_ref[ref],
                "source_semantic_hash": row["semantic_hash"],
                "domain_epoch": row["domain_epoch"],
                "value": row["value"],
            })

        reentry_targets: set[str] = set()
        if mode == "TRUTHFUL":
            reentry_targets = set(previous_focus) & set(selection.candidate_refs)
        elif mode == "SHUFFLED_CONTROL" and previous_focus:
            # The rank path performs the shuffled control; the observable remains lesionable.
            reentry_targets = set(previous_focus) & set(selection.candidate_refs)

        assembly_hash = h({
            "implementation": IMPLEMENTATION_ID,
            "basis_epoch": spec.basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "source_event_ids": [str(e["event_id"]) for e in events],
            "source_event_seq_before": cursor,
            "source_event_seq_after": source_seq_after,
            "changed_refs": changed_refs,
            "selection_hash": selection.selection_hash,
            "focus_refs": list(selection.focus_refs),
            "focus_source_hashes": focus_hashes,
            "focus_guard_shadow_root": guard.shadow_root_hash,
        })

        model_candidate = None
        model_candidate_hash = None
        model_call_count = 0
        if model_assistant is not None:
            model_candidate = model_assistant({
                "invocation_id": spec.invocation_id,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus_context,
                "changed_refs": changed_refs,
                "physical_rank_mode": selection.physical_read_mode,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            })
            encoded = cjson(model_candidate).encode("utf-8")
            if len(encoded) > MAX_MODEL_OUTPUT_BYTES:
                raise ValueError("model candidate exceeds V6 receipt bound")
            model_candidate_hash = h(model_candidate)
            model_call_count = 1

        return self._commit(
            invocation_id=spec.invocation_id,
            spec_hash=spec_hash,
            mode="COGNITIVE",
            pre_state_hash=pre_state_hash,
            basis_epoch=spec.basis_epoch,
            basis_semantic_state_hash=self.ledger.semantic_state_hash,
            observed_head_seq=observed_head_seq,
            source_seq_before=cursor,
            source_seq_after=source_seq_after,
            source_epoch_after=source_epoch_after,
            source_hash_after=source_hash_after,
            source_event_count=len(events),
            backlog_after=0,
            focus_refs=tuple(selection.focus_refs),
            candidate_refs=tuple(selection.candidate_refs),
            assembly_hash=assembly_hash,
            selection_hash=selection.selection_hash,
            physical_rank_mode=selection.physical_read_mode,
            integrity_mode=integrity_mode,
            focus_guard_passed=True,
            conflicts_present=selection.conflicts_present,
            unknown_present=selection.unknown_present,
            reentry_count=int(mode == "TRUTHFUL" and bool(reentry_targets)),
            memory_update_observed_count=memory_updates,
            model_candidate=model_candidate,
            model_candidate_hash=model_candidate_hash,
            model_call_count=model_call_count,
            now=now,
        )

    # --------------------------------------------------------------------------- bounded catchup
    def catch_up(
        self,
        *,
        invocation_id: str,
        basis_epoch: int,
        max_source_events: int = 32,
        now: str = "V6_CATCH_UP",
    ) -> PulseReceiptV6:
        if not invocation_id.strip():
            raise ValueError("invocation_id required")
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"V6 catch-up basis {basis_epoch}!={self.ledger.epoch}")
        if not 1 <= max_source_events <= self.MAX_SOURCE_EVENTS_HARD:
            raise ValueError("max_source_events out of bounds")
        spec_hash = h({
            "mode": "CATCH_UP", "invocation_id": invocation_id,
            "basis_epoch": basis_epoch, "max_source_events": max_source_events,
        })
        existing = self._existing(invocation_id, spec_hash)
        if existing is not None:
            return existing
        if not self._scheduler_enabled():
            raise PulseV6ControlError("pulse scheduler is paused")
        state = self._verify_state()
        if str(state["status"]) != "PULSING":
            raise PulseV6ControlError(f"V6 execution state={state['status']}")
        pre_state_hash = str(state["state_hash"])
        cursor = int(state["last_source_event_seq"])
        observed_head_seq = self._max_event_seq()
        events = self._pending_events(cursor=cursor, limit=max_source_events)
        if events:
            self._full_integrity()
            last = events[-1]
            source_seq_after = int(last["seq"])
            source_epoch_after = int(last["epoch"])
            source_hash_after = str(last["semantic_state_hash"])
            integrity_mode = "FULL_CANONICAL_CATCH_UP"
        else:
            source_seq_after = cursor
            source_epoch_after = int(state["source_epoch"])
            source_hash_after = str(state["source_semantic_state_hash"])
            integrity_mode = "EXECUTION_STATE_ONLY_IDLE_CATCH_UP"
        changed_refs, memory_updates = self._changed_refs(events)
        backlog_after = int(self.con.execute(
            "SELECT COUNT(*) FROM events WHERE seq>?", (source_seq_after,)
        ).fetchone()[0])
        assembly_hash = h({
            "implementation": IMPLEMENTATION_ID,
            "mode": "CATCH_UP",
            "basis_epoch": basis_epoch,
            "source_event_ids": [str(e["event_id"]) for e in events],
            "source_event_seq_before": cursor,
            "source_event_seq_after": source_seq_after,
            "changed_refs": changed_refs,
        })
        return self._commit(
            invocation_id=invocation_id,
            spec_hash=spec_hash,
            mode="CATCH_UP",
            pre_state_hash=pre_state_hash,
            basis_epoch=basis_epoch,
            basis_semantic_state_hash=self.ledger.semantic_state_hash,
            observed_head_seq=observed_head_seq,
            source_seq_before=cursor,
            source_seq_after=source_seq_after,
            source_epoch_after=source_epoch_after,
            source_hash_after=source_hash_after,
            source_event_count=len(events),
            backlog_after=backlog_after,
            focus_refs=(), candidate_refs=(), assembly_hash=assembly_hash,
            selection_hash=None, physical_rank_mode="NONE_CATCH_UP",
            integrity_mode=integrity_mode, focus_guard_passed=False,
            conflicts_present=0, unknown_present=0, reentry_count=0,
            memory_update_observed_count=memory_updates,
            model_candidate=None, model_candidate_hash=None, model_call_count=0,
            now=now,
        )

    # ------------------------------------------------------------------------- pause / recovery
    def set_status(self, status: str, *, now: str) -> None:
        if status not in {"PULSING", "PAUSED", "STOPPED", "QUARANTINED"}:
            raise ValueError(status)
        self.con.execute("BEGIN IMMEDIATE")
        try:
            row = self._verify_state()
            material = self._state_material(row)
            material["status"] = status
            state_hash = h(material)
            self.con.execute(
                "UPDATE pulse_execution_state_v6 SET status=?,state_hash=?,updated_at=? WHERE singleton_id=1",
                (status, state_hash, now),
            )
            self.con.commit()
        except Exception:
            self.con.rollback(); raise

    def recover_last_known_good(self, *, now: str) -> int:
        checkpoint = self.con.execute(
            """SELECT * FROM pulse_execution_checkpoints_v6
               ORDER BY pulse_index DESC LIMIT 1"""
        ).fetchone()
        if checkpoint is None:
            raise PulseV6IntegrityError("no V6 checkpoint")
        material = _decode_json_object(str(checkpoint["snapshot_json"]), label="V6 checkpoint")
        expected = h(material)
        if expected != str(checkpoint["state_hash"]):
            raise PulseV6IntegrityError("V6 checkpoint hash mismatch")
        required = {
            "entity_id","lineage_id","status","pulse_count","source_event_count",
            "last_source_event_seq","source_epoch","source_semantic_state_hash",
            "last_focus_json","last_assembly_hash",
        }
        if not required.issubset(material):
            raise PulseV6IntegrityError("V6 checkpoint missing fields")
        self.con.execute("BEGIN IMMEDIATE")
        try:
            self.con.execute(
                """UPDATE pulse_execution_state_v6 SET
                   entity_id=?,lineage_id=?,status=?,pulse_count=?,source_event_count=?,
                   last_source_event_seq=?,source_epoch=?,source_semantic_state_hash=?,
                   last_focus_json=?,last_assembly_hash=?,state_hash=?,updated_at=?
                   WHERE singleton_id=1""",
                (
                    material["entity_id"], material["lineage_id"], material["status"],
                    int(material["pulse_count"]), int(material["source_event_count"]),
                    int(material["last_source_event_seq"]), int(material["source_epoch"]),
                    material["source_semantic_state_hash"], material["last_focus_json"],
                    material.get("last_assembly_hash"), expected, now,
                ),
            )
            self.con.commit()
        except Exception:
            self.con.rollback(); raise
        self._verify_state()
        return int(material["pulse_count"])
