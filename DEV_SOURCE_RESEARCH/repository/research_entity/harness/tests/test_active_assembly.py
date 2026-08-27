import itertools
import random
import unittest

from research_entity.harness.reference.active_assembly import (
    AssemblyPacket,
    ActiveAssemblyError,
    compile_active_assembly,
    packet_identity_sha256,
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

    def test_same_ancestry_opposites_remain_visible_without_replication_credit(self):
        yes = AssemblyPacket("yes", "same-family", "knowledge", .9, .9, .5, .1, 7, "k", "yes", "yes-ref")
        no = AssemblyPacket("no", "same-family", "knowledge", .8, .9, .7, .2, 7, "k", "no", "no-ref")
        out = compile_active_assembly([yes, no], current_epoch=7, max_items=2, max_per_ancestry=1)
        self.assertEqual({item["packet_id"] for item in out["items"]}, {"yes", "no"})
        for item in out["items"]:
            self.assertEqual(item["selection_role"], "CONFLICT_VISIBILITY")
            self.assertFalse(item["independent_replication_credit"])

    def test_tight_total_budget_stays_hard_for_same_ancestry_conflict(self):
        yes = AssemblyPacket("yes", "same-family", "knowledge", .9, .9, .5, .1, 7, "k", "yes", "yes-ref")
        no = AssemblyPacket("no", "same-family", "knowledge", .8, .9, .7, .2, 7, "k", "no", "no-ref")
        out = compile_active_assembly([yes, no], current_epoch=7, max_items=1, max_per_ancestry=1)
        self.assertEqual(len(out["items"]), 1)
        self.assertEqual(set(out["reexpand_refs"]), {"no-ref"})

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

    def test_conflicting_duplicate_packet_id_fails_closed(self):
        a = AssemblyPacket("same", "fam", "knowledge", .8, .8, .8, .1, 7, "claim", "A", "r1", "peer-a")
        b = AssemblyPacket("same", "fam", "knowledge", .8, .8, .8, .1, 7, "claim", "B", "r2", "peer-b")
        for pair in ([a, b], [b, a]):
            with self.assertRaisesRegex(ActiveAssemblyError, "PACKET_ID_COLLISION:same"):
                compile_active_assembly(pair, current_epoch=7)

    def test_exact_duplicate_delivery_is_idempotent(self):
        packet = AssemblyPacket("same", "fam", "knowledge", .8, .8, .8, .1, 7, "claim", "A", "r1", "peer-a")
        single = compile_active_assembly([packet], current_epoch=7)
        duplicate = compile_active_assembly([packet, packet], current_epoch=7)
        self.assertEqual(single["assembly_sha256"], duplicate["assembly_sha256"])
        self.assertEqual(single["items"], duplicate["items"])
        self.assertEqual(duplicate["input_duplicate_count"], 1)
        self.assertEqual(single["input_duplicate_count"], 0)

    def test_selected_packet_exposes_bound_identity_fingerprint(self):
        packet = AssemblyPacket("id", "fam", "knowledge", .8, .7, .6, .1, 7)
        out = compile_active_assembly([packet], current_epoch=7)
        self.assertEqual(out["items"][0]["packet_identity_sha256"], packet_identity_sha256(packet))
        self.assertEqual(len(out["items"][0]["packet_identity_sha256"]), 64)

    def test_bad_empty_identity_fails_closed(self):
        packet = AssemblyPacket("", "fam", "knowledge", .8, .7, .6, .1, 7)
        with self.assertRaisesRegex(ActiveAssemblyError, "BAD_IDENTITY:packet_id"):
            compile_active_assembly([packet], current_epoch=7)

    def test_randomized_collision_fuzz(self):
        rng = random.Random(202608091921)
        trials = 10000
        silent = 0
        for i in range(trials):
            a = AssemblyPacket(
                f"id{i}", f"fam{rng.randrange(5)}", "knowledge",
                rng.random(), rng.random(), rng.random(), rng.random(), 1,
                "claim", f"A{rng.randrange(7)}", f"ref{i}", "peer-a"
            )
            b = AssemblyPacket(
                a.packet_id, a.ancestry_family, a.kind,
                a.relevance, a.impact, a.novelty, a.uncertainty, a.valid_epoch,
                a.claim_key, a.claim_value + ":mut", a.reexpand_ref, "peer-b"
            )
            try:
                compile_active_assembly([a, b], current_epoch=1)
                silent += 1
            except ActiveAssemblyError as exc:
                self.assertIn("PACKET_ID_COLLISION", str(exc))
        self.assertEqual(silent, 0)

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
