import random
import unittest

from possibility_preprocessor_v1 import PossibilityPreprocessor, PossibilityRule


class PossibilityPreprocessorTests(unittest.TestCase):
    def make_index(self, seed=7):
        rng = random.Random(seed)
        n = 96
        edges = set()
        while len(edges) < 260:
            a = rng.randrange(n)
            b = rng.randrange(n)
            if a != b:
                edges.add((a, b))
        rules = []
        for pid in range(240):
            req = tuple(sorted(rng.sample(range(n), rng.choice((2, 2, 3)))))
            rules.append(PossibilityRule(pid, req, rng.random()))
        return PossibilityPreprocessor(n, edges, rules), rng

    def brute_query(self, index, cues, k=10):
        active = 0
        for cue in cues:
            active |= index._compute_closure2(cue)
        ranked = []
        for rule, mask in zip(index.rules, index.rule_masks):
            if mask & active == mask:
                ranked.append((rule.utility, rule.possibility_id))
        ranked.sort(reverse=True)
        return [pid for _, pid in ranked[:k]]

    def test_query_matches_bruteforce(self):
        index, rng = self.make_index()
        for _ in range(200):
            cues = rng.sample(range(index.token_count), 3)
            self.assertEqual(index.query(cues), self.brute_query(index, cues))

    def test_1000_dependency_additions_remain_exact(self):
        index, rng = self.make_index()
        added = 0
        while added < 1000:
            a = rng.randrange(index.token_count)
            b = rng.randrange(index.token_count)
            if a == b or b in index.adj.get(a, ()):
                continue
            index.add_dependency(a, b)
            ok, bad = index.verify_exact()
            self.assertTrue(ok, bad[:10])
            added += 1

    def test_deletion_falls_back_to_targeted_recompute(self):
        index, _ = self.make_index()
        existing = [(a, b) for a, targets in index.adj.items() for b in targets]
        for a, b in existing[:100]:
            index.remove_dependency(a, b)
            ok, bad = index.verify_exact()
            self.assertTrue(ok, bad[:10])


if __name__ == '__main__':
    unittest.main()
