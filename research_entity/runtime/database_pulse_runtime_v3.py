from __future__ import annotations

"""FRANK Database Pulse Runtime V3 research candidate.

V3 fuses three independently useful research lines already present in the repository:

* U12 / DatabasePulseV0: dedicated endogenous Pulse state plane, indexed delta queue,
  atomic delta acknowledgement + receipt + last-known-good checkpoint, pause/recovery.
* Database Pulse v1: explicit re-entry controls and the hard boundary that selection/model
  output is context only and never external effect authority.
* PulseActiveFieldV2: rebuildable salience-aware projection which performs salience
  preselection before max_candidates and incrementally refreshes from StateLedger events.

Key architectural change relative to database_pulse_runtime_v2.py:
Pulse execution does NOT write pulse:latest/pulse:metrics into canonical StateLedger state.
Therefore an idle endogenous Pulse advances the dedicated Pulse/entity clock but does not
advance the authoritative semantic StateLedger epoch/hash or invalidate unrelated prepared
semantic QueryReceipts.  Pulse cognition is persisted atomically inside the U12 Pulse
state/receipt/checkpoint transaction.

Correctness is intentionally preferred over optimistic performance: V3 recomputes the
canonical StateLedger semantic/trace roots before each Pulse.  A later candidate may replace
that O(N) integrity check only with byte-equivalent incremental evidence; V3 does not weaken
fail-closed corruption detection merely to make a benchmark look faster.

This is a research candidate, not a promoted FRANK Harness component and not effect authority.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Callable, Iterable

from research_entity.harness.reference.state_ledger import StateLedger, StaleEpoch, cjson, h
from research_entity.runtime.database_pulse_active_field_v2 import (
    PROJECTION_VERSION,
    PulseActiveFieldV2,
)
from research_entity.runtime.database_pulse_v0 import (
    DatabasePulseV0,
    PulseIntegrityError,
    PulseStateError,
    PulseStaleEpochError,
    _json,
    _sha,
)


IMPLEMENTATION_ID = "database_pulse_runtime_v3_u12_active_field"
PULSE_CONTRACT = "research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md"
REENTRY_MODES = {
    "TRUTHFUL",
    "NO_REENTRY",
    "SHUFFLED_CONTROL",
    "PROVENANCE_BROKEN_CONTROL",
}
MAX_MODEL_OUTPUT_BYTES = 65536

V3_SCHEMA = r"""
CREATE TABLE IF NOT EXISTS frank_database_pulse_source_bridge_meta(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  last_event_seq INTEGER NOT NULL DEFAULT 0 CHECK(last_event_seq >= 0),
  ledger_epoch INTEGER NOT NULL DEFAULT 0 CHECK(ledger_epoch >= 0),
  semantic_state_hash TEXT NOT NULL,
  bridge_count INTEGER NOT NULL DEFAULT 0 CHECK(bridge_count >= 0),
  updated_at TEXT NOT NULL
);
"""


@dataclass(frozen=True)
class PulseReceiptV3:
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
    assembly_hash: str
    projection_refresh_mode: str
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
    receipt_hash: str
    authority: str = "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


class DatabasePulseRuntimeV3(DatabasePulseV0):
    """U12 transactional Pulse plane with active-field cognition and no semantic self-churn."""

    MAX_CANDIDATES_HARD = 512
    MAX_FOCUS_HARD = 64
    MAX_DELTAS_HARD = 4096

    def __init__(
        self,
        ledger: StateLedger,
        *,
        entity_id: str = "dr-unterweger-frank-personal-entity",
        lineage_id: str = "frank-v0.1-database-pulse-v3",
        now: str = "V3_INIT",
    ):
        self.ledger = ledger
        u12 = Path(__file__).with_name("RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql").read_text(
            encoding="utf-8"
        )
        ledger.conn.executescript(u12)
        ledger.conn.executescript(V3_SCHEMA)
        ledger.conn.commit()
        super().__init__(ledger.conn)
        self.bootstrap(entity_id=entity_id, lineage_id=lineage_id, now=now)
        self.active_field = PulseActiveFieldV2(ledger)

    def _full_ledger_integrity(self) -> dict[str, str]:
        """Byte-exact StateLedger integrity gate; deliberately full until safely optimized."""
        try:
            semantic, trace = self.ledger._roots()
        except Exception as exc:
            raise PulseIntegrityError(f"cannot recompute authoritative StateLedger roots: {exc}") from exc
        if semantic != self.ledger.semantic_state_hash:
            raise PulseIntegrityError(
                f"StateLedger semantic root mismatch expected={self.ledger.semantic_state_hash} actual={semantic}"
            )
        if trace != self.ledger.trace_root_hash:
            raise PulseIntegrityError(
                f"StateLedger trace root mismatch expected={self.ledger.trace_root_hash} actual={trace}"
            )
        return {"semantic_state_hash": semantic, "trace_root_hash": trace}

    def _bridge_meta(self):
        return self.con.execute(
            "SELECT * FROM frank_database_pulse_source_bridge_meta WHERE singleton_id=1"
        ).fetchone()

    @staticmethod
    def _source_ref(op: dict[str, Any]) -> str | None:
        domain = str(op.get("domain") or "").strip()
        key = str(op.get("key") or "").strip()
        if not domain or not key or domain in {"pulse", "pulse_control"}:
            return None
        return f"{domain}:{key}"

    def bridge_stateledger_events(
        self,
        *,
        source_domains: tuple[str, ...],
        now: str,
    ) -> dict[str, Any]:
        """Idempotently bridge authoritative semantic event deltas into the U12 hot queue.

        The bridge cursor is execution metadata, not semantic truth.  Its writes therefore do
        not advance the StateLedger semantic epoch.  Delta rows retain event/epoch/ref/hash
        provenance and U12 will acknowledge them only inside a successful Pulse transaction.
        """
        domains = tuple(dict.fromkeys(source_domains))
        if not domains:
            raise ValueError("source_domains required")
        allowed = set(domains)
        current_seq = int(
            self.con.execute("SELECT COALESCE(MAX(seq),0) FROM events").fetchone()[0]
        )
        meta = self._bridge_meta()
        after_seq = 0 if meta is None else int(meta["last_event_seq"])
        if after_seq > current_seq:
            raise PulseIntegrityError("Pulse source bridge cursor is ahead of authoritative event log")
        if meta is not None and after_seq == current_seq:
            if int(meta["ledger_epoch"]) != self.ledger.epoch:
                raise PulseIntegrityError("semantic epoch advanced without authoritative event sequence advance")
            if str(meta["semantic_state_hash"]) != self.ledger.semantic_state_hash:
                raise PulseIntegrityError("semantic root changed without authoritative event sequence advance")
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
                    domain = ref.split(":", 1)[0]
                    if domain not in allowed:
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
            old_bridge_count = 0 if meta is None else int(meta["bridge_count"])
            self.con.execute(
                """INSERT INTO frank_database_pulse_source_bridge_meta
                  (singleton_id,last_event_seq,ledger_epoch,semantic_state_hash,bridge_count,updated_at)
                  VALUES(1,?,?,?,?,?)
                  ON CONFLICT(singleton_id) DO UPDATE SET
                    last_event_seq=excluded.last_event_seq,
                    ledger_epoch=excluded.ledger_epoch,
                    semantic_state_hash=excluded.semantic_state_hash,
                    bridge_count=excluded.bridge_count,
                    updated_at=excluded.updated_at""",
                (
                    current_seq,
                    self.ledger.epoch,
                    self.ledger.semantic_state_hash,
                    old_bridge_count + 1,
                    now,
                ),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        return {
            "mode": "DELTA_BRIDGE" if meta is not None else "BOOTSTRAP_BRIDGE",
            "events_consumed": len(events),
            "admitted_deltas": admitted,
            "changed_refs": changed_refs,
            "last_event_seq": current_seq,
        }

    def _previous_cognitive_receipt(self) -> dict[str, Any] | None:
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
            receipt = json.loads(row["receipt_clay"])
        except Exception as exc:
            raise PulseIntegrityError("latest Pulse receipt is unreadable") from exc
        if not isinstance(receipt, dict):
            raise PulseIntegrityError("latest Pulse receipt body is not an object")
        if receipt.get("implementation") != IMPLEMENTATION_ID:
            return None
        supplied = receipt.get("receipt_hash")
        plain = dict(receipt)
        plain.pop("receipt_hash", None)
        if not isinstance(supplied, str) or h(plain) != supplied:
            raise PulseIntegrityError("latest V3 cognitive receipt hash mismatch")
        return receipt

    @staticmethod
    def _memory_updates(deltas: Iterable[Any]) -> int:
        return sum(1 for d in deltas if str(d["changed_ref"]).startswith("memory:"))

    def run_pulse(
        self,
        *,
        basis_epoch: int,
        source_domains: tuple[str, ...] = (
            "self", "world", "memory", "goal", "task", "semantic", "capability", "percept"
        ),
        max_candidates: int = 128,
        max_focus: int = 12,
        max_deltas: int = 32,
        reentry_mode: str = "TRUTHFUL",
        model_assistant: Callable[[dict[str, Any]], Any] | None = None,
        now: str,
        expected_source_epoch: int | None = None,
        expected_graph_epoch: int | None = None,
        fault_after_apply: bool = False,
    ) -> PulseReceiptV3:
        domains = tuple(dict.fromkeys(source_domains))
        if not domains or any(d in {"pulse", "pulse_control"} for d in domains):
            raise ValueError("source_domains must be explicit and exclude pulse domains")
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
            raise StaleEpoch(f"Pulse V3 basis {basis_epoch}!={self.ledger.epoch}")

        roots = self._full_ledger_integrity()
        semantic_hash = roots["semantic_state_hash"]
        trace_hash = roots["trace_root_hash"]
        bridge = self.bridge_stateledger_events(source_domains=domains, now=now)
        previous = self._previous_cognitive_receipt()
        previous_focus = tuple(str(x) for x in (previous or {}).get("focus_refs", ()))
        shuffle_salt = None
        if mode == "SHUFFLED_CONTROL" and previous is not None:
            shuffle_salt = h(
                {"previous_receipt_hash": previous.get("receipt_hash"), "control": "SHUFFLED"}
            )
        selection = self.active_field.select(
            source_domains=domains,
            basis_epoch=basis_epoch,
            max_candidates=max_candidates,
            max_focus=max_focus,
            reentry_mode=mode,
            previous_focus_refs=previous_focus,
            shuffle_salt=shuffle_salt,
            now=now,
        )
        if self.ledger.epoch != basis_epoch:
            raise StaleEpoch("StateLedger epoch changed during Pulse V3 candidate assembly")
        if self.ledger.semantic_state_hash != semantic_hash:
            raise StaleEpoch("StateLedger semantic root changed during Pulse V3 candidate assembly")
        if self.ledger.trace_root_hash != trace_hash:
            raise StaleEpoch("StateLedger trace root changed during Pulse V3 candidate assembly")
        if selection.semantic_state_hash != semantic_hash:
            raise PulseIntegrityError("active-field selection semantic root mismatch")

        model_output: Any = None
        model_candidate: dict[str, Any] | None = None
        if model_assistant is not None:
            context = {
                "basis_epoch": basis_epoch,
                "semantic_state_hash": semantic_hash,
                "candidate_generation": PROJECTION_VERSION,
                "focus_refs": list(selection.focus_refs),
                "selection_hash": selection.selection_hash,
                "authority": "CONTEXT_ONLY_NO_EFFECT_AUTHORITY",
            }
            model_output = model_assistant(context)
            encoded = cjson(model_output)
            if len(encoded.encode("utf-8")) > MAX_MODEL_OUTPUT_BYTES:
                raise ValueError("model candidate exceeds bounded V3 receipt size")
            model_candidate = {
                "epistemic": "UNKNOWN",
                "candidate": model_output,
                "candidate_hash": h(model_output),
                "authority": "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION",
            }

        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self.ledger.epoch != basis_epoch or self.ledger.semantic_state_hash != semantic_hash:
                raise StaleEpoch("semantic basis changed before Pulse V3 commit")
            old = self._verify_state()
            if old["status"] != "PULSING":
                raise PulseStateError(f"Pulse V3 blocked in state={old['status']}")

            semantic_head = self._semantic_head()
            if expected_source_epoch is not None and (
                semantic_head is None or int(semantic_head["source_epoch"]) != expected_source_epoch
            ):
                raise PulseStaleEpochError("semantic source epoch mismatch")
            if expected_graph_epoch is not None and (
                semantic_head is None or int(semantic_head["graph_epoch"]) != expected_graph_epoch
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
                    raise PulseIntegrityError(f"delta payload hash mismatch: {delta['delta_id']}")

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
            backlog_before = int(
                self.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue "
                    "WHERE applied_pulse_id IS NULL"
                ).fetchone()[0]
            )
            previous_focus_set = set(previous_focus)
            current_focus_set = set(selection.focus_refs)
            truthful_reentry_count = int(
                mode == "TRUTHFUL" and bool(previous_focus_set & current_focus_set)
            )
            state_delta = 1 + len(deltas)
            state_body = {
                "mode": "ACTIVE_FIELD_DELTA_DRIVEN_V3",
                "implementation": IMPLEMENTATION_ID,
                "basis_epoch": basis_epoch,
                "semantic_state_hash": semantic_hash,
                "source_event_seq": int(bridge["last_event_seq"]),
                "last_delta_ids": [str(d["delta_id"]) for d in deltas],
                "semantic_access": semantic_access,
                "backlog_before": backlog_before,
                "candidate_generation": PROJECTION_VERSION,
                "projection_refresh_mode": selection.refresh_mode,
                "projection_last_event_seq": selection.projection_last_event_seq,
                "selection_hash": selection.selection_hash,
                "focus_refs": list(selection.focus_refs),
                "candidate_refs": list(selection.candidate_refs),
                "conflicts_present": selection.conflicts_present,
                "unknown_present": selection.unknown_present,
                "reentry_mode": mode,
                "reentry_count": truthful_reentry_count,
                "model_candidate_hash": None if model_candidate is None else model_candidate["candidate_hash"],
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
                raise RuntimeError("injected V3 fault before state/receipt/checkpoint commit")

            backlog_after = int(
                self.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue "
                    "WHERE applied_pulse_id IS NULL"
                ).fetchone()[0]
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
            assembly_hash = h(
                {
                    "basis_epoch": basis_epoch,
                    "semantic_state_hash": semantic_hash,
                    "candidate_generation": PROJECTION_VERSION,
                    "selection_hash": selection.selection_hash,
                    "focus_refs": list(selection.focus_refs),
                    "source_hashes": [
                        str(
                            self.con.execute(
                                "SELECT semantic_hash FROM pulse_active_field WHERE domain=? AND k=?",
                                tuple(ref.split(":", 1)),
                            ).fetchone()[0]
                        )
                        for ref in selection.focus_refs
                    ],
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
                "schema_version": "3.0-research",
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
                "candidate_generation": PROJECTION_VERSION,
                "projection_refresh_mode": selection.refresh_mode,
                "projection_last_event_seq": selection.projection_last_event_seq,
                "selection_hash": selection.selection_hash,
                "focus_refs": list(selection.focus_refs),
                "candidate_refs": list(selection.candidate_refs),
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
                raise PulseIntegrityError("V3 post-state/checkpoint hash divergence")
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

        if self.ledger.epoch != basis_epoch:
            raise PulseIntegrityError("V3 Pulse execution mutated authoritative semantic epoch")
        if self.ledger.semantic_state_hash != semantic_hash:
            raise PulseIntegrityError("V3 Pulse execution mutated authoritative semantic root")
        if self.ledger.trace_root_hash != trace_hash:
            raise PulseIntegrityError("V3 Pulse execution mutated authoritative trace root")
        return PulseReceiptV3(
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
            assembly_hash=assembly_hash,
            projection_refresh_mode=selection.refresh_mode,
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
            receipt_hash=receipt_body["receipt_hash"],
        )
