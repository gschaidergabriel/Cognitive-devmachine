from __future__ import annotations

import unittest

from tools import trigger1_nuisance_residualize as residual

H = "b" * 64


def payload():
    sem = {
        "AFFIRMATIVE": [1.0, 0.0, 0.0, 0.40, 0.00, 0.0, 0.0, 0.0],
        "NEGATIVE": [-1.0, 0.0, 0.0, -0.40, 0.00, 0.0, 0.0, 0.0],
        "NEUTRAL": [0.0, 1.0, 0.0, 0.00, 0.35, 0.0, 0.0, 0.0],
    }
    nuisance = {
        "CANONICAL_LABEL_LEXEME": [[0,0,1,0,0,0,0,0], [0,0,0,1,0,0,0,0]],
        "SEMANTIC_SYNONYM_LEXICON": [[0,0,0,1,1,0,0,0]],
        "GENERIC_INSTRUCTION_COMPLIANCE": [[0,0,0,0,0,1,0,0]],
        "OUTPUT_CODE_IDENTITY": [[0,0,0,0,1,0,0,0], [0,0,0,0,0,1,0,0]],
    }
    return {
        "schema": residual.INPUT_SCHEMA,
        "dimension": 8,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "semantic_source_receipt_sha256": H,
        "nuisance_source_receipt_sha256": H,
        "semantic_vectors": sem,
        "nuisance_vectors": nuisance,
    }


class ResidualizeTest(unittest.TestCase):
    def test_projects_required_nuisance_and_retains_semantics(self):
        r = residual.residualize(payload())
        self.assertLessEqual(
            r["post_projection_max_abs_nuisance_cosine"],
            residual.MAX_POST_PROJECTION_ABS_NUISANCE_COSINE,
        )
        self.assertGreaterEqual(
            r["retained_semantic_subspace_norm_fraction"],
            residual.MIN_RETAINED_SEMANTIC_NORM_FRACTION,
        )
        self.assertGreaterEqual(r["nuisance_subspace_rank"], 4)
        self.assertFalse(r["runtime_credit_minted"])

    def test_missing_compliance_family_fails(self):
        p = payload()
        p["nuisance_vectors"].pop("GENERIC_INSTRUCTION_COMPLIANCE")
        with self.assertRaisesRegex(ValueError, "EXACT_REQUIRED_NUISANCE_FAMILIES_REQUIRED"):
            residual.residualize(p)

    def test_holdout_fit_is_forbidden(self):
        p = payload()
        p["fit_split"] = "HOLDOUT"
        with self.assertRaisesRegex(ValueError, "CALIBRATION_ONLY"):
            residual.residualize(p)

    def test_semantics_fully_inside_nuisance_subspace_fail(self):
        p = payload()
        p["semantic_vectors"] = {
            "AFFIRMATIVE": [0,0,1,0,0,0,0,0],
            "NEGATIVE": [0,0,-1,0,0,0,0,0],
            "NEUTRAL": [0,0,0,1,0,0,0,0],
        }
        with self.assertRaisesRegex(ValueError, "PROJECTED_SEMANTIC_DEGENERATE|SEMANTIC_RESIDUAL_TOO_SMALL"):
            residual.residualize(p)

    def test_deterministic_result_hash(self):
        a = residual.residualize(payload())
        b = residual.residualize(payload())
        self.assertEqual(a["result_sha256"], b["result_sha256"])
        self.assertEqual(a["projected_semantic_vector_sha256"], b["projected_semantic_vector_sha256"])


if __name__ == "__main__":
    unittest.main()
