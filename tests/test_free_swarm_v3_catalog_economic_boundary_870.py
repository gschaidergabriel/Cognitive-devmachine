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

import run_6000_free_swarm_v3 as v3


class FreeSwarmV3CatalogEconomicBoundaryTests(unittest.TestCase):
    def test_catalog_hook_is_local_route_bound_implementation(self) -> None:
        self.assertIs(v3.fabric.opt.fetch_catalog, v3.route_bound_catalog)

    def test_current_owner_directive_replaces_old_compatibility_pointer(self) -> None:
        self.assertEqual(
            v3.fabric.base.OWNER_DIRECTIVE_PATH,
            ROOT / "governance/CLAY_FREE_SWARM_OWNER_ADMISSION_2026-08-24.md",
        )

    def test_catalog_never_needs_provider_network_and_filters_unbound_route(self) -> None:
        spec = next(s for s in v3.fabric.base.PROVIDERS if s.name == "openrouter")
        old = os.environ.get(spec.models_env)
        os.environ[spec.models_env] = "openrouter/free,example/paid-route"
        seen: list[tuple[str, str]] = []

        def fake_binding(provider, credential_fingerprint, model, endpoint, *, artifacts):
            del credential_fingerprint, endpoint, artifacts
            seen.append((provider, model))
            if model == "openrouter/free":
                return {"ok": True, "admission_epoch": "8.71"}
            return {"ok": False, "reason": "NOT_ZERO_COST_BOUND"}

        try:
            with mock.patch.object(v3, "current_lane_binding", side_effect=fake_binding), \
                    mock.patch("urllib.request.urlopen", side_effect=AssertionError("provider network forbidden")):
                rows = v3.route_bound_catalog(
                    "openrouter",
                    "https://openrouter.ai/api/v1/models",
                    "sentinel-not-a-real-key",
                    1.0,
                )
        finally:
            if old is None:
                os.environ.pop(spec.models_env, None)
            else:
                os.environ[spec.models_env] = old

        self.assertEqual([row["id"] for row in rows], ["openrouter/free"])
        self.assertEqual(
            rows[0]["_clay_catalog_source"],
            "LOCAL_ROUTE_BOUND_NO_PROVIDER_NETWORK",
        )
        self.assertEqual(
            seen,
            [("openrouter", "openrouter/free"), ("openrouter", "example/paid-route")],
        )

    def test_unknown_provider_fails_closed_without_binding_or_network(self) -> None:
        with mock.patch.object(v3, "current_lane_binding") as binding, \
                mock.patch("urllib.request.urlopen", side_effect=AssertionError("provider network forbidden")):
            self.assertEqual(v3.route_bound_catalog("unknown", "https://invalid.example/models", "x", 1.0), [])
        binding.assert_not_called()


if __name__ == "__main__":
    unittest.main()
