from __future__ import annotations

import hashlib
import unittest

from tools.trigger2_qwen35_model_call_receipt_contract_v1 import (
    OUTPUT_SCHEMA,
    adjudicate,
    normalize_input_identity,
)


def h(label: str) -> str:
    return hashlib.sha256(label.encode()).hexdigest()


def tensor(label: str):
    return {
        "sha256": h(label + ":tensor"),
        "raw_bytes_sha256": h(label + ":raw"),
        "dtype": "torch.int64",
        "shape": [1, 4],
        "numel": 4,
        "raw_nbytes": 32,
    }


def base_input():
    child = {
        "schema": "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_CHILD/v1",
        "pass": True,
        "forward_observed": True,
        "canonical_messages_sha256": h("messages"),
        "resolved_chat_template": "PRESENT",
        "chat_template_text_sha256": h("chat-template"),
        "apply_chat_template_parameters": {"tokenize": False, "add_generation_prompt": True},
        "rendered_utf8_sha256": h("rendered"),
        "rendered_utf8_nbytes": 123,
        "input_ids": tensor("ids"),
        "attention_mask": tensor("mask"),
        "runtime": {"python": "3.12.0", "torch": "2.x", "transformers": "5.x", "platform": "linux"},
        "loader": {"model_class": "Qwen3_5ForCausalLM", "tokenizer_class": "Qwen3_5Tokenizer"},
    }
    return {
        "schema": "CLAY_TRIGGER2_CHECKPOINT_INPUT_IDENTITY_ABI/v1",
        "pass": True,
        "candidate_id": "QWEN35_08B_BASE",
        "render_mode": "native",
        "consumed_identity_match": True,
        "prompt_input_identity_complete": True,
        "checkpoint_bundle_identity": {
            "candidate_id": "QWEN35_08B_BASE",
            "repo": "Qwen/Qwen3.5-0.8B-Base",
            "requested_revision": "d" * 40,
            "file_manifest_sha256": h("manifest"),
            "config_json_sha256": h("config"),
            "tokenizer_json_sha256": h("tokenizer"),
            "tokenizer_config_json_sha256": h("tokenizer-config"),
            "chat_template_jinja_sha256": h("chat-template-file"),
        },
        "consumed_identity": {
            "pass": True,
            "unknown_opened_local_files": [],
            "digest_mismatches": [],
            "missing_weight_shards": [],
            "expected_weight_shards": ["model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors"],
            "opened_weight_shards": ["model-00001-of-00002.safetensors", "model-00002-of-00002.safetensors"],
        },
        "child": child,
    }


def bound_output(inp):
    ni = normalize_input_identity(inp)
    return {
        "schema": OUTPUT_SCHEMA,
        "pass": True,
        "candidate_id": inp["candidate_id"],
        "runtime_call_id": "call-001",
        "output_kind": "GENERATED_TOKEN_IDS",
        "model_output_sha256": h("output"),
        "model_output_nbytes": 64,
        "input_receipt_sha256": ni["input_receipt_sha256"],
        "input_binding_sha256": ni["input_binding_sha256"],
    }


class ContractTests(unittest.TestCase):
    def test_positive_contract(self):
        inp = base_input()
        out = bound_output(inp)
        r = adjudicate(inp, out)
        self.assertTrue(r["pass"])
        self.assertEqual(r["status"], "PASS_RECEIPT_CONTRACT_ONLY")
        self.assertEqual(r["credit_boundary"]["training_credit"], 0)

    def test_checkpoint_manifest_drift_breaks_bound_output(self):
        inp = base_input()
        out = bound_output(inp)
        inp["checkpoint_bundle_identity"]["file_manifest_sha256"] = h("mutated-manifest")
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure"], "OUTPUT_INPUT_RECEIPT_TRANSPLANT")

    def test_tokenizer_template_drift_breaks_bound_output(self):
        inp = base_input()
        out = bound_output(inp)
        inp["checkpoint_bundle_identity"]["tokenizer_json_sha256"] = h("other-tokenizer")
        inp["child"]["chat_template_text_sha256"] = h("other-template")
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])

    def test_rendered_prompt_drift_breaks_bound_output(self):
        inp = base_input()
        out = bound_output(inp)
        inp["child"]["rendered_utf8_sha256"] = h("different-rendered-prompt")
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])

    def test_token_id_drift_breaks_bound_output(self):
        inp = base_input()
        out = bound_output(inp)
        inp["child"]["input_ids"]["sha256"] = h("different-token-ids")
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])

    def test_output_transplant_across_candidate_rejects(self):
        inp = base_input()
        out = bound_output(inp)
        out["candidate_id"] = "QWEN35_08B_POSTTRAINED"
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure"], "OUTPUT_CANDIDATE_TRANSPLANT")

    def test_unproven_consumption_rejects(self):
        inp = base_input()
        inp["consumed_identity_match"] = "UNPROVEN_BY_LOADER_PROBE_V1"
        out = {
            "schema": OUTPUT_SCHEMA,
            "pass": True,
            "candidate_id": inp["candidate_id"],
            "runtime_call_id": "call-002",
            "output_kind": "FORWARD_LOGITS",
            "model_output_sha256": h("out2"),
            "model_output_nbytes": 32,
            "input_receipt_sha256": h("not-relevant"),
            "input_binding_sha256": h("not-relevant2"),
        }
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure"], "CONSUMED_IDENTITY_POSITIVE_REQUIRED")

    def test_missing_consumed_weight_shard_rejects(self):
        inp = base_input()
        inp["consumed_identity"]["missing_weight_shards"] = ["model-00002-of-00002.safetensors"]
        out = {
            "schema": OUTPUT_SCHEMA,
            "pass": True,
            "candidate_id": inp["candidate_id"],
            "runtime_call_id": "call-003",
            "output_kind": "FORWARD_LOGITS",
            "model_output_sha256": h("out3"),
            "model_output_nbytes": 32,
            "input_receipt_sha256": h("x"),
            "input_binding_sha256": h("y"),
        }
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure"], "CONSUMED_IDENTITY_MISSING_WEIGHT_SHARDS")

    def test_output_digest_format_rejects(self):
        inp = base_input()
        out = bound_output(inp)
        out["model_output_sha256"] = "bad"
        r = adjudicate(inp, out)
        self.assertFalse(r["pass"])
        self.assertEqual(r["failure"], "MODEL_OUTPUT_SHA256_INVALID")


if __name__ == "__main__":
    unittest.main()
