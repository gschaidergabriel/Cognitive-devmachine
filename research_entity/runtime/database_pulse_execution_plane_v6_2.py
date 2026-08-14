from __future__ import annotations

"""Database Pulse execution plane V6.2 control/recovery journal hardening.

V6/V6.1 atomically receipt cognitive/catch-up transitions, but control transitions such as
PAUSED->PULSING and last-known-good recovery also mutate the physical execution state.  V6.2
makes those state transitions durable and auditable without placing them in semantic StateLedger.

A SQLite AFTER INSERT trigger mirrors every V6 Pulse receipt into one total-order transition log
inside the same transaction as the Pulse receipt.  V6.2 control receipts use a second trigger
into the same log.  This avoids duplicating the V6 commit implementation while preserving
transaction atomicity.  Python verification re-hashes the authoritative source receipts and
checks pre/post state-hash continuity from the bootstrap checkpoint to current execution state.

No semantic truth or external effect authority is added.
"""

import json
from typing import Any

from research_entity.harness.reference.state_ledger import cjson, h
from research_entity.runtime.database_pulse_execution_plane_v6 import PulseV6IntegrityError
from research_entity.runtime.database_pulse_execution_plane_v6_1 import (
    DatabasePulseExecutionPlaneV6_1,
)


IMPLEMENTATION_ID = "database_pulse_execution_plane_v6_2_control_journal"

CONTROL_SCHEMA = """
CREATE TABLE IF NOT EXISTS pulse_execution_control_receipts_v6_2(
  control_id TEXT PRIMARY KEY,
  action TEXT NOT NULL CHECK(action IN ('SET_STATUS','RECOVER_LKG')),
  pulse_count INTEGER NOT NULL CHECK(pulse_count>=0),
  from_status TEXT,
  to_status TEXT NOT NULL,
  pre_state_hash TEXT NOT NULL,
  post_state_hash TEXT NOT NULL,
  checkpoint_id TEXT,
  pre_integrity TEXT NOT NULL,
  receipt_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pulse_execution_transition_log_v6_2(
  transition_seq INTEGER PRIMARY KEY AUTOINCREMENT,
  transition_kind TEXT NOT NULL CHECK(transition_kind IN ('PULSE','CONTROL')),
  ref_id TEXT NOT NULL UNIQUE,
  pre_state_hash TEXT NOT NULL,
  post_state_hash TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TRIGGER IF NOT EXISTS trg_pulse_execution_v6_2_from_pulse_receipt
AFTER INSERT ON pulse_execution_receipts_v6
BEGIN
  INSERT INTO pulse_execution_transition_log_v6_2(
    transition_kind,ref_id,pre_state_hash,post_state_hash,created_at
  ) VALUES(
    'PULSE',NEW.invocation_id,NEW.pre_state_hash,NEW.post_state_hash,NEW.created_at
  );
END;

CREATE TRIGGER IF NOT EXISTS trg_pulse_execution_v6_2_from_control_receipt
AFTER INSERT ON pulse_execution_control_receipts_v6_2
BEGIN
  INSERT INTO pulse_execution_transition_log_v6_2(
    transition_kind,ref_id,pre_state_hash,post_state_hash,created_at
  ) VALUES(
    'CONTROL',NEW.control_id,NEW.pre_state_hash,NEW.post_state_hash,NEW.created_at
  );
END;
"""


