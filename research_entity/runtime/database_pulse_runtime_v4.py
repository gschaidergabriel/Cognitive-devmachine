from __future__ import annotations

"""FRANK Database Pulse Runtime V4 research candidate.

Current fusion target:

  authoritative StateLedger
      -> physical salience expression index (rebuildable, no second semantic table)
      -> bounded ranked candidate assembly + re-entry controls
      -> U12 dedicated Pulse state/delta/receipt/checkpoint plane
      -> optional UNKNOWN model context
      -> NO external effect authority

V4 differs from the semantic-StateLedger Pulse v2 by keeping endogenous Pulse execution state
outside canonical semantic StateLedger state. Idle Pulses therefore advance the dedicated U12
entity/Pulse clock without advancing StateLedger.global_epoch, semantic_state_hash or trace root.

V4 differs from the ActiveField fusion by preferring the simpler AuthoritativeRankIndexV3
counterbaseline: salience ordering is maintained as a SQLite expression index directly over the
authoritative `state` rows. The index is physical and rebuildable. StateLedger remains semantic
truth; dropping/rebuilding the index cannot change semantic meaning.

Bootstrap/migration law:
* Fresh V4 over a valid current StateLedger snapshots the current semantic epoch into U12 and
  starts the bridge cursor at the current event-log head. Historical events are not needlessly
  replayed into the hot delta queue.
* Existing U12 state that lags StateLedger resumes from its recorded source_epoch and bridges only
  newer authoritative events.
* Any incoherent/future source epoch fails closed.

Large new semantic bursts are backlog-gated. If U12 cannot acknowledge the complete new delta set
within the cognitive Pulse budget, V4 refuses to publish a focus and exposes bounded zero-model
catch-up Pulses instead. Cognition never runs ahead of the U12 source epoch.

Correctness is preferred over optimistic performance: the canonical StateLedger semantic/trace
roots are fully recomputed once per guarded operation. A future incremental integrity accelerator
must be byte-equivalent before replacing this gate.

Research candidate only. This module is not a promoted FRANK Harness component and never grants
external effect authority.
"""

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.runtime.database_pulse_rank_index_v3 import (
    AuthoritativeRankIndexV3,
    IMPLEMENTATION_ID as RANK_IMPLEMENTATION_ID,
    INDEX_NAME,
    SCORE_EXPR,
)
from research_entity.runtime.database_pulse_v0 import (
    DatabasePulseV0,
    PulseIntegrityError,
    PulseStateError,
    PulseStaleEpochError,
    _json,
    _sha,
)


IMPLEMENTATION_ID = "database_pulse_runtime_v4_u12_authoritative_rank_index"
PULSE_CONTRACT = "research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md"
REENTRY_MODES = {
    "TRUTHFUL",
    "NO_REENTRY",
    "SHUFFLED_CONTROL",
    "PROVENANCE_BROKEN_CONTROL",
}
MAX_MODEL_OUTPUT_BYTES = 65536

