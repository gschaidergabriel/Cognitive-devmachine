from __future__ import annotations

import copy
import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_semantic_simplex_calibration as simplex

HEX64 = "a" * 64


def base_payload(families: list[dict]) -> dict:
    return {
        "schema": simplex.INPUT_SCHEMA,
        "source_identity": {
            "checkpoint_sha256": HEX64,
            "tokenizer_sha256": HEX64,
            "runtime_build_sha256": HEX64,
            "layer": 20,
        },
        "label_free": {
            "scan_pass": True,
            "scan_receipt_sha256": HEX64,
            "holdout_opened": False,
        },
        "rank_gate": {
            "rank1_ratio_max": 0.10,
            "rank2_ratio_min": 0.50,
            "min_h1_family_cosine": 0.90,
            "min_h2_family_cosine": 0.90,
            "null_samples": 128,
            "null_quantile": 0.95,
            "rank2_null_multiplier": 1.05,
        },
        "families": families,
    }


def rank1_families(count: int = 8) -> list[dict]:
    rows = []
    for i in range(count):
        offset = [0.0, i * 0.2, i * 0.1]
        rows.append({
            "family_id": f"r1-{i}",
            "centroids": {
                "AFFIRMATIVE": [1.0 + offset[0], offset[1], offset[2]],
                "NEGATIVE": [-1.0 + offset[0], offset[1], offset[2]],
                "NEUTRAL": [offset[0], offset[1], offset[2]],
            },
        })
    return rows


def rank2_families(count: int = 12, *, invert_last_h2: bool = False) -> list[dict]:
    rows = []
    a = [1.0, 0.0, 0.0]
    n = [-0.5, 0.8660254037844386, 0.0]
    u = [-0.5, -0.8660254037844386, 0.0]
    for i in range(count):
        offset = [i * 0.07, (i % 3) * 0.05, i * 0.01]
        negative = n
        neutral = u
        if invert_last_h2 and i == count - 1:
            negative, neutral = neutral, negative

        def shifted(v: list[float]) -> list[float]:
            return [v[j] + offset[j] for j in range(3)]

        rows.append({
            "family_id": f"r2-{i}",
            "centroids": {
                "AFFIRMATIVE": shifted(a),
                "NEGATIVE": shifted(negative),
                "NEUTRAL": shifted(neutral),
            },
        })
    return rows


def parsed_families(rows: list[dict]) -> list[dict]:
    return [
        {
            semantic_class: simplex.np.asarray(row["centroids"][semantic_class], dtype=simplex.np.float64)
            for semantic_class in simplex.CLASSES
        }
        for row in rows
    ]


class Trigger1SemanticSimplexCalibrationTests(unittest.TestCase):
    def test_clean_rank1_geometry_selects_one_dimensional_future_test(self):
        result = simplex.adjudicate(base_payload(rank1_families()))
        self.assertEqual("CALIBRATION_MEASUREMENT_COMPLETE", result["status"])
        self.assertEqual("ONE_DIMENSIONAL_SUPPORTED", result["decision"])
        self.assertEqual(0.0, result["sigma2_over_sigma1"])
        self.assertFalse(result["holdout_opened"])
        self.assertFalse(result["jspace_model_runtime_credit"])

    def test_clean_triangle_geometry_requires_two_dimensional_future_test(self):
        result = simplex.adjudicate(base_payload(rank2_families()))
        self.assertEqual("TWO_DIMENSIONAL_REQUIRED", result["decision"])
        self.assertGreater(result["sigma2_over_sigma1"], 0.99)
        self.assertGreater(
            result["singular_values"][1],
            result["null"]["sigma2_threshold"] * result["null"]["rank2_null_multiplier"],
        )
        self.assertGreaterEqual(result["cross_family"]["min_h2_cosine"], 0.99)

    def test_rank2_pooled_signal_with_one_reversed_family_is_unresolved(self):
        result = simplex.adjudicate(base_payload(rank2_families(invert_last_h2=True)))
        self.assertEqual("UNRESOLVED", result["decision"])
        self.assertEqual(
            "RANK2_MAGNITUDE_PRESENT_BUT_H2_CROSS_FAMILY_COHERENCE_INSUFFICIENT",
            result["decision_reason"],
        )
        self.assertLess(result["cross_family"]["min_h2_cosine"], 0.0)

    def test_holdout_opened_fails_closed(self):
        payload = base_payload(rank1_families())
        payload["label_free"]["holdout_opened"] = True
        result = simplex.adjudicate(payload)
        self.assertEqual("INVALID_INPUT_FAIL_CLOSED", result["status"])
        self.assertEqual("UNRESOLVED", result["decision"])
        self.assertIn("CALIBRATION_CAPSULE_REQUIRES_HOLDOUT_CLOSED", result["failures"])

    def test_null_measurement_is_deterministic_for_identical_input(self):
        payload = base_payload(rank2_families())
        first = simplex.adjudicate(payload)
        second = simplex.adjudicate(payload)
        self.assertEqual(first["input_sha256"], second["input_sha256"])
        self.assertEqual(first["null"], second["null"])
        self.assertEqual(first["decision"], second["decision"])

    def test_gate_threshold_edits_do_not_redraw_null_permutations(self):
        first_payload = base_payload(rank2_families())
        second_payload = copy.deepcopy(first_payload)
        second_payload["rank_gate"]["rank1_ratio_max"] = 0.05
        second_payload["rank_gate"]["rank2_ratio_min"] = 0.60
        second_payload["rank_gate"]["min_h1_family_cosine"] = 0.80
        second_payload["rank_gate"]["min_h2_family_cosine"] = 0.80

        first = simplex.adjudicate(first_payload)
        second = simplex.adjudicate(second_payload)

        self.assertNotEqual(first["input_sha256"], second["input_sha256"])
        self.assertEqual(first["null"]["seed_sha256"], second["null"]["seed_sha256"])
        self.assertEqual(first["null"]["sigma2_threshold"], second["null"]["sigma2_threshold"])
        self.assertEqual(first["null"]["max_sigma2"], second["null"]["max_sigma2"])

    def test_globally_identical_nonidentity_relabeling_is_forced_out_of_null(self):
        families = parsed_families(rank2_families(count=3))
        observed_sigma2 = float(simplex.geometry(families)[2][1])

        selected_seed = None
        selected_index = None
        for nonce in range(10000):
            seed = hashlib.sha256(f"same-permutation-{nonce}".encode("utf-8")).hexdigest()
            indices = []
            for family_index in range(len(families)):
                digest = hashlib.sha256(
                    f"{seed}|null|0|family|{family_index}".encode("utf-8")
                ).digest()
                indices.append(int.from_bytes(digest[:8], "big") % len(simplex.PERMUTATIONS))
            if len(set(indices)) == 1 and indices[0] != 0:
                selected_seed = seed
                selected_index = indices[0]
                break

        self.assertIsNotNone(selected_seed)
        self.assertIsNotNone(selected_index)
        null_sigma2 = simplex.deterministic_null_sigma2(families, selected_seed, 1)[0]
        self.assertLess(null_sigma2, observed_sigma2 - 1e-12)


if __name__ == "__main__":
    unittest.main()
