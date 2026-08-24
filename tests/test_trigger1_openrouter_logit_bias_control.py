#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger1_openrouter_logit_bias_control.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_openrouter_logit_bias_control", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Trigger1OpenRouterLogitVectorTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.vector = {"10": 2.0, "20": -1.0, "30": 0.5}
        self.exact_model = "example/model:free"
        self.tokenizer_id = "example/model"
        self.tokenizer_sha256 = "a" * 64
        self.provenance = {
            "providers": {
                "openrouter": {
                    "allowed_routes": [self.exact_model],
                    "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                    "source": "provider-side-test-evidence",
                    "route_evidence": {
                        self.exact_model: {
                            "source": "provider-side-test-evidence/exact-model",
                            "price": "FREE",
                            "prompt_token_price": 0,
                            "completion_token_price": 0,
                            "exact_model_identity": True,
                            "weights_repository": self.tokenizer_id,
                            "weights_revision": "revision-1",
                            "tokenizer_json_sha256": self.tokenizer_sha256,
                        }
                    },
                }
            }
        }

    def test_current_dynamic_free_router_is_never_exact_model_identity(self):
        result = self.mod.exact_free_route_gate(
            self.mod.DYNAMIC_FREE_ROUTER,
            {
                "providers": {
                    "openrouter": {
                        "allowed_routes": [self.mod.DYNAMIC_FREE_ROUTER],
                        "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                    }
                }
            },
        )
        self.assertFalse(result["ok"])
        self.assertEqual(
            "DYNAMIC_FREE_ROUTER_CANNOT_BIND_MODEL_TOKENIZER_IDENTITY",
            result["reason"],
        )

    def test_unbound_exact_route_fails_closed(self):
        result = self.mod.exact_free_route_gate("vendor/not-bound:free", self.provenance)
        self.assertFalse(result["ok"])
        self.assertEqual("EXACT_MODEL_ROUTE_NOT_ZERO_PRICE_BOUND", result["reason"])

    def test_allowed_route_without_route_specific_evidence_fails_closed(self):
        provenance = {
            "providers": {
                "openrouter": {
                    "allowed_routes": [self.exact_model],
                    "evidence_kind": "EXACT_ROUTE_ZERO_PRICE",
                }
            }
        }
        result = self.mod.exact_free_route_gate(self.exact_model, provenance)
        self.assertFalse(result["ok"])
        self.assertEqual("ROUTE_SPECIFIC_ZERO_PRICE_EVIDENCE_REQUIRED", result["reason"])

    def test_exact_route_binds_model_revision_and_tokenizer(self):
        result = self.mod.exact_free_route_gate(self.exact_model, self.provenance)
        self.assertTrue(result["ok"])
        self.assertEqual(self.tokenizer_id, result["weights_repository"])
        self.assertEqual("revision-1", result["weights_revision"])
        self.assertEqual(self.tokenizer_sha256, result["tokenizer_json_sha256"])
        self.assertEqual(64, len(result["route_evidence_sha256"]))

    def test_control_family_has_required_matched_controls(self):
        family = self.mod.control_family(self.vector)
        self.assertEqual(
            {
                "BASELINE",
                "+VECTOR",
                "SIGN_FLIP",
                "NULL_VECTOR",
                "ORTHOGONAL_SAME_NORM",
                "PERMUTED_SAME_NORM",
            },
            set(family),
        )
        primary = list(family["+VECTOR"].values())
        sign = list(family["SIGN_FLIP"].values())
        null = list(family["NULL_VECTOR"].values())
        orth = list(family["ORTHOGONAL_SAME_NORM"].values())
        perm = list(family["PERMUTED_SAME_NORM"].values())
        self.assertEqual([-x for x in primary], sign)
        self.assertTrue(all(x == 0.0 for x in null))
        self.assertAlmostEqual(sum(x * y for x, y in zip(primary, orth)), 0.0, places=10)
        self.assertAlmostEqual(
            math.sqrt(sum(x * x for x in primary)),
            math.sqrt(sum(x * x for x in orth)),
            places=10,
        )
        self.assertAlmostEqual(
            math.sqrt(sum(x * x for x in primary)),
            math.sqrt(sum(x * x for x in perm)),
            places=10,
        )
        self.assertNotEqual(primary, perm)

    def test_request_requires_parameter_consumption_and_no_fallback(self):
        result = self.mod.build_request(
            model=self.exact_model,
            tokenizer_id=self.tokenizer_id,
            tokenizer_sha256=self.tokenizer_sha256,
            prompt="fixed holdout prompt",
            vector=self.vector,
            control="+VECTOR",
            seed=17,
            max_tokens=64,
            provenance=self.provenance,
        )
        body = result["body"]
        identity = result["identity"]
        self.assertEqual(self.exact_model, body["model"])
        self.assertEqual(self.vector, body["logit_bias"])
        self.assertTrue(body["provider"]["require_parameters"])
        self.assertFalse(body["provider"]["allow_fallbacks"])
        self.assertEqual(17, body["seed"])
        self.assertTrue(body["logprobs"])
        self.assertEqual(self.tokenizer_id, identity["weights_repository"])
        self.assertEqual("revision-1", identity["weights_revision"])
        self.assertEqual(
            "OUTPUT_LOGIT_VECTOR_CONTROL_COMPONENT_ONLY",
            identity["credit_scope"],
        )
        self.assertEqual(64, len(identity["request_identity_sha256"]))

    def test_tokenizer_identity_mismatch_fails_closed(self):
        with self.assertRaisesRegex(
            self.mod.Trigger1LogitVectorError,
            "TOKENIZER_ID_ROUTE_IDENTITY_MISMATCH",
        ):
            self.mod.build_request(
                model=self.exact_model,
                tokenizer_id="wrong/tokenizer",
                tokenizer_sha256=self.tokenizer_sha256,
                prompt="fixed holdout prompt",
                vector=self.vector,
                control="+VECTOR",
                seed=17,
                provenance=self.provenance,
            )
        with self.assertRaisesRegex(
            self.mod.Trigger1LogitVectorError,
            "TOKENIZER_SHA256_ROUTE_IDENTITY_MISMATCH",
        ):
            self.mod.build_request(
                model=self.exact_model,
                tokenizer_id=self.tokenizer_id,
                tokenizer_sha256="b" * 64,
                prompt="fixed holdout prompt",
                vector=self.vector,
                control="+VECTOR",
                seed=17,
                provenance=self.provenance,
            )

    def test_baseline_omits_logit_bias(self):
        result = self.mod.build_request(
            model=self.exact_model,
            tokenizer_id=self.tokenizer_id,
            tokenizer_sha256=self.tokenizer_sha256,
            prompt="fixed holdout prompt",
            vector=self.vector,
            control="BASELINE",
            seed=17,
            provenance=self.provenance,
        )
        self.assertNotIn("logit_bias", result["body"])

    def test_tokenizer_digest_is_mandatory(self):
        with self.assertRaisesRegex(
            self.mod.Trigger1LogitVectorError,
            "TOKENIZER_SHA256_REQUIRED",
        ):
            self.mod.build_request(
                model=self.exact_model,
                tokenizer_id=self.tokenizer_id,
                tokenizer_sha256="unknown",
                prompt="fixed holdout prompt",
                vector=self.vector,
                control="+VECTOR",
                seed=17,
                provenance=self.provenance,
            )


if __name__ == "__main__":
    unittest.main()