class DatabasePulseExecutionPlaneV6_2(DatabasePulseExecutionPlaneV6_1):
    """Preferred V6 tip with total-order execution transition evidence."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.con.executescript(CONTROL_SCHEMA)
        self.con.commit()
        self._adopt_or_verify_transition_log()

    def _bootstrap_state_hash(self) -> str:
        row = self.con.execute(
            """SELECT state_hash FROM pulse_execution_checkpoints_v6
               WHERE pulse_index=0 ORDER BY rowid ASC LIMIT 1"""
        ).fetchone()
        if row is None:
            raise PulseV6IntegrityError("V6.2 bootstrap checkpoint missing")
        return str(row["state_hash"])

    @staticmethod
    def _control_body(row: Any) -> dict[str, Any]:
        return {
            "control_id": str(row["control_id"]),
            "action": str(row["action"]),
            "pulse_count": int(row["pulse_count"]),
            "from_status": row["from_status"],
            "to_status": str(row["to_status"]),
            "pre_state_hash": str(row["pre_state_hash"]),
            "post_state_hash": str(row["post_state_hash"]),
            "checkpoint_id": row["checkpoint_id"],
            "pre_integrity": str(row["pre_integrity"]),
        }

    def _control_row(self, control_id: str):
        row = self.con.execute(
            "SELECT * FROM pulse_execution_control_receipts_v6_2 WHERE control_id=?",
            (control_id,),
        ).fetchone()
        if row is None:
            return None
        if h(self._control_body(row)) != str(row["receipt_hash"]):
            raise PulseV6IntegrityError(f"V6.2 control receipt hash mismatch: {control_id}")
        return row

    def _adopt_or_verify_transition_log(self) -> None:
        pulse_count = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_receipts_v6"
        ).fetchone()[0])
        control_count = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_control_receipts_v6_2"
        ).fetchone()[0])
        log_count = int(self.con.execute(
            "SELECT COUNT(*) FROM pulse_execution_transition_log_v6_2"
        ).fetchone()[0])
        if log_count == pulse_count + control_count:
            self.verify_execution_chain()
            return
        if log_count != 0 or control_count != 0:
            raise PulseV6IntegrityError("partial V6.2 transition log cannot be auto-adopted")
        if pulse_count:
            # Existing V6/V6.1 lineage can be adopted only when no unreceipted control transition
            # is visible: receipt post hashes must already form a complete chain to current state.
            rows = list(self.con.execute(
                "SELECT * FROM pulse_execution_receipts_v6 ORDER BY pulse_index"
            ))
            expected = self._bootstrap_state_hash()
            for row in rows:
                validated = self._receipt_row(str(row["invocation_id"]))
                if validated is None or str(row["pre_state_hash"]) != expected:
                    raise PulseV6IntegrityError(
                        "existing V6 lineage has a control/recovery gap; explicit migration required"
                    )
                expected = str(row["post_state_hash"])
            if expected != str(self._verify_state()["state_hash"]):
                raise PulseV6IntegrityError(
                    "existing V6 lineage does not terminate at current execution state"
                )
            self.con.execute("BEGIN IMMEDIATE")
            try:
                for row in rows:
                    self.con.execute(
                        """INSERT INTO pulse_execution_transition_log_v6_2(
                           transition_kind,ref_id,pre_state_hash,post_state_hash,created_at
                        ) VALUES('PULSE',?,?,?,?,?)""".replace("VALUES('PULSE',?,?,?,?,?)", "VALUES('PULSE',?,?,?,?)"),
                        (
                            str(row["invocation_id"]), str(row["pre_state_hash"]),
                            str(row["post_state_hash"]), str(row["created_at"]),
                        ),
                    )
                self.con.commit()
            except Exception:
                self.con.rollback(); raise
        self.verify_execution_chain()

    def set_status(self, status: str, *, now: str, control_id: str | None = None) -> None:
        if status not in {"PULSING", "PAUSED", "STOPPED", "QUARANTINED"}:
            raise ValueError(status)
        cid = control_id or f"status:{status}:{now}"
        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self._control_row(cid) is not None:
                self.con.rollback(); return
            row = self._verify_state()
            pre_hash = str(row["state_hash"])
            material = self._state_material(row)
            from_status = str(material["status"])
            material["status"] = status
            post_hash = h(material)
            checkpoint_id = f"control:{cid}:{post_hash[:16]}"
            body = {
                "control_id": cid,
                "action": "SET_STATUS",
                "pulse_count": int(material["pulse_count"]),
                "from_status": from_status,
                "to_status": status,
                "pre_state_hash": pre_hash,
                "post_state_hash": post_hash,
                "checkpoint_id": checkpoint_id,
                "pre_integrity": "VERIFIED",
            }
            self.con.execute(
                """UPDATE pulse_execution_state_v6 SET status=?,state_hash=?,updated_at=?
                   WHERE singleton_id=1""",
                (status, post_hash, now),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_control_receipts_v6_2(
                   control_id,action,pulse_count,from_status,to_status,pre_state_hash,post_state_hash,
                   checkpoint_id,pre_integrity,receipt_hash,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, "SET_STATUS", int(material["pulse_count"]), from_status, status,
                    pre_hash, post_hash, checkpoint_id, "VERIFIED", h(body), now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_checkpoints_v6(
                   checkpoint_id,pulse_index,snapshot_json,state_hash,created_at
                ) VALUES(?,?,?,?,?)""",
                (checkpoint_id, int(material["pulse_count"]), cjson(material), post_hash, now),
            )
            self.con.commit()
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise
        self.verify_execution_chain()

    def recover_last_known_good(
        self,
        *,
        now: str,
        control_id: str | None = None,
    ) -> int:
        cid = control_id or f"recover:{now}"
        existing = self._control_row(cid)
        if existing is not None:
            return int(existing["pulse_count"])

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
               ORDER BY pulse_index DESC,rowid DESC"""
        ):
            try:
                material = json.loads(str(checkpoint["snapshot_json"]))
            except Exception:
                continue
            if not isinstance(material, dict):
                continue
            if h(material) != str(checkpoint["state_hash"]):
                continue
            cursor = int(material.get("last_source_event_seq", -1))
            source_epoch = int(material.get("source_epoch", -1))
            source_hash = str(material.get("source_semantic_state_hash", ""))
            if cursor < 0 or cursor > self._max_event_seq() or source_epoch < 0 or source_epoch > self.ledger.epoch:
                continue
            if cursor > 0:
                event = self._event_at_seq(cursor)
                if event is None or int(event["epoch"]) != source_epoch or str(event["semantic_state_hash"]) != source_hash:
                    continue
            chosen = (checkpoint, material)
            break
        if chosen is None:
            raise PulseV6IntegrityError("no cryptographically/source-coherent V6 checkpoint")
        checkpoint, material = chosen
        target_hash = str(checkpoint["state_hash"])
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
            "post_state_hash": target_hash,
            "checkpoint_id": checkpoint_id,
            "pre_integrity": pre_integrity,
        }

        self.con.execute("BEGIN IMMEDIATE")
        try:
            if self._control_row(cid) is not None:
                self.con.rollback()
                return int(material["pulse_count"])
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
                    material.get("last_assembly_hash"), target_hash, now,
                ),
            )
            self.con.execute(
                """INSERT INTO pulse_execution_control_receipts_v6_2(
                   control_id,action,pulse_count,from_status,to_status,pre_state_hash,post_state_hash,
                   checkpoint_id,pre_integrity,receipt_hash,created_at
                ) VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    cid, "RECOVER_LKG", int(material["pulse_count"]), from_status, to_status,
                    observed_pre_hash, target_hash, checkpoint_id, pre_integrity,
                    h(receipt_body), now,
                ),
            )
            self.con.commit()
        except Exception:
            if self.con.in_transaction:
                self.con.rollback()
            raise
        self._verify_state()
        # If the corruption did not alter the stored state_hash, the recovery transition remains
        # chain-contiguous.  If the state_hash itself was corrupted, verification intentionally
        # reports a discontinuity instead of hiding the damaged observation.
        if pre_integrity == "VERIFIED" or observed_pre_hash == self._previous_transition_post_hash():
            self.verify_execution_chain()
        return int(material["pulse_count"])

    def _previous_transition_post_hash(self) -> str | None:
        row = self.con.execute(
            """SELECT post_state_hash FROM pulse_execution_transition_log_v6_2
               ORDER BY transition_seq DESC LIMIT 1 OFFSET 1"""
        ).fetchone()
        return None if row is None else str(row[0])

    def verify_execution_chain(self) -> dict[str, Any]:
        expected = self._bootstrap_state_hash()
        checked = 0
        for log in self.con.execute(
            "SELECT * FROM pulse_execution_transition_log_v6_2 ORDER BY transition_seq"
        ):
            kind = str(log["transition_kind"])
            ref = str(log["ref_id"])
            if kind == "PULSE":
                source = self._receipt_row(ref)
                if source is None:
                    raise PulseV6IntegrityError(f"transition references missing Pulse receipt: {ref}")
                pre = str(source["pre_state_hash"]); post = str(source["post_state_hash"])
            elif kind == "CONTROL":
                source = self._control_row(ref)
                if source is None:
                    raise PulseV6IntegrityError(f"transition references missing control receipt: {ref}")
                pre = str(source["pre_state_hash"]); post = str(source["post_state_hash"])
            else:
                raise PulseV6IntegrityError(f"unknown transition kind: {kind}")
            if pre != str(log["pre_state_hash"]) or post != str(log["post_state_hash"]):
                raise PulseV6IntegrityError(f"transition/source receipt mismatch: {ref}")
            if pre != expected:
                raise PulseV6IntegrityError(
                    f"execution transition chain discontinuity at seq={log['transition_seq']} ref={ref}"
                )
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
            "bootstrap_state_hash": self._bootstrap_state_hash(),
            "current_state_hash": str(current["state_hash"]),
            "authority": "EXECUTION_CONTINUITY_VERIFICATION_ONLY_NO_SEMANTIC_OR_EFFECT_AUTHORITY",
        }
