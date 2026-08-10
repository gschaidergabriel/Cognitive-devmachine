import unittest

from .state_ledger import StateLedger, StaleEpoch
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec


class EmergentAssemblyTests(unittest.TestCase):
    def make_multihop(self):
        ledger = StateLedger()
        plane = UnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        plane.transact(
            event_id='eap-seed',
            idem='eap-seed',
            base_epoch=0,
            event_type='EAP_SEED',
            writer='test',
            ops=[
                {'op':'SET','domain':'semantic','key':'a','value':{'label':'alpha'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'b','value':{'label':'beta'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'c','value':{'label':'gamma'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':0.9},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'bc','value':{'source':'semantic:b','target':'semantic:c','strength':0.8},'epistemic':'KNOWN','status':'CURRENT'},
            ],
        )
        return ledger, plane

    def test_multihop_assembly_is_deterministic_derived_projection(self):
        ledger, plane = self.make_multihop()
        spec = PossibilitySpec('eap-a', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=3)
        first = plane.compile_active_assembly(spec)
        second = plane.compile_active_assembly(spec)
        self.assertEqual([x['ref'] for x in first['selected']], ['semantic:a','semantic:b','semantic:c'])
        self.assertEqual(first['selection_hash'], second['selection_hash'])
        self.assertTrue(first['derived'])
        self.assertFalse(first['persistent_second_store'])
        self.assertEqual(first['authority'], 'ASSEMBLY_CONTEXT_ONLY')
        ledger.close()

    def test_stale_assembly_basis_is_rejected(self):
        ledger, plane = self.make_multihop()
        old = ledger.epoch
        plane.transact(
            event_id='eap-new',
            idem='eap-new',
            base_epoch=ledger.epoch,
            event_type='EAP_UPDATE',
            writer='test',
            ops=[{'op':'SET','domain':'semantic','key':'d','value':1,'epistemic':'KNOWN','status':'CURRENT'}],
        )
        with self.assertRaises(StaleEpoch):
            plane.compile_active_assembly(PossibilitySpec('stale', seed_refs=('semantic:a',), basis_epoch=old))
        ledger.close()

    def test_conflict_negative_space_blocks_epistemic_laundering(self):
        ledger = StateLedger()
        plane = UnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        plane.transact(
            event_id='negative-space',
            idem='negative-space',
            base_epoch=0,
            event_type='NEGATIVE_SPACE',
            writer='test',
            ops=[
                {'op':'SET','domain':'semantic','key':'anchor','value':'anchor','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'real','value':'real','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'conflict','value':'uncertain','epistemic':'CONFLICT','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'decoy','value':'decoy','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ar','value':{'source':'semantic:anchor','target':'semantic:real','strength':0.60},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ac','value':{'source':'semantic:anchor','target':'semantic:conflict','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'cd','value':{'source':'semantic:conflict','target':'semantic:decoy','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ],
        )
        out = plane.compile_active_assembly(
            PossibilitySpec('negative-space', seed_refs=('semantic:anchor',), basis_epoch=ledger.epoch, max_items=4)
        )
        refs = [x['ref'] for x in out['selected']]
        self.assertIn('semantic:real', refs)
        self.assertNotIn('semantic:decoy', refs)
        self.assertIn('semantic:conflict', out['blocked_propagation_refs'])
        ledger.close()

    def test_conflict_path_can_propagate_only_when_explicitly_admitted(self):
        ledger, plane = self.make_multihop()
        plane.transact(
            event_id='conflict-node',
            idem='conflict-node',
            base_epoch=ledger.epoch,
            event_type='CONFLICT',
            writer='test',
            ops=[
                {'op':'SET','domain':'semantic','key':'x','value':'x','epistemic':'CONFLICT','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'y','value':'y','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ax','value':{'source':'semantic:a','target':'semantic:x','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'xy','value':{'source':'semantic:x','target':'semantic:y','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ],
        )
        blocked = plane.compile_active_assembly(
            PossibilitySpec('blocked', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=8)
        )
        admitted = plane.compile_active_assembly(
            PossibilitySpec(
                'admitted',
                seed_refs=('semantic:a',),
                allow_epistemic=('KNOWN','CONFLICT'),
                basis_epoch=ledger.epoch,
                max_items=8,
            )
        )
        self.assertNotIn('semantic:y', [x['ref'] for x in blocked['selected']])
        self.assertIn('semantic:y', [x['ref'] for x in admitted['selected']])
        ledger.close()

    def test_non_dependency_write_refreshes_compiled_state_incrementally(self):
        ledger, plane = self.make_multihop()
        first = plane.compile_active_assembly(
            PossibilitySpec('before', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=3)
        )
        plane.transact(
            event_id='semantic-update',
            idem='semantic-update',
            base_epoch=ledger.epoch,
            event_type='SEMANTIC_UPDATE',
            writer='test',
            ops=[{'op':'SET','domain':'semantic','key':'b','value':{'label':'beta2'},'epistemic':'KNOWN','status':'CURRENT'}],
        )
        second = plane.compile_active_assembly(
            PossibilitySpec('after', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=3)
        )
        self.assertNotEqual(first['compiled_index_hash'], second['compiled_index_hash'])
        b = next(x for x in second['selected'] if x['ref'] == 'semantic:b')
        self.assertEqual(b['value']['label'], 'beta2')
        ledger.close()

    def test_dependency_write_forces_safe_rebuild_and_new_path_appears(self):
        ledger, plane = self.make_multihop()
        before = plane.compile_active_assembly(
            PossibilitySpec('before-dep', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=8, max_hops=4)
        )
        self.assertNotIn('semantic:d', [x['ref'] for x in before['selected']])
        plane.transact(
            event_id='dependency-update',
            idem='dependency-update',
            base_epoch=ledger.epoch,
            event_type='DEPENDENCY_UPDATE',
            writer='test',
            ops=[
                {'op':'SET','domain':'semantic','key':'d','value':'delta','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'cd','value':{'source':'semantic:c','target':'semantic:d','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ],
        )
        after = plane.compile_active_assembly(
            PossibilitySpec('after-dep', seed_refs=('semantic:a',), basis_epoch=ledger.epoch, max_items=8, max_hops=4)
        )
        self.assertIn('semantic:d', [x['ref'] for x in after['selected']])
        ledger.close()


if __name__ == '__main__':
    unittest.main()
