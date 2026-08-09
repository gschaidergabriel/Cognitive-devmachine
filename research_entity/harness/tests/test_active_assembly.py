import itertools
import random
import unittest

from research_entity.harness.reference.active_assembly import (
    AssemblyPacket,
    ActiveAssemblyError,
    compile_active_assembly,
    packet_score,
)


class ActiveAssemblyTests(unittest.TestCase):
    def fixture(self):
        return [
            AssemblyPacket("echo1", "famA", "knowledge", .99, .8, .2, .05, 7, "claim", "yes", "r1"),
            AssemblyPacket("echo2", "famA", "knowledge", .98, .8, .2, .05, 7, "claim", "yes", "r2"),
            AssemblyPacket("counter", "famB", "knowledge", .84, .9, .9, .2, 7, "claim", "no", "r3"),
            AssemblyPacket("cap", "famC", "capability", .8, .7, .5, .1, 7, reexpand_ref="capref"),
        ]

    def test_permutation_determinism(self):
        hashes = {
            compile_active_assembly(p, current_epoch=7, max_items=3, max_per_ancestry=1)["assembly_sha256"]
            for p in itertools.permutations(self.fixture())
        }
        self.assertEqual(len(hashes), 1)

    def test_shared_ancestry_cannot_hide_explicit_counterevidence(self):
        out = compile_active_assembly(self.fixture(), current_epoch=7, max_items=3, max_per_ancestry=1)
        self.assertIn("counter", [item["packet_id"] for item in out["items"]])

    def test_cognitive_packet_cannot_mint_authority(self):
        packet = AssemblyPacket("bad", "peer", "peer_result", 1, 1, 1, 0, 7, proposed_authority=True)
        with self.assertRaisesRegex(ActiveAssemblyError, "AUTHORITY_MINT_ATTEMPT"):
            compile_active_assembly([packet], current_epoch=7)

    def test_selected_capability_is_visible_but_not_authority(self):
        out = compile_active_assembly(self.fixture(), current_epoch=7)
        cap = next(item for item in out["items"] if item["packet_id"] == "cap")
        self.assertFalse(cap["execution_authority"])

    def test_stale_packet_is_omitted_with_reexpansion_reference(self):
        old = AssemblyPacket("old", "fam", "knowledge", 1, 1, 1, 0, 6, reexpand_ref="oldref")
        out = compile_active_assembly([old], current_epoch=7)
        self.assertEqual(out["items"], [])
        self.assertEqual(out["reexpand_refs"], ["oldref"])

    def test_budget_is_hard(self):
        out = compile_active_assembly(self.fixture(), current_epoch=7, max_items=2)
        self.assertEqual(len(out["items"]), 2)

    def test_scores_must_be_bounded(self):
        bad = AssemblyPacket("bad", "fam", "knowledge", 1.1, 1, 1, 0, 7)
        with self.assertRaisesRegex(ActiveAssemblyError, "BAD_SCORE"):
            packet_score(bad)

    def test_randomized_echo_fixture(self):
        rng = random.Random(20260809)
        trials = 5000
        naive_counter = 0
        aware_counter = 0
        for i in range(trials):
            candidates = [
                AssemblyPacket(
                    f"e{i}_{j}", "shared", "knowledge",
                    rng.uniform(.80, 1), rng.uniform(.5, .9), rng.uniform(.05, .3), rng.uniform(.02, .15),
                    1, "claim", "A"
                )
                for j in range(rng.randint(3, 10))
            ]
            candidates.append(AssemblyPacket(
                f"c{i}", "independent", "knowledge",
                rng.uniform(.65, .9), rng.uniform(.75, 1), rng.uniform(.6, 1), rng.uniform(.1, .35),
                1, "claim", "B"
            ))
            candidates.append(AssemblyPacket(
                f"x{i}", "other", "knowledge",
                rng.uniform(.5, .8), rng.uniform(.4, .8), rng.uniform(.3, .8), rng.uniform(.1, .4), 1
            ))
            naive = sorted(candidates, key=lambda p: (-packet_score(p), p.packet_id))[:3]
            naive_counter += any(p.claim_value == "B" for p in naive)
            aware = compile_active_assembly(candidates, current_epoch=1, max_items=3, max_per_ancestry=1)
            aware_counter += any(item["claim_value"] == "B" for item in aware["items"])
        self.assertEqual(aware_counter, trials)
        self.assertLess(naive_counter, aware_counter)


if __name__ == "__main__":
    unittest.main()
