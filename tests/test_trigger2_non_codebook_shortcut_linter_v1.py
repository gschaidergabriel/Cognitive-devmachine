from __future__ import annotations

import itertools
import unittest

from tools.trigger2_non_codebook_shortcut_linter_v1 import analyze

CLASSES = ("ALLOW", "DENY", "ABSTAIN")
TEMPLATES = ("procedural", "evidence", "state", "counterfactual")
POLARITIES = ("DIRECT", "INVERTED")
PERMS = tuple(itertools.permutations(range(3)))
ORDERS = tuple(itertools.permutations(CLASSES))


def target_class(base: str, polarity: str) -> str:
    if polarity == "DIRECT":
        return base
    return {"ALLOW": "DENY", "DENY": "ALLOW", "ABSTAIN": "ABSTAIN"}[base]


def rows_for_formula(*, repaired: bool, blocks: int = 1) -> list[dict]:
    rows: list[dict] = []
    row_index = 0
    for block in range(blocks):
        atoms = (f"B{block}A", f"B{block}B", f"B{block}C")
        for perm_index, perm in enumerate(PERMS):
            mapping = {CLASSES[i]: atoms[perm[i]] for i in range(3)}
            for template_index, template in enumerate(TEMPLATES):
                for polarity_index, polarity in enumerate(POLARITIES):
                    for base_class_index, base_class in enumerate(CLASSES):
                        # Current-main formula couples lexical surface to block + S3 permutation.
                        # Repair removes both causal mapping variables from lexical selection.
                        if repaired:
                            variant = (template_index + polarity_index + base_class_index) % 3
                        else:
                            variant = (
                                block
                                + perm_index
                                + template_index
                                + polarity_index
                                + base_class_index
                            ) % 3
                        tc = target_class(base_class, polarity)
                        order = ORDERS[row_index % len(ORDERS)]
                        codebook = "\n".join(
                            ["CODEBOOK"]
                            + [f"{klass} -> {mapping[klass]}" for klass in order]
                            + ["END_CODEBOOK"]
                        )
                        prompt = (
                            codebook
                            + f"\n\nSITUATION\n{template}|{polarity}|{base_class}|variant={variant}"
                            + "\nQuestion: q"
                        )
                        rows.append(
                            {
                                "prompt": prompt,
                                "target": mapping[tc],
                                "curriculum": {
                                    "base_semantic_class": base_class,
                                    "target_semantic_class": tc,
                                    "template_family": template,
                                    "query_polarity": polarity,
                                    "lexical_variant_index": variant,
                                    "codebook_order": list(order),
                                },
                            }
                        )
                        row_index += 1
    return rows


class Trigger2NonCodebookShortcutLinterTests(unittest.TestCase):
    def test_current_formula_is_detected(self):
        audit = analyze(rows_for_formula(repaired=False, blocks=1))
        self.assertFalse(audit["pass"])
        self.assertAlmostEqual(audit["outside_surface_target_mi_bits"], 0.6960736118322682, places=12)
        self.assertGreater(audit["outside_surface_lookup_accuracy"], audit["marginal_target_chance"])

    def test_repaired_formula_removes_surface_shortcut(self):
        audit = analyze(rows_for_formula(repaired=True, blocks=1))
        self.assertTrue(audit["pass"], audit["failures"])
        self.assertAlmostEqual(audit["outside_surface_target_mi_bits"], 0.0, places=12)
        self.assertAlmostEqual(
            audit["outside_surface_lookup_accuracy"], audit["marginal_target_chance"], places=12
        )

    def test_repair_stays_clean_across_blocks(self):
        audit = analyze(rows_for_formula(repaired=True, blocks=4))
        self.assertTrue(audit["pass"], audit["failures"])
        self.assertAlmostEqual(audit["outside_surface_target_mi_bits"], 0.0, places=12)


if __name__ == "__main__":
    unittest.main()
