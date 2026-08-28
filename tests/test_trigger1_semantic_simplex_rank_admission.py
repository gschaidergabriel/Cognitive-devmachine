#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import unittest
from unittest import mock

from tools import trigger1_semantic_simplex_rank_admission as admission


def h(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload() -> dict:
    rows = []
    for family_index in range(6):
        family = f"g{family_index}"
        for semantic, activation in {
            "AFFIRMATIVE": [1.0, 0.0, float(family_index), 0.0],
            "NEGATIVE": [-1.0, 0.0, float(family_index), 0.0],
            "NEUTRAL": [0.0, 0.0, float(family_index), 0.0],
        }.items():
            rows.append(
                {
                    "row_id": f"{family}:{semantic}",
                    "family_group_id": family,
                    "semantic_class": semantic,
                    "prompt_sha256": h(f"prompt:{family}:{semantic}"),
                    "label_free": True,
                    "output_code_free": True,
                    "activation": activation,
                }
            )
    return {
        "schema": admission.INPUT_SCHEMA,
        "source_identity": {
            "model_checkpoint_sha256": "1" * 64,
            "tokenizer_sha256": "2" * 64,
            "runtime_build_sha256": "3" * 64,
            "activation_site": "model.model.layers[20]:output:last_token",
            "token_scope": "LAST_TOKEN_ONLY",
            "layer": 20,
        },
        "design_attestation": {
            "calibration_only": True,
            "fresh_holdout_opened": False,
            "label_free_model_facing_prompts": True,
            "lexically_disjoint_families": True,
            "output_code_independent": True,
        },
        "dimension": 4,
        "decision_config": {
            "alpha": 0.05,
            "rank1_equivalence_max_ratio": 0.10,
            "rank2_min_ratio": 0.25,
            "rank2_min_lofo_cosine": 0.90,
            "min_matched_families": 6,
            "max_exact_signflip_families": 16,
            "monte_carlo_signflips": 4096,
        },
        "rows": rows,
    }


class SemanticSimplexRankAdmissionTests(unittest.TestCase):
    def test_valid_packet_delegates_to_single_numeric_analyzer(self):
        expected = {
            "schema": admission.rank.OUTPUT_SCHEMA,
            "analysis_receipt_sha256": "a" * 64,
            "verdict": "ONE_DIMENSIONAL_SUPPORTED",
        }
        with mock.patch.object(admission.rank, "analyze", return_value=expected) as analyze:
            result = admission.admit_and_analyze(payload())
        self.assertEqual(result["admission"], "PASS")
        self.assertEqual(result["numeric_result"]["verdict"], "ONE_DIMENSIONAL_SUPPORTED")
        self.assertFalse(result["promotion_boundary"]["fresh_holdout_opened"])
        self.assertEqual(result["promotion_boundary"]["new_runtime_credit"], 0)
        analyze.assert_called_once()
        delegated = analyze.call_args.args[0]
        self.assertEqual(delegated["schema"], admission.rank.INPUT_SCHEMA)
        self.assertNotIn("source_identity", delegated)
        self.assertNotIn("design_attestation", delegated)
        self.assertNotIn("prompt_sha256", delegated["rows"][0])

    def test_open_holdout_fails_closed_before_numeric_analysis(self):
        data = payload()
        data["design_attestation"]["fresh_holdout_opened"] = True
        with mock.patch.object(admission.rank, "analyze") as analyze:
            with self.assertRaisesRegex(admission.AdmissionError, "fresh_holdout_opened"):
                admission.admit_and_analyze(data)
        analyze.assert_not_called()

    def test_non_label_free_row_fails_closed_before_numeric_analysis(self):
        data = payload()
        data["rows"][0]["label_free"] = False
        with mock.patch.object(admission.rank, "analyze") as analyze:
            with self.assertRaisesRegex(admission.AdmissionError, "label_free"):
                admission.admit_and_analyze(data)
        analyze.assert_not_called()

    def test_output_code_contamination_fails_closed(self):
        data = payload()
        data["rows"][0]["output_code_free"] = False
        with self.assertRaisesRegex(admission.AdmissionError, "output_code_free"):
            admission.admit_and_analyze(data)

    def test_reused_prompt_hash_fails_closed(self):
        data = payload()
        data["rows"][1]["prompt_sha256"] = data["rows"][0]["prompt_sha256"]
        with self.assertRaisesRegex(admission.AdmissionError, "REUSED"):
            admission.admit_and_analyze(data)

    def test_bad_source_hash_fails_closed(self):
        data = payload()
        data["source_identity"]["runtime_build_sha256"] = "unknown"
        with self.assertRaisesRegex(admission.AdmissionError, "runtime_build_sha256"):
            admission.admit_and_analyze(data)


if __name__ == "__main__":
    unittest.main()
