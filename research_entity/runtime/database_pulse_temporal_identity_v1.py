from __future__ import annotations

"""Atomic binding of a real Database Pulse to self.root entity identity and time orientation.

A PREPARE is only an intent. The AFTER INSERT trigger materializes entity_pulses + link receipt
inside the same SQLite transaction as the authoritative DATABASE_PULSE event. If the process
dies after PREPARE but before the event, no cognitive Pulse is fabricated.
"""

import json
import time
from dataclasses import asdict
from typing import Any

from research_entity.runtime.binary_entity_temporal_pulse_v2 import (
    BinaryEntityTemporalStore,
    StaleLease,
    TemporalOrientation,
    clock_snapshot,
    read_linux_boot_id,
    read_systemd_invocation_id,
)

PREP_SCHEMA = r'''
CREATE TABLE IF NOT EXISTS pulse_temporal_prepare(
  pulse_id TEXT PRIMARY KEY,
  entity_id TEXT NOT NULL,
  pulse_seq INTEGER NOT NULL,
  basis_epoch INTEGER NOT NULL,
  lease_id TEXT NOT NULL,
  lease_epoch INTEGER NOT NULL,
  observed_at_utc_ns INTEGER NOT NULL,
  boottime_ns INTEGER NOT NULL,
  monotonic_ns INTEGER NOT NULL,
  host_id TEXT NOT NULL,
  boot_id TEXT NOT NULL,
  invocation_id TEXT NOT NULL,
  orientation_json TEXT NOT NULL,
  status TEXT NOT NULL CHECK(status IN ('PREPARED','COMMITTED','ABORTED_RECOVERED')),
  committed_event_id TEXT,
  committed_event_epoch INTEGER,
  prepared_at_utc_ns INTEGER NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS ux_pulse_temporal_live_seq
  ON pulse_temporal_prepare(entity_id,pulse_seq)
  WHERE status IN ('PREPARED','COMMITTED');
CREATE TABLE IF NOT EXISTS pulse_temporal_links(
  pulse_id TEXT PRIMARY KEY,
  event_id TEXT NOT NULL UNIQUE,
  event_epoch INTEGER NOT NULL,
  entity_id TEXT NOT NULL,
  pulse_seq INTEGER NOT NULL,
  orientation_json TEXT NOT NULL,
  linked_at_utc_ns INTEGER NOT NULL
);
DROP TRIGGER IF EXISTS database_pulse_requires_temporal_prepare;
CREATE TRIGGER database_pulse_requires_temporal_prepare
BEFORE INSERT ON events
WHEN NEW.event_type='DATABASE_PULSE'
BEGIN
  SELECT CASE WHEN NOT EXISTS(
    SELECT 1 FROM pulse_temporal_prepare p
    JOIN entity_runtime_lease l ON l.entity_id=p.entity_id
    WHERE p.pulse_id=substr(NEW.event_id,length('database-pulse:')+1)
      AND p.status='PREPARED'
      AND p.basis_epoch=NEW.base_epoch
      AND l.active=1
      AND l.lease_id=p.lease_id
      AND l.lease_epoch=p.lease_epoch
      AND l.host_id=p.host_id
      AND l.boot_id=p.boot_id
      AND l.invocation_id=p.invocation_id
  ) THEN RAISE(ABORT,'DATABASE_PULSE_REQUIRES_CURRENT_TEMPORAL_ENTITY_PREPARE') END;
END;
DROP TRIGGER IF EXISTS database_pulse_commits_temporal_prepare;
CREATE TRIGGER database_pulse_commits_temporal_prepare
AFTER INSERT ON events
WHEN NEW.event_type='DATABASE_PULSE'
BEGIN
  INSERT INTO entity_pulses(
    entity_id,pulse_seq,pulse_id,event_id,event_epoch,lease_id,lease_epoch,
    observed_at_utc_ns,boottime_ns,monotonic_ns,host_id,boot_id,invocation_id,entity_age_ns,
    wall_gap_ns,boottime_gap_ns,monotonic_gap_ns,inferred_suspend_ns,gap_class,
    missed_logical_slots,clock_confidence,continuity_class)
  SELECT p.entity_id,p.pulse_seq,p.pulse_id,NEW.event_id,NEW.epoch,p.lease_id,p.lease_epoch,
         p.observed_at_utc_ns,p.boottime_ns,p.monotonic_ns,p.host_id,p.boot_id,p.invocation_id,
         json_extract(p.orientation_json,'$.entity_age_ns'),
         json_extract(p.orientation_json,'$.wall_gap_ns'),
         json_extract(p.orientation_json,'$.boottime_gap_ns'),
         json_extract(p.orientation_json,'$.monotonic_gap_ns'),
         json_extract(p.orientation_json,'$.inferred_suspend_ns'),
         json_extract(p.orientation_json,'$.gap_class'),
         json_extract(p.orientation_json,'$.missed_logical_slots'),
         json_extract(p.orientation_json,'$.clock_confidence'),
         json_extract(p.orientation_json,'$.continuity_class')
  FROM pulse_temporal_prepare p
  WHERE p.pulse_id=substr(NEW.event_id,length('database-pulse:')+1)
    AND p.status='PREPARED';

  INSERT INTO pulse_temporal_links(
    pulse_id,event_id,event_epoch,entity_id,pulse_seq,orientation_json,linked_at_utc_ns)
  SELECT p.pulse_id,NEW.event_id,NEW.epoch,p.entity_id,p.pulse_seq,p.orientation_json,
         CAST(strftime('%s','now') AS INTEGER)*1000000000
  FROM pulse_temporal_prepare p
  WHERE p.pulse_id=substr(NEW.event_id,length('database-pulse:')+1)
    AND p.status='PREPARED';

  UPDATE pulse_temporal_prepare
  SET status='COMMITTED',committed_event_id=NEW.event_id,committed_event_epoch=NEW.epoch
  WHERE pulse_id=substr(NEW.event_id,length('database-pulse:')+1)
    AND status='PREPARED';
END;
'''


