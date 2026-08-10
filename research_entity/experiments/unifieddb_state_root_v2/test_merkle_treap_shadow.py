from __future__ import annotations

import random
import unittest

from merkle_treap_shadow import MerkleTreapShadow


def row(i: int, revision: int = 0):
    return {
        "domain": f"d{i % 7}",
        "key": f"k{i:05d}",
        "value": {"i": i, "revision": revision},
        "epistemic": "KNOWN" if i % 11 else "CONFLICT",
        "status": "CURRENT" if i % 13 else "SUPERSEDED",
        "domain_epoch": 1 + revision,
        "semantic_hash": f"sem-{i}-{revision}",
    }


class MerkleTreapShadowTests(unittest.TestCase):
    def test_rebuild_is_order_independent(self):
        rows = [row(i) for i in range(500)]
        expected = MerkleTreapShadow.rebuild(rows).state_merkle_root
        for seed in range(8):
            shuffled = rows[:]
            random.Random(seed).shuffle(shuffled)
            self.assertEqual(expected, MerkleTreapShadow.rebuild(shuffled).state_merkle_root)

    def test_incremental_existing_updates_match_full_rebuild(self):
        rows = {i: row(i) for i in range(1000)}
        shadow = MerkleTreapShadow.rebuild(rows.values())
        rng = random.Random(20260810)
        for revision in range(1, 400):
            i = rng.randrange(1000)
            rows[i] = row(i, revision)
            shadow.upsert(rows[i])
        check = shadow.verify_rebuild(rows.values())
        self.assertTrue(check["verified"], check)

    def test_incremental_new_keys_match_full_rebuild(self):
        rows = {i: row(i) for i in range(200)}
        shadow = MerkleTreapShadow.rebuild(rows.values())
        for i in range(200, 350):
            rows[i] = row(i, i)
            receipt = shadow.upsert(rows[i])
            self.assertTrue(receipt["inserted"])
        self.assertTrue(shadow.verify_rebuild(rows.values())["verified"])

    def test_semantic_row_change_changes_root(self):
        rows = [row(i) for i in range(50)]
        shadow = MerkleTreapShadow.rebuild(rows)
        before = shadow.state_merkle_root
        changed = row(7, 99)
        shadow.upsert(changed)
        self.assertNotEqual(before, shadow.state_merkle_root)

    def test_wrapper_binds_epoch_domain_epochs_and_chain(self):
        shadow = MerkleTreapShadow.rebuild([row(1)])
        a = shadow.wrapper_root(global_epoch=1, domain_epochs={"d1": 1}, semantic_chain_hash="a")
        b = shadow.wrapper_root(global_epoch=2, domain_epochs={"d1": 1}, semantic_chain_hash="a")
        c = shadow.wrapper_root(global_epoch=1, domain_epochs={"d1": 2}, semantic_chain_hash="a")
        d = shadow.wrapper_root(global_epoch=1, domain_epochs={"d1": 1}, semantic_chain_hash="b")
        self.assertEqual(4, len({a, b, c, d}))

    def test_duplicate_semantic_key_fails_closed(self):
        with self.assertRaises(ValueError):
            MerkleTreapShadow.rebuild([row(1), row(1)])


if __name__ == "__main__":
    unittest.main()
