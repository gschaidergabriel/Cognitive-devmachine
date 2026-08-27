#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger1_openrouter_free_route_audit.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_openrouter_free_route_audit", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Trigger1OpenRouterFreeRouteAuditTests(unittest.TestCase):
    def setUp(self):
        self.mod = load_module()
        self.sha = "a" * 64
        self.prov = {"providers": {"openrouter": {"allowed_routes": ["vendor/model:free"]}}}

    def card(self, model="vendor/model:free", price="0", params=None, hf="vendor/model"):
        return {
            "id": model,
            "hugging_face_id": hf,
            "pricing": {"prompt": price, "completion": price},
            "architecture": {"tokenizer": "Example"},
            "supported_parameters": params or ["logit_bias", "logprobs", "seed", "max_tokens"],
        }

    def test_ready_requires_all_bindings(self):
        row = self.mod.audit_model(
            self.card(),
            economic_provenance=self.prov,
            tokenizer_bindings={"vendor/model:free": {"tokenizer_id": "vendor/tokenizer", "tokenizer_sha256": self.sha}},
        )
        self.assertEqual("READY", row["status"])
        self.assertEqual([], row["blockers"])

    def test_zero_price_free_variant_without_logit_bias_is_blocked(self):
        row = self.mod.audit_model(
            self.card(params=["logprobs", "seed", "max_tokens"]),
            economic_provenance=self.prov,
            tokenizer_bindings={"vendor/model:free": {"tokenizer_id": "vendor/tokenizer", "tokenizer_sha256": self.sha}},
        )
        self.assertIn("PARAMETER_UNSUPPORTED:logit_bias", row["blockers"])

    def test_paid_route_with_logit_bias_is_blocked(self):
        row = self.mod.audit_model(
            self.card(price="0.000001"),
            economic_provenance=self.prov,
            tokenizer_bindings={"vendor/model:free": {"tokenizer_id": "vendor/tokenizer", "tokenizer_sha256": self.sha}},
        )
        self.assertIn("EXACT_ROUTE_NOT_ZERO_PRICE", row["blockers"])

    def test_dynamic_free_router_is_never_ready(self):
        prov = {"providers": {"openrouter": {"allowed_routes": [self.mod.DYNAMIC_FREE_ROUTER]}}}
        row = self.mod.audit_model(
            self.card(model=self.mod.DYNAMIC_FREE_ROUTER),
            economic_provenance=prov,
            tokenizer_bindings={self.mod.DYNAMIC_FREE_ROUTER: {"tokenizer_id": "router", "tokenizer_sha256": self.sha}},
        )
        self.assertIn("DYNAMIC_FREE_ROUTER_CANNOT_BIND_MODEL_TOKENIZER_IDENTITY", row["blockers"])

    def test_exact_free_route_not_in_economic_provenance_is_blocked(self):
        row = self.mod.audit_model(
            self.card(),
            economic_provenance={"providers": {"openrouter": {"allowed_routes": ["openrouter/free"]}}},
            tokenizer_bindings={"vendor/model:free": {"tokenizer_id": "vendor/tokenizer", "tokenizer_sha256": self.sha}},
        )
        self.assertIn("EXACT_ROUTE_NOT_ECONOMICALLY_ADMITTED", row["blockers"])

    def test_canonical_route_evidence_can_supply_exact_tokenizer_binding(self):
        prov = {
            "providers": {
                "openrouter": {
                    "allowed_routes": ["vendor/model:free"],
                    "route_evidence": {
                        "vendor/model:free": {
                            "weights_repository": "vendor/model",
                            "weights_revision": "rev123",
                            "tokenizer_json_sha256": self.sha,
                        }
                    },
                }
            }
        }
        row = self.mod.audit_model(self.card(), economic_provenance=prov)
        self.assertEqual("READY", row["status"])
        self.assertEqual(self.sha, row["tokenizer_binding"]["tokenizer_sha256"])
        self.assertIn("vendor/model@rev123", row["tokenizer_binding"]["tokenizer_id"])

    def test_open_weight_candidate_without_exact_tokenizer_digest_stays_blocked(self):
        row = self.mod.audit_model(self.card(), economic_provenance=self.prov)
        self.assertIn("EXACT_TOKENIZER_BINDING_MISSING", row["blockers"])

    def test_catalog_only_surfaces_parameter_capable_open_weight_candidates(self):
        catalog = {"data": [
            self.card(model="a/free:free", params=["logit_bias", "logprobs", "seed"]),
            self.card(model="b/free:free", params=["logprobs", "seed"]),
            self.card(model="c/paid", price="0.1", params=["logit_bias", "logprobs", "seed"]),
        ]}
        result = self.mod.audit_catalog(
            catalog,
            economic_provenance={"providers": {"openrouter": {"allowed_routes": []}}},
        )
        self.assertEqual(2, result["exact_zero_price_routes"])
        self.assertEqual(1, result["parameter_capable_open_weight_candidates"])
        self.assertEqual("a/free:free", result["candidates"][0]["model"])
        self.assertEqual([], result["ready_routes"])


if __name__ == "__main__":
    unittest.main()
