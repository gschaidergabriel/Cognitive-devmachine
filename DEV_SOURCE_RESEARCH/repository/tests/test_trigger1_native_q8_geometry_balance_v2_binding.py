from __future__ import annotations

from copy import deepcopy
import unittest
import numpy as np

from tools import trigger1_native_q8_geometry_balance_v2 as subject
from tools import trigger1_semantic_simplex_rank_analyze as ranker


def make_payload() -> dict:
    rows = []
    h1 = np.array([1.0, 0.0, 0.0, 0.0])
    d2 = np.array([0.0, 1.0, 0.0, 0.0])
    for i in range(6):
        a = (2.0 / 3.0) * h1
        n = -(1.0 / 3.0) * h1 + 0.5 * d2
        u = -(1.0 / 3.0) * h1 - 0.5 * d2
        for name, vec in (("AFFIRMATIVE", a), ("NEGATIVE", n), ("NEUTRAL", u)):
            rows.append({"row_id": f"f{i}:{name}", "family_group_id": f"f{i}", "semantic_class": name, "activation": vec.tolist()})
    return {
        "schema": ranker.INPUT_SCHEMA,
        "dimension": 4,
        "decision_config": {
            "alpha": 0.05,
            "rank1_equivalence_max_ratio": 0.10,
            "rank2_min_ratio": 0.25,
            "rank2_min_lofo_cosine": 0.90,
            "min_matched_families": 6,
            "max_exact_signflip_families": 16,
            "monte_carlo_signflips": 4096
        },
        "rows": rows
    }


class Q8GeometryRankBindingTests(unittest.TestCase):
    def test_same_payload_rank_is_admitted(self):
        data = make_payload()
        result = subject.finalize(data, ranker.analyze(data))
        self.assertTrue(result["rank_binding"]["declared_equals_recomputed"])
        self.assertFalse(result["model_executed"])

    def test_rank_from_another_payload_is_rejected(self):
        first = make_payload()
        declared = ranker.analyze(first)
        second = deepcopy(first)
        second["rows"][0]["activation"][2] = 0.25
        with self.assertRaisesRegex(subject.GeometryBindingError, "INPUT_PAYLOAD"):
            subject.finalize(second, declared)

    def test_changed_rank_with_recomputed_digest_is_rejected(self):
        data = make_payload()
        declared = deepcopy(ranker.analyze(data))
        declared["verdict"] = "ONE_DIMENSIONAL_SUPPORTED"
        core = dict(declared)
        core.pop("analysis_receipt_sha256")
        declared["analysis_receipt_sha256"] = ranker.canonical_sha(core)
        with self.assertRaisesRegex(subject.GeometryBindingError, "EXACT_RECOMPUTATION"):
            subject.finalize(data, declared)


if __name__ == "__main__":
    unittest.main()
