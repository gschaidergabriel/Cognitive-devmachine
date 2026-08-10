from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .database_pulse import (
    DatabasePulse,
    PulseConfig,
    PulseStateCorrupt,
    replay_entity_trace,
)
from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import QuerySpec, UnifiedDBQueryPlane


class DatabasePulseTests(unittest.TestCase):
    def seeded(self, path=':memory:', config=PulseConfig()):
        ledger = StateLedger(path)
        ledger.append_event(
            event_id='seed', idem='seed', base_epoch=ledger.epoch,
            event_type='SEED', writer='test',
            ops=[
                {'op':'SET','domain':'memory','key':'known','value':{'v':1},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'goal','key':'open','value':{'v':2},'epistemic':'UNKNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'conflict','value':{'v':3},'epistemic':'CONFLICT','status':'CURRENT'},
            ],
        )
        return ledger, DatabasePulse(ledger, config)

    def test_zero_model_pulse_records_execution_without_semantic_churn(self):
        ledger, pulse = self.seeded()
        epoch_before = ledger.epoch
        hash_before = ledger.semantic_state_hash
        trace_before = ledger.trace_root_hash
        out = pulse.run('p1', basis_epoch=ledger.epoch)
        self.assertEqual(out['commit_status'], 'RECORDED')
        self.assertEqual(out['mode'], 'ZERO_MODEL_DELTA_AWARE')
        self.assertEqual(out['model_call_count'], 0)
        self.assertEqual(out['tool_call_count'], 0)
        self.assertEqual(out['effect_count'], 0)
        self.assertEqual(out['pulse_state_transition_count'], 1)
        self.assertEqual(out['semantic_state_transition_count'], 0)
        self.assertEqual(out['pulse_count'], 1)
        self.assertTrue(out['bootstrap'])
        self.assertEqual(out['census_count'], 3)
        self.assertEqual(out['observed_change_count'], 3)
        self.assertEqual(out['memory_update_observed_count'], 1)
        self.assertEqual(out['authority'], 'OBSERVATION_AND_EXECUTION_RECEIPT_ONLY')
        self.assertEqual(ledger.epoch, epoch_before)
        self.assertEqual(ledger.semantic_state_hash, hash_before)
        self.assertEqual(ledger.trace_root_hash, trace_before)
        self.assertEqual(out['semantic_epoch_after'], epoch_before)
        self.assertEqual(out['semantic_state_hash_after'], hash_before)
        ledger.close()

    def test_idle_second_pulse_does_not_self_excite_or_advance_semantic_epoch(self):
        ledger, pulse = self.seeded()
        semantic_epoch = ledger.epoch
        first = pulse.run('p1')
        second = pulse.run('p2')
        self.assertEqual(first['pulse_count'], 1)
        self.assertEqual(second['pulse_count'], 2)
        self.assertFalse(second['bootstrap'])
        self.assertEqual(second['previous_basis_epoch'], semantic_epoch)
        self.assertEqual(second['basis_epoch'], semantic_epoch)
        self.assertEqual(second['delta_event_count'], 0)
        self.assertEqual(second['observed_change_count'], 0)
        refs = [x['ref'] for x in second['active_refs']]
        self.assertIn('goal:open', refs)
        self.assertIn('semantic:conflict', refs)
        self.assertNotIn('memory:known', refs)
        self.assertEqual(ledger.epoch, semantic_epoch)
        ledger.close()

    def test_prepared_semantic_query_receipt_survives_idle_pulse(self):
        ledger, pulse = self.seeded()
        plane = UnifiedDBQueryPlane(ledger)
        receipt = plane.query(QuerySpec('before-pulse', domains=('memory',), basis_epoch=ledger.epoch))
        semantic_hash = ledger.semantic_state_hash
        pulse.run('idle')
        selected = plane.select_for_assembly(receipt)
        self.assertEqual(ledger.semantic_state_hash, semantic_hash)
        self.assertEqual(receipt.basis_epoch, ledger.epoch)
        self.assertEqual([x['key'] for x in selected['selected']], ['known'])
        ledger.close()

    def test_incremental_pulse_observes_only_new_source_delta(self):
        ledger, pulse = self.seeded()
        pulse.run('p1')
        ledger.append_event(
            event_id='memory-update', idem='memory-update', base_epoch=ledger.epoch,
            event_type='MEMORY_UPDATE', writer='test',
            ops=[{'op':'SET','domain':'memory','key':'known','value':{'v':4},'epistemic':'KNOWN','status':'CURRENT'}],
        )
        out = pulse.run('p2')
        self.assertEqual(out['delta_event_count'], 1)
        self.assertEqual(out['observed_change_count'], 1)
        self.assertEqual(out['memory_update_observed_count'], 1)
        changed = [x for x in out['active_refs'] if x['changed']]
        self.assertEqual([x['ref'] for x in changed], ['memory:known'])
        ledger.close()

    def test_retry_same_pulse_id_is_idempotent(self):
        ledger, pulse = self.seeded()
        first = pulse.run('same')
        epoch_after = ledger.epoch
        second = pulse.run('same')
        self.assertEqual(second['commit_status'], 'ALREADY_RECORDED')
        self.assertEqual(second['receipt_hash'], first['receipt_hash'])
        self.assertEqual(second['pulse_chain_hash'], first['pulse_chain_hash'])
        self.assertEqual(ledger.epoch, epoch_after)
        self.assertEqual(pulse.journal.verify_all()['pulse_count'], 1)
        ledger.close()

    def test_stale_basis_fails_closed_without_receipt(self):
        ledger, pulse = self.seeded()
        before = ledger.epoch
        with self.assertRaises(StaleEpoch):
            pulse.run('stale', basis_epoch=before - 1)
        self.assertEqual(ledger.epoch, before)
        self.assertEqual(pulse.journal.verify_all()['pulse_count'], 0)
        ledger.close()

    def test_corrupt_receipt_chain_fails_closed(self):
        ledger, pulse = self.seeded()
        pulse.run('p1')
        ledger.conn.execute(
            "UPDATE database_pulse_receipts SET receipt_json='{}' WHERE pulse_id='p1'"
        )
        ledger.conn.commit()
        before = ledger.epoch
        with self.assertRaises(PulseStateCorrupt):
            pulse.run('blocked')
        self.assertEqual(ledger.epoch, before)
        self.assertIsNone(
            ledger.conn.execute(
                "SELECT 1 FROM database_pulse_receipts WHERE pulse_id='blocked'"
            ).fetchone()
        )
        ledger.close()

    def test_persistent_restart_resumes_pulse_count_and_cursor(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / 'frank.db')
            ledger, pulse = self.seeded(path)
            first = pulse.run('p1')
            semantic_hash = ledger.semantic_state_hash
            ledger.close()

            reopened = StateLedger(path)
            out = DatabasePulse(reopened).run('p2')
            self.assertEqual(first['pulse_count'], 1)
            self.assertEqual(out['pulse_count'], 2)
            self.assertEqual(out['observed_change_count'], 0)
            self.assertEqual(reopened.semantic_state_hash, semantic_hash)
            reopened.close()

    def test_replay_preserves_semantic_state_and_pulse_receipt_chain(self):
        ledger, pulse = self.seeded()
        pulse.run('p1')
        ledger.append_event(
            event_id='delta', idem='delta', base_epoch=ledger.epoch,
            event_type='DELTA', writer='test',
            ops=[{'op':'SET','domain':'memory','key':'known','value':{'v':9},'epistemic':'KNOWN','status':'CURRENT'}],
        )
        pulse.run('p2')
        last = pulse.run('p3')
        events = ledger.export_events()
        receipts = pulse.journal.export_receipts()
        expected_semantic_hash = ledger.semantic_state_hash
        expected_chain = pulse.journal.verify_all()['pulse_chain_hash']
        ledger.close()

        replayed, replay_pulse = replay_entity_trace(events, receipts)
        self.assertEqual(replayed.semantic_state_hash, expected_semantic_hash)
        verify = replay_pulse.journal.verify_all()
        self.assertEqual(verify['pulse_count'], 3)
        self.assertEqual(verify['pulse_chain_hash'], expected_chain)
        again = replay_pulse.run('p3')
        self.assertEqual(again['commit_status'], 'ALREADY_RECORDED')
        self.assertEqual(again['receipt_hash'], last['receipt_hash'])
        replayed.close()

    def test_bootstrap_is_bounded_and_reports_truncation(self):
        ledger, pulse = self.seeded(
            config=PulseConfig(bootstrap_scan_limit=2, max_active_refs=24, max_delta_events=4096)
        )
        out = pulse.run('bounded')
        self.assertTrue(out['bootstrap_truncated'])
        self.assertEqual(out['census_count'], 3)
        self.assertEqual(out['observed_change_count'], 2)
        ledger.close()

    def test_exactly_one_semantic_delta_fits_budget_one(self):
        ledger, pulse = self.seeded(
            config=PulseConfig(bootstrap_scan_limit=32, max_active_refs=24, max_delta_events=1)
        )
        pulse.run('p1')
        ledger.append_event(
            event_id='d1', idem='d1', base_epoch=ledger.epoch, event_type='D', writer='test',
            ops=[{'op':'SET','domain':'memory','key':'a','value':1,'epistemic':'KNOWN','status':'CURRENT'}],
        )
        out = pulse.run('p2')
        self.assertEqual(out['delta_event_count'], 1)
        self.assertEqual(out['observed_change_count'], 1)
        ledger.close()

    def test_delta_budget_overflow_requires_explicit_rebootstrap(self):
        ledger, pulse = self.seeded(
            config=PulseConfig(bootstrap_scan_limit=32, max_active_refs=24, max_delta_events=1)
        )
        pulse.run('p1')
        ledger.append_event(
            event_id='d1', idem='d1', base_epoch=ledger.epoch, event_type='D', writer='test',
            ops=[{'op':'SET','domain':'memory','key':'a','value':1,'epistemic':'KNOWN','status':'CURRENT'}],
        )
        ledger.append_event(
            event_id='d2', idem='d2', base_epoch=ledger.epoch, event_type='D', writer='test',
            ops=[{'op':'SET','domain':'memory','key':'b','value':2,'epistemic':'KNOWN','status':'CURRENT'}],
        )
        before = ledger.epoch
        with self.assertRaises(PulseStateCorrupt):
            pulse.run('p2')
        self.assertEqual(ledger.epoch, before)
        self.assertEqual(pulse.journal.verify_all()['pulse_count'], 1)
        ledger.close()


if __name__ == '__main__':
    unittest.main()
