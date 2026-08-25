import unittest

from tools import trigger1_semantic_simplex_rank_v1 as mod


def sha(ch):
    return ch * 64


def base_payload(rows):
    return {
        "schema": mod.INPUT_SCHEMA,
        "model_facing_label_free": True,
        "lexically_disjoint_families": True,
        "scenario_family_matched_triplets": True,
        "holdout_opened": False,
        "repo_head": "a" * 40,
        "checkpoint_sha256": sha("b"),
        "tokenizer_sha256": sha("c"),
        "runtime_build_sha256": sha("d"),
        "activation_site": "model.layers.20.resid_post:last_token",
        "layer": 20,
        "records": rows,
    }


def payload_rank1():
    rows = []
    for i, jitter in enumerate((0.00, 0.04, -0.03, 0.02), 1):
        y = 0.3 * i
        rows += [
            {"family_id": f"F{i}", "semantic_class": "AFFIRMATIVE", "activation": [2.0 + jitter, y, 0.0]},
            {"family_id": f"F{i}", "semantic_class": "NEGATIVE", "activation": [-2.0 + jitter, y, 0.0]},
            {"family_id": f"F{i}", "semantic_class": "NEUTRAL", "activation": [0.0 + jitter, y, 0.0]},
        ]
    return base_payload(rows)


def payload_rank2():
    rows = []
    for i, scale in enumerate((0.92, 1.0, 1.08, 1.16), 1):
        z = 0.2 * i
        rows += [
            {"family_id": f"G{i}", "semantic_class": "AFFIRMATIVE", "activation": [2 * scale, 0, z]},
            {"family_id": f"G{i}", "semantic_class": "NEGATIVE", "activation": [-1 * scale, 1.8 * scale, z]},
            {"family_id": f"G{i}", "semantic_class": "NEUTRAL", "activation": [-1 * scale, -1.8 * scale, z]},
        ]
    return base_payload(rows)


class SemanticSimplexRankTests(unittest.TestCase):
    def test_rank1(self):
        self.assertEqual(mod.analyze(payload_rank1())["verdict"], "ONE_DIMENSIONAL_SUPPORTED")

    def test_rank2(self):
        self.assertEqual(mod.analyze(payload_rank2())["verdict"], "TWO_DIMENSIONAL_REQUIRED")

    def test_deterministic(self):
        self.assertEqual(mod.analyze(payload_rank2()), mod.analyze(payload_rank2()))

    def test_requires_matched_triplets_flag(self):
        p = payload_rank1()
        p["scenario_family_matched_triplets"] = False
        with self.assertRaisesRegex(ValueError, "SCENARIO_FAMILY_MATCHED_TRIPLETS_REQUIRED"):
            mod.analyze(p)

    def test_rejects_opened_holdout(self):
        p = payload_rank1()
        p["holdout_opened"] = True
        with self.assertRaisesRegex(ValueError, "HOLDOUT_MUST_REMAIN_UNOPENED"):
            mod.analyze(p)

    def test_rejects_model_facing_text(self):
        p = payload_rank1()
        p["records"][0]["prompt"] = "AFFIRMATIVE"
        with self.assertRaisesRegex(ValueError, "MODEL_FACING_TEXT_MUST_NOT_ENTER_RANK_ANALYZER"):
            mod.analyze(p)

    def test_rejects_incomplete_family(self):
        p = payload_rank1()
        p["records"] = p["records"][:-1]
        with self.assertRaisesRegex(ValueError, "FAMILY_MUST_CONTAIN_EXACTLY_THREE_CLASSES"):
            mod.analyze(p)

    def test_rejects_dimension_mismatch(self):
        p = payload_rank1()
        p["records"][0]["activation"] = [1, 2]
        with self.assertRaisesRegex(ValueError, "VECTOR_DIMENSION_MISMATCH"):
            mod.analyze(p)

    def test_high_norm_single_family_cannot_force_promotion(self):
        p = payload_rank1()
        for row in p["records"]:
            if row["family_id"] == "F1":
                if row["semantic_class"] == "AFFIRMATIVE":
                    row["activation"] = [200, 0, 0]
                elif row["semantic_class"] == "NEGATIVE":
                    row["activation"] = [-100, 180, 0]
                else:
                    row["activation"] = [-100, -180, 0]
        self.assertEqual(mod.analyze(p)["verdict"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
