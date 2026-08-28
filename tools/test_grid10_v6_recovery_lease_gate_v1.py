#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import json
import sqlite3
import tempfile
import unittest

from grid10_v6_crash_reconciliation_v1 import (
    STATUS_PREPARED,
    STATUS_RECOVERY_REQUIRED,
    install_reconciliation_schema,
    prepare_cycle_intent,
)
from grid10_v6_recovery_lease_gate_v1 import (
    RecoveryLeaseNotAuthorized,
    persist_recovery_classification_with_canonical_lease,
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


def _seed_recovery_required_evidence(
    path: Path,
    *,
    tick_id: str = "t1",
    agency_epoch_at_prepare: int = 0,
    agency_epoch_after: int = 1,
    control_epoch: int = 1,
    control_snapshot_digest: str = "control-digest",
) -> None:
    """Create the smallest exact DB evidence for POST_V4 recovery classification."""
    install_reconciliation_schema(path)
    prepare_cycle_intent(
        path,
        tick_id=tick_id,
        agency_epoch_at_prepare=agency_epoch_at_prepare,
        control_epoch=control_epoch,
        control_snapshot_digest=control_snapshot_digest,
        prepared_ts=0.0,
    )
    con = _connect(path)
    try:
        con.execute(
            """CREATE TABLE IF NOT EXISTS grid10_cognitive_cycles(
                 tick_id TEXT PRIMARY KEY,
                 agency_epoch_before INTEGER NOT NULL,
                 agency_epoch_after INTEGER NOT NULL
               )"""
        )
        con.execute(
            "INSERT INTO grid10_cognitive_cycles VALUES(?,?,?)",
            (tick_id, agency_epoch_at_prepare, agency_epoch_after),
        )
    finally:
        con.close()


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

    def test_claimed_at_in_future_fails_closed(self):
        _seed(self.db, claimed_at="2026-08-28T12:30:01Z")
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_TIME_WINDOW"):
            self._verify()

    def test_exact_expiry_boundary_fails_closed(self):
        _seed(self.db, expires_at=NOW)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_TIME_WINDOW"):
            self._verify()

    def test_inactive_lease_state_fails_closed(self):
        _seed(self.db, state="RELEASED")
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_NOT_ACTIVE_STATE"):
            self._verify()

    def test_unknown_lease_token_fails_closed(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_TOKEN_NOT_FOUND"):
            self._verify(lease_token="not-the-bound-token")

    def test_wrong_spec_revision_fails_closed(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "LEASE_SPEC_REV_MISMATCH"):
            self._verify(spec_rev=2)

    def test_empty_executor_and_token_fail_closed(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "EMPTY_EXECUTOR_NODE"):
            self._verify(executor_node="")
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "EMPTY_LEASE_TOKEN"):
            self._verify(lease_token="")

    def test_invalid_tick_identity_fails_closed(self):
        _seed(self.db)
        with self.assertRaisesRegex(RecoveryLeaseNotAuthorized, "INVALID_TICK_ID"):
            self._verify(tick_id="")

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

    def test_persist_recovery_classification_records_lease_proof_without_raw_token(self):
        _seed(self.db, claimed_at="2020-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z")
        _seed_recovery_required_evidence(self.db)
        result, proof, envelope_digest = persist_recovery_classification_with_canonical_lease(
            self.db,
            tick_id="t1",
            work_id=recovery_work_id_for_tick("t1"),
            spec_rev=1,
            executor_node="worker-a",
            lease_token="lease-a",
            terminal_ts=1.0,
        )
        self.assertEqual(result.status, STATUS_RECOVERY_REQUIRED)
        self.assertEqual(proof.work_id, recovery_work_id_for_tick("t1"))
        self.assertEqual(len(envelope_digest), 64)
        con = _connect(self.db)
        try:
            row = con.execute(
                "SELECT status,classification_json,classification_digest FROM grid10_v6_cycle_intents WHERE tick_id=?",
                ("t1",),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], STATUS_RECOVERY_REQUIRED)
        self.assertEqual(row["classification_digest"], envelope_digest)
        envelope = json.loads(row["classification_json"])
        self.assertEqual(envelope["lease_proof"]["work_id"], recovery_work_id_for_tick("t1"))
        self.assertEqual(envelope["classification"]["same_tick_retry_authorized"], False)
        self.assertNotIn("lease-a", row["classification_json"])

    def test_persist_recovery_classification_is_create_once_and_preserves_first_proof(self):
        _seed(self.db, claimed_at="2020-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z")
        _seed_recovery_required_evidence(self.db)
        _, _, first_digest = persist_recovery_classification_with_canonical_lease(
            self.db,
            tick_id="t1",
            work_id=recovery_work_id_for_tick("t1"),
            spec_rev=1,
            executor_node="worker-a",
            lease_token="lease-a",
            terminal_ts=1.0,
        )
        con = _connect(self.db)
        try:
            first = con.execute(
                "SELECT terminal_ts,classification_json,classification_digest FROM grid10_v6_cycle_intents WHERE tick_id=?",
                ("t1",),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(first)
        first_json = first["classification_json"]
        self.assertEqual(first["terminal_ts"], 1.0)
        self.assertEqual(first["classification_digest"], first_digest)

        with self.assertRaisesRegex(
            RecoveryLeaseNotAuthorized,
            "RECOVERY_INTENT_NOT_PREPARED:RECOVERY_REQUIRED_POST_V4_COMMIT:t1",
        ):
            persist_recovery_classification_with_canonical_lease(
                self.db,
                tick_id="t1",
                work_id=recovery_work_id_for_tick("t1"),
                spec_rev=1,
                executor_node="worker-a",
                lease_token="lease-a",
                terminal_ts=2.0,
            )

        con = _connect(self.db)
        try:
            second = con.execute(
                "SELECT terminal_ts,classification_json,classification_digest FROM grid10_v6_cycle_intents WHERE tick_id=?",
                ("t1",),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(second)
        self.assertEqual(second["terminal_ts"], 1.0)
        self.assertEqual(second["classification_json"], first_json)
        self.assertEqual(second["classification_digest"], first_digest)

    def test_persist_recovery_classification_rejects_external_time_override_before_mutation(self):
        _seed(self.db, claimed_at="2020-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z")
        _seed_recovery_required_evidence(self.db)
        with self.assertRaisesRegex(
            RecoveryLeaseNotAuthorized,
            "EXTERNAL_CHECKED_AT_OVERRIDE_FORBIDDEN",
        ):
            persist_recovery_classification_with_canonical_lease(
                self.db,
                tick_id="t1",
                work_id=recovery_work_id_for_tick("t1"),
                spec_rev=1,
                executor_node="worker-a",
                lease_token="lease-a",
                checked_at=NOW,
            )
        con = _connect(self.db)
        try:
            row = con.execute(
                "SELECT status,classification_json FROM grid10_v6_cycle_intents WHERE tick_id=?",
                ("t1",),
            ).fetchone()
        finally:
            con.close()
        self.assertEqual(row["status"], STATUS_PREPARED)
        self.assertIsNone(row["classification_json"])

    def test_persist_recovery_classification_rejects_without_v4_commit_and_rolls_back(self):
        _seed(self.db, claimed_at="2020-01-01T00:00:00Z", expires_at="2099-01-01T00:00:00Z")
        install_reconciliation_schema(self.db)
        prepare_cycle_intent(
            self.db,
            tick_id="t1",
            agency_epoch_at_prepare=0,
            control_epoch=1,
            control_snapshot_digest="control-digest",
            prepared_ts=0.0,
        )
        with self.assertRaisesRegex(
            RecoveryLeaseNotAuthorized,
            "RECOVERY_MUTATION_REQUIRES_RECOVERY_REQUIRED:ABORTED_BEFORE_V4_COMMIT",
        ):
            persist_recovery_classification_with_canonical_lease(
                self.db,
                tick_id="t1",
                work_id=recovery_work_id_for_tick("t1"),
                spec_rev=1,
                executor_node="worker-a",
                lease_token="lease-a",
            )
        con = _connect(self.db)
        try:
            row = con.execute(
                "SELECT status,classification_json,classification_digest FROM grid10_v6_cycle_intents WHERE tick_id=?",
                ("t1",),
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        self.assertEqual(row["status"], STATUS_PREPARED)
        self.assertIsNone(row["classification_json"])
        self.assertIsNone(row["classification_digest"])


if __name__ == "__main__":
    unittest.main()
