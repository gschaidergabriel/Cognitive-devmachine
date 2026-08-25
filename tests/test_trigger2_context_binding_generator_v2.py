#!/usr/bin/env python3
from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools" / "trigger2_context_binding_generator_v2.py"
spec = importlib.util.spec_from_file_location("trigger2_context_binding_generator_v2", MODULE_PATH)
assert spec and spec.loader
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class Trigger2ContextBindingGeneratorV2Tests(unittest.TestCase):
    def setUp(self):
        self.rows = mod.generate_rows(mod.demo_atoms(), blocks=1, split="TRAIN", seed=20260825)

    def test_row_count_and_clean_audit(self):
        self.assertEqual(len(self.rows), 864)
        audit = mod.validate_rows(self.rows)
        self.assertEqual(audit["status"], "PASS", audit["failures"])
        self.assertEqual(audit["expected_rows_per_block"], 864)

    def test_every_semantic_mapping_cell_crosses_all_display_orders(self):
        cells = {}
        for row in self.rows:
            m = row["curriculum"]
            key = (
                m["block_id"], m["template_family"], m["query_polarity"],
                m["base_semantic_class"], tuple(m["s3_permutation"]),
            )
            cells.setdefault(key, []).append(row)
        self.assertEqual(len(cells), 144)
        for cell in cells.values():
            self.assertEqual(len(cell), 6)
            self.assertEqual(
                {tuple(r["curriculum"]["codebook_order"]) for r in cell},
                set(mod.CODEBOOK_ORDERS),
            )
            self.assertEqual(len({r["target"] for r in cell}), 1)
            self.assertEqual(len({mod._outside_codebook(r["prompt"]) for r in cell}), 1)

    def test_every_semantic_order_cell_crosses_all_s3_mappings(self):
        cells = {}
        for row in self.rows:
            m = row["curriculum"]
            key = (
                m["block_id"], m["template_family"], m["query_polarity"],
                m["base_semantic_class"], tuple(m["codebook_order"]),
            )
            cells.setdefault(key, []).append(row)
        self.assertEqual(len(cells), 144)
        for cell in cells.values():
            self.assertEqual(len(cell), 6)
            self.assertEqual(
                {tuple(r["curriculum"]["s3_permutation"]) for r in cell},
                set(mod.S3_PERMUTATIONS),
            )
            self.assertEqual(len({mod._outside_codebook(r["prompt"]) for r in cell}), 1)

    def test_display_order_has_zero_mutual_information(self):
        audit = mod.validate_rows(self.rows)
        for value in audit["display_order_mutual_information_bits"].values():
            self.assertAlmostEqual(value, 0.0, places=14)

    def test_drop_one_order_variant_fails_closed(self):
        audit = mod.validate_rows(self.rows[1:])
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(x.startswith("DISPLAY_ORDER_CELL_NOT_COMPLETE:") for x in audit["failures"]))

    def test_wrong_target_fails_closed(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["target"] = rows[0]["curriculum"]["atom_triplet"][1]
        audit = mod.validate_rows(rows)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(x.startswith("TARGET_SYMBOL_MISMATCH:") for x in audit["failures"]))

    def test_metadata_only_s3_permutation_fails_closed(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["curriculum"]["s3_permutation"] = [2, 1, 0]
        audit = mod.validate_rows(rows)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(x.startswith("S3_PERMUTATION_NOT_CAUSAL:") for x in audit["failures"]))

    def test_class_word_leak_outside_codebook_fails_closed(self):
        rows = copy.deepcopy(self.rows)
        rows[0]["prompt"] = rows[0]["prompt"].replace("SITUATION\n", "SITUATION\nALLOW ")
        audit = mod.validate_rows(rows)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(x.startswith("CLASS_WORD_LEAK:") for x in audit["failures"]))

    def test_atom_leak_outside_codebook_fails_closed(self):
        rows = copy.deepcopy(self.rows)
        atom = rows[0]["curriculum"]["atom_triplet"][0]
        rows[0]["prompt"] += "\n" + atom
        audit = mod.validate_rows(rows)
        self.assertEqual(audit["status"], "FAIL")
        self.assertTrue(any(x.startswith("TARGET_ATOM_LEAK_OUTSIDE_CODEBOOK:") for x in audit["failures"]))

    def test_rejected_or_atom_and_unbound_atoms_fail_before_generation(self):
        with self.assertRaisesRegex(ValueError, "rejected ABI atom 'or'"):
            mod.generate_rows([mod.Atom("or", 1, 1), mod.Atom("x", 2, 1), mod.Atom("y", 3, 1)])
        with self.assertRaisesRegex(ValueError, "externally observed single-token atoms"):
            mod.generate_rows([mod.Atom("x", None, 1), mod.Atom("y", 2, 1), mod.Atom("z", 3, 1)])


if __name__ == "__main__":
    unittest.main()
