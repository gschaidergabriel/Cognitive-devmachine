from dataclasses import dataclass
import unittest

from research_entity.harness.reference.possibility_field_compiler import (
    PossibilityFieldCompiler,
    PossibilityFieldQuery,
)
from research_entity.harness.reference.possibility_frontier import (
    CapabilityEdge,
    RouteConstraints,
    StalePossibilityEpoch,
    compile_frontier,
)
from research_entity.runtime.semantic_gap_controller_v15 import (
    EvidenceItem,
    EvidenceRequirement,
    SufficiencyGapControllerV15,
)


@dataclass(frozen=True)
class SemanticResult:
    refs: tuple[str, ...]
    mode: str = 'MISS'
    seed_id: str | None = None
    generation_id: str | None = None
    sufficient: bool = False


class FakeSemantic:
    def __init__(self, result):
        self.result = result
        self.calls = 0
    def query_seed(self, *args, **kwargs):
        self.calls += 1
        return self.result


class Ledger:
    def __init__(self, epoch): self.epoch = epoch


class FakeEAP:
    def __init__(self, epoch=7, selected=()):
        self.ledger = Ledger(epoch)
        self.calls = 0
        self.selected = selected
    def compile_active_assembly(self, spec):
        self.calls += 1
        return {
            'selected': [{'ref': ref} for ref in self.selected],
            'suppressed': [{'ref': 'semantic:conflict'}],
            'blocked_propagation_refs': ('semantic:conflict',),
            'selection_hash': 'assembly-hash',
        }


