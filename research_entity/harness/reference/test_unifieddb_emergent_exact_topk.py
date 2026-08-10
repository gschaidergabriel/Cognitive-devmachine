import unittest

from .state_ledger import StateLedger
from .unifieddb_query_plane import UnifiedDBQueryPlane
from .unifieddb_emergent_preprocessor import UnifiedDBEmergentPlane, PossibilitySpec
from .unifieddb_emergent_exact_topk import (
    ExactTopKUnifiedDBEmergentPlane,
    IncrementalExactTopKUnifiedDBEmergentPlane,
)


def selected_signature(assembly):
    return [
        (
            item['ref'],
            item['activation_score'],
            item['hop'],
            item['via_ref'],
            item['relation_type'],
            item['dependency_ref'],
        )
        for item in assembly['selected']
    ]


class ExactTopKTests(unittest.TestCase):
    def seed_tree(self, plane, *, equal_weights=False):
        ops = []
        for index in range(50):
            ops.append({
                'op':'SET','domain':'semantic','key':f'n{index:02d}',
                'value':{'label':f'node-{index:02d}'},'epistemic':'KNOWN','status':'CURRENT',
            })
        edge_number = 0
        for index in range(50):
            for ordinal, child in enumerate((3*index+1,3*index+2,3*index+3)):
                if child >= 50:
                    continue
                weight = 1.0 if equal_weights else (0.97,0.91,0.84)[ordinal]
                ops.append({
                    'op':'SET','domain':'dependency','key':f'e{edge_number:03d}',
                    'value':{
                        'source':f'semantic:n{index:02d}',
                        'target':f'semantic:n{child:02d}',
                        'strength':weight,
                        'relation_type':'POSSIBILITY',
                    },
                    'epistemic':'KNOWN','status':'CURRENT',
                })
                edge_number += 1
        result = plane.transact(
            event_id='tree-seed', idem='tree-seed', base_epoch=plane.ledger.epoch,
            event_type='TREE_SEED', writer='test', ops=ops,
        )
        self.assertEqual(result['status'],'COMMITTED')

    def test_strict_score_bound_preserves_selected_topk_and_reduces_expansions(self):
        base_ledger = StateLedger()
        opt_ledger = StateLedger()
        base = UnifiedDBEmergentPlane(UnifiedDBQueryPlane(base_ledger))
        opt = ExactTopKUnifiedDBEmergentPlane(UnifiedDBQueryPlane(opt_ledger))
        self.seed_tree(base)
        self.seed_tree(opt)
        base_out = base.compile_active_assembly(PossibilitySpec(
            'base', seed_refs=('semantic:n00',), basis_epoch=base_ledger.epoch,
            max_items=12, max_hops=3, frontier_budget=512, min_edge_weight=0.0,
        ))
        opt_out = opt.compile_active_assembly(PossibilitySpec(
            'opt', seed_refs=('semantic:n00',), basis_epoch=opt_ledger.epoch,
            max_items=12, max_hops=3, frontier_budget=512, min_edge_weight=0.0,
        ))
        self.assertEqual(selected_signature(base_out), selected_signature(opt_out))
        self.assertLess(opt_out['frontier_expansions'], base_out['frontier_expansions'])
        self.assertEqual(opt_out['frontier_stop_reason'],'EXACT_TOP_K_SCORE_BOUND')
        self.assertFalse(opt_out['frontier_exhausted'])
        base_ledger.close(); opt_ledger.close()

    def test_equal_score_ties_are_not_pruned(self):
        base_ledger = StateLedger()
        opt_ledger = StateLedger()
        base = UnifiedDBEmergentPlane(UnifiedDBQueryPlane(base_ledger))
        opt = ExactTopKUnifiedDBEmergentPlane(UnifiedDBQueryPlane(opt_ledger))
        self.seed_tree(base, equal_weights=True)
        self.seed_tree(opt, equal_weights=True)
        spec_base = PossibilitySpec(
            'base-tie', seed_refs=('semantic:n00',), basis_epoch=base_ledger.epoch,
            max_items=5, max_hops=1, frontier_budget=512, min_edge_weight=0.0, hop_decay=1.0,
        )
        spec_opt = PossibilitySpec(
            'opt-tie', seed_refs=('semantic:n00',), basis_epoch=opt_ledger.epoch,
            max_items=5, max_hops=1, frontier_budget=512, min_edge_weight=0.0, hop_decay=1.0,
        )
        base_out = base.compile_active_assembly(spec_base)
        opt_out = opt.compile_active_assembly(spec_opt)
        self.assertEqual(selected_signature(base_out), selected_signature(opt_out))
        self.assertEqual(opt_out['frontier_stop_reason'],'FRONTIER_EXHAUSTED')
        base_ledger.close(); opt_ledger.close()

    def test_negative_space_gate_remains_causally_active(self):
        ledger = StateLedger()
        opt = ExactTopKUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        opt.transact(
            event_id='negative', idem='negative', base_epoch=0,
            event_type='NEGATIVE', writer='test', ops=[
                {'op':'SET','domain':'semantic','key':'anchor','value':'anchor','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'real','value':'real','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'conflict','value':'conflict','epistemic':'CONFLICT','status':'CURRENT'},
                {'op':'SET','domain':'semantic','key':'decoy','value':'decoy','epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ar','value':{'source':'semantic:anchor','target':'semantic:real','strength':0.60},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'ac','value':{'source':'semantic:anchor','target':'semantic:conflict','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
                {'op':'SET','domain':'dependency','key':'cd','value':{'source':'semantic:conflict','target':'semantic:decoy','strength':1.0},'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        out = opt.compile_active_assembly(PossibilitySpec(
            'negative', seed_refs=('semantic:anchor',), basis_epoch=ledger.epoch,
            max_items=2, max_hops=2, frontier_budget=32, min_edge_weight=0.0,
        ))
        refs = [item['ref'] for item in out['selected']]
        self.assertEqual(refs,['semantic:anchor','semantic:real'])
        self.assertNotIn('semantic:decoy',refs)
        self.assertIn('semantic:conflict',out['blocked_propagation_refs'])
        ledger.close()

    def test_incremental_exact_topk_survives_dependency_patch(self):
        ledger = StateLedger()
        plane = IncrementalExactTopKUnifiedDBEmergentPlane(UnifiedDBQueryPlane(ledger))
        self.seed_tree(plane)
        before = plane.compile_active_assembly(PossibilitySpec(
            'before', seed_refs=('semantic:n00',), basis_epoch=ledger.epoch,
            max_items=12, max_hops=3, frontier_budget=512, min_edge_weight=0.0,
        ))
        plane.transact(
            event_id='weight-update', idem='weight-update', base_epoch=ledger.epoch,
            event_type='WEIGHT_UPDATE', writer='test', ops=[
                {'op':'SET','domain':'dependency','key':'e000',
                 'value':{'source':'semantic:n00','target':'semantic:n01','strength':0.55,'relation_type':'POSSIBILITY'},
                 'epistemic':'KNOWN','status':'CURRENT'},
            ]
        )
        after = plane.compile_active_assembly(PossibilitySpec(
            'after', seed_refs=('semantic:n00',), basis_epoch=ledger.epoch,
            max_items=12, max_hops=3, frontier_budget=512, min_edge_weight=0.0,
        ))
        self.assertEqual(after['preprocessor_version'],'EAP-EXACT-TOPK-1.5')
        self.assertEqual(after['frontier_stop_reason'],'EXACT_TOP_K_SCORE_BOUND')
        self.assertNotEqual(selected_signature(before),selected_signature(after))
        self.assertEqual(plane.preprocessor._compiled_epoch,ledger.epoch)
        ledger.close()


if __name__ == '__main__':
    unittest.main()