class TemporalPulseBinder:
    def __init__(self, ledger):
        self.ledger = ledger
        self.conn = ledger.conn
        self.store = BinaryEntityTemporalStore(self.conn)
        self.conn.executescript(PREP_SCHEMA)

    def prepare(
        self,
        *,
        entity_id: str,
        pulse_id: str,
        basis_epoch: int,
        lease_id: str,
        interval_ns: int,
        utc_ns: int | None = None,
        boottime_ns: int | None = None,
        monotonic_ns: int | None = None,
        boot_id: str | None = None,
        invocation_id: str | None = None,
    ) -> TemporalOrientation:
        existing = self.conn.execute(
            "SELECT * FROM pulse_temporal_prepare WHERE pulse_id=?", (pulse_id,)
        ).fetchone()
        if existing:
            if (
                int(existing["basis_epoch"]) != int(basis_epoch)
                or existing["entity_id"] != entity_id
                or existing["lease_id"] != lease_id
            ):
                raise RuntimeError("pulse id replay conflicts with original temporal identity/basis")
            if existing["status"] in {"COMMITTED", "PREPARED"}:
                return TemporalOrientation(**json.loads(existing["orientation_json"]))
            raise RuntimeError("pulse id was aborted; mint new pulse id")

        if basis_epoch != self.ledger.epoch:
            raise ValueError("stale pulse basis")
        current = clock_snapshot()
        utc_ns = current["utc_ns"] if utc_ns is None else utc_ns
        boottime_ns = current["boottime_ns"] if boottime_ns is None else boottime_ns
        monotonic_ns = current["monotonic_ns"] if monotonic_ns is None else monotonic_ns
        boot_id = boot_id or read_linux_boot_id()
        invocation_id = invocation_id or read_systemd_invocation_id()

        self.conn.execute("BEGIN IMMEDIATE")
        try:
            inflight = self.conn.execute(
                "SELECT pulse_id FROM pulse_temporal_prepare "
                "WHERE entity_id=? AND status='PREPARED'",
                (entity_id,),
            ).fetchone()
            if inflight:
                raise RuntimeError(f"entity already has prepared pulse {inflight[0]}")
            orientation = self.store.preview_orientation(
                entity_id,
                pulse_id=pulse_id,
                lease_id=lease_id,
                interval_ns=interval_ns,
                utc_ns=utc_ns,
                boottime_ns=boottime_ns,
                monotonic_ns=monotonic_ns,
                boot_id=boot_id,
                invocation_id=invocation_id,
            )
            self.conn.execute(
                "INSERT INTO pulse_temporal_prepare VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    pulse_id,
                    entity_id,
                    orientation.pulse_seq,
                    basis_epoch,
                    lease_id,
                    orientation.lease_epoch,
                    utc_ns,
                    boottime_ns,
                    monotonic_ns,
                    orientation.host_id,
                    boot_id,
                    invocation_id,
                    json.dumps(asdict(orientation), sort_keys=True, separators=(",", ":")),
                    "PREPARED",
                    None,
                    None,
                    time.time_ns(),
                ),
            )
            self.conn.execute("COMMIT")
            return orientation
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def recover_stale_prepared(self, entity_id: str, *, current_lease_id: str) -> int:
        current = self.store.current_lease(entity_id)
        if not current or current["lease_id"] != current_lease_id:
            raise StaleLease("current lease mismatch")
        self.conn.execute("BEGIN IMMEDIATE")
        try:
            count = self.conn.execute(
                "UPDATE pulse_temporal_prepare SET status='ABORTED_RECOVERED' "
                "WHERE entity_id=? AND status='PREPARED' AND lease_id<>?",
                (entity_id, current_lease_id),
            ).rowcount
            self.conn.execute("COMMIT")
            return count
        except Exception:
            self.conn.execute("ROLLBACK")
            raise

    def link(self, pulse_id: str) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM pulse_temporal_links WHERE pulse_id=?", (pulse_id,)
        ).fetchone()
        return dict(row) if row else None


