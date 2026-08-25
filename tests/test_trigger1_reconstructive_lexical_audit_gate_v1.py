from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_reconstructive_lexical_audit_gate_v1 as gate
import trigger1_native_q8_jspace_basis_build as current_basis


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def triad(family: str, words: tuple[str, str, str], *, field: str, target: str) -> list[dict]:
    return [
        {
            field: family,
            target: semantic,
            "prompt": f"/no_think Internally represent {word}. Do not answer with a code or class label.",
        }
        for semantic, word in zip(gate.TARGETS, words)
    ]


def candidate() -> dict:
    basis_words = (
        ("ratified", "vetoed", "unsettled"),
        ("admitted", "barred", "unresolved"),
        ("endorsed", "spurned", "undetermined"),
        ("activated", "disabled", "unspecified"),
        ("included", "excluded", "unclassified"),
        ("validated", "invalidated", "unascertained"),
    )
    basis_rows: list[dict] = []
    for index, words in enumerate(basis_words):
        basis_rows.extend(triad(f"basis-{index}", words, field="family_group_id", target="semantic_class"))

    calibration_words = (
        ("sanctioned", "prohibited", "pending"),
        ("welcomed", "rebuffed", "uncommitted"),
        ("authorized", "forbidden", "unresolvedly"),
    )
    holdout_words = (
        ("confirmed", "cancelled", "indeterminate"),
        ("chosen", "discarded", "unselected"),
        ("opened", "sealed", "unknown"),
    )

    def plan(split: str, families: tuple[tuple[str, str, str], ...]) -> dict:
        rows: list[dict] = []
        for index, words in enumerate(families):
            family = h(f"{split}:{index}")
            for semantic, word in zip(gate.TARGETS, words):
                rows.append({
                    "scenario_family_sha256": family,
                    "semantic_target": semantic,
                    "prompt": (
                        f"/no_think The observed relation is {word}. "
                        "Temporary action codes: A=first B=second C=third. Return only the code."
                    ),
                })
        return {"cases": rows}

    return {
        "reconstructive_lexical_audit": {"basis_rows": basis_rows},
        "preregistration_evidence": {
            "case_plans": {
                "CALIBRATION": plan("calibration", calibration_words),
                "HOLDOUT": plan("holdout", holdout_words),
            }
        },
        "abstract_state_deconfound": {
            "basis_model_facing_canonical_labels_absent": True,
            "holdout_model_facing_canonical_labels_absent": True,
            "basis_holdout_lexically_disjoint": True,
            "semantic_synonym_lexicon_disjoint": True,
            "lexical_audit_receipt_sha256": "a" * 64,
        },
    }


class ReconstructiveLexicalAuditTest(unittest.TestCase):
    def test_exact_text_reconstruction_passes_strict_disjoint_design(self):
        result = gate.adjudicate(candidate())
        self.assertTrue(result["pass"], result["failures"])

    def test_evaluation_abc_codebook_is_allowed(self):
        result = gate.adjudicate(candidate())
        self.assertTrue(result["pass"], result["failures"])

    def test_basis_abc_output_identity_is_forbidden(self):
        c = candidate()
        c["reconstructive_lexical_audit"]["basis_rows"][0]["prompt"] += " A"
        result = gate.adjudicate(c)
        self.assertFalse(result["pass"])
        self.assertTrue(any("BASIS_OUTPUT_CODE_IDENTITY" in x for x in result["failures"]))

    def test_distinct_family_hash_does_not_hide_reused_discriminative_word(self):
        c = candidate()
        rows = c["reconstructive_lexical_audit"]["basis_rows"]
        rows[3]["prompt"] = rows[3]["prompt"].replace("admitted", "ratified")
        result = gate.adjudicate(c)
        self.assertFalse(result["pass"])
        self.assertTrue(any("BASIS_DISCRIMINATIVE_LEXICAL_OVERLAP" in x for x in result["failures"]))

    def test_canonical_semantic_metadata_label_in_model_text_fails(self):
        c = candidate()
        c["preregistration_evidence"]["case_plans"]["HOLDOUT"]["cases"][0]["prompt"] += " AFFIRMATIVE"
        result = gate.adjudicate(c)
        self.assertFalse(result["pass"])
        self.assertTrue(any("CANONICAL_SEMANTIC_LABEL" in x for x in result["failures"]))

    def test_current_q8_basis_does_not_silently_pass_strict_lexical_disjointness(self):
        c = candidate()
        c["reconstructive_lexical_audit"]["basis_rows"] = current_basis.design_rows()
        result = gate.adjudicate(c)
        self.assertFalse(result["pass"])
        self.assertTrue(any("BASIS_DISCRIMINATIVE_LEXICAL_OVERLAP" in x for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
