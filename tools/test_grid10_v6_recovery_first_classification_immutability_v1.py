#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_v6_crash_reconciliation_v1 import (
    STATUS_RECOVERY_REQUIRED,
    install_reconciliation_schema,
    prepare_cycle_intent,
)
from grid10_v6_recovery_lease_gate_v1 import (
    RecoveryLeaseNotAuthorized,
    persist_recovery_classification_with_canonical_lease,
    recovery_work_id_for_tick,
)


class RecoveryFirstClassificationImmutabilityTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "u.sqlite"
        self.tick_id = "immutability-tick"
        self.work_id = recovery_work_id_for_tick(self.tick_id)
        con = sqlite3.connect(str(self.db), isolation_level=None)
        try:
            con.executescript(
                """
                CREATE TABLE clay_work_items(
                  work_id TEXT PRIMARY KEY,
                  goal_ref TEXT NOT NULL,
                  origin_class TEXT NOT NULL,
                  created_by TEXT NOT NULL,
                  created_at TEXT NOT NULL,
                  terminal_status TEXT,
                  terminal_at TEXT
                );
                CREATE TABLE clay_work_spec_revisions(
                  work_id TEXT NOT NULL,
                  spec_rev INTEGER NOT NULL,
                  status TEXT NOT NULL,
                  PRIMARY KEY(work_id,spec_rev)
                );
                CREATE TABLE clay_work_leases(
                  lease_id TEXT PRIMARY KEY,
                  work_id TEXT NOT NULL,
                  spec_rev INTEGER NOT NULL,
                  executor_node TEXT NOT NULL,
                  lease_token TEXT NOT NULL UNIQUE,
                  claimed_at TEXT NOT NULL,
                  expires_at TEXT NOT NULL,
                  state TEXT NOT NULL
                );
                """
            )
            con.execute(
                "INSERT INTO clay_work_items VALUES(?,?,?,?,?,?,?)",
                (self.work_id, "goal", "TEST", "test", "2026-08-28T00:00:00Z", None, None),
            )
            con.execute(
                "INSERT INTO clay_work_spec_revisions VALUES(?,?,?)",
                (self.work_id, 1, "READY"),
            )
            con.execute(
                "INSERT INTO clay_work_leases VALUES(?,?,?,?,?,?,?,?)",
                (
                    "lease-id",
                    self.work_id,
                    1,
                    "worker-a",
                    "lease-token",
                    "2020-01-01T00:00:00Z",
                    "2099-01-01T00:00:00Z",
                    "RUNNING",
                ),
            )
        finally:
            con.close()

        install_reconciliation_schema(self.db)
        prepare_cycle_intent(
            self.db,
            tick_id=self.tick_id,
            agency_epoch_at_prepare=0,
            control_epoch=1,
            control_snapshot_digest="ctrl",
            prepared_ts=0.0,
        )
        con = sqlite3.connect(str(self.db), isolation_level=None)
        try:
            con.execute(
                """CREATE TABLE grid10_cognitive_cycles(
                     tick_id TEXT PRIMARY KEY,
                     agency_epoch_before INTEGER NOT NULL,
                     agency_epoch_after INTEGER NOT NULL
                   )"""
            )
            con.execute(
                "INSERT INTO grid10_cognitive_cycles VALUES(?,?,?)",
                (self.tick_id, 0, 1),
            )
        finally:
            con.close()

    def tearDown(self):
        self.td.cleanup()

    def _persist(self, terminal_ts: float):
        return persist_recovery_classification_with_canonical_lease(
            self.db,
            tick_id=self.tick_id,
            work_id=self.work_id,
            spec_rev=1,
            executor_node="worker-a",
            lease_token="lease-token",
            terminal_ts=terminal_ts,
        )

    def _stored(self):
        con = sqlite3.connect(str(self.db))
        con.row_factory = sqlite3.Row
        try:
            return dict(
                con.execute(
                    """SELECT status,terminal_ts,classification_json,classification_digest
                       FROM grid10_v6_cycle_intents WHERE tick_id=?""",
                    (self.tick_id,),
                ).fetchone()
            )
        finally:
            con.close()

    def test_second_recovery_persistence_cannot_rewrite_first_evidence(self):
        result, _proof, _digest = self._persist(1.0)
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)
        first = self._stored()
        self.assertEqual(first["status"], STATUS_RECOVERY_REQUIRED)

        with self.assertRaisesRegex(
            RecoveryLeaseNotAuthorized,
            "RECOVERY_INTENT_NOT_PREPARED:RECOVERY_REQUIRED_POST_V4_COMMIT",
        ):
            self._persist(2.0)

        second = self._stored()
        self.assertEqual(second, first)


if __name__ == "__main__":
    unittest.main()