class TemporalDatabasePulseRuntimeV6:
    """Composition wrapper: time/entity orientation is mandatory prebound Pulse context."""

    def __init__(
        self,
        base_runtime,
        *,
        entity_id: str,
        lease_id: str,
        interval_ns: int = 1_000_000_000,
    ):
        self.base = base_runtime
        self.ledger = base_runtime.ledger
        self.entity_id = entity_id
        self.lease_id = lease_id
        self.interval_ns = interval_ns
        self.binder = TemporalPulseBinder(self.ledger)

    def run_pulse(
        self,
        spec,
        *,
        writer: str = "database-pulse-runtime-v6-temporal",
        model_assistant=None,
        committed_at=None,
        clock_override: dict[str, Any] | None = None,
    ):
        override = clock_override or {}
        orientation = self.binder.prepare(
            entity_id=self.entity_id,
            pulse_id=spec.pulse_id,
            basis_epoch=spec.basis_epoch,
            lease_id=self.lease_id,
            interval_ns=self.interval_ns,
            utc_ns=override.get("utc_ns"),
            boottime_ns=override.get("boottime_ns"),
            monotonic_ns=override.get("monotonic_ns"),
            boot_id=override.get("boot_id"),
            invocation_id=override.get("invocation_id"),
        )

        wrapped = None
        if model_assistant is not None:
            def wrapped(context):
                return model_assistant(
                    {
                        **context,
                        "mandatory_context": {
                            "temporal_orientation": asdict(orientation),
                            "identity_lineage_relations": self.binder.store.lineage_relations(
                                self.entity_id
                            ),
                            "epistemic_law": (
                                "missed_logical_slots_are_not_materialized_cognitive_pulses"
                            ),
                        },
                    }
                )

        receipt = self.base.run_pulse(
            spec,
            writer=writer,
            model_assistant=wrapped,
            committed_at=committed_at,
        )
        link = self.binder.link(spec.pulse_id)
        if not link:
            raise RuntimeError("pulse committed without atomic temporal link")
        return {
            "pulse_receipt": receipt,
            "temporal_orientation": asdict(orientation),
            "temporal_link": link,
        }
