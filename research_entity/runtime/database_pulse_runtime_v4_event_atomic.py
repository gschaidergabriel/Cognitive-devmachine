from __future__ import annotations

"""Event-atomic refinement of Database Pulse Runtime V4.

A StateLedger event is one admitted semantic transaction and may contain many ops. Mapping each
op to an independent U12 delta lets a bounded catch-up split one semantic transaction across
Pulses while `source_epoch` already advances to that event's epoch. That is incoherent.

This refinement maps exactly one authoritative StateLedger event to exactly one U12 queue delta.
All changed refs / operations are retained inside the hash-verified payload. Possibility
invalidations are expanded per changed ref only when that whole event-delta is atomically applied.
Therefore U12 source_epoch can never represent partial acknowledgement of a StateLedger epoch.

The class otherwise inherits V4's snapshot bootstrap, authoritative rank index, backlog gate,
re-entry controls, full integrity gate, atomic receipt/checkpoint publication and no-effect
boundary.
"""

import json
from typing import Any, Iterable

from research_entity.harness.reference.state_ledger import h
from research_entity.runtime.database_pulse_runtime_v4 import DatabasePulseRuntimeV4
from research_entity.runtime.database_pulse_v0 import PulseIntegrityError, _json, _sha


IMPLEMENTATION_ID_EVENT_ATOMIC = "database_pulse_runtime_v4_event_atomic"


