from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
sys.path.insert(0, str(TOOLS))

import jspace_cross_runtime_target_binding_v1 as bridge


def h(ch: str) -> str:
    return ch * 64


def source_packet() -> dict:
    source_runtime = {
        "repo_head": "a" * 40,
        "runtime_build_sha256": h("1"),
        "checkpoint_sha256": h("2"),
        "tokenizer_sha256": h("3"),
    }
    packet = {
        "schema": bridge.SOURCE_SCHEMA,
        "abi_role": bridge.SOURCE_ROLE,
        "truth_status": bridge.TRUTH_STATUS,
        "canonical_truth": False,
        "source_model_runtime_identity": source_runtime,
        "target_model_runtime_identity": {
            "provider": "local",
            "model_or_route": "Qwen/Qwen3-0.6B@pytorch-source",
            "execution_surface": "LOCAL_LOOPBACK_API",
            "runtime_build_sha256": source_runtime["runtime_build_sha256"],
            "checkpoint_sha256": source_runtime["checkpoint_sha256"],
            "tokenizer_sha256": source_runtime["tokenizer_sha256"],
        },
        "target_activation_site": "model.model.layers[20]:output:last_token",
        "intervention_operator": "ADD",
        "vector_identity": {
            "source_packet_sha256": h("4"),
            "local_vector_sha256": h("5"),
            "applied_vector_sha256": h("6"),
            "adapter_sha256": h("7"),
        },
    }
    packet["packet_sha256"] = bridge.digest(packet)
    return packet


def target_spec() -> dict:
    return {
        "schema": bridge.TARGET_SPEC_SCHEMA,
        "native_runtime_observed": False,
        "target_runtime_identity": {
            "provider": "local",
            "model_or_route": "Qwen3-0.6B-Q8_0@exact-gguf",
            "execution_surface": "LOCAL_LLAMA_CPP_NATIVE_CVEC",
            "artifact_format": "GGUF_Q8_0",
            "runtime_source_commit": "b" * 40,
            "runtime_build_sha256": h("8"),
            "checkpoint_sha256": h("9"),
            "tokenizer_sha256": h("a"),
        },
        "target_vector_binding": {
            "api_symbol": bridge.NATIVE_CVEC_API,
            "source_local_vector_sha256": h("5"),
            "source_applied_vector_sha256": h("6"),
            "source_activation_site": "model.model.layers[20]:output:last_token",
            "target_cvec_sha256": h("b"),
            "source_vector_dimension": 1024,
            "target_cvec_dimension": 1024,
            "conversion_method": "EXACT_1024D_SOURCE_AXIS_TO_NATIVE_CVEC",
            "conversion_receipt_sha256": h("c"),
            "dimension_receipt_sha256": h("d"),
            "target_layer_mapping": {
                "source_layer": 20,
                "target_layer_start": 20,
                "target_layer_end": 20,
                "mapping_semantics": "EXACT_TRANSFORMER_BLOCK_INDEX_AFTER_ARCHITECTURE_ATTESTATION",
                "mapping_receipt_sha256": h("e"),
            },
        },
    }


class CrossRuntimeTargetBindingTests(unittest.TestCase):
    def test_happy_path_is_deterministic_and_nonpromoting(self) -> None:
        one = bridge.build_binding(source_packet(), target_spec())
        two = bridge.build_binding(deepcopy(source_packet()), deepcopy(target_spec()))
        self.assertEqual(one, two)
        self.assertEqual("EXPLICIT_CROSS_RUNTIME_TARGET", one["runtime_identity_relation"])
        self.assertEqual(h("8"), one["target_model_runtime_identity"]["runtime_build_sha256"])
        self.assertEqual(h("9"), one["target_model_runtime_identity"]["checkpoint_sha256"])
        self.assertNotEqual(
            one["source_model_runtime_identity"]["runtime_build_sha256"],
            one["target_model_runtime_identity"]["runtime_build_sha256"],
        )
        self.assertFalse(one["runtime_observed"])
        self.assertFalse(one["promotion_fences"]["native_cvec_runtime_credit"])
        ok, failures = bridge.validate_binding(one)
        self.assertTrue(ok)
        self.assertEqual([], failures)

    def test_same_runtime_cannot_masquerade_as_cross_runtime_target(self) -> None:
        spec = target_spec()
        source = source_packet()["source_model_runtime_identity"]
        for key in ("runtime_build_sha256", "checkpoint_sha256", "tokenizer_sha256"):
            spec["target_runtime_identity"][key] = source[key]
        result = bridge.adjudicate(source_packet(), spec)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("TARGET_RUNTIME_MUST_DIFFER_FROM_SOURCE", result["failures"][0])

    def test_source_packet_with_preexisting_cross_runtime_hash_is_rejected(self) -> None:
        packet = source_packet()
        packet["target_model_runtime_identity"]["runtime_build_sha256"] = h("f")
        packet.pop("packet_sha256")
        packet["packet_sha256"] = bridge.digest(packet)
        result = bridge.adjudicate(packet, target_spec())
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("SOURCE_PACKET_ALREADY_CROSS_RUNTIME:runtime_build_sha256", result["failures"][0])

    def test_wrong_native_api_symbol_blocks(self) -> None:
        spec = target_spec()
        spec["target_vector_binding"]["api_symbol"] = "invented_cvec_api"
        result = bridge.adjudicate(source_packet(), spec)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("TARGET_CVEC_API_SYMBOL_INVALID", result["failures"][0])

    def test_source_vector_mismatch_blocks(self) -> None:
        spec = target_spec()
        spec["target_vector_binding"]["source_local_vector_sha256"] = h("0")
        result = bridge.adjudicate(source_packet(), spec)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("SOURCE_LOCAL_VECTOR_IDENTITY_MISMATCH", result["failures"][0])

    def test_dimension_change_blocks_without_silent_projection(self) -> None:
        spec = target_spec()
        spec["target_vector_binding"]["target_cvec_dimension"] = 2048
        result = bridge.adjudicate(source_packet(), spec)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("CROSS_RUNTIME_VECTOR_DIMENSION_MISMATCH", result["failures"][0])

    def test_runtime_credit_cannot_be_predeclared(self) -> None:
        spec = target_spec()
        spec["native_runtime_observed"] = True
        result = bridge.adjudicate(source_packet(), spec)
        self.assertEqual("BLOCKED", result["status"])
        self.assertIn("PREEXECUTION_BINDING_MUST_NOT_CLAIM_RUNTIME", result["failures"][0])

    def test_binding_tamper_breaks_digest(self) -> None:
        binding = bridge.build_binding(source_packet(), target_spec())
        binding["target_intervention"]["target_cvec_dimension"] = 2048
        ok, failures = bridge.validate_binding(binding)
        self.assertFalse(ok)
        self.assertIn("BINDING_SHA256_MISMATCH", failures)


if __name__ == "__main__":
    unittest.main()
