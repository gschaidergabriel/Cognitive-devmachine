import sqlite3
import unittest

from research_entity.runtime.binary_entity_temporal_pulse_v2 import (
    BinaryEntityTemporalStore,
    IdentityCollision,
)


class BinaryEntityTemporalPulseV2Test(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:', isolation_level=None)
        self.conn.row_factory = sqlite3.Row
        self.store = BinaryEntityTemporalStore(self.conn)
        self.digest = 'a' * 64
        self.store.admit_artifact(self.digest, 'build-a', now_ns=1)
        self.root = self.store.mint_root(
            artifact_digest=self.digest, state_lineage_hash='s0', now_ns=2
        )

    def tearDown(self):
        self.conn.close()

    def test_copy_storm_mints_unique_entity_versions_same_artifact(self):
        copies = [
            self.store.copy_entity(
                self.root['entity_id'], state_lineage_hash=f's{i}', now_ns=10
            )
            for i in range(300)
        ]
        self.assertEqual(len({x['entity_id'] for x in copies}), 300)
        self.assertEqual(len({x['entity_version'] for x in copies}), 300)
        self.assertTrue(all(x['artifact_digest'] == self.digest for x in copies))
        self.assertEqual(self.store.peer_count(copies[0]['entity_id']), 300)

    def test_lineage_relations_derive_parent_child_sibling_without_peer_matrix(self):
        a = self.store.copy_entity(self.root['entity_id'], now_ns=3)
        b = self.store.copy_entity(self.root['entity_id'], now_ns=3)
        c = self.store.copy_entity(a['entity_id'], now_ns=3)
        ra = {x['entity_id']: x['relation'] for x in self.store.lineage_relations(a['entity_id'])}
        self.assertEqual(ra[self.root['entity_id']], 'PARENT')
        self.assertEqual(ra[b['entity_id']], 'SIBLING')
        self.assertEqual(ra[c['entity_id']], 'CHILD')

    def test_live_same_entity_clone_fails_closed_but_reboot_can_cas_supersede(self):
        eid = self.root['entity_id']
        self.store.claim_runtime(
            eid, lease_id='L1', host_id='h', boot_id='B1', invocation_id='I1', now_ns=3
        )
        with self.assertRaises(IdentityCollision):
            self.store.claim_runtime(
                eid, lease_id='L2', host_id='h', boot_id='B1', invocation_id='I2'
            )
        lease = self.store.claim_runtime(
            eid,
            lease_id='L2',
            host_id='h',
            boot_id='B2',
            invocation_id='I2',
            allow_supersede=True,
            now_ns=4,
        )
        self.assertEqual(lease['lease_epoch'], 2)

    def test_gap_classifier_separates_suspend_process_restart_and_power_gap(self):
        prev = {
            'observed_at_utc_ns': 1_000_000_000,
            'boottime_ns': 1_000_000_000,
            'monotonic_ns': 1_000_000_000,
            'boot_id': 'B1',
            'invocation_id': 'I1',
        }
        suspend = self.store.classify_gap(
            prev,
            utc_ns=11_000_000_000,
            boottime_ns=11_000_000_000,
            monotonic_ns=2_000_000_000,
            boot_id='B1',
            invocation_id='I1',
            interval_ns=1_000_000_000,
        )
        self.assertEqual(suspend['gap_class'], 'SUSPEND_GAP')
        self.assertEqual(suspend['inferred_suspend_ns'], 9_000_000_000)
        restart = self.store.classify_gap(
            prev,
            utc_ns=4_000_000_000,
            boottime_ns=4_000_000_000,
            monotonic_ns=4_000_000_000,
            boot_id='B1',
            invocation_id='I2',
            interval_ns=1_000_000_000,
        )
        self.assertEqual(restart['gap_class'], 'PROCESS_RESTART_SAME_BOOT')
        power = self.store.classify_gap(
            prev,
            utc_ns=7 * 3600 * 1_000_000_000,
            boottime_ns=100,
            monotonic_ns=100,
            boot_id='B2',
            invocation_id='I2',
            interval_ns=1_000_000_000,
        )
        self.assertEqual(power['gap_class'], 'BOOT_OR_POWER_GAP')
        self.assertGreater(power['missed_logical_slots'], 25_000)
        self.assertIn('COMPUTE_NOT_EVIDENCED', power['continuity_class'])


if __name__ == '__main__':
    unittest.main()
