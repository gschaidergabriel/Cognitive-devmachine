#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from grid10_v6_recovery_lease_gate_v1 import (
    RecoveryLeaseNotAuthorized,
    persist_recovery_classification_with_canonical_lease,
    recovery_work_id_for_tick,
)


class RecoveryMutationTimeFenceTests(unittest.TestCase):
    def test_mutating_path_rejects_external_checked_at_before_db_access(self):
        with tempfile.TemporaryDirectory() as td:
            missing_db = Path(td) / "does-not-exist.sqlite"
            with self.assertRaisesRegex(
                RecoveryLeaseNotAuthorized,
                "EXTERNAL_CHECKED_AT_OVERRIDE_FORBIDDEN",
            ):
                persist_recovery_classification_with_canonical_lease(
                    missing_db,
                    tick_id="t1",
                    work_id=recovery_work_id_for_tick("t1"),
                    spec_rev=1,
                    executor_node="worker-a",
                    lease_token="lease-a",
                    checked_at="2026-08-28T12:00:00Z",
                )
            self.assertFalse(missing_db.exists())

    def test_historical_time_cannot_be_used_to_replay_expired_authority(self):
        with tempfile.TemporaryDirectory() as td:
            missing_db = Path(td) / "replay.sqlite"
            with self.assertRaisesRegex(
                RecoveryLeaseNotAuthorized,
                "EXTERNAL_CHECKED_AT_OVERRIDE_FORBIDDEN",
            ):
                persist_recovery_classification_with_canonical_lease(
                    missing_db,
                    tick_id="t-expired",
                    work_id=recovery_work_id_for_tick("t-expired"),
                    spec_rev=7,
                    executor_node="old-worker",
                    lease_token="old-lease-token",
                    checked_at="2000-01-01T00:00:00Z",
                )
            self.assertFalse(missing_db.exists())


if __name__ == "__main__":
    unittest.main()
