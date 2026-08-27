"""FRANK Database Pulse v0 research candidate.

Implements the owner-fixed Database Pulse as an endogenous, delta-driven state/cognition
cycle. It is deliberately independent of continuous LLM inference: a pulse can execute
with zero model calls. UnifiedDB state/provenance remains authoritative; ClayGraph and
compiled semantic access remain rebuildable projections. Pulse receipts do not grant
external effect authority.

The hot path consumes only an indexed bounded delta queue. State, delta acknowledgements,
U10 invalidations, receipt and last-known-good checkpoint commit in one SQLite transaction.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from typing import Any


class PulseError(RuntimeError):
    pass


class PulseIntegrityError(PulseError):
    pass


class PulseStateError(PulseError):
    pass


class PulseStaleEpochError(PulseError):
    pass


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PulseReceipt:
    pulse_id: str
    pulse_index: int
    pre_state_hash: str
    post_state_hash: str
    applied_delta_count: int
    backlog_after: int
    source_epoch: int
    graph_epoch: int
    semantic_generation_id: str | None
    model_call_count: int
    tool_call_count: int
    effect_count: int


class DatabasePulseV0:
    """Bounded transactional Pulse over admitted UnifiedDB deltas."""

    def __init__(self, con: sqlite3.Connection):
        self.con = con
        self.con.row_factory = sqlite3.Row

    def _table(self, name: str) -> bool:
        return self.con.execute(
            "SELECT 1 FROM sqlite_master WHERE type IN ('table','view') AND name=?", (name,)
        ).fetchone() is not None

    def _state(self) -> sqlite3.Row:
        row = self.con.execute(
            "SELECT * FROM frank_database_pulse_state WHERE singleton_id=1"
        ).fetchone()
        if row is None:
            raise PulseStateError("pulse state not bootstrapped")
        return row

    @staticmethod
    def _material_from_mapping(row: Any) -> dict[str, Any]:
        return {
            "entity_id": row["entity_id"],
            "lineage_id": row["lineage_id"],
            "status": row["status"],
            "pulse_count": int(row["pulse_count"]),
            "state_transition_count": int(row["state_transition_count"]),
            "entity_epoch": int(row["entity_epoch"]),
            "last_applied_delta_seq": int(row["last_applied_delta_seq"]),
            "source_epoch": int(row["source_epoch"]),
            "graph_epoch": int(row["graph_epoch"]),
            "semantic_generation_id": row["semantic_generation_id"],
            "state_clay": row["state_clay"],
        }

    @classmethod
    def _state_hash(cls, row: Any) -> str:
        return _sha(_json(cls._material_from_mapping(row)))

    def _verify_state(self, row: sqlite3.Row | None = None) -> sqlite3.Row:
        row = row or self._state()
        actual = self._state_hash(row)
        if actual != row["state_hash"]:
            raise PulseIntegrityError(
                f"state hash mismatch expected={row['state_hash']} actual={actual}"
            )
        last_seq = int(row["last_applied_delta_seq"])
        orphan = self.con.execute(
            """SELECT delta_id FROM frank_database_pulse_delta_queue
               WHERE applied_pulse_id IS NULL AND seq<=? LIMIT 1""",
            (last_seq,),
        ).fetchone()
        if orphan is not None:
            raise PulseIntegrityError(
                f"queue/state boundary mismatch at unapplied delta={orphan['delta_id']}"
            )
        return row

    def _snapshot(self, row: sqlite3.Row) -> tuple[str, str]:
        material = self._material_from_mapping(row)
        text = _json(material)
        return text, _sha(text)

    def bootstrap(
        self,
        *,
        entity_id: str,
        lineage_id: str,
        source_epoch: int = 0,
        graph_epoch: int = 0,
        now: str = "BOOTSTRAP",
    ) -> None:
        if self.con.execute(
            "SELECT 1 FROM frank_database_pulse_state WHERE singleton_id=1"
        ).fetchone():
            self._verify_state()
            return
        state_clay = _json(
            {"mode": "BOOTSTRAPPED", "last_delta_ids": [], "semantic_access": "UNBOUND"}
        )
        material = {
            "entity_id": entity_id,
            "lineage_id": lineage_id,
            "status": "PULSING",
            "pulse_count": 0,
            "state_transition_count": 0,
            "entity_epoch": 0,
            "last_applied_delta_seq": 0,
            "source_epoch": source_epoch,
            "graph_epoch": graph_epoch,
            "semantic_generation_id": None,
            "state_clay": state_clay,
        }
        state_hash = _sha(_json(material))
        with self.con:
            self.con.execute(
                """INSERT INTO frank_database_pulse_state
                  (singleton_id,entity_id,lineage_id,status,pulse_count,state_transition_count,
                   entity_epoch,last_applied_delta_seq,source_epoch,graph_epoch,
                   semantic_generation_id,state_clay,state_hash,updated_at)
                  VALUES(1,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    entity_id,
                    lineage_id,
                    "PULSING",
                    0,
                    0,
                    0,
                    0,
                    source_epoch,
                    graph_epoch,
                    None,
                    state_clay,
                    state_hash,
                    now,
                ),
            )
            self.con.execute(
                """INSERT INTO frank_database_pulse_checkpoints
                  (checkpoint_id,pulse_id,pulse_index,snapshot_clay,state_hash,created_at)
                  VALUES(?,?,?,?,?,?)""",
                (f"bootstrap:{lineage_id}", None, 0, _json(material), state_hash, now),
            )

    def admit_delta(
        self,
        *,
        delta_id: str,
        changed_ref: str,
        reason_class: str,
        payload: Any,
        source_epoch: int,
        graph_epoch: int | None,
        now: str,
    ) -> bool:
        """Admit one idempotent, provenance-addressable delta."""
        payload_clay = payload if isinstance(payload, str) else _json(payload)
        payload_hash = _sha(payload_clay)
        with self.con:
            cur = self.con.execute(
                """INSERT OR IGNORE INTO frank_database_pulse_delta_queue
                  (delta_id,changed_ref,reason_class,payload_clay,payload_hash,source_epoch,
                   graph_epoch,admitted_at)
                  VALUES(?,?,?,?,?,?,?,?)""",
                (
                    delta_id,
                    changed_ref,
                    reason_class,
                    payload_clay,
                    payload_hash,
                    source_epoch,
                    graph_epoch,
                    now,
                ),
            )
        return cur.rowcount == 1

    def _semantic_head(self) -> sqlite3.Row | None:
        if not self._table("semantic_access_head"):
            return None
        return self.con.execute(
            """SELECT generation_id,source_epoch,graph_epoch,derivation_hash
               FROM semantic_access_head WHERE head_key='CURRENT'"""
        ).fetchone()

    def _publish_invalidation(self, delta: sqlite3.Row, now: str) -> None:
        """Bridge admitted changes into the U10 possibility compiler when present."""
        if not self._table("clay_possibility_invalidation_queue"):
            return
        repair_mode = (
            "FACET_ONLY"
            if str(delta["reason_class"]).upper().startswith("FACET")
            else "ANCHOR_RECOMPILE"
        )
        self.con.execute(
            """INSERT OR IGNORE INTO clay_possibility_invalidation_queue
              (invalidation_id,source_epoch,graph_epoch,changed_ref,reason_class,
               affected_anchor_refs_clay,repair_mode,evidence_refs_clay,requested_at,status)
              VALUES(?,?,?,?,?,'[]',?,'[]',?,'OPEN')""",
            (
                f"pulse:{delta['delta_id']}",
                delta["source_epoch"],
                delta["graph_epoch"],
                delta["changed_ref"],
                delta["reason_class"],
                repair_mode,
                now,
            ),
        )

    def pulse(
        self,
        *,
        max_deltas: int = 32,
        now: str,
        model_call_count: int = 0,
        tool_call_count: int = 0,
        effect_count: int = 0,
        expected_source_epoch: int | None = None,
        expected_graph_epoch: int | None = None,
        fault_after_apply: bool = False,
    ) -> PulseReceipt:
        """Execute one Pulse.

        `fault_after_apply` is an explicit test-only lesion proving that delta acknowledgement
        cannot escape the enclosing transaction before state/receipt/checkpoint publication.
        """
        if max_deltas < 0:
            raise ValueError("max_deltas must be >= 0")
        if min(model_call_count, tool_call_count, effect_count) < 0:
            raise ValueError("call/effect counts must be >= 0")

        self.con.execute("BEGIN IMMEDIATE")
        try:
            old = self._verify_state()
            if old["status"] != "PULSING":
                raise PulseStateError(f"pulse blocked in state={old['status']}")

            head = self._semantic_head()
            if expected_source_epoch is not None and (
                head is None or int(head["source_epoch"]) != expected_source_epoch
            ):
                raise PulseStaleEpochError("semantic source epoch mismatch")
            if expected_graph_epoch is not None and (
                head is None or int(head["graph_epoch"]) != expected_graph_epoch
            ):
                raise PulseStaleEpochError("semantic graph epoch mismatch")

            deltas = self.con.execute(
                """SELECT * FROM frank_database_pulse_delta_queue
                   WHERE applied_pulse_id IS NULL AND seq>?
                   ORDER BY seq LIMIT ?""",
                (int(old["last_applied_delta_seq"]), max_deltas),
            ).fetchall()
            for delta in deltas:
                if _sha(delta["payload_clay"]) != delta["payload_hash"]:
                    raise PulseIntegrityError(
                        f"delta payload hash mismatch: {delta['delta_id']}"
                    )

            new_source = max(
                [int(old["source_epoch"])] + [int(d["source_epoch"]) for d in deltas]
            )
            new_graph = max(
                [int(old["graph_epoch"])] + [int(d["graph_epoch"] or 0) for d in deltas]
            )
            semantic_generation_id: str | None = None
            semantic_access = "UNAVAILABLE"
            if head is not None:
                if (
                    int(head["source_epoch"]) == new_source
                    and int(head["graph_epoch"]) == new_graph
                ):
                    semantic_generation_id = str(head["generation_id"])
                    semantic_access = "COHERENT"
                else:
                    # Never reuse an old compiled projection across a Pulse epoch boundary.
                    semantic_access = "STALE_FAIL_CLOSED"

            pulse_index = int(old["pulse_count"]) + 1
            last_seq = int(old["last_applied_delta_seq"])
            if deltas:
                last_seq = max(int(d["seq"]) for d in deltas)
            backlog_before = int(
                self.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue WHERE applied_pulse_id IS NULL"
                ).fetchone()[0]
            )
            state_clay = _json(
                {
                    "mode": "DELTA_DRIVEN",
                    "last_delta_ids": [d["delta_id"] for d in deltas],
                    "semantic_access": semantic_access,
                    "backlog_before": backlog_before,
                }
            )
            material = {
                "entity_id": old["entity_id"],
                "lineage_id": old["lineage_id"],
                "status": "PULSING",
                "pulse_count": pulse_index,
                "state_transition_count": int(old["state_transition_count"]) + len(deltas),
                "entity_epoch": int(old["entity_epoch"]) + 1,
                "last_applied_delta_seq": last_seq,
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
                raise RuntimeError("injected fault before state/receipt commit")

            backlog_after = int(
                self.con.execute(
                    "SELECT COUNT(*) FROM frank_database_pulse_delta_queue WHERE applied_pulse_id IS NULL"
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
                    last_seq,
                    new_source,
                    new_graph,
                    semantic_generation_id,
                    state_clay,
                    post_hash,
                    now,
                ),
            )
            receipt_clay = _json(
                {
                    "delta_ids": [d["delta_id"] for d in deltas],
                    "semantic_access": semantic_access,
                    "authority": "PULSE_STATE_TRANSITION_NOT_EFFECT_AUTHORITY",
                }
            )
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
                    model_call_count,
                    tool_call_count,
                    effect_count,
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
                raise PulseIntegrityError("post-state/checkpoint hash divergence")
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
            return PulseReceipt(
                pulse_id,
                pulse_index,
                old["state_hash"],
                post_hash,
                len(deltas),
                backlog_after,
                new_source,
                new_graph,
                semantic_generation_id,
                model_call_count,
                tool_call_count,
                effect_count,
            )
        except Exception:
            self.con.rollback()
            raise

    def set_status(self, status: str, *, now: str) -> None:
        if status not in {"PULSING", "PAUSED", "DEGRADED", "QUARANTINED", "STOPPED"}:
            raise ValueError(status)
        with self.con:
            old = self._verify_state()
            material = self._material_from_mapping(old)
            material["status"] = status
            state_hash = _sha(_json(material))
            self.con.execute(
                """UPDATE frank_database_pulse_state
                   SET status=?,state_hash=?,updated_at=? WHERE singleton_id=1""",
                (status, state_hash, now),
            )

    def recover_last_known_good(self, *, now: str) -> int:
        """Restore only from the newest cryptographically self-consistent checkpoint."""
        checkpoint = self.con.execute(
            """SELECT * FROM frank_database_pulse_checkpoints
               ORDER BY pulse_index DESC,created_at DESC LIMIT 1"""
        ).fetchone()
        if checkpoint is None:
            raise PulseIntegrityError("no checkpoint")
        material = json.loads(checkpoint["snapshot_clay"])
        if _sha(_json(material)) != checkpoint["state_hash"]:
            raise PulseIntegrityError("checkpoint hash mismatch")
        with self.con:
            self.con.execute(
                """UPDATE frank_database_pulse_state SET entity_id=?,lineage_id=?,status=?,
                   pulse_count=?,state_transition_count=?,entity_epoch=?,last_applied_delta_seq=?,
                   source_epoch=?,graph_epoch=?,semantic_generation_id=?,state_clay=?,state_hash=?,
                   updated_at=? WHERE singleton_id=1""",
                (
                    material["entity_id"],
                    material["lineage_id"],
                    material["status"],
                    material["pulse_count"],
                    material["state_transition_count"],
                    material["entity_epoch"],
                    material["last_applied_delta_seq"],
                    material["source_epoch"],
                    material["graph_epoch"],
                    material["semantic_generation_id"],
                    material["state_clay"],
                    checkpoint["state_hash"],
                    now,
                ),
            )
        self._verify_state()
        return int(material["pulse_count"])
