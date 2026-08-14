from __future__ import annotations

"""Database Pulse execution plane V6.3 lineage-preserving recovery hardening.

V6.2 adds a total-order transition journal.  V6.3 tightens two corner cases:

* control ids are true idempotency keys: reusing one for a different control action/status is a
  conflict, never a silent success;
* automatic LKG recovery may restore only the latest trusted transition-head state hash.  It may
  repair corrupted physical state, including a corrupted stored state_hash, but it may not
  silently rewind already receipted execution history.  Rewinding requires an explicit future
  fork/new-lineage protocol.

The transition verifier recognizes exactly one discontinuity class: a RECOVER_LKG receipt whose
pre-state was explicitly marked corrupt/unverified and whose post-state restores the already
trusted head hash.  The damaged observation remains visible in the control receipt.
"""

import json
from typing import Any

from research_entity.harness.reference.state_ledger import cjson, h
from research_entity.runtime.database_pulse_execution_plane_v6 import PulseV6IntegrityError
from research_entity.runtime.database_pulse_execution_plane_v6_2 import (
    DatabasePulseExecutionPlaneV6_2,
)


IMPLEMENTATION_ID = "database_pulse_execution_plane_v6_3_lineage_preserving_recovery"


class PulseV63ControlConflict(PulseV6IntegrityError):
    pass


class DatabasePulseExecutionPlaneV6_3(DatabasePulseExecutionPlaneV6_2):
    """Preferred V6 tip: complete control trace + strict lineage-preserving recovery."""

    def _trusted_transition_head_hash(self) -> str:
        row = self.con.execute(
            """SELECT post_state_hash FROM pulse_execution_transition_log_v6_2
               ORDER BY transition_seq DESC LIMIT 1"""
        ).fetchone()
        return self._bootstrap_state_hash() if row is None else str(row[0])

    def set_status(self, status: str, *, now: str, control_id: str | None = None) -> None:
        if status not in {"PULSING", "PAUSED", "STOPPED", "QUARANTINED"}:
            raise ValueError(status)
        cid = control_id or f"status:{status}:{now}"
        existing = self._control_row(cid)
        if existing is not None:
            if str(existing["action"]) != "SET_STATUS" or str(existing["to_status"]) != status:
                raise PulseV63ControlConflict("control_id reused with different SET_STATUS semantics")
            return
        super().set_status(status, now=now, control_id=cid)

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

        trusted_head = self._trusted_transition_head_hash()
        raw = self._state()
        observed_pre_hash = str(raw["state_hash"])
        pre_integrity = "VERIFIED"
        try:
            self._verify_state(raw)
        except Exception:
            pre_integrity = "CORRUPT_OR_UNVERIFIED"

        chosen = None
        for checkpoint in self.con.execute(
            """SELECT * FROM pulse_execution_checkpoints_v6
               WHERE state_hash=? ORDER BY pulse_index DESC,rowid DESC""",
            (trusted_head,),
        ):
            try:
                material = json.loads(str(checkpoint["snapshot_json"]))
            except Exception:
                continue
            if not isinstance(material, dict) or h(material) != trusted_head:
                continue
            cursor = int(material.get("last_source_event_seq", -1))
            source_epoch = int(material.get("source_epoch", -1))
            source_hash = str(material.get("source_semantic_state_hash", ""))
            if cursor < 0 or cursor > self._max_event_seq() or source_epoch < 0 or source_epoch > self.ledger.epoch:
                continue
            if cursor > 0:
                event = self._event_at_seq(cursor)
                if event is None:
                    continue
                if int(event["epoch"]) != source_epoch or str(event["semantic_state_hash"]) != source_hash:
                    continue
            elif source_epoch != 0 and cursor == 0:
                # A non-genesis semantic source must have a concrete event boundary.
                continue
            chosen = (checkpoint, material)
            break
        if chosen is None:
            raise PulseV6IntegrityError(
                "no valid checkpoint for latest trusted execution head; automatic rewind forbidden"
            )

        checkpoint, material = chosen
        checkpoint_id = str(checkpoint["checkpoint_id"])
        from_status = str(raw["status"])
        to_status = str(material["status"])
        receipt_body = {
            "control_id": cid,
            "action": "RECOVER_LKG",
            "pulse_count": int(material["pulse_count"]),
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
            # The trusted transition head may not move between selection and recovery commit.
            if self._trusted_transition_head_hash() != trusted_head:
                raise PulseV6IntegrityError("trusted execution head advanced during recovery")
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
                    material.get("last_assembly_hash"), trusted_head, now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_control_receipts_v6_2(
                   control_id,action,pulse_count,from_status,to_status,pre_state_hash,post_state_hash,
                   checkpoint_id,pre_integrity,receipt_hash,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, "RECOVER_LKG", int(material["pulse_count"]), from_status, to_status,
                    observed_pre_hash, trusted_head, checkpoint_id, pre_integrity,
                    h(receipt_body), now,
                ),
            )
            self.con.commit()
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise
        self._verify_state()
        self.verify_execution_chain()
        return int(material["pulse_count"])

    def verify_execution_chain(self) -> dict[str, Any]:
        expected = self._bootstrap_state_hash()
        checked = 0
        repaired_corrupt_observations = 0
        for log in self.con.execute(
            "SELECT * FROM pulse_execution_transition_log_v6_2 ORDER BY transition_seq"
        ):
            kind = str(log["transition_kind"])
            ref = str(log["ref_id"])
            control = None
            if kind == "PULSE":
                source = self._receipt_row(ref)
                if source is None:
                    raise PulseV6IntegrityError(f"transition references missing Pulse receipt: {ref}")
                pre = str(source["pre_state_hash"]); post = str(source["post_state_hash"])
            elif kind == "CONTROL":
                control = self._control_row(ref)
                if control is None:
                    raise PulseV6IntegrityError(f"transition references missing control receipt: {ref}")
                pre = str(control["pre_state_hash"]); post = str(control["post_state_hash"])
            else:
                raise PulseV6IntegrityError(f"unknown transition kind: {kind}")
            if pre != str(log["pre_state_hash"]) or post != str(log["post_state_hash"]):
                raise PulseV6IntegrityError(f"transition/source receipt mismatch: {ref}")

            if pre != expected:
                healing_recovery = (
                    control is not None
                    and str(control["action"]) == "RECOVER_LKG"
                    and str(control["pre_integrity"]) == "CORRUPT_OR_UNVERIFIED"
                    and post == expected
                )
                if not healing_recovery:
                    raise PulseV6IntegrityError(
                        f"execution transition chain discontinuity at seq={log['transition_seq']} ref={ref}"
                    )
                repaired_corrupt_observations += 1
            expected = post
            checked += 1

        current = self._verify_state()
        if expected != str(current["state_hash"]):
            raise PulseV6IntegrityError("execution transition chain does not terminate at current state")
        pulse_receipts = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_receipts_v6"
        ).fetchone()[0])
        control_receipts = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_control_receipts_v6_2"
        ).fetchone()[0])
        if checked != pulse_receipts + control_receipts:
            raise PulseV6IntegrityError("execution transition log cardinality mismatch")
        return {
            "pass": True,
            "transition_count": checked,
            "pulse_receipts": pulse_receipts,
            "control_receipts": control_receipts,
            "repaired_corrupt_observations": repaired_corrupt_observations,
            "bootstrap_state_hash": self._bootstrap_state_hash(),
            "current_state_hash": str(current["state_hash"]),
            "authority": "EXECUTION_CONTINUITY_VERIFICATION_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY",
        }
