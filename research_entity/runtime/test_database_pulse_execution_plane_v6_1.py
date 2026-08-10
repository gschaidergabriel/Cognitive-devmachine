from __future__ import annotations

import json
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_execution_plane_v6 import PulseSpecV6, PulseV6IntegrityError
from research_entity.runtime.database_pulse_execution_plane_v6_1 import DatabasePulseExecutionPlaneV6_1
from research_entity.runtime.test_database_pulse_execution_plane_v6 import seed_ledger, roots


class DatabasePulseExecutionPlaneV6_1Tests(unittest.TestCase):
    def test_model_output_is_explicit_unknown_context_envelope(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_1(ledger, now="init")
            before = roots(ledger)
            receipt = runtime.run_pulse(PulseSpecV6(
                invocation_id="v61-model", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ), model_assistant=lambda ctx: {"claim":"maybe","focus":ctx["focus"][0]["ref"]}, now="model")
            self.assertEqual(receipt.model_call_count, 1)
            row = ledger.conn.execute(
                "SELECT model_candidate_json FROM pulse_execution_receipts_v6 WHERE invocation_id='v61-model'"
            ).fetchone()
            body = json.loads(row[0])
            self.assertEqual(body["epistemic"], "UNKNOWN")
            self.assertEqual(body["authority"], "CONTEXT_ONLY_REQUIRES_EXTERNAL_ADMISSION")
            self.assertEqual(body["candidate"]["claim"], "maybe")
            self.assertEqual(before, roots(ledger))
            self.assertEqual(receipt.tool_call_count, 0)
            self.assertEqual(receipt.effect_count, 0)
        finally:
            ledger.close()

    def test_idempotent_read_verifies_persisted_receipt_hash(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_1(ledger, now="init")
            spec = PulseSpecV6(
                invocation_id="v61-hash", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            )
            runtime.run_pulse(spec, now="first")
            ledger.conn.execute(
                "UPDATE pulse_execution_receipts_v6 SET receipt_hash='CORRUPT' WHERE invocation_id='v61-hash'"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime.run_pulse(spec, now="retry")
        finally:
            ledger.close()

    def test_receipt_row_integrity_check_covers_direct_lookup(self):
        ledger = seed_ledger()
        try:
            runtime = DatabasePulseExecutionPlaneV6_1(ledger, now="init")
            runtime.run_pulse(PulseSpecV6(
                invocation_id="direct-row", basis_epoch=ledger.epoch,
                source_domains=("memory",), max_candidates=8, max_focus=1,
            ))
            row = runtime._receipt_row("direct-row")
            self.assertIsNotNone(row)
            ledger.conn.execute(
                "UPDATE pulse_execution_receipts_v6 SET model_call_count=model_call_count+1 WHERE invocation_id='direct-row'"
            )
            ledger.conn.commit()
            with self.assertRaises(PulseV6IntegrityError):
                runtime._receipt_row("direct-row")
        finally:
            ledger.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
