from __future__ import annotations

import unittest

from research_entity.runtime.database_pulse_execution_plane_v6 import (
    PulseSpecV6,
    PulseV6ControlError,
    PulseV6IntegrityError,
)
from research_entity.runtime.database_pulse_execution_plane_v6_1 import (
    DatabasePulseExecutionPlaneV6_1,
)
from research_entity.runtime.database_pulse_execution_plane_v6_3 import (
    DatabasePulseExecutionPlaneV6_3,
    PulseV63ControlConflict,
)
from research_entity.runtime.test_database_pulse_execution_plane_v6 import seed_ledger, roots


class DatabasePulseExecutionPlaneV6_3Tests(unittest.TestCase):
    def test_pulse_pause_resume_pulse_is_one_verified_transition_chain(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            semantic_before = roots(ledger)
            runtime.run_pulse(PulseSpecV6(
                invocation_id="p1", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="p1")
            runtime.set_status("PAUSED", now="pause", control_id="pause-1")
            with self.assertRaises(PulseV6ControlError):
                runtime.run_pulse(PulseSpecV6(
                    invocation_id="blocked", basis_epoch=ledger.epoch,
                    source_domains=("memory",), max_candidates=8, max_focus=1,
                ))
            runtime.set_status("PULSING", now="resume", control_id="resume-1")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="p2", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="p2")
            verified = runtime.verify_execution_chain()
            self.assertTrue(verified["pass"])
            self.assertEqual(verified["transition_count"], 4)
            self.assertEqual(verified["pulse_receipts"], 2)
            self.assertEqual(verified["control_receipts"], 2)
            self.assertEqual(semantic_before, roots(ledger))
        finally:
            ledger.close()

    def test_control_id_is_true_idempotency_key(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            runtime.set_status("PAUSED", now="pause", control_id="same-control")
            runtime.set_status("PAUSED", now="retry", control_id="same-control")
            self.assertEqual(ledger.conn.execute(
                "SELECT COUNT(*) FROM pulse_execution_control_receipts_v6_2 WHERE control_id='same-control'"
            ).fetchone()[0], 1)
            with self.assertRaises(PulseV63ControlConflict):
                runtime.set_status("PULSING", now="conflict", control_id="same-control")
        finally:
            ledger.close()

    def test_non_hash_state_corruption_recovers_latest_trusted_head_and_preserves_chain(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            pulse = runtime.run_pulse(PulseSpecV6(
                invocation_id="before-corrupt", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="before-corrupt")
            trusted = runtime._trusted_transition_head_hash()
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET last_assembly_hash='RAW_CORRUPTION' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime._verify_state()
            recovered_count = runtime.recover_last_known_good(
                now="recover", control_id="recover-nonhash"
            )
            self.assertEqual(recovered_count, pulse.pulse_index)
            self.assertEqual(str(runtime._verify_state()["state_hash"]), trusted)
            verified = runtime.verify_execution_chain()
            self.assertTrue(verified["pass"])
            self.assertEqual(verified["repaired_corrupt_observations"], 0)
        finally:
            ledger.close()

    def test_corrupted_stored_state_hash_is_healed_but_damage_remains_receipted(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="head", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="head")
            trusted = runtime._trusted_transition_head_hash()
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET state_hash='CORRUPT_HASH' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            runtime.recover_last_known_good(now="recover-hash", control_id="recover-hash")
            self.assertEqual(str(runtime._verify_state()["state_hash"]), trusted)
            control = runtime._control_row("recover-hash")
            self.assertEqual(control["pre_integrity"], "CORRUPT_OR_UNVERIFIED")
            self.assertEqual(control["pre_state_hash"], "CORRUPT_HASH")
            verified = runtime.verify_execution_chain()
            self.assertEqual(verified["repaired_corrupt_observations"], 1)
        finally:
            ledger.close()

    def test_corrupt_latest_checkpoint_does_not_authorize_silent_rewind(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="p1", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="p1")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="p2", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="p2")
            trusted = runtime._trusted_transition_head_hash()
            ledger.conn.execute(
                "UPDATE pulse_execution_checkpoints_v6 SET snapshot_json='{}' WHERE state_hash=?",
                (trusted,),
            )
            ledger.conn.execute(
                "UPDATE pulse_execution_state_v6 SET state_hash='CORRUPT_HEAD' WHERE singleton_id=1"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime.recover_last_known_good(now="must-not-rewind", control_id="no-rewind")
            self.assertIsNone(runtime._control_row("no-rewind"))
        finally:
            ledger.close()

    def test_control_receipt_tamper_fails_chain_verification(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_3(ledger, now="init")
            runtime.set_status("PAUSED", now="pause", control_id="pause-tamper")
            ledger.conn.execute(
                "UPDATE pulse_execution_control_receipts_v6_2 SET receipt_hash='BAD' WHERE control_id='pause-tamper'"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime.verify_execution_chain()
        finally:
            ledger.close()

    def test_existing_v61_lineage_with_only_pulses_can_be_adopted(self):
        ledger = seed_ledger()
        try:
            old = DatabasePulseExecutionPlaneV6_1(ledger, now="old-init")
            old.run_pulse(PulseSpecV6(
                invocation_id="old-p1", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), now="old-p1")
            upgraded = DatabasePulseExecutionPlaneV6_3(ledger, now="upgrade")
            verified = upgraded.verify_execution_chain()
            self.assertEqual(verified["pulse_receipts"], 1)
            self.assertEqual(verified["control_receipts"], 0)
            self.assertEqual(verified["transition_count"], 1)
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
