import unittest
from research_entity.harness.reference.possibility_frontier import (
    CapabilityEdge,
    RouteConstraints,
    StalePossibilityEpoch,
    best_route,
    compile_frontier,
)


class PossibilityFrontierTests(unittest.TestCase):
    def test_composition_can_beat_direct(self):
        edges = [
            CapabilityEdge('direct', 'a', 'c', 9, 90, .80, 1, True, True, 'L0'),
            CapabilityEdge('ab', 'a', 'b', 1, 10, .99, 1, True, True, 'L1'),
            CapabilityEdge('bc', 'b', 'c', 1, 10, .99, 1, True, True, 'L2'),
        ]
        compiled = compile_frontier(edges, source_epoch=4, graph_epoch=9, max_hops=2)
        route = best_route(compiled, 'a', 'c', source_epoch=4, graph_epoch=9)
        self.assertEqual(route.edge_refs, ('ab', 'bc'))

    def test_guards_never_upgrade_during_composition(self):
        edges = [
            CapabilityEdge('ab', 'a', 'b', 1, 1, .99, 2, True, True, 'L1'),
            CapabilityEdge('bc', 'b', 'c', 1, 1, .99, 0, False, False, 'L2'),
        ]
        compiled = compile_frontier(edges, source_epoch=1, graph_epoch=1, max_hops=2)
        route = compiled.routes[('a', 'c')][0]
        self.assertEqual(route.authority, 0)
        self.assertFalse(route.fresh)
        self.assertFalse(route.local)
        self.assertIsNone(best_route(
            compiled, 'a', 'c', RouteConstraints(min_authority=1, require_fresh=True),
            source_epoch=1, graph_epoch=1,
        ))

    def test_pareto_removes_dominated_route(self):
        edges = [
            CapabilityEdge('x1', 'a', 'b', 1, 1, .99, 1, True, True, 'L1'),
            CapabilityEdge('x2', 'a', 'b', 2, 2, .90, 1, True, True, 'L1'),
        ]
        compiled = compile_frontier(edges, source_epoch=1, graph_epoch=1, max_hops=1)
        self.assertEqual([r.edge_refs for r in compiled.routes[('a', 'b')]], [('x1',)])

    def test_epoch_mismatch_fails_closed(self):
        compiled = compile_frontier(
            [CapabilityEdge('x', 'a', 'b')], source_epoch=2, graph_epoch=3,
        )
        with self.assertRaises(StalePossibilityEpoch):
            best_route(compiled, 'a', 'b', source_epoch=1, graph_epoch=3)

    def test_energy_beam_is_explicitly_approximate(self):
        compiled = compile_frontier(
            [CapabilityEdge('x', 'a', 'b')], source_epoch=1, graph_epoch=1,
            beam_per_node=16, hub_penalty=.03,
        )
        self.assertTrue(compiled.approximate)
        self.assertEqual(compiled.beam_per_node, 16)
        self.assertEqual(compiled.authority, 'NON_AUTHORITATIVE_DERIVED_PREPROCESSOR')


if __name__ == '__main__':
    unittest.main()
