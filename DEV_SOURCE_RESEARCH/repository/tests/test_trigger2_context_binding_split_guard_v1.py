from __future__ import annotations

import unittest

from tools import trigger2_context_binding_generator_v1 as gen
from tools import trigger2_context_binding_split_guard_v1 as guard


def row(split: str, template: str, situation: str, atom_ids: list[int], family: str) -> dict:
    return {
        "split": split,
        "family_id": family,
        "provenance_ancestry_id": f"prov-{family}",
        "curriculum": {"template_family": template, "atom_token_ids": atom_ids},
        "prompt": (
            "CODEBOOK\nALLOW -> x\nDENY -> y\nABSTAIN -> z\nEND_CODEBOOK\n\n"
            f"SITUATION\n{situation}\n\nQuestion: choose the mapped marker."
        ),
    }


class Trigger2ContextBindingSplitGuardTests(unittest.TestCase):
    def test_accepts_explicitly_disjoint_bundle(self):
        rows = [
            row("TRAIN", "train_a", "train-only lexical family one", [1, 2, 3], "f-train"),
            row("VALIDATION", "val_a", "validation-only lexical family two", [4, 5, 6], "f-val"),
            row("HOLDOUT", "hold_a", "holdout-only lexical family three", [7, 8, 9], "f-hold"),
        ]
        result = guard.adjudicate(rows)
        self.assertTrue(result["pass"], result["failures"])

    def test_rejects_semantic_template_and_holdout_atom_reuse(self):
        same = "identical semantic-bearing text and query stem"
        rows = [
            row("TRAIN", "shared_template", same, [1, 2, 3], "f-train"),
            row("VALIDATION", "shared_template", same, [4, 5, 6], "f-val"),
            row("HOLDOUT", "shared_template", same, [2, 7, 8], "f-hold"),
        ]
        result = guard.adjudicate(rows)
        self.assertFalse(result["pass"])
        joined = "\n".join(result["failures"])
        self.assertIn("MODEL_VISIBLE_SEMANTIC_OVERLAP:TRAIN:HOLDOUT", joined)
        self.assertIn("TEMPLATE_FAMILY_OVERLAP:TRAIN:HOLDOUT", joined)
        self.assertIn("HOLDOUT_ATOM_REUSE:TRAIN:HOLDOUT", joined)

    def test_current_v1_multisplit_reuse_is_quarantined(self):
        # v1 exposes a split switch but uses the same SEMANTIC_BANK/templates for all splits.
        # The guard must make that unsafe multi-split use fail closed rather than treating
        # split labels as evidence of lexical/template independence.
        atoms = gen.demo_atoms()
        rows = []
        for split in ("TRAIN", "VALIDATION", "HOLDOUT"):
            rows.extend(gen.generate_rows(atoms, split=split, blocks=1, seed=20260825))
        result = guard.adjudicate(rows)
        self.assertFalse(result["pass"])
        joined = "\n".join(result["failures"])
        self.assertIn("MODEL_VISIBLE_SEMANTIC_OVERLAP:TRAIN:HOLDOUT", joined)
        self.assertIn("TEMPLATE_FAMILY_OVERLAP:TRAIN:HOLDOUT", joined)
        self.assertIn("HOLDOUT_ATOM_REUSE:TRAIN:HOLDOUT", joined)

    def test_recognizes_current_codebook_delimiter_families(self):
        prompts = [
            "CODEBOOK\nALLOW -> x\nDENY -> y\nABSTAIN -> z\nEND_CODEBOOK\ncase-a",
            "<CODEBOOK>ALLOW=>x;DENY=>y;ABSTAIN=>z</CODEBOOK>\ncase-b",
            "CODEBOOK_BEGIN ALLOW -> x; DENY -> y; ABSTAIN -> z CODEBOOK_END\ncase-c",
        ]
        surfaces = [guard.model_visible_semantic_surface(x) for x in prompts]
        self.assertIn("case-a", surfaces[0])
        self.assertIn("case-b", surfaces[1])
        self.assertIn("case-c", surfaces[2])

    def test_missing_atom_identity_fails_closed(self):
        rows = []
        for split, template in (("TRAIN", "ta"), ("VALIDATION", "va"), ("HOLDOUT", "ha")):
            rows.append({
                "split": split,
                "family_id": f"f-{split}",
                "provenance_ancestry_id": f"p-{split}",
                "curriculum": {"template_family": template},
                "prompt": f"<CODEBOOK>ALLOW=>x;DENY=>y;ABSTAIN=>z</CODEBOOK>\n{split}-only-surface",
            })
        result = guard.adjudicate(rows)
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("ATOM_IDENTITY_MISSING:HOLDOUT") for x in result["failures"]))

    def test_rejects_missing_split(self):
        result = guard.adjudicate([
            row("TRAIN", "train_a", "train text", [1, 2, 3], "f-train"),
            row("VALIDATION", "val_a", "val text", [4, 5, 6], "f-val"),
        ])
        self.assertFalse(result["pass"])
        self.assertTrue(any(x.startswith("MISSING_SPLITS:HOLDOUT") for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
