import sqlite3
import unittest

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.binary_entity_temporal_pulse_v2 import BinaryEntityTemporalStore
from research_entity.runtime.database_pulse_candidate_v1 import PulseSpec
from research_entity.runtime.database_pulse_runtime_v5 import DatabasePulseRuntimeV5
from research_entity.runtime.database_pulse_temporal_identity_v1 import TemporalDatabasePulseRuntimeV6


class DatabasePulseTemporalIdentityIntegrationTest(unittest.TestCase):
    def setUp(self):
        self.ledger = StateLedger(':memory:')
        self.store = BinaryEntityTemporalStore(self.ledger.conn)
        self.digest = 'b' * 64
        self.store.admit_artifact(self.digest, 'frank-test-build', now_ns=1)
        self.root = self.store.mint_root(
            artifact_digest=self.digest, state_lineage_hash='state-0', now_ns=2
        )
        self.store.claim_runtime(
            self.root['entity_id'],
            lease_id='lease-1',
            host_id='target-vps',
            boot_id='boot-1',
            invocation_id='inv-1',
            now_ns=3,
        )
        self.base = DatabasePulseRuntimeV5(self.ledger)
        self.runtime = TemporalDatabasePulseRuntimeV6(
            self.base,
            entity_id=self.root['entity_id'],
            lease_id='lease-1',
            interval_ns=1_000_000_000,
        )
        self.base.set_scheduler(
            enabled=True,
            event_id='scheduler-on',
            base_epoch=self.ledger.epoch,
            actor='test',
            reason='temporal integration test',
        )
        self.ledger.append_event(
            event_id='seed-memory',
            idem='seed-memory',
            base_epoch=self.ledger.epoch,
            event_type='TEST_SEED',
            writer='test',
            ops=[{
                'op': 'SET',
                'domain': 'memory',
                'key': 'critical',
                'value': {
                    'priority': 1.0,
                    'urgency': 0.8,
                    'salience': 0.9,
                    'novelty': 0.7,
                    'payload': 'x',
                },
                'epistemic': 'KNOWN',
                'status': 'CURRENT',
            }],
            provenance={'test': True},
            source={'test': True},
            execution={'effect': 'NONE'},
        )

    def tearDown(self):
        self.ledger.close()

    def spec(self, pulse_id):
        return PulseSpec(
            pulse_id=pulse_id,
            basis_epoch=self.ledger.epoch,
            source_domains=('memory',),
            max_candidates=8,
            max_focus=2,
        )

    def test_real_v5_unprepared_database_pulse_fails_closed(self):
        before = self.ledger.epoch
        spec = self.spec('unprepared')
        with self.assertRaises(sqlite3.IntegrityError):
            self.base.run_pulse(spec)
        self.assertEqual(self.ledger.epoch, before)
        self.assertIsNone(self.runtime.binder.link('unprepared'))

    def test_real_v5_pulse_atomically_binds_temporal_identity_and_model_context(self):
        captured = {}

        def model(context):
            captured.update(context)
            return {'candidate': 'unknown-test'}

        spec = self.spec('p1')
        result = self.runtime.run_pulse(
            spec,
            model_assistant=model,
            clock_override={
                'utc_ns': 10_000_000_000,
                'boottime_ns': 5_000_000_000,
                'monotonic_ns': 5_000_000_000,
                'boot_id': 'boot-1',
                'invocation_id': 'inv-1',
            },
        )
        self.assertEqual(result['temporal_orientation']['gap_class'], 'GENESIS')
        self.assertEqual(
            result['temporal_link']['event_epoch'], result['pulse_receipt'].committed_epoch
        )
        self.assertEqual(
            captured['mandatory_context']['temporal_orientation']['entity_version'],
            self.root['entity_version'],
        )
        self.assertEqual(
            self.ledger.conn.execute('SELECT count(*) FROM entity_pulses').fetchone()[0], 1
        )
        self.assertEqual(
            self.ledger.conn.execute('SELECT count(*) FROM pulse_temporal_links').fetchone()[0], 1
        )

    def test_committed_pulse_retry_is_idempotent_after_epoch_advanced(self):
        basis = self.ledger.epoch
        spec = PulseSpec(
            pulse_id='p-retry',
            basis_epoch=basis,
            source_domains=('memory',),
            max_candidates=8,
            max_focus=2,
        )
        first = self.runtime.run_pulse(
            spec,
            clock_override={
                'utc_ns': 10,
                'boottime_ns': 10,
                'monotonic_ns': 10,
                'boot_id': 'boot-1',
                'invocation_id': 'inv-1',
            },
        )
        second = self.runtime.run_pulse(
            spec,
            clock_override={
                'utc_ns': 999,
                'boottime_ns': 999,
                'monotonic_ns': 999,
                'boot_id': 'boot-1',
                'invocation_id': 'inv-1',
            },
        )
        self.assertEqual(
            first['pulse_receipt'].receipt_hash, second['pulse_receipt'].receipt_hash
        )
        self.assertEqual(
            self.ledger.conn.execute(
                "SELECT count(*) FROM entity_pulses WHERE pulse_id='p-retry'"
            ).fetchone()[0],
            1,
        )
        self.assertFalse(self.ledger.conn.in_transaction)

    def test_crash_after_prepare_then_new_lease_recovery_creates_no_phantom_pulse(self):
        spec = self.spec('crash-before-event')
        self.runtime.binder.prepare(
            entity_id=self.root['entity_id'],
            pulse_id=spec.pulse_id,
            basis_epoch=spec.basis_epoch,
            lease_id='lease-1',
            interval_ns=1_000_000_000,
            utc_ns=10,
            boottime_ns=10,
            monotonic_ns=10,
            boot_id='boot-1',
            invocation_id='inv-1',
        )
        self.store.claim_runtime(
            self.root['entity_id'],
            lease_id='lease-2',
            host_id='target-vps',
            boot_id='boot-1',
            invocation_id='inv-2',
            expected_previous_lease_id='lease-1',
            allow_supersede=True,
            now_ns=20,
        )
        self.assertEqual(
            self.runtime.binder.recover_stale_prepared(
                self.root['entity_id'], current_lease_id='lease-2'
            ),
            1,
        )
        self.assertEqual(
            self.ledger.conn.execute(
                "SELECT count(*) FROM entity_pulses WHERE pulse_id='crash-before-event'"
            ).fetchone()[0],
            0,
        )
        self.assertIsNone(self.runtime.binder.link('crash-before-event'))


if __name__ == '__main__':
    unittest.main()
