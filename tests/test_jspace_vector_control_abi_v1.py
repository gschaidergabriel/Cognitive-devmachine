from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import jspace_vector_control_abi_v1 as abi

H64 = "a" * 64
B64 = "b" * 64
C64 = "c" * 64
D64 = "d" * 64
HEAD40 = "e" * 40


def candidate() -> dict:
    controls = {
        name: {"runtime_receipt_sha256": abi.digest({"control": name})}
        for name in abi.REQUIRED_CONTROLS
    }
    return {
        "schema": abi.CANDIDATE_SCHEMA,
        "source_identity": {
            "repo_head": HEAD40,
            "runtime_build_sha256": H64,
            "checkpoint_sha256": B64,
            "tokenizer_sha256": C64,
        },
        "intervention": {
            "runtime_observed": True,
            "invocation_id": "invocation-1",
            "activation_site": "model.model.layers[12]:output:last_token",
            "source_packet_sha256": D64,
            "adapter_sha256": abi.digest("adapter"),
            "local_vector_sha256": abi.digest("local-vector"),
            "applied_vector_sha256": abi.digest("applied-vector"),
            "runtime_intervention_receipt_sha256": abi.digest("runtime-intervention"),
            "gain": 4.0,
        },
        "controls": controls,
        "calibration": {"family_id": abi.digest("calibration"), "seeds": [1, 2]},
        "holdout": {
            "family_id": abi.digest("holdout"),
            "seeds": [3, 4],
            "evaluation_independent_of_vector_derivation": True,
            "metric_definition_sha256": abi.digest({"metric": "target"}),
        },
        "vector_derivation": {
            "method": "CALIBRATION_ONLY_INTERMEDIATE_RESIDUAL_CONTRAST",
            "uses_holdout_data": False,
            "uses_evaluation_output_labels": False,
            "derivation_family_id": abi.digest("derivation-family"),
            "derivation_receipt_sha256": abi.digest("derivation-receipt"),
        },
        "target": {
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@exact-revision",
            "execution_surface": "LOCAL_LOOPBACK_API",
        },
        "jspace_vector_control_evidence": {
            "schema": abi.EVIDENCE_SCHEMA,
            "intervention_operator": "ADD",
            "token_position_policy": "LAST_PROMPT_TOKEN",
            "target_metric_definition": {
                "schema": "TARGET_METRIC/v1",
                "name": "counterbalanced_directional_effect",
            },
            "off_target_metric_definition": {
                "schema": "OFF_TARGET_METRIC/v1",
                "name": "unrelated_family_damage",
            },
            "allowed_magnitude_envelope": {
                "gain_min": -6.0,
                "gain_max": 6.0,
                "envelope_receipt_sha256": abi.digest("gain-envelope"),
            },
            "holdout_used_for_derivation": False,
            "frozen_calibration_receipt_sha256": abi.digest("frozen-calibration"),
        },
    }


class JSpaceVectorControlAbiV1Tests(unittest.TestCase):
    def test_full_packet_is_deterministic_and_namespace_explicit(self):
        src = candidate()
        one = abi.build_packet(src)
        two = abi.build_packet(deepcopy(src))
        self.assertEqual(one, two)
        self.assertEqual(abi.SCHEMA, one["schema"])
        self.assertEqual(abi.ABI_ROLE, one["abi_role"])
        self.assertEqual(
            {
                "full_control_packet": True,
                "q8_wire_codec": False,
                "partial_derivation_descriptor": False,
            },
            one["namespace_semantics"],
        )
        self.assertFalse(one["canonical_truth"])
        self.assertEqual(abi.TRUTH_STATUS, one["truth_status"])
        ok, failures = abi.validate_packet(one)
        self.assertTrue(ok)
        self.assertEqual([], failures)

    def test_missing_explicit_control_evidence_blocks_instead_of_inferring(self):
        src = candidate()
        del src["jspace_vector_control_evidence"]
        result = abi.adjudicate(src)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("EXPLICIT_CONTROL_ABI_EVIDENCE_REQUIRED", result["failures"][0])
        self.assertIsNone(result["packet"])
        self.assertFalse(result["canonical_credit_minted"])

    def test_missing_off_target_metric_blocks(self):
        src = candidate()
        del src["jspace_vector_control_evidence"]["off_target_metric_definition"]
        result = abi.adjudicate(src)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("OFF_TARGET_METRIC_DEFINITION_REQUIRED", result["failures"][0])

    def test_gain_outside_predeclared_envelope_blocks(self):
        src = candidate()
        src["intervention"]["gain"] = 9.0
        result = abi.adjudicate(src)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("APPLIED_GAIN_OUTSIDE_ALLOWED_ENVELOPE", result["failures"][0])

    def test_same_schema_with_non_full_role_is_rejected_as_namespace_collision(self):
        packet = abi.build_packet(candidate())
        packet["abi_role"] = "Q8_WIRE_CODEC"
        material = dict(packet)
        material.pop("packet_sha256", None)
        packet["packet_sha256"] = abi.digest(material)
        ok, failures = abi.validate_packet(packet)
        self.assertFalse(ok)
        self.assertIn("JSPACE_VECTOR_CONTROL_ABI_ROLE_COLLISION", failures)

    def test_packet_hash_tamper_fails_closed(self):
        packet = abi.build_packet(candidate())
        packet["intervention_operator"] = "ABLATE"
        ok, failures = abi.validate_packet(packet)
        self.assertFalse(ok)
        self.assertIn("PACKET_SHA256_MISMATCH", failures)


if __name__ == "__main__":
    unittest.main()
