import importlib.util
from pathlib import Path
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
MODULE_PATH = TOOLS / "validate_jspace_trace_abi_v1.py"
spec = importlib.util.spec_from_file_location("jspace_trace_abi_v1", MODULE_PATH)
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def valid_trace():
    return {
        "schema": "JSPACE_TRACE_ABI/v1",
        "causal_event_id": "event-1",
        "admission_id": "admission-1",
        "generation": 7,
        "model_id": "Qwen/Qwen3-0.6B",
        "model_revision": "c1899de289a04d12100db370d81485cdf75e47ca",
        "checkpoint_sha256": "a" * 64,
        "tokenizer_sha256": "b" * 64,
        "runtime_build_sha256": "c" * 64,
        "loader_consumption_identity": "UNKNOWN",
        "inference_receipt_id": "inference-1",
        "jspace_adapter_id": "qwen06-midlayer-v1",
        "activation_site": {"layer": 12, "component": "residual", "position": "last_prompt_token"},
        "token_position_policy": "LAST_PROMPT_TOKEN",
        "observation_class": "RAW_ACTIVATION_MEASUREMENT",
        "activation_or_projection_sha256": "d" * 64,
        "semantic_family_id": "semantic-family-1",
        "task_family_id": "task-family-1",
        "context_polarity_id": "NONE",
        "split_id": "CAUSAL_HOLDOUT",
        "intervention_id": "NONE",
        "control_class": "NONE",
        "target_metrics": [],
        "off_target_metrics": [],
        "result_classification": "MEASUREMENT_ONLY",
        "credit_scope": "JSPACE_OBSERVATION_COMPONENT_ONLY",
        "canonical_truth": False,
        "truth_status": "CANDIDATE_MEASUREMENT_ONLY",
    }


class JSpaceTraceAbiV1Tests(unittest.TestCase):
    def test_valid_minimal_observation_trace(self):
        self.assertEqual(validator.validate_trace(valid_trace()), [])

    def test_unknown_loader_identity_is_explicitly_allowed_without_credit_promotion(self):
        row = valid_trace()
        row["loader_consumption_identity"] = "UNKNOWN"
        self.assertEqual(validator.validate_trace(row), [])

    def test_wrong_schema_fails_closed(self):
        row = valid_trace()
        row["schema"] = "JSPACE_TRACE_ABI/v2"
        self.assertIn("WRONG_SCHEMA", validator.validate_trace(row))

    def test_bad_artifact_hash_fails_closed(self):
        row = valid_trace()
        row["checkpoint_sha256"] = "not-a-sha"
        self.assertIn("INVALID_SHA256:checkpoint_sha256", validator.validate_trace(row))

    def test_canonical_truth_promotion_is_rejected(self):
        row = valid_trace()
        row["canonical_truth"] = True
        self.assertIn("CANONICAL_TRUTH_PROMOTION_FORBIDDEN", validator.validate_trace(row))

    def test_control_requires_intervention_identity(self):
        row = valid_trace()
        row["control_class"] = "ORTHOGONAL_SAME_NORM"
        self.assertIn("CONTROL_WITHOUT_INTERVENTION", validator.validate_trace(row))

    def test_intervention_requires_control_class(self):
        row = valid_trace()
        row["intervention_id"] = "intervention-1"
        self.assertIn("INTERVENTION_WITHOUT_CONTROL_CLASS", validator.validate_trace(row))

    def test_family_split_is_closed_enum(self):
        row = valid_trace()
        row["split_id"] = "TRAIN"
        self.assertIn("INVALID_SPLIT_ID", validator.validate_trace(row))


if __name__ == "__main__":
    unittest.main()