V4_SCHEMA = r"""
CREATE TABLE IF NOT EXISTS frank_database_pulse_v4_bridge_meta(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  last_event_seq INTEGER NOT NULL DEFAULT 0 CHECK(last_event_seq >= 0),
  ledger_epoch INTEGER NOT NULL DEFAULT 0 CHECK(ledger_epoch >= 0),
  semantic_state_hash TEXT NOT NULL,
  bridge_count INTEGER NOT NULL DEFAULT 0 CHECK(bridge_count >= 0),
  bootstrap_mode TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class PulseReceiptV4:
    pulse_id: str
    pulse_index: int
    basis_epoch: int
    semantic_state_hash: str
    pre_state_hash: str
    post_state_hash: str
    applied_delta_count: int
    backlog_after: int
    focus_refs: tuple[str, ...]
    candidate_refs: tuple[str, ...]
    candidate_scores: tuple[float, ...]
    candidate_universe_count: int
    query_truncated: bool
    assembly_hash: str
    conflicts_present: int
    unknown_present: int
    reentry_count: int
    model_call_count: int
    tool_call_count: int
    effect_count: int
    memory_update_observed_count: int
    state_transition_count_delta: int
    semantic_state_transition_count: int
    graph_change_count: int
    hypothesis_count: int
    source_event_seq: int
    bridge_mode: str
    rank_index_name: str
    receipt_hash: str
    authority: str = "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


class DatabasePulseRuntimeV4(DatabasePulseV0):
    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64
    MAX_DELTAS_HARD = 65536

    def __init__(
        self,
        ledger: StateLedger,
        *,
        entity_id: str = "dr-unterweger-frank-personal-entity",
        lineage_id: str = "frank-v0.1-database-pulse-v4",
        now: str = "V4_INIT",
    ):
        self.ledger = ledger
        u12 = Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(
            encoding="utf-8"
        )
        ledger.conn.executescript(u12)
        ledger.conn.executescript(V4_SCHEMA)
        ledger.conn.commit()
        super().__init__(ledger.conn)

        existed = self.con.execute(
            "SELECT 1 FROM frank_database_pulse_state WHERE singleton_id=1"
        ).fetchone() is not None
        if not existed:
            # Fresh V4 may adopt the already-verified current StateLedger as its initial source
            # epoch. This is a snapshot bootstrap, not retroactive Pulse credit for old events.
            self.bootstrap(
                entity_id=entity_id,
                lineage_id=lineage_id,
                source_epoch=ledger.epoch,
                graph_epoch=0,
                now=now,
            )
        else:
            self._verify_state()

        self.rank_index = AuthoritativeRankIndexV3(ledger)
        self.rank_index.ensure_index()
        self._integrity_cache: dict[str, str] | None = None
        self._ensure_bridge_anchor(now=now, fresh_v4=not existed)

    # ------------------------------------------------------------------ integrity
    def _full_ledger_integrity(self) -> dict[str, str]:
        if self._integrity_cache is not None:
            return dict(self._integrity_cache)
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
        self._integrity_cache = {
            "semantic_state_hash": semantic,
            "trace_root_hash": trace,
        }
        return dict(self._integrity_cache)

    def _reset_integrity_cache(self) -> None:
        self._integrity_cache = None

    # ------------------------------------------------------------------ bridge
    def _bridge_meta(self):
        return self.con.execute(
            "SELECT * FROM frank_database_pulse_v4_bridge_meta WHERE singleton_id=1"
        ).fetchone()

    def _max_event_seq(self) -> int:
        return int(self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0])

    def _event_anchor_for_epoch(self, source_epoch: int) -> tuple[int, str]:
        if source_epoch <= 0:
            # StateLedger genesis root is available from the current object only at epoch 0.
            if self.ledger.epoch == 0:
                return 0, self.ledger.semantic_state_hash
            return 0, "UNKNOWN_HISTORICAL_GENESIS_ROOT"
        row = self.con.execute(
            "SELECT seq,semantic_state_hash FROM events WHERE epoch<=? ORDER BY epoch DESC LIMIT 1",
            (source_epoch,),
        ).fetchone()
        if row is None:
            return 0, "UNKNOWN_HISTORICAL_ROOT"
        return int(row["seq"]), str(row["semantic_state_hash"])

    def _ensure_bridge_anchor(self, *, now: str, fresh_v4: bool) -> None:
        if self._bridge_meta() is not None:
            return
        pulse_state = self._verify_state()
        source_epoch = int(pulse_state["source_epoch"])
        if source_epoch > self.ledger.epoch:
            raise PulseIntegrityError(
                f"U12 source_epoch {source_epoch} is ahead of StateLedger epoch {self.ledger.epoch}"
            )
        current_seq = self._max_event_seq()
        if fresh_v4 or source_epoch == self.ledger.epoch:
            last_seq = current_seq
            root = self.ledger.semantic_state_hash
            mode = "CURRENT_SNAPSHOT_BOOTSTRAP" if fresh_v4 else "ALIGNED_U12_MIGRATION"
            ledger_epoch = self.ledger.epoch
        else:
            last_seq, root = self._event_anchor_for_epoch(source_epoch)
            mode = "LAGGING_U12_MIGRATION"
            ledger_epoch = source_epoch
        with self.con:
            self.con.execute(
                """INSERT INTO frank_database_pulse_v4_bridge_meta
                  (singleton_id,last_event_seq,ledger_epoch,semantic_state_hash,bridge_count,
                   bootstrap_mode,updated_at)
                  VALUES(1,?,?,?,?,?,?)""",
                (last_seq, ledger_epoch, root, 0, mode, now),
            )

    @staticmethod
    def _source_ref(op: dict[str, Any]) -> str | None:
        domain = str(op.get("domain") or "").strip()
        key = str(op.get("key") or "").strip()
        if not domain or not key or domain in {"pulse", "pulse_control"}:
            return None
        return f"{domain}:{key}"

    def bridge_stateledger_events(self, *, now: str) -> dict[str, Any]:
        """Bridge every new authoritative semantic event into the entity-level U12 delta queue."""
        current_seq = self._max_event_seq()
        meta = self._bridge_meta()
        if meta is None:
            raise PulseIntegrityError("V4 source bridge is not anchored")
        after_seq = int(meta["last_event_seq"])
        if after_seq > current_seq:
            raise PulseIntegrityError("V4 bridge cursor is ahead of authoritative event log")
        if after_seq == current_seq:
            if int(meta["ledger_epoch"]) != self.ledger.epoch:
                raise PulseIntegrityError(
                    "StateLedger epoch advanced without authoritative event sequence advance"
                )
            if str(meta["semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise PulseIntegrityError(
                    "StateLedger semantic root changed without authoritative event sequence advance"
                )
            return {
                "mode": "NO_CHANGE",
                "events_consumed": 0,
                "admitted_deltas": 0,
                "changed_refs": [],
                "last_event_seq": current_seq,
            }

        events = self.con.execute(
            "SELECT seq,event_id,epoch,ops_json,semantic_state_hash FROM events "
            "WHERE seq>? AND seq<=? ORDER BY seq",
            (after_seq, current_seq),
        ).fetchall()
        admitted = 0
        changed_refs: list[str] = []
        self.con.execute("BEGIN IMMEDIATE")
        try:
            for event in events:
                try:
                    ops = json.loads(event["ops_json"])
                except Exception as exc:
                    raise PulseIntegrityError(
                        f"unreadable StateLedger event ops at seq={event['seq']}: {exc}"
                    ) from exc
                for op_index, op in enumerate(ops):
                    ref = self._source_ref(op)
                    if ref is None:
                        continue
                    payload = {
                        "event_seq": int(event["seq"]),
                        "event_id": str(event["event_id"]),
                        "event_epoch": int(event["epoch"]),
                        "op_index": op_index,
                        "operation": str(op.get("op") or ""),
                        "changed_ref": ref,
                        "event_semantic_state_hash": str(event["semantic_state_hash"]),
                    }
                    payload_clay = _json(payload)
                    delta_id = (
                        f"stateledger:{int(event['seq'])}:{op_index}:"
                        f"{h({'ref': ref, 'payload': payload})[:16]}"
                    )
                    cur = self.con.execute(
                        """INSERT OR IGNORE INTO frank_database_pulse_delta_queue
                          (delta_id,changed_ref,reason_class,payload_clay,payload_hash,source_epoch,
                           graph_epoch,admitted_at)
                          VALUES(?,?,?,?,?,?,?,?)""",
                        (
                            delta_id,
                            ref,
                            f"STATELEDGER_{str(op.get('op') or 'CHANGE').upper()}",
                            payload_clay,
                            _sha(payload_clay),
                            int(event["epoch"]),
                            0,
                            now,
                        ),
                    )
                    admitted += int(cur.rowcount == 1)
                    if ref not in changed_refs:
                        changed_refs.append(ref)
            self.con.execute(
                """UPDATE frank_database_pulse_v4_bridge_meta SET
                   last_event_seq=?,ledger_epoch=?,semantic_state_hash=?,bridge_count=bridge_count+1,
                   updated_at=? WHERE singleton_id=1""",
                (
                    current_seq,
                    self.ledger.epoch,
                    self.ledger.semantic_state_hash,
                    now,
                ),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        return {
            "mode": "DELTA_BRIDGE",
            "events_consumed": len(events),
            "admitted_deltas": admitted,
            "changed_refs": changed_refs,
            "last_event_seq": current_seq,
        }

    def backlog_count(self) -> int:
        return int(
            self.con.execute(
                "SELECT COUNT(*) FROM frank_database_pulse_delta_queue "
                "WHERE applied_pulse_id IS NULL"
            ).fetchone()[0]
        )

    # ------------------------------------------------------------------ receipts/reentry
    def _previous_v4_receipt(self) -> dict[str, Any] | None:
        row = self.con.execute(
            "SELECT pulse_id,post_state_hash,receipt_clay FROM frank_database_pulse_receipts "
            "ORDER BY pulse_index DESC LIMIT 1"
        ).fetchone()
        if row is None:
            return None
        checkpoint = self.con.execute(
            "SELECT state_hash FROM frank_database_pulse_checkpoints WHERE pulse_id=? "
            "ORDER BY pulse_index DESC LIMIT 1",
            (row["pulse_id"],),
        ).fetchone()
        if checkpoint is None or str(checkpoint["state_hash"]) != str(row["post_state_hash"]):
            raise PulseIntegrityError("latest Pulse receipt/checkpoint provenance mismatch")
        try:
            body = json.loads(row["receipt_clay"])
        except Exception as exc:
            raise PulseIntegrityError("latest Pulse receipt is unreadable") from exc
        if not isinstance(body, dict) or body.get("implementation") != IMPLEMENTATION_ID:
            return None
        supplied = body.get("receipt_hash")
        plain = dict(body)
        plain.pop("receipt_hash", None)
        if not isinstance(supplied, str) or h(plain) != supplied:
            raise PulseIntegrityError("latest V4 cognitive receipt hash mismatch")
        return body

    @staticmethod
    def _memory_updates(deltas: Iterable[Any]) -> int:
        return sum(1 for d in deltas if str(d["changed_ref"]).startswith("memory:"))

    # ------------------------------------------------------------------ bounded catch-up
    def drain_backlog(self, *, basis_epoch: int, max_deltas: int = 512, now: str):
        """One bounded zero-cognition U12 catch-up Pulse."""
        if int(basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"V4 catch-up basis {basis_epoch}!={self.ledger.epoch}")
        if not (1 <= max_deltas <= self.MAX_DELTAS_HARD):
            raise ValueError("max_deltas out of bounds")
        self._reset_integrity_cache()
        try:
            self._full_ledger_integrity()
            self.bridge_stateledger_events(now=now)
            before = (
                self.ledger.epoch,
                self.ledger.semantic_state_hash,
                self.ledger.trace_root_hash,
            )
            receipt = DatabasePulseV0.pulse(
                self,
                max_deltas=max_deltas,
                now=now,
                model_call_count=0,
                tool_call_count=0,
                effect_count=0,
            )
            after = (
                self.ledger.epoch,
                self.ledger.semantic_state_hash,
                self.ledger.trace_root_hash,
            )
            if after != before:
                raise PulseStateError("V4 catch-up mutated authoritative StateLedger semantics")
            return receipt
        finally:
            self._reset_integrity_cache()

    # ------------------------------------------------------------------ cognitive pulse
    def run_pulse(
        self,
        *,
        basis_epoch: int,
        source_domains: tuple[str, ...] = (
            "self", "world", "memory", "goal", "task", "semantic", "capability", "percept"
        ),
        max_candidates: int = 128,
        max_focus: int = 12,
        max_deltas: int = 512,
        reentry_mode: str = "TRUTHFUL",
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        now: str,
        expected_source_epoch: int | None = None,
        expected_graph_epoch: int | None = None,
        fault_after_apply: bool = False,
    ) -> PulseReceiptV4:
        domains = tuple(dict.fromkeys(source_domains))
        if not domains or any(d in {"pulse", "pulse_control"} for d in domains):
            raise ValueError("source_domains must be explicit and exclude Pulse domains")
        if not (1 <= max_candidates <= self.MAX_CANDIDATES_HARD):
            raise ValueError("max_candidates out of bounds")
        if not (1 <= max_focus <= min(max_candidates, self.MAX_FOCUS_HARD)):
            raise ValueError("max_focus out of bounds")
        if not (0 <= max_deltas <= self.MAX_DELTAS_HARD):
            raise ValueError("max_deltas out of bounds")
        mode = reentry_mode.upper()
        if mode not in REENTRY_MODES:
            raise ValueError(f"unsupported reentry mode: {reentry_mode}")
        if int(basis_epoch) != self.ledger.epoch:
            raise StaleEpoch(f"V4 Pulse basis {basis_epoch}!={self.ledger.epoch}")

        self._reset_integrity_cache()
        try:
            roots = self._full_ledger_integrity()
            semantic_hash = roots["semantic_state_hash"]
            trace_hash = roots["trace_root_hash"]
            bridge = self.bridge_stateledger_events(now=now)
            backlog = self.backlog_count()
            if backlog > max_deltas:
                raise PulseStateError(
                    f"V4 cognitive Pulse blocked: U12 backlog {backlog} exceeds max_deltas "
                    f"{max_deltas}; run bounded drain_backlog() before cognitive assembly"
                )

            previous = self._previous_v4_receipt()
            previous_focus = tuple(str(x) for x in (previous or {}).get("focus_refs", ()))
            shuffle_salt = None
            if mode == "SHUFFLED_CONTROL" and previous is not None:
                shuffle_salt = h(
                    {"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"}
                )

            selection = self.rank_index.select(
                source_domains=domains,
                basis_epoch=basis_epoch,
                max_candidates=max_candidates,
                max_focus=max_focus,
                reentry_mode=mode,
                previous_focus_refs=previous_focus,
                shuffle_salt=shuffle_salt,
            )
            if self.ledger.epoch != basis_epoch:
                raise StaleEpoch("StateLedger epoch changed during V4 ranked assembly")
            if self.ledger.semantic_state_hash != semantic_hash:
                raise StaleEpoch("StateLedger semantic root changed during V4 ranked assembly")
            if self.ledger.trace_root_hash != trace_hash:
                raise StaleEpoch("StateLedger trace root changed during V4 ranked assembly")
            if selection.semantic_state_hash != semantic_hash:
                raise PulseIntegrityError("rank-index selection semantic root mismatch")
            if not any(INDEX_NAME in item for item in selection.query_plan):
                raise PulseIntegrityError(
                    f"rank selection did not use required physical index {INDEX_NAME}: {selection.query_plan}"
                )

            model_candidate: dict[str, Any] | None = None
            if model_assistant is not None:
                context = {
                    "basis_epoch": basis_epoch,
                    "semantic_state_hash": semantic_hash,
                    "candidate_generation": RANK_IMPLEMENTATION_ID,
                    "focus_refs": list(selection.focus_refs),
                    "candidate_refs": list(selection.candidate_refs),
                    "selection_hash": selection.selection_hash,
                    "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
                }
                model_output = model_assistant(context)
                encoded = cjson(model_output)
                if len(encoded.encode("utf-8")) > MAX_MODEL_OUTPUT_BYTES:
                    raise ValueError("model candidate exceeds bounded V4 receipt size")
                model_candidate = {
                    "epistemic": "UNKNOWN",
                    "candidate": model_output,
                    "candidate_hash": h(model_output),
                    "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
                }

            self.con.execute("BEGIN IMMEDIATE")
            try:
                if self.ledger.epoch != basis_epoch or self.ledger.semantic_state_hash != semantic_hash:
                    raise StaleEpoch("semantic basis changed before V4 Pulse commit")
                old = self._verify_state()
                if old["status"] != "PULSING":
                    raise PulseStateError(f"V4 Pulse blocked in state={old['status']}")

                semantic_head = self._semantic_head()
                if expected_source_epoch is not None and (
                    semantic_head is None
                    or int(semantic_head["source_epoch"]) != expected_source_epoch
                ):
                    raise PulseStaleEpochError("semantic source epoch mismatch")
                if expected_graph_epoch is not None and (
                    semantic_head is None
                    or int(semantic_head["graph_epoch"]) != expected_graph_epoch
                ):
                    raise PulseStaleEpochError("semantic graph epoch mismatch")

                deltas = self.con.execute(
                    """SELECT * FROM frank_database_pulse_delta_queue
                       WHERE applied_pulse_id IS NULL AND seq>?
                       ORDER BY seq LIMIT ?""",
                    (int(old["last_applied_delta_seq"]), max_deltas),
                ).fetchall()
                for delta in deltas:
                    if _sha(str(delta["payload_clay"])) != str(delta["payload_hash"]):
                        raise PulseIntegrityError(
                            f"delta payload hash mismatch: {delta['delta_id']}"
                        )
                if len(deltas) != backlog:
                    raise PulseStateError(
                        f"V4 bounded cognition expected to close backlog={backlog} but selected {len(deltas)} deltas"
                    )

                new_source = max(
                    [int(old["source_epoch"])] + [int(d["source_epoch"]) for d in deltas]
                )
                new_graph = max(
                    [int(old["graph_epoch"])] + [int(d["graph_epoch"] or 0) for d in deltas]
                )
                semantic_generation_id: str | None = None
                semantic_access = "UNAVAILABLE"
                if semantic_head is not None:
                    if (
                        int(semantic_head["source_epoch"]) == new_source
                        and int(semantic_head["graph_epoch"]) == new_graph
                    ):
                        semantic_generation_id = str(semantic_head["generation_id"])
                        semantic_access = "COHERENT"
                    else:
                        semantic_access = "STALE_FAIL_CLOSED"

                pulse_index = int(old["pulse_count"]) + 1
                last_delta_seq = int(old["last_applied_delta_seq"])
                if deltas:
                    last_delta_seq = max(int(d["seq"]) for d in deltas)
                previous_focus_set = set(previous_focus)
                current_focus_set = set(selection.focus_refs)
                truthful_reentry_count = int(
                    mode == "TRUTHFUL" and bool(previous_focus_set & current_focus_set)
                )
                state_delta = 1 + len(deltas)
                state_body = {
                    "mode": "U12_AUTHORITATIVE_RANK_INDEX_V4",
                    "implementation": IMPLEMENTATION_ID,
                    "basis_epoch": basis_epoch,
                    "semantic_state_hash": semantic_hash,
                    "source_event_seq": int(bridge["last_event_seq"]),
                    "last_delta_ids": [str(d["delta_id"]) for d in deltas],
                    "semantic_access": semantic_access,
                    "candidate_generation": RANK_IMPLEMENTATION_ID,
                    "rank_index_name": INDEX_NAME,
                    "selection_hash": selection.selection_hash,
                    "focus_refs": list(selection.focus_refs),
                    "candidate_universe_count": selection.candidate_universe_count,
                    "query_truncated": selection.query_truncated,
                    "conflicts_present": selection.conflicts_present,
                    "unknown_present": selection.unknown_present,
                    "reentry_mode": mode,
                    "reentry_count": truthful_reentry_count,
                    "model_candidate_hash": (
                        None if model_candidate is None else model_candidate["candidate_hash"]
                    ),
                    "authority": "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
                }
                state_clay = _json(state_body)
                material = {
                    "entity_id": old["entity_id"],
                    "lineage_id": old["lineage_id"],
                    "status": "PULSING",
                    "pulse_count": pulse_index,
                    "state_transition_count": int(old["state_transition_count"]) + state_delta,
                    "entity_epoch": int(old["entity_epoch"]) + 1,
                    "last_applied_delta_seq": last_delta_seq,
                    "source_epoch": new_source,
                    "graph_epoch": new_graph,
                    "semantic_generation_id": semantic_generation_id,
                    "state_clay": state_clay,
                }
                post_hash = _sha(_json(material))
                pulse_id = f"pulse:{old['lineage_id']}:{pulse_index}:{post_hash[:16]}"

                for delta in deltas:
                    self._publish_invalidation(delta, now)
                    self.con.execute(
                        "UPDATE frank_database_pulse_delta_queue SET applied_pulse_id=? WHERE seq=?",
                        (pulse_id, delta["seq"]),
                    )
                if fault_after_apply:
                    raise RuntimeError(
                        "injected V4 fault before state/receipt/checkpoint commit"
                    )

                backlog_after = int(
                    self.con.execute(
                        "SELECT COUNT(*) FROM frank_database_pulse_delta_queue "
                        "WHERE applied_pulse_id IS NULL"
                    ).fetchone()[0]
                )
                if backlog_after != 0:
                    raise PulseStateError(
                        f"V4 cognitive commit cannot publish with residual backlog={backlog_after}"
                    )

                self.con.execute(
                    """UPDATE frank_database_pulse_state SET status='PULSING',pulse_count=?,
                       state_transition_count=?,entity_epoch=?,last_applied_delta_seq=?,source_epoch=?,
                       graph_epoch=?,semantic_generation_id=?,state_clay=?,state_hash=?,updated_at=?
                       WHERE singleton_id=1""",
                    (
                        material["pulse_count"],
                        material["state_transition_count"],
                        material["entity_epoch"],
                        last_delta_seq,
                        new_source,
                        new_graph,
                        semantic_generation_id,
                        state_clay,
                        post_hash,
                        now,
                    ),
                )

                memory_updates = self._memory_updates(deltas)
                score_hash = hashlib.sha256(SCORE_EXPR.encode()).hexdigest()
                assembly_hash = h(
                    {
                        "basis_epoch": basis_epoch,
                        "semantic_state_hash": semantic_hash,
                        "candidate_generation": RANK_IMPLEMENTATION_ID,
                        "index_name": INDEX_NAME,
                        "score_expression_sha256": score_hash,
                        "selection_hash": selection.selection_hash,
                        "candidate_refs": list(selection.candidate_refs),
                        "candidate_scores": list(selection.candidate_scores),
                        "focus_refs": list(selection.focus_refs),
                    }
                )
                observables = {
                    "pulse_count": 1,
                    "state_transition_count": state_delta,
                    "semantic_state_transition_count": 0,
                    "graph_change_count": 0,
                    "hypothesis_count": int(model_candidate is not None),
                    "memory_update_observed_count": memory_updates,
                    "reentry_count": truthful_reentry_count,
                    "model_call_count": int(model_candidate is not None),
                    "tool_call_count": 0,
                    "effect_count": 0,
                }
                receipt_body: dict[str, Any] = {
                    "schema_version": "4.0-research",
                    "implementation": IMPLEMENTATION_ID,
                    "pulse_contract": PULSE_CONTRACT,
                    "pulse_id": pulse_id,
                    "pulse_index": pulse_index,
                    "basis_epoch": basis_epoch,
                    "semantic_state_hash": semantic_hash,
                    "trace_root_hash": trace_hash,
                    "pre_state_hash": str(old["state_hash"]),
                    "post_state_hash": post_hash,
                    "source_event_seq": int(bridge["last_event_seq"]),
                    "bridge_mode": bridge["mode"],
                    "bridge_admitted_deltas": int(bridge["admitted_deltas"]),
                    "applied_delta_ids": [str(d["delta_id"]) for d in deltas],
                    "candidate_generation": RANK_IMPLEMENTATION_ID,
                    "rank_index_name": INDEX_NAME,
                    "score_expression_sha256": score_hash,
                    "query_plan": list(selection.query_plan),
                    "selection_hash": selection.selection_hash,
                    "candidate_refs": list(selection.candidate_refs),
                    "candidate_scores": list(selection.candidate_scores),
                    "focus_refs": list(selection.focus_refs),
                    "candidate_universe_count": selection.candidate_universe_count,
                    "query_truncated": selection.query_truncated,
                    "assembly_hash": assembly_hash,
                    "conflicts_present": selection.conflicts_present,
                    "unknown_present": selection.unknown_present,
                    "reentry_mode": mode,
                    "model_candidate": model_candidate,
                    "observables": observables,
                    "semantic_access": semantic_access,
                    "authority": "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
                    "effect_authority": "NONE",
                }
                receipt_body["receipt_hash"] = h(receipt_body)
                receipt_clay = _json(receipt_body)
                self.con.execute(
                    """INSERT INTO frank_database_pulse_receipts
                      (pulse_id,pulse_index,pre_state_hash,post_state_hash,applied_delta_count,
                       backlog_after,model_call_count,tool_call_count,effect_count,source_epoch,
                       graph_epoch,semantic_generation_id,receipt_clay,created_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        pulse_id,
                        pulse_index,
                        old["state_hash"],
                        post_hash,
                        len(deltas),
                        backlog_after,
                        observables["model_call_count"],
                        0,
                        0,
                        new_source,
                        new_graph,
                        semantic_generation_id,
                        receipt_clay,
                        now,
                    ),
                )
                new_row = self._state()
                snapshot, snapshot_hash = self._snapshot(new_row)
                if snapshot_hash != post_hash:
                    raise PulseIntegrityError("V4 post-state/checkpoint hash divergence")
                self.con.execute(
                    """INSERT INTO frank_database_pulse_checkpoints
                      (checkpoint_id,pulse_id,pulse_index,snapshot_clay,state_hash,created_at)
                      VALUES(?,?,?,?,?,?)""",
                    (
                        f"checkpoint:{pulse_id}",
                        pulse_id,
                        pulse_index,
                        snapshot,
                        post_hash,
                        now,
                    ),
                )
                self.con.commit()
            except Exception:
                self.con.rollback()
                raise

            after_semantic = (
                self.ledger.epoch,
                self.ledger.semantic_state_hash,
                self.ledger.trace_root_hash,
            )
            before_semantic = (basis_epoch, semantic_hash, trace_hash)
            if after_semantic != before_semantic:
                raise PulseIntegrityError(
                    "V4 endogenous Pulse mutated authoritative StateLedger semantic state"
                )
            return PulseReceiptV4(
                pulse_id=pulse_id,
                pulse_index=pulse_index,
                basis_epoch=basis_epoch,
                semantic_state_hash=semantic_hash,
                pre_state_hash=str(old["state_hash"]),
                post_state_hash=post_hash,
                applied_delta_count=len(deltas),
                backlog_after=backlog_after,
                focus_refs=tuple(selection.focus_refs),
                candidate_refs=tuple(selection.candidate_refs),
                candidate_scores=tuple(selection.candidate_scores),
                candidate_universe_count=selection.candidate_universe_count,
                query_truncated=selection.query_truncated,
                assembly_hash=assembly_hash,
                conflicts_present=selection.conflicts_present,
                unknown_present=selection.unknown_present,
                reentry_count=truthful_reentry_count,
                model_call_count=observables["model_call_count"],
                tool_call_count=0,
                effect_count=0,
                memory_update_observed_count=memory_updates,
                state_transition_count_delta=state_delta,
                semantic_state_transition_count=0,
                graph_change_count=0,
                hypothesis_count=observables["hypothesis_count"],
                source_event_seq=int(bridge["last_event_seq"]),
                bridge_mode=str(bridge["mode"]),
                rank_index_name=INDEX_NAME,
                receipt_hash=receipt_body["receipt_hash"],
            )
        finally:
            self._reset_integrity_cache()
