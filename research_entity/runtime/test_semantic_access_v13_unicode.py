from __future__ import annotations

import sqlite3
import unittest
from pathlib import Path

from semantic_retrieval_runtime_v13 import (
    CyclePinnedSemanticAccessV13,
    NORMALIZER_VERSION,
    norm,
)

HERE = Path(__file__).resolve().parent


class SemanticAccessV13UnicodeTests(unittest.TestCase):
    def setUp(self):
        con = self.con = sqlite3.connect(":memory:")
        con.executescript((HERE / "RAE_UNIFIEDDB_V10_SEMANTIC_ACCESS_FABRIC.sql").read_text())
        con.executescript((HERE / "RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql").read_text())
        con.executescript((HERE / "RAE_UNIFIEDDB_V13_CYCLE_PINNED_FLAT_ACCESS.sql").read_text())
        con.execute(
            "INSERT INTO semantic_access_generations VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            ("g1", 1, 1, "d", "h1", 4, 4, "{}", "CURRENT", "t", "t", "t"),
        )
        con.execute("INSERT INTO semantic_access_head VALUES('CURRENT','g1',1,1,'h1','t')")
        for rank, (label, target) in enumerate(
            (("Öl", "record:oil"), ("Él", "record:spanish-pronoun"), ("北京", "record:beijing"), ("Москва", "record:moscow")),
            start=1,
        ):
            con.execute(
                "INSERT INTO semantic_access_flat_v13 VALUES(?,?,?,?,?,?,?,?)",
                ("g1", norm(label), target, target, rank, 1.0, 3.0, "{}"),
            )
        con.commit()
        self.runtime = CyclePinnedSemanticAccessV13(con)
        self.pin = self.runtime.pin("cycle-unicode", source_epoch=1, graph_epoch=1, pinned_at="t")

    def tearDown(self):
        self.con.close()

    def test_normalizer_version_is_explicit(self):
        self.assertEqual(NORMALIZER_VERSION, "unicode_nfkc_casefold_v1")

    def test_german_and_accented_keys_do_not_false_collide(self):
        self.assertNotEqual(norm("Öl"), norm("Él"))
        self.assertEqual(self.runtime.query(self.pin, "ÖL")[0], ("record:oil",))
        self.assertEqual(self.runtime.query(self.pin, "él")[0], ("record:spanish-pronoun",))

    def test_non_latin_keys_remain_addressable(self):
        self.assertEqual(norm("北京"), "北京")
        self.assertEqual(norm("Москва"), "москва")
        self.assertEqual(self.runtime.query(self.pin, "北京")[0], ("record:beijing",))
        self.assertEqual(self.runtime.query(self.pin, "МОСКВА")[0], ("record:moscow",))

    def test_nfkc_casefold_handles_german_sharp_s(self):
        self.assertEqual(norm("Straße"), norm("STRASSE"))

    def test_punctuation_only_query_abstains(self):
        rows, _ = self.runtime.query(self.pin, "— !!! …")
        self.assertEqual(rows, ())

    def test_limit_cannot_disable_bounded_read(self):
        for bad in (0, -1, 4097):
            with self.subTest(limit=bad):
                with self.assertRaises(ValueError):
                    self.runtime.query(self.pin, "Öl", limit=bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
