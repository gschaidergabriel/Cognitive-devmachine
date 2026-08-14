import itertools
import unittest

from research_entity.harness.reference.active_assembly import (
    AssemblyPacket,
    ActiveAssemblyError,
    compile_active_assembly,
)


def p(packet_id, family, scoreish, cost, *, claim_key=None, claim_value=None, reexpand_ref=None):
    return AssemblyPacket(
        packet_id, family, "knowledge",
        scoreish, scoreish, scoreish, 0.1, 7,
        claim_key, claim_value, reexpand_ref,
        context_cost=cost,
    )


class ActiveAssemblyContextBudgetTests(unittest.TestCase):
    def test_context_cost_budget_is_hard(self):
        out = compile_active_assembly(
            [p("a", "A", .95, 7), p("b", "B", .9, 4), p("c", "C", .8, 3)],
            current_epoch=7,
            max_items=8,
            max_context_cost=10,
        )
        self.assertLessEqual(out["context_cost_used"], 10)
        self.assertEqual(out["context_cost_remaining"], 0)

    def test_default_preserves_count_only_compatibility(self):
        out = compile_active_assembly(
            [p("a", "A", .95, 100), p("b", "B", .9, 100)],
            current_epoch=7,
            max_items=2,
        )
        self.assertEqual(len(out["items"]), 2)
        self.assertIsNone(out["max_context_cost"])
        self.assertEqual(out["context_cost_used"], 200)

    def test_invalid_packet_cost_fails_closed(self):
        bad = AssemblyPacket("bad", "A", "knowledge", 1, 1, 1, 0, 7, context_cost=0)
        with self.assertRaisesRegex(ActiveAssemblyError, "BAD_CONTEXT_COST"):
            compile_active_assembly([bad], current_epoch=7)

    def test_invalid_context_budget_fails_closed(self):
        with self.assertRaisesRegex(ActiveAssemblyError, "BAD_CONTEXT_BUDGET"):
            compile_active_assembly([p("a", "A", .9, 1)], current_epoch=7, max_context_cost=0)

    def test_overbudget_packet_retains_reexpansion_reference(self):
        out = compile_active_assembly(
            [p("big", "A", .99, 20, reexpand_ref="detail:big"), p("small", "B", .8, 3)],
            current_epoch=7,
            max_context_cost=5,
        )
        self.assertEqual([x["packet_id"] for x in out["items"]], ["small"])
        self.assertIn("detail:big", out["reexpand_refs"])
        self.assertEqual(out["omitted_reasons"]["CONTEXT_COST_BUDGET"], 1)

    def test_conflict_visibility_never_breaks_cost_budget(self):
        candidates = [
            p("yes", "same", .95, 6, claim_key="k", claim_value="yes"),
            p("no", "same", .90, 6, claim_key="k", claim_value="no"),
            p("x", "C", .70, 2),
        ]
        out = compile_active_assembly(
            candidates,
            current_epoch=7,
            max_items=3,
            max_per_ancestry=1,
            max_context_cost=8,
        )
        self.assertLessEqual(out["context_cost_used"], 8)
        self.assertEqual(len([x for x in out["items"] if x["claim_key"] == "k"]), 1)
        self.assertGreaterEqual(out["omitted_reasons"].get("CONTEXT_COST_BUDGET", 0), 1)

    def test_cost_budgeted_hash_remains_permutation_invariant(self):
        candidates = [p("a", "A", .95, 5), p("b", "B", .9, 4), p("c", "C", .85, 3)]
        hashes = {
            compile_active_assembly(xs, current_epoch=7, max_context_cost=8)["assembly_sha256"]
            for xs in itertools.permutations(candidates)
        }
        self.assertEqual(len(hashes), 1)

    def test_context_cost_is_bound_into_packet_identity(self):
        a = p("same", "A", .9, 2)
        b = p("same", "A", .9, 3)
        with self.assertRaisesRegex(ActiveAssemblyError, "PACKET_ID_COLLISION:same"):
            compile_active_assembly([a, b], current_epoch=7, max_context_cost=10)


if __name__ == "__main__":
    unittest.main()