class DatabasePulseRuntimeV4EventAtomic(DatabasePulseRuntimeV4):
    """Current preferred V4 refinement: one U12 delta per authoritative StateLedger event."""

    def bridge_stateledger_events(self, *, now: str) -> dict[str, Any]:
        current_seq = self._max_event_seq()
        meta = self._bridge_meta()
        if meta is None:
            raise PulseIntegrityError("V4 event-atomic source bridge is not anchored")
        after_seq = int(meta["last_event_seq"])
        if after_seq > current_seq:
            raise PulseIntegrityError("V4 event-atomic bridge cursor is ahead of event log")
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
        all_changed_refs: list[str] = []
        self.con.execute("BEGIN IMMEDIATE")
        try:
            for event in events:
                try:
                    ops = json.loads(event["ops_json"])
                except Exception as exc:
                    raise PulseIntegrityError(
                        f"unreadable StateLedger event ops at seq={event['seq']}: {exc}"
                    ) from exc
                changes: list[dict[str, str]] = []
                seen: set[str] = set()
                for op in ops:
                    ref = self._source_ref(op)
                    if ref is None:
                        continue
                    operation = str(op.get("op") or "CHANGE").upper()
                    changes.append({"ref": ref, "operation": operation})
                    if ref not in seen:
                        seen.add(ref)
                        all_changed_refs.append(ref)
                if not changes:
                    # Pulse/pulse_control-only semantic events intentionally do not enter the
                    # entity-level source queue, but the bridge cursor still advances past them.
                    continue
                payload = {
                    "event_seq": int(event["seq"]),
                    "event_id": str(event["event_id"]),
                    "event_epoch": int(event["epoch"]),
                    "event_semantic_state_hash": str(event["semantic_state_hash"]),
                    "changes": changes,
                    "changed_refs": list(dict.fromkeys(x["ref"] for x in changes)),
                    "atomicity": "ONE_STATELEDGER_EVENT_ONE_U12_DELTA",
                }
                payload_clay = _json(payload)
                delta_id = (
                    f"stateledger-event:{int(event['seq'])}:"
                    f"{h({'event_id': event['event_id'], 'payload': payload})[:20]}"
                )
                cur = self.con.execute(
                    """INSERT OR IGNORE INTO frank_database_pulse_delta_queue
                      (delta_id,changed_ref,reason_class,payload_clay,payload_hash,source_epoch,
                       graph_epoch,admitted_at)
                      VALUES(?,?,?,?,?,?,?,?)""",
                    (
                        delta_id,
                        f"stateledger-event:{event['event_id']}",
                        "STATELEDGER_EVENT",
                        payload_clay,
                        _sha(payload_clay),
                        int(event["epoch"]),
                        0,
                        now,
                    ),
                )
                admitted += int(cur.rowcount == 1)
            self.con.execute(
                """UPDATE frank_database_pulse_v4_bridge_meta SET
                   last_event_seq=?,ledger_epoch=?,semantic_state_hash=?,bridge_count=bridge_count+1,
                   updated_at=? WHERE singleton_id=1""",
                (current_seq, self.ledger.epoch, self.ledger.semantic_state_hash, now),
            )
            self.con.commit()
        except Exception:
            self.con.rollback()
            raise
        return {
            "mode": "EVENT_ATOMIC_DELTA_BRIDGE",
            "events_consumed": len(events),
            "admitted_deltas": admitted,
            "changed_refs": list(dict.fromkeys(all_changed_refs)),
            "last_event_seq": current_seq,
        }

    @staticmethod
    def _payload(delta) -> dict[str, Any]:
        try:
            body = json.loads(str(delta["payload_clay"]))
        except Exception as exc:
            raise PulseIntegrityError(
                f"event-atomic delta payload unreadable: {delta['delta_id']}"
            ) from exc
        if not isinstance(body, dict) or body.get("atomicity") != "ONE_STATELEDGER_EVENT_ONE_U12_DELTA":
            # Migration compatibility: legacy U12/V4 op-level deltas may still exist. Keep the
            # parent semantics for those instead of silently reinterpreting their payload.
            return {}
        changes = body.get("changes")
        if not isinstance(changes, list):
            raise PulseIntegrityError(
                f"event-atomic delta changes malformed: {delta['delta_id']}"
            )
        return body

    def _publish_invalidation(self, delta, now: str) -> None:
        body = self._payload(delta)
        if not body:
            return super()._publish_invalidation(delta, now)
        if not self._table("clay_possibility_invalidation_queue"):
            return
        changes = body["changes"]
        seen: set[tuple[str, str]] = set()
        for index, item in enumerate(changes):
            if not isinstance(item, dict):
                raise PulseIntegrityError(
                    f"event-atomic change is not object: {delta['delta_id']}"
                )
            ref = str(item.get("ref") or "")
            operation = str(item.get("operation") or "CHANGE").upper()
            if not ref or ":" not in ref:
                raise PulseIntegrityError(
                    f"event-atomic change ref malformed: {delta['delta_id']}"
                )
            dedup = (ref, operation)
            if dedup in seen:
                continue
            seen.add(dedup)
            reason = f"STATELEDGER_{operation}"
            repair_mode = "FACET_ONLY" if reason.startswith("FACET") else "ANCHOR_RECOMPILE"
            self.con.execute(
                """INSERT OR IGNORE INTO clay_possibility_invalidation_queue
                  (invalidation_id,source_epoch,graph_epoch,changed_ref,reason_class,
                   affected_anchor_refs_clay,repair_mode,evidence_refs_clay,requested_at,status)
                  VALUES(?,?,?,?,?,'[]',?,'[]',?,'OPEN')""",
                (
                    f"pulse:{delta['delta_id']}:{index}:{h({'ref':ref,'op':operation})[:12]}",
                    delta["source_epoch"],
                    delta["graph_epoch"],
                    ref,
                    reason,
                    repair_mode,
                    now,
                ),
            )

    @classmethod
    def _memory_updates(cls, deltas: Iterable[Any]) -> int:
        refs: set[str] = set()
        for delta in deltas:
            body = cls._payload(delta)
            if not body:
                if str(delta["changed_ref"]).startswith("memory:"):
                    refs.add(str(delta["changed_ref"]))
                continue
            for ref in body.get("changed_refs", ()):  # validated by bridge; re-check type lightly
                ref = str(ref)
                if ref.startswith("memory:"):
                    refs.add(ref)
        return len(refs)
