from __future__ import annotations

"""Database Pulse execution plane V6.4 sparse-checkpoint/replay-recovery candidate.

V6.3 proves an explicit receipt/control transition chain but still persists a full execution-state
checkpoint for every Pulse.  That is recovery-friendly but write-heavy for idle/endogenous
Pulses.  V6.4 keeps every state transition and receipt exactly as before while retaining full
Pulse checkpoints only periodically.  A BEFORE INSERT trigger suppresses non-boundary Pulse
checkpoints inside the same transaction; control/recovery checkpoints are never suppressed.

Recovery is lineage preserving: the latest trusted execution head is deterministically replayed
from the bootstrap snapshot through the cryptographically verified Pulse/control receipt chain.
A recovery never rewinds receipted history.  After replay recovery, a fresh control checkpoint is
persisted at the trusted head so subsequent recovery need not rely on the damaged physical row.

This is a physical execution optimization only.  StateLedger remains semantic truth, RankPath
remains a separate physical optimization, and no effect authority is added.
"""

import json
from typing import Any

from research_entity.harness.reference.state_ledger import cjson, h
from research_entity.runtime.database_pulse_execution_plane_v6 import PulseV6IntegrityError
from research_entity.runtime.database_pulse_execution_plane_v6_3 import (
    DatabasePulseExecutionPlaneV6_3,
    PulseV63ControlConflict,
)


IMPLEMENTATION_ID = "database_pulse_execution_plane_v6_4_sparse_checkpoint_replay"

POLICY_SCHEMA = """
CREATE TABLE IF NOT EXISTS pulse_execution_checkpoint_policy_v6_4(
  singleton_id INTEGER PRIMARY KEY CHECK(singleton_id=1),
  pulse_interval INTEGER NOT NULL CHECK(pulse_interval>=1),
  policy_version TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_pulse_execution_v6_4_sparse_checkpoint
BEFORE INSERT ON pulse_execution_checkpoints_v6
WHEN NEW.checkpoint_id LIKE 'pulse-v6:%'
 AND (
   NEW.pulse_index % (
     SELECT pulse_interval FROM pulse_execution_checkpoint_policy_v6_4 WHERE singleton_id=1
   )
 ) != 0
BEGIN
  SELECT RAISE(IGNORE);
END;
"""


