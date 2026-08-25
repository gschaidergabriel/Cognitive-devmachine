import unittest
from trigger1_cvec_carrier_decomposition import evaluate, OBS_SCHEMA, REQUIRED_MODES


def row(case, mode, a, b=0.0, c=0.0, target="AFFIRMATIVE", code="A"):
    return {
        "schema": OBS_SCHEMA,
        "case_id": case,
        "position_mode": mode,
        "semantic_target": target,
        "output_code_identity": code,
        "token_logits": {"A": a, "B": b, "C": c},
    }


class CarrierDecompositionTests(unittest.TestCase):
    def test_exact_paired_decomposition_and_batch_drift(self):
        vals = {
            "BASELINE_FULL": 1.0,
            "BASELINE_SPLIT": 1.1,
            "BROADCAST_FULL": 3.0,
            "BROADCAST_SPLIT": 3.2,
            "LAST_TOKEN_ONLY_SPLIT": 2.7,
            "PREFIX_ONLY_SPLIT": 1.5,
        }
        result = evaluate([row("x", m, vals[m]) for m in REQUIRED_MODES])
        self.assertEqual(result["status"], "PASS_STRUCTURAL_EVALUATION")
        d = result["cases"][0]["deltas"]
        self.assertAlmostEqual(d["batch_baseline_drift"], 0.1)
        self.assertAlmostEqual(d["broadcast_split_vs_baseline_split"], 2.1)
        self.assertAlmostEqual(d["last_only_vs_baseline_split"], 1.6)
        self.assertAlmostEqual(d["prefix_only_vs_baseline_split"], 0.4)
        self.assertAlmostEqual(d["split_nonadditive_interaction"], 0.1)
        self.assertTrue(result["cases"][0]["broadcast_last_sign_concordant"])
        self.assertFalse(result["claim_boundary"]["causal_identity_between_broadcast_and_last_token"])

    def test_missing_mode_fails_closed(self):
        result = evaluate([row("x", m, 1.0) for m in REQUIRED_MODES[:-1]])
        self.assertEqual(result["status"], "INVALID_OR_INCOMPLETE")
        self.assertTrue(any(x.startswith("CASE_MISSING_MODES") for x in result["failures"]))

    def test_duplicate_mode_fails_closed(self):
        rows = [row("x", m, 1.0) for m in REQUIRED_MODES]
        rows.append(row("x", "BASELINE_FULL", 1.0))
        result = evaluate(rows)
        self.assertEqual(result["status"], "INVALID_OR_INCOMPLETE")
        self.assertTrue(any(x.startswith("DUPLICATE_CASE_MODE") for x in result["failures"]))

    def test_metadata_drift_fails_closed(self):
        rows = [row("x", m, 1.0) for m in REQUIRED_MODES]
        rows[-1]["semantic_target"] = "NEGATIVE"
        result = evaluate(rows)
        self.assertEqual(result["status"], "INVALID_OR_INCOMPLETE")
        self.assertTrue(any(x.startswith("CASE_METADATA_DRIFT") for x in result["failures"]))


if __name__ == "__main__":
    unittest.main()
