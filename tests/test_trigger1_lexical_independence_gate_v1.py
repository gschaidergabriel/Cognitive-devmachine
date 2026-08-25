from __future__ import annotations

import hashlib
import unittest

from tools import trigger1_lexical_independence_gate_v1 as gate
from tools import trigger1_native_q8_jspace_basis_build as current_basis


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def triad(prefix: str, family: str, words: tuple[str, str, str], *, field: str, target: str) -> list[dict]:
    rows = []
    for semantic, word in zip(gate.TARGETS, words):
        rows.append({
            field: family,
            target: semantic,
            "prompt": f"/no_think Internally represent {word}. Do not answer with a code or class label.",
        })
    return rows


def clean_candidate() -> dict:
    basis_words = (
        ("ratified", "vetoed", "unsettled"),
        ("admitted", "barred", "unresolved"),
        ("endorsed", "spurned", "undetermined"),
        ("activated", "disabled", "unspecified"),
        ("included", "excluded", "unclassified"),
        ("validated", "invalidated", "unascertained"),
    )
    basis = []
    for i, words in enumerate(basis_words):
        basis += triad("basis", f"basis-{i}", words, field="family_group_id", target="semantic_class")

    cal_words = (
        ("sanctioned", "prohibited", "pending"),
        ("welcomed", "rebuffed", "uncommitted"),
        ("authorized", "forbidden", "unresolvedly"),
    )
    hold_words = (
        ("confirmed", "cancelled", "indeterminate"),
        ("chosen", "discarded", "unselected"),
        ("opened", "sealed", "unknown"),
    )

    def plan(split: str, families: tuple[tuple[str, str, str], ...]) -> dict:
        cases = []
        for i, words in enumerate(families):
            fam = h(f"{split}-scenario-{i}")
            for semantic, word in zip(gate.TARGETS, words):
                cases.append({
                    "scenario_family_sha256": fam,
                    "semantic_target": semantic,
                    "prompt": f"/no_think The observed relation is {word}. Return only the temporary action code.",
                })
        return {"cases": cases}

    return {
        "runtime_intervention_class": "LOCAL_LLAMA_CPP_CVEC_APPLIED",
        "intervention": {
            "token_scope": "ALL_PROMPT_TOKENS",
            "strict_last_token_replication_claimed": False,
        },
        "lexical_independence_evidence": {"basis_rows": basis},
        "preregistration_evidence": {
            "case_plans": {
                "CALIBRATION": plan("cal", cal_words),
                "HOLDOUT": plan("hold", hold_words),
            }
        },
        "calibration": {"semantic_target_x_output_code_factorial": True},
        "holdout": {
            "semantic_target_x_output_code_factorial": True,
            "semantic_target_interaction_test": True,
            "per_family_semantic_target_interaction": True,
            "off_target_drift_test": True,
            "off_target_drift_within_preregistered_threshold": True,
            "off_target_drift_receipt_sha256": "a" * 64,
        },
    }


class Trigger1LexicalIndependenceGateTests(unittest.TestCase):
    def test_strict_cross_family_and_cross_partition_design_passes(self):
        verdict = gate.validate(clean_candidate())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertTrue(verdict["generic_compliance_counterhypothesis_rejected_by_design_candidate"])
        self.assertFalse(verdict["native_last_token_causal_identity_required"])

    def test_reused_discriminative_word_fails_even_with_distinct_family_ids(self):
        candidate = clean_candidate()
        rows = candidate["lexical_independence_evidence"]["basis_rows"]
        rows[3]["prompt"] = rows[3]["prompt"].replace("admitted", "ratified")
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("BASIS_DISCRIMINATIVE_LEXICAL_OVERLAP" in f for f in verdict["failures"]))

    def test_canonical_semantic_label_in_model_prompt_fails(self):
        candidate = clean_candidate()
        candidate["lexical_independence_evidence"]["basis_rows"][0]["prompt"] += " AFFIRMATIVE"
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("MODEL_FACING_LABEL" in f for f in verdict["failures"]))

    def test_native_scope_cannot_claim_last_token_identity(self):
        candidate = clean_candidate()
        candidate["intervention"]["strict_last_token_replication_claimed"] = True
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertIn("NATIVE_CVEC_MUST_NOT_CLAIM_LAST_TOKEN_CAUSAL_IDENTITY", verdict["failures"])

    def test_existing_q8_basis_is_not_silently_promoted_as_strict_lexically_disjoint(self):
        candidate = clean_candidate()
        candidate["lexical_independence_evidence"]["basis_rows"] = current_basis.design_rows()
        verdict = gate.validate(candidate)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("BASIS_DISCRIMINATIVE_LEXICAL_OVERLAP" in f for f in verdict["failures"]))


if __name__ == "__main__":
    unittest.main()