class DatabasePulseExecutionPlaneV6_4(DatabasePulseExecutionPlaneV6_3):
    """Preferred performance candidate after V6.3 continuity closure."""

    def __init__(self, *args, checkpoint_interval: int = 32, **kwargs):
        if isinstance(checkpoint_interval, bool) or not isinstance(checkpoint_interval, int):
            raise TypeError("checkpoint_interval must be int")
        if not 1 <= checkpoint_interval <= 1_000_000:
            raise ValueError("checkpoint_interval out of bounds")
        super().__init__(*args, **kwargs)
        self.con.executescript(POLICY_SCHEMA)
        row = self.con.execute(
            "SELECT pulse_interval FROM pulse_execution_checkpoint_policy_v6_4 WHERE singleton_id=1"
        ).fetchone()
        if row is None:
            with self.con:
                self.con.execute(
                    "INSERT INTO pulse_execution_checkpoint_policy_v6_4 VALUES(1,?,?)",
                    (checkpoint_interval, IMPLEMENTATION_ID),
                )
        elif int(row[0]) != checkpoint_interval:
            raise PulseV6IntegrityError(
                f"persisted V6.4 checkpoint interval {int(row[0])} != requested {checkpoint_interval}"
            )
        self.checkpoint_interval = checkpoint_interval

    def checkpoint_stats(self) -> dict[str, int]:
        total = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_checkpoints_v6"
        ).fetchone()[0])
        pulse = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_checkpoints_v6 WHERE checkpoint_id LIKE 'pulse-v6:%'"
        ).fetchone()[0])
        control = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_checkpoints_v6 WHERE checkpoint_id LIKE 'control:%'"
        ).fetchone()[0])
        return {
            "total": total,
            "pulse": pulse,
            "control": control,
            "interval": self.checkpoint_interval,
        }

    def _bootstrap_material(self) -> dict[str, Any]:
        row = self.con.execute(
            """SELECT snapshot_json,state_hash FROM pulse_execution_checkpoints_v6
               WHERE pulse_index=0 ORDER BY rowid ASC LIMIT 1"""
        ).fetchone()
        if row is None:
            raise PulseV6IntegrityError("V6.4 bootstrap checkpoint missing")
        try:
            material = json.loads(str(row["snapshot_json"]))
        except Exception as exc:
            raise PulseV6IntegrityError("V6.4 bootstrap checkpoint unreadable") from exc
        if not isinstance(material, dict) or h(material) != str(row["state_hash"]):
            raise PulseV6IntegrityError("V6.4 bootstrap checkpoint hash mismatch")
        return material

    @staticmethod
    def _apply_pulse_material(material: dict[str, Any], receipt: Any) -> dict[str, Any]:
        out = dict(material)
        out["pulse_count"] = int(receipt["pulse_index"])
        out["source_event_count"] = int(out["source_event_count"]) + int(receipt["source_event_count"])
        out["last_source_event_seq"] = int(receipt["source_event_seq_after"])
        out["source_epoch"] = int(receipt["source_epoch_after"])
        out["source_semantic_state_hash"] = str(receipt["source_semantic_state_hash_after"])
        out["last_focus_json"] = str(receipt["focus_json"])
        out["last_assembly_hash"] = str(receipt["assembly_hash"])
        return out

    def replay_trusted_head_material(self) -> dict[str, Any]:
        """Rebuild the trusted execution state without trusting the mutable current state row."""
        material = self._bootstrap_material()
        expected = h(material)
        repaired_corrupt_observations = 0
        transition_count = 0

        for log in self.con.execute(
            "SELECT * FROM pulse_execution_transition_log_v6_2 ORDER BY transition_seq"
        ):
            kind = str(log["transition_kind"])
            ref = str(log["ref_id"])
            if kind == "PULSE":
                source = self._receipt_row(ref)
                if source is None:
                    raise PulseV6IntegrityError(f"V6.4 replay missing Pulse receipt: {ref}")
                pre = str(source["pre_state_hash"])
                post = str(source["post_state_hash"])
                if pre != str(log["pre_state_hash"]) or post != str(log["post_state_hash"]):
                    raise PulseV6IntegrityError(f"V6.4 Pulse transition/log mismatch: {ref}")
                if pre != expected:
                    raise PulseV6IntegrityError(f"V6.4 Pulse chain discontinuity: {ref}")
                material = self._apply_pulse_material(material, source)
                if h(material) != post:
                    raise PulseV6IntegrityError(f"V6.4 replayed Pulse material mismatch: {ref}")
                expected = post
            elif kind == "CONTROL":
                source = self._control_row(ref)
                if source is None:
                    raise PulseV6IntegrityError(f"V6.4 replay missing control receipt: {ref}")
                pre = str(source["pre_state_hash"])
                post = str(source["post_state_hash"])
                if pre != str(log["pre_state_hash"]) or post != str(log["post_state_hash"]):
                    raise PulseV6IntegrityError(f"V6.4 control transition/log mismatch: {ref}")
                action = str(source["action"])
                if action == "SET_STATUS":
                    if pre != expected:
                        raise PulseV6IntegrityError(f"V6.4 SET_STATUS chain discontinuity: {ref}")
                    material = dict(material)
                    material["status"] = str(source["to_status"])
                    if h(material) != post:
                        raise PulseV6IntegrityError(f"V6.4 replayed SET_STATUS material mismatch: {ref}")
                    expected = post
                elif action == "RECOVER_LKG":
                    healing = (
                        pre != expected
                        and str(source["pre_integrity"]) == "CORRUPT_OR_UNVERIFIED"
                        and post == expected
                    )
                    no_op = pre == expected and post == expected
                    if not (healing or no_op):
                        raise PulseV6IntegrityError(f"V6.4 invalid recovery transition: {ref}")
                    if healing:
                        repaired_corrupt_observations += 1
                    # Trusted material is intentionally unchanged by lineage-preserving recovery.
                else:
                    raise PulseV6IntegrityError(f"V6.4 unknown control action: {action}")
            else:
                raise PulseV6IntegrityError(f"V6.4 unknown transition kind: {kind}")
            transition_count += 1

        trusted = self._trusted_transition_head_hash()
        if h(material) != trusted or expected != trusted:
            raise PulseV6IntegrityError("V6.4 replay does not terminate at trusted execution head")
        material = dict(material)
        material["_replay_transition_count"] = transition_count
        material["_repaired_corrupt_observations"] = repaired_corrupt_observations
        return material

    def recover_last_known_good(
        self,
        *,
        now: str,
        control_id: str | None = None,
    ) -> int:
        cid = control_id or f"recover:{now}"
        existing = self._control_row(cid)
        if existing is not None:
            if str(existing["action"]) != "RECOVER_LKG":
                raise PulseV63ControlConflict("control_id reused across control action classes")
            return int(existing["pulse_count"])

        replay = self.replay_trusted_head_material()
        transition_count = int(replay.pop("_replay_transition_count"))
        replay.pop("_repaired_corrupt_observations", None)
        trusted_head = h(replay)
        if trusted_head != self._trusted_transition_head_hash():
            raise PulseV6IntegrityError("V6.4 replay/trusted-head mismatch before recovery")

        raw = self._state()
        observed_pre_hash = str(raw["state_hash"])
        pre_integrity = "VERIFIED"
        try:
            self._verify_state(raw)
        except Exception:
            pre_integrity = "CORRUPT_OR_UNVERIFIED"

        from_status = str(raw["status"])
        to_status = str(replay["status"])
        checkpoint_id = f"control:{cid}:{trusted_head[:16]}"
        receipt_body = {
            "control_id": cid,
            "action": "RECOVER_LKG",
            "pulse_count": int(replay["pulse_count"]),
            "from_status": from_status,
            "to_status": to_status,
            "pre_state_hash": observed_pre_hash,
            "post_state_hash": trusted_head,
            "checkpoint_id": checkpoint_id,
            "pre_integrity": pre_integrity,
        }

        self.con.execute("BEGIN IMMEDIATE")
        try:
            raced = self._control_row(cid)
            if raced is not None:
                self.con.rollback()
                if str(raced["action"]) != "RECOVER_LKG":
                    raise PulseV63ControlConflict("concurrent control_id action mismatch")
                return int(raced["pulse_count"])
            if self._trusted_transition_head_hash() != trusted_head:
                raise PulseV6IntegrityError("trusted execution head advanced during V6.4 recovery")
            self.con.execute(
                """UPDATE pulse_execution_state_v6 SET
                   entity_id=?,lineage_id=?,status=?,pulse_count=?,source_event_count=?,
                   last_source_event_seq=?,source_epoch=?,source_semantic_state_hash=?,
                   last_focus_json=?,last_assembly_hash=?,state_hash=?,updated_at=?
                   WHERE singleton_id=1""",
                (
                    replay["entity_id"], replay["lineage_id"], replay["status"],
                    int(replay["pulse_count"]), int(replay["source_event_count"]),
                    int(replay["last_source_event_seq"]), int(replay["source_epoch"]),
                    replay["source_semantic_state_hash"], replay["last_focus_json"],
                    replay.get("last_assembly_hash"), trusted_head, now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_control_receipts_v6_2(
                   control_id,action,pulse_count,from_status,to_status,pre_state_hash,post_state_hash,
                   checkpoint_id,pre_integrity,receipt_hash,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, "RECOVER_LKG", int(replay["pulse_count"]), from_status, to_status,
                    observed_pre_hash, trusted_head, checkpoint_id, pre_integrity,
                    h(receipt_body), now,
                ),
            )
            # Control checkpoints are never suppressed by the sparse Pulse-checkpoint trigger.
            self.con.execute(
                """INSERT INTO pulse_execution_checkpoints_v6(
                   checkpoint_id,pulse_index,snapshot_json,state_hash,created_at
                ) VALUES(?,?,?,?,?)""",
                (checkpoint_id, int(replay["pulse_count"]), cjson(replay), trusted_head, now),
            )
            self.con.commit()
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise

        self._verify_state()
        verified = self.verify_execution_chain()
        if int(verified["transition_count"]) != transition_count + 1:
            raise PulseV6IntegrityError("V6.4 recovery transition count mismatch")
        return int(replay["pulse_count"])
