#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path
import sys
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_6000_free_swarm_v3 as gated


class FreeOnlyCatalogPreflight870(unittest.TestCase):
    def setUp(self) -> None:
        gated._EVIDENCE_CACHE.clear()
        self.spec = gated.fabric.base.ProviderSpec(
            name="mistral",
            endpoint="https://api.mistral.ai/v1/chat/completions",
            key_envs=("MISTRAL_API_KEY",),
            keys_list_env="MISTRAL_API_KEYS",
            models_env="MISTRAL_SWARM_MODELS",
            default_models=("mistral-small-latest",),
            attestation_env="CLAY_MISTRAL_FREE_ATTESTED",
            default_max_concurrency=1,
        )

    def test_active_v3_replaces_v2_network_catalog_discovery(self) -> None:
        self.assertIs(
            gated.fabric.opt.discover_and_export,
            gated.route_safe_discover_and_export,
        )

    def test_static_default_discovery_never_calls_provider_catalog(self) -> None:
        env = {
            "CLAY_FREE_ONLY_ATTESTED": "1",
            "CLAY_MISTRAL_FREE_ATTESTED": "1",
        }
        with (
            mock.patch.object(gated.fabric.base, "PROVIDERS", (self.spec,)),
            mock.patch.object(gated.fabric, "load_provider_admission", return_value={"authority_epoch": "8.70"}),
            mock.patch.object(gated.fabric, "provider_is_admitted_free", return_value=True),
            mock.patch.object(gated.fabric.base, "collect_keys", return_value=["synthetic-key"]),
            mock.patch.object(
                gated.fabric.opt,
                "fetch_catalog",
                side_effect=AssertionError("provider catalog network must not run before route binding"),
            ) as catalog,
            mock.patch.dict(os.environ, env, clear=False),
        ):
            os.environ.pop("MISTRAL_SWARM_MODELS", None)
            report = gated.route_safe_discover_and_export(0.01)

        catalog.assert_not_called()
        self.assertEqual(
            report["mistral"]["source"],
            "static_defaults_no_catalog_economic_provenance",
        )
        self.assertFalse(report["mistral"]["catalog_network_attempted"])
        self.assertTrue(report["mistral"]["route_binding_deferred_to_current_lane_binding"])
        self.assertEqual(report["mistral"]["models"], ["mistral-small-latest"])

    def test_environment_override_is_network_free_and_preserved(self) -> None:
        env = {
            "CLAY_FREE_ONLY_ATTESTED": "1",
            "CLAY_MISTRAL_FREE_ATTESTED": "1",
            "MISTRAL_SWARM_MODELS": "model-a,model-b",
        }
        with (
            mock.patch.object(gated.fabric.base, "PROVIDERS", (self.spec,)),
            mock.patch.object(gated.fabric, "load_provider_admission", return_value={"authority_epoch": "8.70"}),
            mock.patch.object(gated.fabric, "provider_is_admitted_free", return_value=True),
            mock.patch.object(gated.fabric.base, "collect_keys", return_value=["synthetic-key"]),
            mock.patch.object(
                gated.fabric.opt,
                "fetch_catalog",
                side_effect=AssertionError("provider catalog network must not run before route binding"),
            ) as catalog,
            mock.patch.dict(os.environ, env, clear=False),
        ):
            report = gated.route_safe_discover_and_export(0.01)

        catalog.assert_not_called()
        self.assertEqual(report["mistral"]["source"], "environment_override")
        self.assertEqual(report["mistral"]["models"], ["model-a", "model-b"])
        self.assertFalse(report["mistral"]["catalog_network_attempted"])


if __name__ == "__main__":
    unittest.main()
