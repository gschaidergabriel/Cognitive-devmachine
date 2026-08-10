from __future__ import annotations

import unittest

from research_entity.runtime.database_pulse_execution_plane_v6 import (
    PulseSpecV6,
    PulseV6IntegrityError,
)
from research_entity.runtime.database_pulse_execution_plane_v6_4 import (
    DatabasePulseExecutionPlaneV6_4,
)
from research_entity.runtime.test_database_pulse_execution_plane_v6 import seed_ledger, roots


class DatabasePulseExecutionPlaneV6_4Tests(unittest.TestCase):
    def test_sparse_policy_keeps_receipts_but_only_periodic_pulse_checkpoints(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=32, now="init"
            )
            semantic_before = roots(ledger)
            for i in range(100):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"idle-{i}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                    full_audit_every=1000,
                ), now=f"idle-{i}")
            stats = runtime.checkpoint_stats()
            self.assertEqual(ledger.conn.execute(
                "SELECT COUNT(*) FROM pulse_execution_receipts_v6"
            ).fetchone()[0], 100)
            self.assertEqual(stats["pulse"], 3)  # 32, 64, 96
            self.assertEqual(stats["total"], 4)  # bootstrap + periodic Pulse checkpoints
            self.assertEqual(runtime.verify_execution_chain()["transition_count"], 100)
            self.assertEqual(semantic_before, roots(ledger))
        finally:
            ledger.close()

    def test_interval_one_is_v63_checkpoint_behavior(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=1, now="init"
            )
            for i in range(12):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"p-{i}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                ))
            stats = runtime.checkpoint_stats()
            self.assertEqual(stats["pulse"], 12)
            self.assertEqual(stats["total"], 13)
        finally:
            ledger.close()

    def test_replay_reconstructs_trusted_head_with_status_controls_between_pulses(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=64, now="init"
            )
            runtime.run_pulse(PulseSpecV6(
                invocation_id="p1", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="p1")
            runtime.set_status("PAUSED", now="pause", control_id="pause")
            runtime.set_status("PULSING", now="resume", control_id="resume")
            for i in range(1, 25):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"p{i+1}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                    full_audit_every=1000,
                ), now=f"p{i+1}")
            replay = runtime.replay_trusted_head_material()
            transition_count = replay.pop("_replay_transition_count")
            replay.pop("_repaired_corrupt_observations")
            current = runtime._state_material(runtime._verify_state())
            self.assertEqual(replay, current)
            self.assertEqual(transition_count, 27)  # 25 Pulse + pause + resume
            self.assertEqual(runtime.checkpoint_stats()["pulse"], 0)
            self.assertEqual(runtime.checkpoint_stats()["control"], 2)
        finally:
            ledger.close()

    def test_corrupted_current_state_recovers_from_receipt_replay_without_head_checkpoint(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=64, now="init"
            )
            for i in range(20):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"p-{i}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                    full_audit_every=1000,
                ), now=f"p-{i}")
            self.assertEqual(runtime.checkpoint_stats()["pulse"], 0)
            trusted = runtime._trusted_transition_head_hash()
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET last_assembly_hash='RAW_CORRUPTION' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime._verify_state()
            recovered = runtime.recover_last_known_good(
                now="recover", control_id="replay-recover"
            )
            self.assertEqual(recovered, 20)
            self.assertEqual(str(runtime._verify_state()["state_hash"]), trusted)
            control = runtime._control_row("replay-recover")
            self.assertEqual(control["pre_integrity"], "CORRUPT_OR_UNVERIFIED")
            self.assertEqual(runtime.checkpoint_stats()["control"], 1)
            verified = runtime.verify_execution_chain()
            self.assertTrue(verified["pass"])
            self.assertEqual(verified["repaired_corrupt_observations"], 1)
        finally:
            ledger.close()

    def test_receipt_tamper_blocks_replay_recovery(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_4(
                ledger, checkpoint_interval=64, now="init"
            )
            for i in range(5):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id=f"p-{i}", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                ))
            ledger.conn.execute(
                "UPDATE pulse_execution_receipts_v6 SET receipt_hash='BAD' WHERE invocation_id='p-2'"
            )
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET state_hash='CORRUPT' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime.recover_last_known_good(now="recover-bad", control_id="recover-bad")
            self.assertIsNone(ledger.conn.execute(
                "SELECT 1 FROM pulse_execution_control_receipts_v6_2 WHERE control_id='recover-bad'"
            ).fetchone())
        finally:
            ledger.close()

    def test_checkpoint_policy_is_persisted_and_cannot_silently_change_on_reopen(self):
        import tempfile
        from pathlib import Path
        from research_entity.harness.reference.state_ledger import StateLedger

        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / "v64.sqlite")
            ledger = seed_ledger(path)
            try:
                DatabasePulseExecutionPlaneV6_4(
                    ledger, checkpoint_interval=16, now="first"
                )
            finally:
                ledger.close()
            ledger2 = StateLedger(path)
            try:
                with self.assertRaises(PulseV6IntegrityError):
                    DatabasePulseExecutionPlaneV6_4(
                        ledger2, checkpoint_interval=32, now="reopen"
                    )
                ok = DatabasePulseExecutionPlaneV6_4(
                    ledger2, checkpoint_interval=16, now="reopen-ok"
                )
                self.assertEqual(ok.checkpoint_interval, 16)
            finally:
                ledger2.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
