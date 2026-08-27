#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import unittest

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from tools import trigger1_native_q8_jspace_basis_build as basis


class NativeQ8JSpaceBasisBuildTests(unittest.TestCase):
    def test_design_has_six_complete_label_free_matched_triplets(self):
        rows = basis.design_rows()
        self.assertEqual(len(rows), 18)
        grouped: dict[str, set[str]] = {}
        for row in rows:
            grouped.setdefault(row["family_group_id"], set()).add(row["semantic_class"])
        self.assertEqual(len(grouped), 6)
        for classes in grouped.values():
            self.assertEqual(classes, set(basis.CLASSES))
        model_text = "\n".join(row["prompt"] for row in rows).upper()
        for forbidden in ("AFFIRMATIVE", "NEGATIVE", "NEUTRAL", " A=", " B=", " C=", "CODEBOOK"):
            self.assertNotIn(forbidden, model_text)

    def test_cvec_layout_places_only_layer20_block(self):
        vector = np.linspace(-1.0, 1.0, basis.N_EMBD, dtype=np.float32)
        raw = basis.cvec_bytes(vector)
        self.assertEqual(len(raw), (basis.N_LAYER - 1) * basis.N_EMBD * 4)
        matrix = np.frombuffer(raw, dtype="<f4").reshape(basis.N_LAYER - 1, basis.N_EMBD)
        for il in range(1, basis.N_LAYER):
            row = matrix[il - 1]
            if il == basis.INJECTION_LAYER:
                np.testing.assert_array_equal(row, vector)
            else:
                self.assertTrue(np.all(row == 0.0), msg=f"nonzero cvec block at layer {il}")

    @staticmethod
    def _synthetic(kind: str) -> tuple[list[dict], dict[str, dict]]:
        rows: list[dict] = []
        observations: dict[str, dict] = {}
        for i in range(6):
            family = f"g{i}"
            common = np.zeros(basis.N_EMBD, dtype=np.float64)
            common[10] = float(i) * 9.0
            common[11] = -float(i) * 5.0
            if kind == "rank1":
                vectors = {
                    "AFFIRMATIVE": common + np.eye(1, basis.N_EMBD, 0, dtype=np.float64)[0],
                    "NEGATIVE": common - np.eye(1, basis.N_EMBD, 0, dtype=np.float64)[0],
                    "NEUTRAL": common.copy(),
                }
            elif kind == "rank2":
                e1 = np.eye(1, basis.N_EMBD, 0, dtype=np.float64)[0]
                e2 = np.eye(1, basis.N_EMBD, 1, dtype=np.float64)[0]
                vectors = {
                    "AFFIRMATIVE": common + e1,
                    "NEGATIVE": common - 0.5 * e1 + e2,
                    "NEUTRAL": common - 0.5 * e1 - e2,
                }
            else:
                raise AssertionError(kind)
            for semantic, activation in vectors.items():
                rid = f"{family}:{semantic.lower()}"
                rows.append({
                    "row_id": rid,
                    "family_group_id": family,
                    "semantic_class": semantic,
                    "prompt": "synthetic",
                    "prompt_sha256": "0" * 64,
                })
                observations[rid] = {"primary_activation": activation.tolist()}
        return rows, observations

    def test_rank1_geometry_stays_one_dimensional_and_zero_sum(self):
        rows, observations = self._synthetic("rank1")
        geom = basis.native_geometry(rows, observations, {"verdict": "ONE_DIMENSIONAL_SUPPORTED"})
        self.assertEqual(geom["rank"], 1)
        self.assertEqual(geom["axes"].shape, (1, basis.N_EMBD))
        total = sum(geom["geometry_vectors"].values())
        self.assertLess(float(np.linalg.norm(total)), 1e-12)
        axis = geom["axes"][0]
        for vector in geom["geometry_vectors"].values():
            residual = vector - float(np.dot(vector, axis)) * axis
            self.assertLess(float(np.linalg.norm(residual)), 1e-12)

    def test_rank2_geometry_is_orthonormal_and_zero_sum(self):
        rows, observations = self._synthetic("rank2")
        geom = basis.native_geometry(rows, observations, {"verdict": "TWO_DIMENSIONAL_REQUIRED"})
        self.assertEqual(geom["rank"], 2)
        self.assertEqual(geom["axes"].shape, (2, basis.N_EMBD))
        gram = geom["axes"] @ geom["axes"].T
        np.testing.assert_allclose(gram, np.eye(2), atol=1e-12, rtol=0.0)
        total = sum(geom["geometry_vectors"].values())
        self.assertLess(float(np.linalg.norm(total)), 1e-12)
        # Three target locations must not collapse onto one identical vector.
        vecs = [geom["geometry_vectors"][name] for name in basis.CLASSES]
        self.assertGreater(float(np.linalg.norm(vecs[0] - vecs[1])), 0.1)
        self.assertGreater(float(np.linalg.norm(vecs[1] - vecs[2])), 0.1)

    def test_unresolved_rank_refuses_to_emit_geometry(self):
        rows, observations = self._synthetic("rank2")
        with self.assertRaisesRegex(RuntimeError, "NATIVE_SIMPLEX_RANK_UNRESOLVED"):
            basis.native_geometry(rows, observations, {"verdict": "UNRESOLVED"})


if __name__ == "__main__":
    unittest.main()
