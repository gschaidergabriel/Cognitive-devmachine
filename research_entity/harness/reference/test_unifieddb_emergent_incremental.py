import unittest

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import PossibilitySpec
from .unifieddb_emergent_incremental import IncrementalUnifiedDBEmergentPlane


class IncrementalEAPTests(unittest.TestCase):
    def make(self):
        ledger = StateLedger()
        plane = IncrementalUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        plane.transact(
            event_id='inc-seed', idem='inc-seed', base_epoch=0,
            event_type='INC_SEED', writer='test', ops=[
                {'op':'SET','domain':'semantic','key':'a','value':'a','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'b','value':'b','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'c','value':'c','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        plane.compile_active_assembly(PossibilitySpec('warm',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=4,max_hops=2,min_edge_weight=0.0))
        return ledger, plane

    def test_dependency_add_is_incremental_and_visible(self):
        ledger, plane = self.make()
        self.assertIsNone(plane.preprocessor._edge_map_state_hash)
        before_hash = plane.preprocessor._compiled_index_hash
        out = plane.transact(
            event_id='inc-add', idem='inc-add', base_epoch=ledger.epoch,
            event_type='INC_ADD', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'bc','value':{'source':'semantic:b','target':'semantic:c','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        self.assertEqual(out['status'],'COMMITTED')
        self.assertEqual(plane.preprocessor._compiled_epoch,ledger.epoch)
        self.assertEqual(plane.preprocessor._edge_map_state_hash,ledger.semantic_state_hash)
        self.assertNotEqual(before_hash,plane.preprocessor._compiled_index_hash)
        assembly = plane.compile_active_assembly(PossibilitySpec('after',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=4,max_hops=2,min_edge_weight=0.0))
        self.assertEqual([x['ref'] for x in assembly['selected']],['semantic:a','semantic:b','semantic:c'])
        self.assertEqual(assembly['incremental_layer_version'],'EAP-INCREMENTAL-1.4')
        self.assertEqual(assembly['reverse_dependency_map_policy'],'LAZY_ON_FIRST_DEPENDENCY_WRITE')
        ledger.close()

    def test_dependency_retraction_removes_edge_without_rebuild_claim(self):
        ledger, plane = self.make()
        plane.transact(
            event_id='inc-retract', idem='inc-retract', base_epoch=ledger.epoch,
            event_type='INC_RETRACT', writer='test', ops=[
                {'op':'RETRACT','domain':'dependency','key':'ab','value':None,'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        assembly = plane.compile_active_assembly(PossibilitySpec('after-retract',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=4,max_hops=2,min_edge_weight=0.0))
        self.assertEqual([x['ref'] for x in assembly['selected']],['semantic:a'])
        self.assertEqual(plane.preprocessor._edge_count,0)
        ledger.close()

    def test_dependency_retarget_removes_old_path_and_adds_new_path(self):
        ledger, plane = self.make()
        plane.transact(
            event_id='inc-retarget', idem='inc-retarget', base_epoch=ledger.epoch,
            event_type='INC_RETARGET', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:c','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        assembly = plane.compile_active_assembly(PossibilitySpec('after-retarget',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=4,max_hops=2,min_edge_weight=0.0))
        self.assertEqual([x['ref'] for x in assembly['selected']],['semantic:a','semantic:c'])
        self.assertEqual(plane.preprocessor._edge_count,1)
        ledger.close()

    def test_repeated_dependency_updates_do_not_duplicate_edges(self):
        ledger, plane = self.make()
        for index, strength in enumerate((0.7,0.8,0.9,1.0), start=1):
            plane.transact(
                event_id=f'inc-weight-{index}', idem=f'inc-weight-{index}', base_epoch=ledger.epoch,
                event_type='INC_WEIGHT', writer='test', ops=[
                    {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':strength},'epistemic':'KNOWN','status':'CURRENT'},
                ]
            )
            self.assertEqual(plane.preprocessor._edge_count,1)
            self.assertEqual(len(plane.preprocessor._adj['semantic:a']),1)
        ledger.close()

    def test_external_write_causes_safe_rebuild_then_lazy_map_rebind(self):
        ledger, plane = self.make()
        old_hash = plane.preprocessor._compiled_index_hash
        ledger.append_event(
            event_id='external', idem='external', base_epoch=ledger.epoch,
            event_type='EXTERNAL', writer='external-test', ops=[
                {'op':'SET','domain':'dependency','key':'ac','value':{'source':'semantic:a','target':'semantic:c','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        self.assertNotEqual(plane.preprocessor._compiled_epoch,ledger.epoch)
        assembly = plane.compile_active_assembly(PossibilitySpec('after-external',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=4,max_hops=2,min_edge_weight=0.0))
        self.assertEqual([x['ref'] for x in assembly['selected']],['semantic:a','semantic:b','semantic:c'])
        self.assertNotEqual(old_hash,plane.preprocessor._compiled_index_hash)
        self.assertIsNone(plane.preprocessor._edge_map_state_hash)
        plane.transact(
            event_id='after-rebuild-dep', idem='after-rebuild-dep', base_epoch=ledger.epoch,
            event_type='AFTER_REBUILD_DEP', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':0.95},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        self.assertEqual(plane.preprocessor._edge_map_state_hash,ledger.semantic_state_hash)
        ledger.close()

    def test_bidirectional_dependency_patch_tracks_both_edges(self):
        ledger, plane = self.make()
        plane.transact(
            event_id='inc-bidir', idem='inc-bidir', base_epoch=ledger.epoch,
            event_type='INC_BIDIR', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':1.0,'bidirectional':True},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        self.assertEqual(plane.preprocessor._edge_count,2)
        reverse = plane.compile_active_assembly(PossibilitySpec('reverse',seed_refs=('semantic:b',),basis_epoch=ledger.epoch,max_items=4,max_hops=1,min_edge_weight=0.0))
        self.assertIn('semantic:a',[x['ref'] for x in reverse['selected']])
        ledger.close()


if __name__ == '__main__':
    unittest.main()
