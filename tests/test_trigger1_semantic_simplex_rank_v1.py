import unittest

from tools import trigger1_semantic_simplex_rank_v1 as mod


def sha(ch: str) -> str:
    return ch * 64


def payload_rank1():
    rows = []
    for i, jitter in enumerate((0.00, 0.04, -0.03, 0.02), start=1):
        fam = f"F{i}"
        rows += [
            {"family_id": fam, "semantic_class": "AFFIRMATIVE", "activation": [2.0 + jitter, 0.02 * i, 0.0]},
            {"family_id": fam, "semantic_class": "NEGATIVE", "activation": [-2.0 + jitter, 0.02 * i, 0.0]},
            {"family_id": fam, "semantic_class": "NEUTRAL", "activation": [0.0 + jitter, 0.02 * i, 0.0]},
        ]
    return {
        "schema": mod.INPUT_SCHEMA,
        "model_facing_label_free": True,
        "lexically_disjoint_families": True,
        "holdout_opened": False,
        "repo_head": "a" * 40,
        "checkpoint_sha256": sha("b"),
        "tokenizer_sha256": sha("c"),
        "runtime_build_sha256": sha("d"),
        "activation_site": "model.layers.20.resid_post:last_token",
        "layer": 20,
        "records": rows,
    }


def payload_rank2():
    rows = []
    for i, scale in enumerate((0.92, 1.0, 1.08, 1.16), start=1):
        fam = f"G{i}"
        bias = 0.015 * i
        rows += [
            {"family_id": fam, "semantic_class": "AFFIRMATIVE", "activation": [2.0 * scale + bias, 0.0, 0.0]},
            {"family_id": fam, "semantic_class": "NEGATIVE", "activation": [-1.0 * scale + bias, 1.8 * scale, 0.0]},
            {"family_id": fam, "semantic_class": "NEUTRAL", "activation": [-1.0 * scale + bias, -1.8 * scale, 0.0]},
        ]
    p = payload_rank1()
    p["records"] = rows
    return p


class SemanticSimplexRankTests(unittest.TestCase):
    def test_rank1_supported(self):
        out = mod.analyze(payload_rank1())
        self.assertEqual(out["verdict"], "ONE_DIMENSIONAL_SUPPORTED")
        self.assertLess(out["observed_geometry"]["sigma2_over_sigma1"], 0.15)

    def test_rank2_required(self):
        out = mod.analyze(payload_rank2())
        self.assertEqual(out["verdict"], "TWO_DIMENSIONAL_REQUIRED")
        self.assertGreaterEqual(out["observed_geometry"]["sigma2_over_sigma1"], 0.15)

    def test_deterministic(self):
        a = mod.analyze(payload_rank2())
        b = mod.analyze(payload_rank2())
        self.assertEqual(a, b)
        self.assertEqual(a["analysis_sha256"], b["analysis_sha256"])

    def test_requires_label_free_flag(self):
        p = payload_rank1()
        p["model_facing_label_free"] = False
        with self.assertRaisesRegex(ValueError, "MODEL_FACING_LABEL_FREE_REQUIRED"):
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
        p["records"][0]["activation"] = [1.0, 2.0]
        with self.assertRaisesRegex(ValueError, "VECTOR_DIMENSION_MISMATCH"):
            mod.analyze(p)


if __name__ == "__main__":
    unittest.main()
