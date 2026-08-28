#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from grid10_v6_recovery_lease_gate_v1 import (
    RecoveryLeaseNotAuthorized,
    recovery_work_id_for_tick,
    verify_active_recovery_lease_in_transaction,
)


NOW = "2026-08-28T12:30:00Z"


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(str(path), isolation_level=None)
    con.row_factory = sqlite3.Row
    return con


def _install_work_fabric(path: Path) -> None:
    con = _connect(path)
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
    finally:
        con.close()


def _seed(
    path: Path,
    *,
    tick_id: str = "t1",
    spec_rev: int = 1,
    executor: str = "worker-a",
    token: str = "lease-a",
    state: str = "RUNNING",
    claimed_at: str = "2026-08-28T12:00:00Z",
    expires_at: str = "2026-08-28T13:00:00Z",
    terminal_status=None,
    spec_status: str = "READY",
):
    work_id = recovery_work_id_for_tick(tick_id)
    con = _connect(path)
    try:
        con.execute(
            "INSERT INTO clay_work_items VALUES(?,?,?,?,?,?,?)",
            (work_id, "goal", "TEST", "test", NOW, terminal_status, None),
        )
        con.execute(
            "INSERT INTO clay_work_spec_revisions VALUES(?,?,?)",
            (work_id, spec_rev, spec_status),
        )
        con.execute(
            "INSERT INTO clay_work_leases VALUES(?,?,?,?,?,?,?,?)",
            ("lease-id-a", work_id, spec_rev, executor, token, claimed_at, expires_at, state),
        )
    finally:
        con.close()
    return work_id


class RecoveryLeaseGateTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "u.sqlite"
        _install_work_fabric(self.db)

    def tearDown(self):
        self.td.cleanup()

    def _verify(self, **overrides):
        kwargs = dict(
            tick_id="t1",
            work_id=recovery_work_id_for_tick("t1"),
            spec_rev=1,
            executor_node="worker-a",
            lease_token="lease-a",
            checked_at=NOW,
        )
        kwargs.update(overrides)
        con = _connect(self.db)
        try:
            con.execute("BEGIN IMMEDIATE")
            proof = verify_active_recovery_lease_in_transaction(con, **kwargs)
            con.execute("ROLLBACK")
            return proof
        finally:
            con.close()

    def test_exact_unique_active_lease_passes(self):
        _seed(self.db)
        proof = self._verify()
        self.assertEqual(proof.work_id, recovery_work_id_for_tick("t1"))
        self.assertEqual(proof.active_same_work_spec_count, 1)
        self.assertEqual(proof.lease_state, "RUNNING")
        self.assertNotEqual(proof.lease_token_digest, "lease-a")

    def test_unrelated_valid_work_lease_cannot_authorize_tick(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "RECOVERY_WORK_ID_MISMATCH"):
            self._verify(work_id="other-work")

    def test_expired_lease_fails_closed(self):
        _seed(self.db, expires_at="2026-08-28T12:29:59Z")
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_TIME_WINDOW"):
            self._verify()

    def test_terminal_work_fails_closed(self):
        _seed(self.db, terminal_status="COMPLETE")
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "WORK_ITEM_TERMINAL"):
            self._verify()

    def test_non_ready_or_stale_spec_fails_closed(self):
        _seed(self.db, spec_status="READY")
        con = _connect(self.db)
        try:
            con.execute(
                "INSERT INTO clay_work_spec_revisions VALUES(?,?,?)",
                (recovery_work_id_for_tick("t1"), 2, "READY"),
            )
        finally:
            con.close()
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "NEWEST_SPEC_REV"):
            self._verify()

    def test_wrong_executor_fails_closed(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_EXECUTOR_MISMATCH"):
            self._verify(executor_node="worker-b")

    def test_ambiguous_second_active_lease_fails_closed(self):
        _seed(self.db)
        con = _connect(self.db)
        try:
            con.execute(
                "INSERT INTO clay_work_leases VALUES(?,?,?,?,?,?,?,?)",
                (
                    "lease-id-b",
                    recovery_work_id_for_tick("t1"),
                    1,
                    "worker-b",
                    "lease-b",
                    "2026-08-28T12:10:00Z",
                    "2026-08-28T12:50:00Z",
                    "CLAIMED",
                ),
            )
        finally:
            con.close()
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "AMBIGUOUS_ACTIVE_LEASE_COUNT:2"):
            self._verify()

    def test_missing_canonical_work_fabric_fails_closed(self):
        empty = Path(self.td.name) / "empty.sqlite"
        con = _connect(empty)
        try:
            con.execute("BEGIN IMMEDIATE")
            with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "CANONICAL_WORK_FABRIC_TABLES_MISSING"):
                verify_active_recovery_lease_in_transaction(
                    con,
                    tick_id="t1",
                    work_id=recovery_work_id_for_tick("t1"),
                    spec_rev=1,
                    executor_node="worker-a",
                    lease_token="lease-a",
                    checked_at=NOW,
                )
            con.execute("ROLLBACK")
        finally:
            con.close()


if __name__ == "__main__":
    unittest.main()
