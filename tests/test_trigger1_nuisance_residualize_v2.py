from __future__ import annotations

import hashlib
import unittest

import numpy as np

from tools import trigger1_nuisance_residualize_v2 as residualizer


SHA_A = "a" * 64
SHA_B = "b" * 64


def vec(*xs: float) -> list[float]:
    return list(xs)


def payload() -> dict:
    # Nuisance span = e0,e1. Semantic simplex lives entirely in e2,e3.
    return {
        "schema": residualizer.v1.INPUT_SCHEMA,
        "fit_split": "CALIBRATION",
        "frozen_before_holdout": True,
        "semantic_source_receipt_sha256": SHA_A,
        "nuisance_source_receipt_sha256": SHA_B,
        "dimension": 6,
        "semantic_vectors": {
            "AFFIRMATIVE": vec(0, 0, 1, 0, 0, 0),
            "NEGATIVE": vec(0, 0, 0, 1, 0, 0),
            "NEUTRAL": vec(0, 0, -1, -1, 0, 0),
        },
        "nuisance_vectors": {
            "CANONICAL_LABEL_LEXEME": [vec(1, 0, 0, 0, 0, 0)],
            "SEMANTIC_SYNONYM_LEXICON": [vec(-1, 0, 0, 0, 0, 0)],
            "GENERIC_INSTRUCTION_COMPLIANCE": [vec(0, 1, 0, 0, 0, 0)],
            "OUTPUT_CODE_IDENTITY": [vec(0, -1, 0, 0, 0, 0)],
        },
    }


class NuisanceResidualizeV2Test(unittest.TestCase):
    def test_exports_rank_complete_deterministic_basis(self):
        out = residualizer.residualize(payload())
        self.assertEqual(out["schema"], residualizer.OUTPUT_SCHEMA)
        self.assertEqual(out["nuisance_subspace_rank"], 2)
        self.assertEqual(out["nuisance_basis_rank"], 2)
        self.assertEqual(len(out["nuisance_basis_axes"]), 2)
        self.assertLessEqual(
            out["nuisance_basis_max_abs_gram_error"],
            residualizer.MAX_BASIS_GRAM_ERROR,
        )
        self.assertLessEqual(
            out["nuisance_basis_max_input_row_span_residual_l2"],
            residualizer.MAX_ROW_SPAN_RESIDUAL,
        )
        self.assertFalse(out["model_executed"])
        self.assertFalse(out["holdout_opened"])
        self.assertFalse(out["runtime_credit_minted"])

    def test_axis_hashes_bind_float32_bytes(self):
        out = residualizer.residualize(payload())
        for i, axis in enumerate(out["nuisance_basis_axes"]):
            self.assertEqual(axis["axis_id"], f"q{i}")
            arr = np.asarray(axis["unit_vector"], dtype="<f4")
            expected = hashlib.sha256(arr.tobytes()).hexdigest()
            self.assertEqual(axis["vector_sha256"], expected)
            self.assertAlmostEqual(axis["l2"], 1.0, places=12)

    def test_binding_is_calibration_only_frozen_and_rank_exact(self):
        out = residualizer.residualize(payload())
        b = out["causal_nuisance_subspace_binding"]
        self.assertEqual(b["schema"], residualizer.BASIS_SCHEMA)
        self.assertEqual(b["producer_schema"], residualizer.OUTPUT_SCHEMA)
        self.assertEqual(b["fit_split"], "CALIBRATION")
        self.assertTrue(b["frozen_before_holdout"])
        self.assertEqual(b["rank"], out["nuisance_basis_rank"])
        self.assertEqual(
            [a["axis_id"] for a in b["axes"]],
            [a["axis_id"] for a in out["nuisance_basis_axes"]],
        )
        self.assertEqual(
            [a["vector_sha256"] for a in b["axes"]],
            [a["vector_sha256"] for a in out["nuisance_basis_axes"]],
        )

    def test_repeat_is_hash_stable(self):
        a = residualizer.residualize(payload())
        b = residualizer.residualize(payload())
        self.assertEqual(a["result_sha256"], b["result_sha256"])
        self.assertEqual(
            a["causal_nuisance_subspace_binding"]["receipt_sha256"],
            b["causal_nuisance_subspace_binding"]["receipt_sha256"],
        )
        self.assertEqual(
            [x["vector_sha256"] for x in a["nuisance_basis_axes"]],
            [x["vector_sha256"] for x in b["nuisance_basis_axes"]],
        )

    def test_fixed_family_order_determines_axis_provenance(self):
        out = residualizer.residualize(payload())
        axes = out["nuisance_basis_axes"]
        self.assertEqual(axes[0]["source_family"], "CANONICAL_LABEL_LEXEME")
        self.assertEqual(axes[0]["source_index"], 0)
        # The opposite e0 row is dependent; q1 therefore comes from the first e1 row.
        self.assertEqual(axes[1]["source_family"], "GENERIC_INSTRUCTION_COMPLIANCE")
        self.assertEqual(axes[1]["source_index"], 0)


if __name__ == "__main__":
    unittest.main()
