from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from .database_pulse import DatabasePulse, PulseConfig, PulseStateCorrupt
from .state_ledger import StateLedger, StaleEpoch


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

    def test_zero_model_pulse_commits_distinct_observables(self):
        ledger, pulse = self.seeded()
        out = pulse.run('p1', basis_epoch=ledger.epoch)
        self.assertEqual(out['commit_status'], 'COMMITTED')
        self.assertEqual(out['mode'], 'ZERO_MODEL')
        self.assertEqual(out['model_call_count'], 0)
        self.assertEqual(out['tool_call_count'], 0)
        self.assertEqual(out['effect_count'], 0)
        self.assertEqual(out['pulse_state_transition_count'], 1)
        self.assertEqual(out['pulse_count'], 1)
        self.assertTrue(out['bootstrap'])
        self.assertEqual(out['census_count'], 3)
        self.assertEqual(out['observed_change_count'], 3)
        self.assertEqual(out['memory_update_observed_count'], 1)
        self.assertEqual(out['authority'], 'OBSERVATION_AND_INTERNAL_STATE_ONLY')
        self.assertTrue(all(not x['ref'].startswith('pulse_runtime:') for x in out['active_refs']))
        ledger.close()

    def test_idle_second_pulse_does_not_self_excite_from_bookkeeping(self):
        ledger, pulse = self.seeded()
        first = pulse.run('p1')
        second = pulse.run('p2')
        self.assertEqual(first['pulse_count'], 1)
        self.assertEqual(second['pulse_count'], 2)
        self.assertFalse(second['bootstrap'])
        self.assertEqual(second['observed_change_count'], 0)
        refs = [x['ref'] for x in second['active_refs']]
        self.assertIn('goal:open', refs)
        self.assertIn('semantic:conflict', refs)
        self.assertNotIn('memory:known', refs)
        self.assertTrue(all(not ref.startswith('pulse_runtime:') for ref in refs))
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
        self.assertEqual(second['commit_status'], 'ALREADY_COMMITTED')
        self.assertEqual(second['receipt_hash'], first['receipt_hash'])
        self.assertEqual(second['commit_epoch'], first['commit_epoch'])
        self.assertEqual(ledger.epoch, epoch_after)
        ledger.close()

    def test_stale_basis_fails_closed_without_commit(self):
        ledger, pulse = self.seeded()
        before = ledger.epoch
        with self.assertRaises(StaleEpoch):
            pulse.run('stale', basis_epoch=before - 1)
        self.assertEqual(ledger.epoch, before)
        ledger.close()

    def test_corrupt_head_fails_closed_without_new_pulse_event(self):
        ledger, _ = self.seeded()
        ledger.append_event(
            event_id='corrupt-head', idem='corrupt-head', base_epoch=ledger.epoch,
            event_type='TEST_CORRUPTION', writer='test',
            ops=[{'op':'SET','domain':'pulse_runtime','key':'head','value':{'pulse_count':'bad'},'epistemic':'KNOWN','status':'CURRENT'}],
        )
        before = ledger.epoch
        pulse = DatabasePulse(ledger)
        with self.assertRaises(PulseStateCorrupt):
            pulse.run('blocked')
        self.assertEqual(ledger.epoch, before)
        self.assertIsNone(ledger.conn.execute("SELECT 1 FROM events WHERE event_id='database-pulse:blocked'").fetchone())
        ledger.close()

    def test_persistent_restart_resumes_pulse_count_and_cursor(self):
        with tempfile.TemporaryDirectory() as td:
            path = str(Path(td) / 'frank.db')
            ledger, pulse = self.seeded(path)
            first = pulse.run('p1')
            ledger.close()

            reopened = StateLedger(path)
            out = DatabasePulse(reopened).run('p2')
            self.assertEqual(first['pulse_count'], 1)
            self.assertEqual(out['pulse_count'], 2)
            self.assertEqual(out['observed_change_count'], 0)
            reopened.close()

    def test_replay_preserves_committed_pulse_semantics(self):
        ledger, pulse = self.seeded()
        out = pulse.run('p1')
        events = ledger.export_events()
        expected_hash = ledger.semantic_state_hash
        ledger.close()

        replayed = StateLedger.replay(events)
        self.assertEqual(replayed.semantic_state_hash, expected_hash)
        head = replayed.get('pulse_runtime', 'head')
        self.assertEqual(head['value']['last_receipt_hash'], out['receipt_hash'])
        again = DatabasePulse(replayed).run('p1')
        self.assertEqual(again['commit_status'], 'ALREADY_COMMITTED')
        self.assertEqual(again['receipt_hash'], out['receipt_hash'])
        replayed.close()

    def test_bootstrap_is_bounded_and_reports_truncation(self):
        ledger, pulse = self.seeded(config=PulseConfig(bootstrap_scan_limit=2, max_active_refs=24, max_delta_events=4096))
        out = pulse.run('bounded')
        self.assertTrue(out['bootstrap_truncated'])
        self.assertEqual(out['census_count'], 3)
        self.assertEqual(out['observed_change_count'], 2)
        ledger.close()

    def test_delta_budget_overflow_requires_explicit_rebootstrap(self):
        ledger, pulse = self.seeded(config=PulseConfig(bootstrap_scan_limit=32, max_active_refs=24, max_delta_events=1))
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
        ledger.close()


if __name__ == '__main__':
    unittest.main()
