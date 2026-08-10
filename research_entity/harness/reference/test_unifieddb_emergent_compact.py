import unittest

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec
from .unifieddb_emergent_compact import (
    CompactUnifiedDBEmergentPlane,
    CompactIncrementalUnifiedDBEmergentPlane,
)


def signature(out):
    return [
        (
            item['ref'], item['value'], item['activation_score'], item['hop'],
            item['via_ref'], item['relation_type'], item['dependency_ref'],
            item['source_semantic_hash'],
        )
        for item in out['selected']
    ]


class CompactEAPTests(unittest.TestCase):
    def seed(self, plane):
        result = plane.transact(
            event_id='compact-seed', idem='compact-seed', base_epoch=plane.ledger.epoch,
            event_type='COMPACT_SEED', writer='test', ops=[
                {'op':'SET','domain':'semantic','key':'a','value':{'label':'amber pump'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'b','value':{'label':'coolant path'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'c','value':{'label':'return path'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':0.9,'relation_type':'FLOW'},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'bc','value':{'source':'semantic:b','target':'semantic:c','strength':0.8,'relation_type':'FLOW'},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        self.assertEqual(result['status'],'COMMITTED')

    def test_compact_cache_preserves_selected_signature_and_drops_dependency_rows(self):
        base_ledger=StateLedger(); compact_ledger=StateLedger()
        base=UnifiedDBEmergentPlane(UnifiedDBQueryPlane(base_ledger))
        compact=CompactUnifiedDBEmergentPlane(UnifiedDBQueryPlane(compact_ledger))
        self.seed(base); self.seed(compact)
        base_out=base.compile_active_assembly(PossibilitySpec('base',seed_refs=('semantic:a',),basis_epoch=base_ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        compact_out=compact.compile_active_assembly(PossibilitySpec('compact',seed_refs=('semantic:a',),basis_epoch=compact_ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        self.assertEqual(signature(base_out),signature(compact_out))
        self.assertIn('dependency:ab',base.preprocessor._rows_by_ref)
        self.assertNotIn('dependency:ab',compact.preprocessor._rows_by_ref)
        self.assertNotIn('dependency:bc',compact.preprocessor._rows_by_ref)
        self.assertEqual(compact_out['dependency_row_cache'],'DISCARDED_AFTER_COMPILE')
        self.assertEqual(compact_out['compact_cache_version'],'EAP-COMPACT-CACHE-1.6')
        base_ledger.close(); compact_ledger.close()

    def test_lazy_lexical_seed_works_without_dependency_row_cache(self):
        ledger=StateLedger(); plane=CompactUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger)); self.seed(plane)
        out=plane.compile_active_assembly(PossibilitySpec('lexical',query_text='amber pump',basis_epoch=ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0,lexical_weight=1.0))
        self.assertEqual(out['selected'][0]['ref'],'semantic:a')
        self.assertNotIn('dependency:ab',plane.preprocessor._rows_by_ref)
        ledger.close()

    def test_incremental_dependency_patch_remains_compact_and_visible(self):
        ledger=StateLedger(); plane=CompactIncrementalUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger)); self.seed(plane)
        plane.compile_active_assembly(PossibilitySpec('warm',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        plane.transact(
            event_id='compact-weight', idem='compact-weight', base_epoch=ledger.epoch,
            event_type='COMPACT_WEIGHT', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'ab','value':{'source':'semantic:a','target':'semantic:b','strength':0.5,'relation_type':'FLOW'},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        out=plane.compile_active_assembly(PossibilitySpec('after',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        self.assertNotIn('dependency:ab',plane.preprocessor._rows_by_ref)
        b=next(item for item in out['selected'] if item['ref']=='semantic:b')
        self.assertAlmostEqual(b['activation_score'],0.5*0.88)
        self.assertEqual(plane.preprocessor._edge_map_state_hash,ledger.semantic_state_hash)
        ledger.close()

    def test_external_dependency_write_rebuilds_compact_cache_safely(self):
        ledger=StateLedger(); plane=CompactIncrementalUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger)); self.seed(plane)
        plane.compile_active_assembly(PossibilitySpec('warm',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        ledger.append_event(
            event_id='external-compact', idem='external-compact', base_epoch=ledger.epoch,
            event_type='EXTERNAL', writer='external-test', ops=[
                {'op':'SET','domain':'dependency','key':'ac','value':{'source':'semantic:a','target':'semantic:c','strength':1.0,'relation_type':'DIRECT'},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        out=plane.compile_active_assembly(PossibilitySpec('rebuilt',seed_refs=('semantic:a',),basis_epoch=ledger.epoch,max_items=3,max_hops=2,min_edge_weight=0.0))
        self.assertIn('semantic:c',[item['ref'] for item in out['selected']])
        self.assertNotIn('dependency:ac',plane.preprocessor._rows_by_ref)
        self.assertIsNone(plane.preprocessor._edge_map_state_hash)
        ledger.close()


if __name__=='__main__':
    unittest.main()