class PossibilityFieldCompilerTests(unittest.TestCase):
    def test_sufficient_generation_stops_without_padding_or_deepening(self):
        semantic = FakeSemantic(SemanticResult(
            ('claim:a','claim:b'), mode='SEMANTIC_GENERATION_SUFFICIENT',
            seed_id='seed:x', generation_id='gen:9', sufficient=True,
        ))
        eap = FakeEAP(selected=('semantic:noise',))
        compiler = PossibilityFieldCompiler(semantic, eap)
        receipt = compiler.compile(PossibilityFieldQuery('q1','known semantic family',7,9,max_items=12))
        self.assertEqual(receipt.mode, 'COMPILED_SUFFICIENT')
        self.assertEqual(receipt.selected_refs, ('claim:a','claim:b'))
        self.assertTrue(receipt.sufficient)
        self.assertEqual(receipt.deepening_count, 0)
        self.assertEqual(eap.calls, 0)

    def test_compositional_route_precedes_generic_deepening(self):
        semantic = FakeSemantic(SemanticResult((), sufficient=False))
        eap = FakeEAP(selected=('semantic:fallback',))
        frontier = compile_frontier([
            CapabilityEdge('direct','ask','done',9,90,.80,1,True,True,'L0'),
            CapabilityEdge('ask-tool','ask','tool',1,10,.99,1,True,True,'L1'),
            CapabilityEdge('tool-done','tool','done',1,10,.99,1,True,True,'L2'),
        ], source_epoch=7, graph_epoch=9, max_hops=2)
        compiler = PossibilityFieldCompiler(
            semantic, eap, frontier_provider=lambda source_epoch, graph_epoch: frontier
        )
        receipt = compiler.compile(PossibilityFieldQuery(
            'q2','execute best route',7,9,
            route_source='ask', route_target='done',
            route_constraints=RouteConstraints(min_authority=1,require_fresh=True),
        ))
        self.assertEqual(receipt.mode, 'COMPILED_COMPOSITIONAL')
        self.assertEqual(receipt.selected_refs, ('ask-tool','tool-done'))
        self.assertEqual(receipt.deepening_count, 1)
        self.assertEqual(eap.calls, 0)

    def test_typed_gap_controller_closes_missing_ref_before_eap(self):
        semantic = FakeSemantic(SemanticResult(('semantic:anchor',), sufficient=False))
        eap = FakeEAP(selected=('semantic:fallback',))
        items = {
            'semantic:anchor': EvidenceItem('semantic:anchor', frozenset({'anchor'})),
            'semantic:needed': EvidenceItem('semantic:needed', frozenset({'need:one'})),
        }
        def expand(query_text, terms, selected, source_epoch, graph_epoch, budget):
            del query_text, selected, source_epoch, graph_epoch, budget
            return [items['semantic:needed']] if 'semantic:needed' in terms else []
        gap = SufficiencyGapControllerV15(expand=expand, max_rounds=1, max_items=8)
        compiler = PossibilityFieldCompiler(
            semantic,
            eap,
            gap_controller=gap,
            evidence_item_resolver=lambda refs: [items[ref] for ref in refs],
        )
        receipt = compiler.compile(PossibilityFieldQuery(
            'q-gap','find exact missing evidence',7,9,
            evidence_requirements=(EvidenceRequirement(
                'need-one', required_refs=frozenset({'semantic:needed'}), min_items=1
            ),),
        ))
        self.assertEqual(receipt.mode, 'GAP_CONTROLLED_SUFFICIENT')
        self.assertEqual(receipt.selected_refs, ('semantic:anchor','semantic:needed'))
        self.assertEqual(receipt.gap_rounds, 1)
        self.assertEqual(receipt.remaining_gap_ids, ())
        self.assertEqual(eap.calls, 0)

    def test_unclosed_typed_gap_falls_to_eap_and_surfaces_gap_id(self):
        semantic = FakeSemantic(SemanticResult(('semantic:anchor',), sufficient=False))
        eap = FakeEAP(selected=('semantic:fallback',))
        items = {'semantic:anchor': EvidenceItem('semantic:anchor', frozenset({'anchor'}))}
        gap = SufficiencyGapControllerV15(expand=lambda *args: [], max_rounds=1, max_items=8)
        compiler = PossibilityFieldCompiler(
            semantic,
            eap,
            gap_controller=gap,
            evidence_item_resolver=lambda refs: [items[ref] for ref in refs],
        )
        receipt = compiler.compile(PossibilityFieldQuery(
            'q-gap-miss','missing evidence stays missing',7,9,
            evidence_requirements=(EvidenceRequirement(
                'need-missing', required_refs=frozenset({'semantic:missing'}), min_items=1
            ),),
        ))
        self.assertEqual(receipt.mode, 'EAP_ACTIVE_ASSEMBLY')
        self.assertEqual(receipt.remaining_gap_ids, ('need-missing',))
        self.assertEqual(receipt.gap_rounds, 1)
        self.assertEqual(eap.calls, 1)

    def test_insufficient_paths_deepen_to_eap_and_preserve_negative_space(self):
        semantic = FakeSemantic(SemanticResult(('legacy:x',), mode='SEMANTIC_SEED_FASTPATH', sufficient=False))
        eap = FakeEAP(selected=('semantic:a','semantic:b'))
        compiler = PossibilityFieldCompiler(semantic, eap)
        receipt = compiler.compile(PossibilityFieldQuery('q3','unknown wrapper',7,9))
        self.assertEqual(receipt.mode, 'EAP_ACTIVE_ASSEMBLY')
        self.assertEqual(receipt.selected_refs, ('semantic:a','semantic:b'))
        self.assertEqual(receipt.suppressed_refs, ('semantic:conflict',))
        self.assertEqual(receipt.blocked_propagation_refs, ('semantic:conflict',))
        self.assertEqual(receipt.deepening_count, 2)
        self.assertEqual(eap.calls, 1)

    def test_empty_deepening_abstains(self):
        compiler = PossibilityFieldCompiler(FakeSemantic(SemanticResult(())), FakeEAP(selected=()))
        receipt = compiler.compile(PossibilityFieldQuery('q4','zzzz unknown',7,9))
        self.assertEqual(receipt.mode, 'ABSTAIN')
        self.assertFalse(receipt.sufficient)

    def test_stale_source_epoch_fails_before_any_retrieval(self):
        semantic = FakeSemantic(SemanticResult(('x',), sufficient=True))
        eap = FakeEAP(epoch=7)
        compiler = PossibilityFieldCompiler(semantic, eap)
        with self.assertRaises(StalePossibilityEpoch):
            compiler.compile(PossibilityFieldQuery('q5','stale',6,9))
        self.assertEqual(semantic.calls, 0)
        self.assertEqual(eap.calls, 0)


if __name__ == '__main__':
    unittest.main()
