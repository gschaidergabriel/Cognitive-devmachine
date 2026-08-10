from __future__ import annotations

"""FRANK Database Pulse V5 research candidate: direct event stream + separate execution clock.

V5 is the convergence candidate after falsifying three earlier directions:

* semantic Pulse bookkeeping in StateLedger -> unnecessary semantic epoch/hash churn;
* lexicographic pre-limit before salience -> bounded high-salience starvation;
* duplicating StateLedger events into a second mandatory Pulse delta log -> avoidable
  synchronization/recovery surface and transaction-boundary risk.

Architecture:

    authoritative StateLedger state + event log
      -> direct event-atomic source cursor (stored inside U12 Pulse state_clay)
      -> adaptive authoritative rank path V4 (online or measured compiled index)
      -> authenticated focus use-boundary guard
      -> optional UNKNOWN model context
      -> U12 Pulse state + receipt + last-known-good checkpoint transaction
      -> NO external effect authority

The StateLedger event is the only authoritative semantic change unit. V5 never copies those
changes into frank_database_pulse_delta_queue. The legacy queue remains available for migration
or non-StateLedger sources, but V5 refuses to mix an unapplied legacy queue with the direct-event
path unless explicitly drained first.

Fresh bootstrap snapshots the already-valid current StateLedger and starts the source cursor at
the current event-log head. Later source events are consumed as whole events. If more events are
pending than the cognitive budget, cognition fails closed and bounded zero-model catch-up Pulses
advance only to complete event boundaries.

Integrity has two layers:
* every focus ref is verified at the causal use boundary against the authenticated state shadow;
* a full canonical StateLedger root audit is required on first Pulse, whenever semantic events
  are pending, and periodically on idle Pulses. Between full audits, no global-integrity claim is
  made; selected context still receives use-boundary verification.

State and receipt hashes form an acyclic provenance graph: Pulse state binds the semantic basis,
source cursor and cognitive assembly hash; the receipt then binds the completed post-state hash.
No state hash depends on a receipt hash that itself depends on that state hash.

This is a research candidate, not a promoted Harness component and never effect authority.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.runtime.auth_shadow_focus_guard import AuthShadowFocusGuard
from research_entity.runtime.database_pulse_candidate_v1 import PULSE_CONTRACT
from research_entity.runtime.database_pulse_rank_path_v4 import (
    AdaptiveAuthoritativeRankPathV4,
    IMPLEMENTATION_ID as RANK_IMPLEMENTATION_ID,
)
from research_entity.runtime.database_pulse_runtime_v4 import (
    DatabasePulseRuntimeV4 as SemanticPulseRuntimeV4,
    PulseRankPolicyV4,
)
from research_entity.runtime.database_pulse_v0 import (
    DatabasePulseV0,
    PulseIntegrityError,
    PulseStateError,
    _json,
    _sha,
)


IMPLEMENTATION_ID = "database_pulse_execution_plane_v5_direct_stateledger_events"
MAX_MODEL_OUTPUT_BYTES = 65536
REENTRY_MODES = {
    "TRUTHFUL",
    "NO_REENTRY",
    "SHUFFLED_CONTROL",
    "PROVENANCE_BROKEN_CONTROL",
}


@dataclass(frozen=True)
class PulseSpecV5:
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
class PulseReceiptV5:
    status: str
    invocation_id: str
    pulse_id: str
    pulse_index: int
    basis_epoch: int
    semantic_state_hash: str
    source_event_count: int
    source_event_seq_before: int
    source_event_seq_after: int
    source_epoch_after: int
    backlog_events_after: int
    focus_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    assembly_hash: str
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


class DatabasePulseExecutionPlaneV5(DatabasePulseV0):
    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64
    MAX_SOURCE_EVENTS_HARD = 65536

    def __init__(
        self,
        ledger: StateLedger,
        *,
        entity_id: str = "dr-unterweger-frank-personal-entity",
        lineage_id: str = "frank-v0.1-database-pulse-v5",
        rank_policy_provider: Callable[[PulseSpecV5], PulseRankPolicyV4] | None = None,
        now: str = "V5_INIT",
    ):
        self.ledger = ledger
        u12 = Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(
            encoding="utf-8"
        )
        ledger.conn.executescript(u12)
        ledger.conn.commit()
        super().__init__(ledger.conn)
        self.rank_path = AdaptiveAuthoritativeRankPathV4(ledger)
        self.rank_policy_provider = rank_policy_provider
        self.focus_guard = AuthShadowFocusGuard(ledger)
        self._bootstrap_or_adopt(
            entity_id=entity_id,
            lineage_id=lineage_id,
            now=now,
        )

    # ---------------------------------------------------------------- source cursor / bootstrap
    def _max_event_seq(self) -> int:
        return int(self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    @staticmethod
    def _decode_state_clay(row) -> dict[str, Any]:
        try:
            body = json.loads(str(row["state_clay"]))
        except Exception as exc:
            raise PulseIntegrityError("Pulse state_clay is unreadable") from exc
        if not isinstance(body, dict):
            raise PulseIntegrityError("Pulse state_clay must be an object")
        return body

    def _event_anchor_for_epoch(self, source_epoch: int) -> int:
        if source_epoch <= 0:
            return 0
        row = self.con.execute(
            "SELECT seq FROM events WHERE epoch<=? ORDER BY epoch DESC,seq DESC LIMIT 1",
            (source_epoch,),
        ).fetchone()
        return 0 if row is None else int(row["seq"])

    def _rewrite_state_clay_for_v5(self, *, cursor: int, mode: str, now: str) -> None:
        self.con.execute("BEGIN IMMEDIATE")
        try:
            old = self._verify_state()
            body = {
                "implementation": IMPLEMENTATION_ID,
                "mode": mode,
                "last_source_event_seq": int(cursor),
                "semantic_state_hash": self.ledger.semantic_state_hash,
                "last_focus_refs": [],
                "last_cognitive_assembly_hash": None,
                "integrity": "MIGRATION_OR_BOOTSTRAP_NO_GLOBAL_CLAIM",
            }
            material = self._material_from_mapping(old)
            material["state_clay"] = _json(body)
            material["state_transition_count"] = int(old["state_transition_count"]) + 1
            material["entity_epoch"] = int(old["entity_epoch"]) + 1
            post_hash = _sha(_json(material))
            self.con.execute(
                """UPDATE frank_database_pulse_state SET
                   state_transition_count=?,entity_epoch=?,state_clay=?,state_hash=?,updated_at=?
                   WHERE singleton_id=1""",
                (
                    material["state_transition_count"],
                    material["entity_epoch"],
                    material["state_clay"],
                    post_hash,
                    now,
                ),
            )
            row = self._state()
            snapshot, snapshot_hash = self._snapshot(row)
            if snapshot_hash != post_hash:
                raise PulseIntegrityError("V5 bootstrap/migration snapshot hash divergence")
            checkpoint_id = f"checkpoint:v5-adopt:{post_hash[:24]}"
            self.con.execute(
                """INSERT OR IGNORE INTO frank_database_pulse_checkpoints
                  (checkpoint_id,pulse_id,pulse_index,snapshot_clay,state_hash,created_at)
                  VALUES(?,NULL,?,?,?,?)""",
                (checkpoint_id, int(row["pulse_count"]), snapshot, post_hash, now),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

    def _bootstrap_or_adopt(self, *, entity_id: str, lineage_id: str, now: str) -> None:
        existed = self.con.execute(
            "SELECT 1 FROM frank_database_pulse_state WHERE singleton_id=1"
        ).fetchone() is not None
        if not existed:
            self.bootstrap(
                entity_id=entity_id,
                lineage_id=lineage_id,
                source_epoch=self.ledger.epoch,
                graph_epoch=0,
                now=now,
            )
            self._rewrite_state_clay_for_v5(
                cursor=self._max_event_seq(),
                mode="CURRENT_STATELEDGER_SNAPSHOT_BOOTSTRAP",
                now=now,
            )
            return

        state = self._verify_state()
        body = self._decode_state_clay(state)
        if body.get("implementation") == IMPLEMENTATION_ID:
            cursor = body.get("last_source_event_seq")
            if not isinstance(cursor, int) or cursor < 0 or cursor > self._max_event_seq():
                raise PulseIntegrityError("V5 source event cursor is invalid")
            if int(state["source_epoch"]) > self.ledger.epoch:
                raise PulseIntegrityError("V5 source_epoch is ahead of StateLedger")
            return

        source_epoch = int(state["source_epoch"])
        if source_epoch > self.ledger.epoch:
            raise PulseIntegrityError("legacy U12 source_epoch is ahead of StateLedger")
        cursor = (
            self._max_event_seq()
            if source_epoch == self.ledger.epoch
            else self._event_anchor_for_epoch(source_epoch)
        )
        self._rewrite_state_clay_for_v5(
            cursor=cursor,
            mode="ADOPTED_EXISTING_U12_SOURCE_EPOCH",
            now=now,
        )

    def _cursor(self) -> int:
        row = self._verify_state()
        body = self._decode_state_clay(row)
        if body.get("implementation") != IMPLEMENTATION_ID:
            raise PulseIntegrityError("Pulse state is not V5-adopted")
        cursor = body.get("last_source_event_seq")
        if not isinstance(cursor, int) or cursor < 0:
            raise PulseIntegrityError("invalid V5 source event cursor")
        return cursor

    # ---------------------------------------------------------------- source events
    def _pending_event_count(self, cursor: int | None = None) -> int:
        c = self._cursor() if cursor is None else int(cursor)
        return int(self.con.execute("SELECT COUNT(*) FROM events WHERE seq>?", (c,)).fetchone()[0])

    def _pending_events(self, *, cursor: int, limit: int):
        return self.con.execute(
            "SELECT seq,event_id,epoch,ops_json,semantic_state_hash FROM events "
            "WHERE seq>? ORDER BY seq LIMIT ?",
            (cursor, limit),
        ).fetchall()

    @staticmethod
    def _event_changes(events: Iterable[Any]) -> tuple[list[str], int]:
        refs: list[str] = []
        memory_refs: set[str] = set()
        for event in events:
            try:
                ops = json.loads(event["ops_json"])
            except Exception as exc:
                raise PulseIntegrityError(
                    f"StateLedger event ops unreadable at seq={event['seq']}"
                ) from exc
            for op in ops:
                domain = str(op.get("domain") or "")
                key = str(op.get("key") or "")
                if not domain or not key or domain in {"pulse", "pulse_control"}:
                    continue
                ref = f"{domain}:{key}"
                if ref not in refs:
                    refs.append(ref)
                if domain == "memory":
                    memory_refs.add(ref)
        return refs, len(memory_refs)

    # ---------------------------------------------------------------- integrity / rank policy
    def _full_integrity(self) -> dict[str, str]:
        try:
            semantic, trace = self.ledger._roots()
        except Exception as exc:
            raise PulseIntegrityError(
                f"cannot recompute authoritative StateLedger roots: {exc}"
            ) from exc
        if semantic != self.ledger.semantic_state_hash:
            raise PulseIntegrityError(
                f"StateLedger semantic root mismatch expected={self.ledger.semantic_state_hash} actual={semantic}"
            )
        if trace != self.ledger.trace_root_hash:
            raise PulseIntegrityError(
                f"StateLedger trace root mismatch expected={self.ledger.trace_root_hash} actual={trace}"
            )
        return {"semantic_state_hash": semantic, "trace_root_hash": trace}

    def _rank_policy(self, spec: PulseSpecV5) -> PulseRankPolicyV4:
        if self.rank_policy_provider is None:
            return SemanticPulseRuntimeV4._safe_unmeasured_policy()
        policy = self.rank_policy_provider(spec)
        if not isinstance(policy, PulseRankPolicyV4):
            raise TypeError("rank_policy_provider must return PulseRankPolicyV4")
        policy.validate()
        return policy

    # ---------------------------------------------------------------- receipts / idempotency
    def _existing_invocation(self, invocation_id: str) -> dict[str, Any] | None:
        rows = self.con.execute(
            "SELECT receipt_clay FROM frank_database_pulse_receipts ORDER BY pulse_index DESC"
        ).fetchall()
        for row in rows:
            try:
                body = json.loads(row["receipt_clay"])
            except Exception:
                continue
            if isinstance(body, dict) and body.get("implementation") == IMPLEMENTATION_ID \
                    and body.get("invocation_id") == invocation_id:
                supplied = body.get("receipt_hash")
                plain = dict(body)
                plain.pop("receipt_hash", None)
                if not isinstance(supplied, str) or h(plain) != supplied:
                    raise PulseIntegrityError("existing V5 receipt hash mismatch")
                return body
        return None

    def _latest_cognitive_receipt(self) -> dict[str, Any] | None:
        rows = self.con.execute(
            "SELECT receipt_clay FROM frank_database_pulse_receipts ORDER BY pulse_index DESC"
        ).fetchall()
        for row in rows:
            try:
                body = json.loads(row["receipt_clay"])
            except Exception:
                continue
            if isinstance(body, dict) and body.get("implementation") == IMPLEMENTATION_ID \
                    and body.get("mode") == "COGNITIVE":
                supplied = body.get("receipt_hash")
                plain = dict(body)
                plain.pop("receipt_hash", None)
                if not isinstance(supplied, str) or h(plain) != supplied:
                    raise PulseIntegrityError("latest V5 cognitive receipt hash mismatch")
                return body
        return None

    @staticmethod
    def _receipt_from_body(body: dict[str, Any], status: str) -> PulseReceiptV5:
        obs = body["observables"]
        return PulseReceiptV5(
            status=status,
            invocation_id=str(body["invocation_id"]),
            pulse_id=str(body["pulse_id"]),
            pulse_index=int(body["pulse_index"]),
            basis_epoch=int(body["basis_epoch"]),
            semantic_state_hash=str(body["semantic_state_hash"]),
            source_event_count=int(body["source_event_count"]),
            source_event_seq_before=int(body["source_event_seq_before"]),
            source_event_seq_after=int(body["source_event_seq_after"]),
            source_epoch_after=int(body["source_epoch_after"]),
            backlog_events_after=int(body["backlog_events_after"]),
            focus_refs=tuple(map(str, body.get("focus_refs", ()))),
            candidate_refs=tuple(map(str, body.get("candidate_refs", ()))),
            assembly_hash=str(body["assembly_hash"]),
            physical_rank_mode=str(body["physical_rank_mode"]),
            integrity_mode=str(body["integrity_mode"]),
            focus_guard_passed=bool(body["focus_guard_passed"]),
            conflicts_present=int(body["conflicts_present"]),
            unknown_present=int(body["unknown_present"]),
            reentry_count=int(obs["reentry_count"]),
            memory_update_observed_count=int(obs["memory_update_observed_count"]),
            model_call_count=int(obs["model_call_count"]),
            tool_call_count=int(obs["tool_call_count"]),
            effect_count=int(obs["effect_count"]),
            receipt_hash=str(body["receipt_hash"]),
        )

    # ---------------------------------------------------------------- atomic U12 commit
    def _commit_transition(
        self,
        *,
        invocation_id: str,
        mode: str,
        basis_epoch: int,
        semantic_hash: str,
        trace_hash: str,
        events,
        focus_refs: tuple[str, ...],
        candidate_refs: tuple[str, ...],
        assembly_hash: str,
        physical_rank_mode: str,
        integrity_mode: str,
        focus_guard_passed: bool,
        conflicts_present: int,
        unknown_present: int,
        reentry_count: int,
        memory_update_count: int,
        model_candidate: dict[str, Any] | None,
        rank_metadata: dict[str, Any],
        now: str,
    ) -> PulseReceiptV5:
        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self.ledger.epoch != basis_epoch or self.ledger.semantic_state_hash != semantic_hash:
                raise StaleEpoch("semantic basis changed before V5 Pulse commit")
            old = self._verify_state()
            if old["status"] != "PULSING":
                raise PulseStateError(f"V5 Pulse blocked in state={old['status']}")
            old_body = self._decode_state_clay(old)
            cursor_before = int(old_body["last_source_event_seq"])
            expected_rows = self._pending_events(cursor=cursor_before, limit=len(events)) if events else []
            if [int(r["seq"]) for r in expected_rows] != [int(r["seq"]) for r in events]:
                raise StaleEpoch("V5 source event stream changed before commit")

            cursor_after = cursor_before if not events else int(events[-1]["seq"])
            source_epoch_after = int(old["source_epoch"])
            if events:
                source_epoch_after = int(events[-1]["epoch"])
            backlog_after = int(
                self.con.execute("SELECT COUNT(*) FROM events WHERE seq>?", (cursor_after,)).fetchone()[0]
            )
            pulse_index = int(old["pulse_count"]) + 1
            state_delta = 1 + len(events)
            model_call_count = int(model_candidate is not None)
            state_body = {
                "implementation": IMPLEMENTATION_ID,
                "mode": mode,
                "last_source_event_seq": cursor_after,
                "semantic_state_hash": semantic_hash,
                "last_focus_refs": list(focus_refs),
                "last_cognitive_assembly_hash": (
                    assembly_hash
                    if mode == "COGNITIVE"
                    else old_body.get("last_cognitive_assembly_hash")
                ),
                "integrity": integrity_mode,
                "focus_guard_passed": focus_guard_passed,
                "physical_rank_mode": physical_rank_mode,
            }
            material = self._material_from_mapping(old)
            material.update({
                "pulse_count": pulse_index,
                "state_transition_count": int(old["state_transition_count"]) + state_delta,
                "entity_epoch": int(old["entity_epoch"]) + 1,
                "source_epoch": source_epoch_after,
                "state_clay": _json(state_body),
            })
            post_hash = _sha(_json(material))
            pulse_id = f"pulse-v5:{old['lineage_id']}:{pulse_index}:{post_hash[:16]}"

            observables = {
                "pulse_count": 1,
                "state_transition_count": state_delta,
                "semantic_state_transition_count": 0,
                "graph_change_count": 0,
                "hypothesis_count": model_call_count,
                "memory_update_observed_count": memory_update_count,
                "reentry_count": reentry_count,
                "model_call_count": model_call_count,
                "tool_call_count": 0,
                "effect_count": 0,
            }
            receipt_body: dict[str, Any] = {
                "schema_version": "5.1-research",
                "implementation": IMPLEMENTATION_ID,
                "pulse_contract": PULSE_CONTRACT,
                "mode": mode,
                "invocation_id": invocation_id,
                "pulse_id": pulse_id,
                "pulse_index": pulse_index,
                "basis_epoch": basis_epoch,
                "semantic_state_hash": semantic_hash,
                "trace_root_hash": trace_hash,
                "pre_state_hash": str(old["state_hash"]),
                "post_state_hash": post_hash,
                "source_event_count": len(events),
                "source_event_seq_before": cursor_before,
                "source_event_seq_after": cursor_after,
                "source_event_ids": [str(e["event_id"]) for e in events],
                "source_event_epochs": [int(e["epoch"]) for e in events],
                "source_epoch_after": source_epoch_after,
                "backlog_events_after": backlog_after,
                "focus_refs": list(focus_refs),
                "candidate_refs": list(candidate_refs),
                "assembly_hash": assembly_hash,
                "physical_rank_mode": physical_rank_mode,
                "integrity_mode": integrity_mode,
                "focus_guard_passed": focus_guard_passed,
                "conflicts_present": conflicts_present,
                "unknown_present": unknown_present,
                "model_candidate": model_candidate,
                "rank_metadata": rank_metadata,
                "observables": observables,
                "authority": "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
                "effect_authority": "NONE",
            }
            receipt_body["receipt_hash"] = h(receipt_body)
            receipt_clay = _json(receipt_body)

            self.con.execute(
                """UPDATE frank_database_pulse_state SET pulse_count=?,state_transition_count=?,
                   entity_epoch=?,source_epoch=?,state_clay=?,state_hash=?,updated_at=?
                   WHERE singleton_id=1""",
                (
                    pulse_index,
                    material["state_transition_count"],
                    material["entity_epoch"],
                    source_epoch_after,
                    material["state_clay"],
                    post_hash,
                    now,
                ),
            )
            self.con.execute(
                """INSERT INTO frank_database_pulse_receipts
                  (pulse_id,pulse_index,pre_state_hash,post_state_hash,applied_delta_count,
                   backlog_after,model_call_count,tool_call_count,effect_count,source_epoch,
                   graph_epoch,semantic_generation_id,receipt_clay,created_at)
                  VALUES(?,?,?,?,0,?,?,?,?,?,?,NULL,?,?)""",
                (
                    pulse_id,
                    pulse_index,
                    old["state_hash"],
                    post_hash,
                    backlog_after,
                    model_call_count,
                    0,
                    0,
                    source_epoch_after,
                    int(old["graph_epoch"]),
                    receipt_clay,
                    now,
                ),
            )
            row = self._state()
            snapshot, snapshot_hash = self._snapshot(row)
            if snapshot_hash != post_hash:
                raise PulseIntegrityError("V5 post-state/checkpoint hash divergence")
            self.con.execute(
                """INSERT INTO frank_database_pulse_checkpoints
                  (checkpoint_id,pulse_id,pulse_index,snapshot_clay,state_hash,created_at)
                  VALUES(?,?,?,?,?,?)""",
                (f"checkpoint:{pulse_id}", pulse_id, pulse_index, snapshot, post_hash, now),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise

        if self.ledger.epoch != basis_epoch or self.ledger.semantic_state_hash != semantic_hash:
            raise PulseIntegrityError("V5 endogenous Pulse mutated authoritative semantic state")
        if self.ledger.trace_root_hash != trace_hash:
            raise PulseIntegrityError("V5 endogenous Pulse mutated authoritative trace root")
        return self._receipt_from_body(receipt_body, "RECORDED")

    # ---------------------------------------------------------------- public catch-up / cognition
    def drain_source_events(
        self,
        *,
        invocation_id: str,
        basis_epoch: int,
        max_source_events: int = 32,
        now: str,
    ) -> PulseReceiptV5:
        if not invocation_id.strip():
            raise ValueError("invocation_id required")
        existing = self._existing_invocation(invocation_id)
        if existing is not None:
            return self._receipt_from_body(existing, "ALREADY_RECORDED")
        if basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"V5 catch-up basis {basis_epoch}!={self.ledger.epoch}")
        if not (1 <= max_source_events <= self.MAX_SOURCE_EVENTS_HARD):
            raise ValueError("max_source_events out of bounds")
        if self.con.execute(
            "SELECT 1 FROM frank_database_pulse_delta_queue WHERE applied_pulse_id IS NULL LIMIT 1"
        ).fetchone() is not None:
            raise PulseStateError("legacy U12 delta backlog must be drained before V5 direct-event mode")

        roots = self._full_integrity()
        cursor = self._cursor()
        events = self._pending_events(cursor=cursor, limit=max_source_events)
        _, memory_updates = self._event_changes(events)
        assembly_hash = h({
            "mode": "SOURCE_EVENT_CATCHUP",
            "basis_epoch": basis_epoch,
            "source_event_ids": [str(e["event_id"]) for e in events],
        })
        return self._commit_transition(
            invocation_id=invocation_id,
            mode="SOURCE_EVENT_CATCHUP",
            basis_epoch=basis_epoch,
            semantic_hash=roots["semantic_state_hash"],
            trace_hash=roots["trace_root_hash"],
            events=events,
            focus_refs=(),
            candidate_refs=(),
            assembly_hash=assembly_hash,
            physical_rank_mode="NONE_CATCHUP",
            integrity_mode="FULL_CANONICAL_ROOT_AUDIT",
            focus_guard_passed=True,
            conflicts_present=0,
            unknown_present=0,
            reentry_count=0,
            memory_update_count=memory_updates,
            model_candidate=None,
            rank_metadata={},
            now=now,
        )

    def run_pulse(
        self,
        spec: PulseSpecV5,
        *,
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        now: str,
    ) -> PulseReceiptV5:
        if not spec.invocation_id.strip():
            raise ValueError("invocation_id required")
        existing = self._existing_invocation(spec.invocation_id)
        if existing is not None:
            return self._receipt_from_body(existing, "ALREADY_RECORDED")
        mode = spec.reentry_mode.upper()
        if mode not in REENTRY_MODES:
            raise ValueError(f"unsupported reentry_mode {spec.reentry_mode}")
        domains = tuple(dict.fromkeys(spec.source_domains))
        if not domains or any(d in {"pulse", "pulse_control"} for d in domains):
            raise ValueError("source_domains must be explicit and exclude pulse domains")
        if not (1 <= spec.max_candidates <= self.MAX_CANDIDATES_HARD):
            raise ValueError("max_candidates out of bounds")
        if not (1 <= spec.max_focus <= min(spec.max_candidates, self.MAX_FOCUS_HARD)):
            raise ValueError("max_focus out of bounds")
        if not (0 <= spec.max_source_events <= self.MAX_SOURCE_EVENTS_HARD):
            raise ValueError("max_source_events out of bounds")
        if not (1 <= spec.full_audit_every <= 4096):
            raise ValueError("full_audit_every out of bounds")
        if spec.basis_epoch != self.ledger.epoch:
            raise StaleEpoch(f"V5 basis {spec.basis_epoch}!={self.ledger.epoch}")
        if self.con.execute(
            "SELECT 1 FROM frank_database_pulse_delta_queue WHERE applied_pulse_id IS NULL LIMIT 1"
        ).fetchone() is not None:
            raise PulseStateError("legacy U12 delta backlog must be drained before V5 direct-event mode")

        old = self._verify_state()
        if old["status"] != "PULSING":
            raise PulseStateError(f"V5 Pulse blocked in state={old['status']}")
        cursor = self._cursor()
        pending_count = self._pending_event_count(cursor)
        if pending_count > spec.max_source_events:
            raise PulseStateError(
                f"V5 cognitive Pulse blocked: {pending_count} source events exceed budget "
                f"{spec.max_source_events}; drain_source_events() in bounded whole-event batches"
            )
        events = self._pending_events(cursor=cursor, limit=spec.max_source_events)
        changed_refs, memory_updates = self._event_changes(events)

        full_due = (
            int(old["pulse_count"]) == 0
            or bool(events)
            or (int(old["pulse_count"]) + 1) % spec.full_audit_every == 0
        )
        if full_due:
            roots = self._full_integrity()
            integrity_mode = "FULL_CANONICAL_ROOT_AUDIT_PLUS_FOCUS_GUARD"
        else:
            roots = {
                "semantic_state_hash": self.ledger.semantic_state_hash,
                "trace_root_hash": self.ledger.trace_root_hash,
            }
            integrity_mode = "FOCUS_USE_GUARD_PERIODIC_FULL_AUDIT_PENDING"

        previous = self._latest_cognitive_receipt()
        previous_focus = tuple(str(x) for x in (previous or {}).get("focus_refs", ()))
        shuffle_salt = None
        if mode == "SHUFFLED_CONTROL" and previous is not None:
            shuffle_salt = h({
                "previous_receipt_hash": previous.get("receipt_hash"),
                "control": "SHUFFLED",
            })
        policy = self._rank_policy(spec)
        selection = self.rank_path.select(
            source_domains=domains,
            basis_epoch=spec.basis_epoch,
            max_candidates=spec.max_candidates,
            max_focus=spec.max_focus,
            economics_without_horizon=policy.economics_without_horizon,
            pulse_history=policy.pulse_history,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
            shuffle_salt=shuffle_salt,
        )
        if selection.semantic_state_hash != self.ledger.semantic_state_hash:
            raise StaleEpoch("V5 rank selection semantic root changed")

        guard = self.focus_guard.refresh_and_verify_refs(selection.focus_refs, now=now)
        if not guard.passed:
            raise PulseIntegrityError("V5 focus use-boundary guard failed")
        if guard.ledger_epoch != spec.basis_epoch:
            raise StaleEpoch("V5 focus guard epoch mismatch")

        focus_context: list[dict[str, Any]] = []
        focus_hashes: list[str] = []
        score_by_ref = dict(zip(selection.candidate_refs, selection.candidate_scores))
        for ref in selection.focus_refs:
            domain, key = ref.split(":", 1)
            row = self.ledger.get(domain, key)
            if row is None or row["epistemic"] != "KNOWN" or row["status"] != "CURRENT":
                raise PulseIntegrityError(f"V5 selected invalid focus ref {ref}")
            focus_hashes.append(str(row["semantic_hash"]))
            focus_context.append({
                "ref": ref,
                "score": score_by_ref[ref],
                "source_semantic_hash": row["semantic_hash"],
                "domain_epoch": row["domain_epoch"],
                "value": row["value"],
            })

        truthful_reentry = int(
            mode == "TRUTHFUL" and bool(set(previous_focus) & set(selection.focus_refs))
        )
        assembly_hash = h({
            "basis_epoch": spec.basis_epoch,
            "semantic_state_hash": self.ledger.semantic_state_hash,
            "source_event_ids": [str(e["event_id"]) for e in events],
            "changed_refs": changed_refs,
            "selection_hash": selection.selection_hash,
            "focus_refs": list(selection.focus_refs),
            "focus_source_hashes": focus_hashes,
            "focus_guard_shadow_root": guard.shadow_root_hash,
        })

        model_candidate = None
        if model_assistant is not None:
            output = model_assistant({
                "invocation_id": spec.invocation_id,
                "basis_epoch": spec.basis_epoch,
                "assembly_hash": assembly_hash,
                "focus": focus_context,
                "candidate_generation": RANK_IMPLEMENTATION_ID,
                "physical_rank_mode": selection.physical_mode,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            })
            encoded = cjson(output)
            if len(encoded.encode("utf-8")) > MAX_MODEL_OUTPUT_BYTES:
                raise ValueError("model candidate exceeds V5 receipt bound")
            model_candidate = {
                "epistemic": "UNKNOWN",
                "candidate": output,
                "candidate_hash": h(output),
                "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
            }

        rank_metadata = {
            "candidate_generation": RANK_IMPLEMENTATION_ID,
            "selection_hash": selection.selection_hash,
            "query_truncated": selection.query_truncated,
            "candidate_universe_count": selection.candidate_universe_count,
            "query_plan": list(selection.query_plan),
            "physical_mode": selection.physical_mode,
            "index_present_before": selection.index_present_before,
            "index_present_after": selection.index_present_after,
            "horizon_status": selection.horizon_status,
            "horizon_reads_lower_bound": selection.horizon_reads_lower_bound,
            "compile_reason": selection.compile_reason,
            "guarded_break_even_reads": selection.guarded_break_even_reads,
            "rank_policy_provenance_ref": policy.provenance_ref,
            "focus_guard": {
                "checked_refs": list(guard.checked_refs),
                "shadow_root_hash": guard.shadow_root_hash,
                "refresh_mode": guard.refresh_mode,
                "global_integrity_claim": guard.global_integrity_claim,
            },
        }
        return self._commit_transition(
            invocation_id=spec.invocation_id,
            mode="COGNITIVE",
            basis_epoch=spec.basis_epoch,
            semantic_hash=roots["semantic_state_hash"],
            trace_hash=roots["trace_root_hash"],
            events=events,
            focus_refs=tuple(selection.focus_refs),
            candidate_refs=tuple(selection.candidate_refs),
            assembly_hash=assembly_hash,
            physical_rank_mode=selection.physical_mode,
            integrity_mode=integrity_mode,
            focus_guard_passed=True,
            conflicts_present=selection.conflicts_present,
            unknown_present=selection.unknown_present,
            reentry_count=truthful_reentry,
            memory_update_count=memory_updates,
            model_candidate=model_candidate,
            rank_metadata=rank_metadata,
            now=now,
        )
