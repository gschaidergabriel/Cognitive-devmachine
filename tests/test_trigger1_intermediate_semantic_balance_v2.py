from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest


stub_base = types.ModuleType("trigger1_local_qwen06_intermediate_api_execute")
stub_base.CANDIDATE_LAYERS = (7, 14, 21)
stub_base.CALIBRATION_GAINS = (1.0, 4.0, 16.0, 64.0)
stub_base.POSITIVE_ANCHORS = ("legacy yes",)
stub_base.NEGATIVE_ANCHORS = ("legacy no",)
stub_base.ROOT = Path("/tmp")
stub_base.__file__ = __file__
stub_base.canonical_sha = lambda value: __import__("hashlib").sha256(
    json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
).hexdigest()
stub_base.sha256_file = lambda path: "f" * 64
sys.modules["trigger1_local_qwen06_intermediate_api_execute"] = stub_base

stub_v1 = types.ModuleType("trigger1_intermediate_semantic_balance")
stub_v1.base = stub_base
stub_v1.main = lambda: 0
sys.modules["trigger1_intermediate_semantic_balance"] = stub_v1

MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "trigger1_intermediate_semantic_balance_v2.py"
spec = importlib.util.spec_from_file_location("balanced_v2", MODULE_PATH)
balanced_v2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(balanced_v2)


class Trigger1IntermediateSemanticBalanceV2(unittest.TestCase):
    def test_derivation_anchors_do_not_contain_evaluation_labels(self):
        self.assertFalse(balanced_v2.derivation_uses_evaluation_output_labels())
        all_tokens = []
        for text in (*balanced_v2.SEMANTIC_POSITIVE_ANCHORS, *balanced_v2.SEMANTIC_NEGATIVE_ANCHORS):
            all_tokens.extend(balanced_v2._tokens(text))
        self.assertNotIn("yes", all_tokens)
        self.assertNotIn("no", all_tokens)

    def test_derivation_metadata_truthfully_marks_all_three_independence_fences(self):
        row = balanced_v2.semantic_derivation_metadata()
        self.assertIs(row["uses_output_head_weights"], False)
        self.assertIs(row["uses_holdout_data"], False)
        self.assertIs(row["uses_evaluation_output_labels"], False)
        self.assertEqual(64, len(row["derivation_family_id"]))
        self.assertEqual(64, len(row["derivation_receipt_sha256"]))

    def test_scientific_metadata_rewrites_source_packet_and_candidate(self):
        result = {
            "source_packet": {
                "intent": "legacy affirmative/YES",
                "basis": "legacy",
            },
            "semantic_balance": {
                "metric_definition_sha256": "a" * 64,
            },
        }
        candidate = {
            "intervention": {"source_packet_sha256": "b" * 64},
            "holdout": {"metric_definition_sha256": "a" * 64},
            "source_identity": {},
            "semantic_balance": {},
        }
        result, candidate = balanced_v2.rewrite_scientific_metadata(
            result,
            candidate,
            v2_wrapper_sha256="c" * 64,
        )
        assert candidate is not None
        self.assertNotIn("affirmative/YES", result["source_packet"]["intent"])
        self.assertFalse(result["source_packet"]["derivation_uses_evaluation_output_labels"])
        self.assertEqual(
            result["source_packet_sha256"],
            candidate["intervention"]["source_packet_sha256"],
        )
        self.assertFalse(candidate["vector_derivation"]["uses_evaluation_output_labels"])
        self.assertTrue(candidate["holdout"]["label_mapping_counterbalanced"])
        self.assertEqual("c" * 64, candidate["source_identity"]["semantic_balance_v2_wrapper_sha256"])

    def test_legacy_no_think_prefix_would_be_detected_as_label_leakage(self):
        original = balanced_v2.SEMANTIC_POSITIVE_ANCHORS
        try:
            balanced_v2.SEMANTIC_POSITIVE_ANCHORS = ("/no_think\nA correct proposition.",)
            self.assertTrue(balanced_v2.derivation_uses_evaluation_output_labels())
        finally:
            balanced_v2.SEMANTIC_POSITIVE_ANCHORS = original


if __name__ == "__main__":
    unittest.main()
