from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import cognitive_engine_route_v1 as route


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def fixtures(target: str = "BUNDLED_LOCAL_08B", mode: str = "FULL_LOCAL_LATENT"):
    cognition = {
        "bundled_manifest_digest": digest("manifest"),
        "local_model_digest": digest("model"),
        "tokenizer_digest": digest("tokenizer"),
        "jspace_profile_digest": digest("jspace"),
        "jacobian_lens_digest": digest("lens"),
        "workspace_calibration_digest": digest("workspace-calibration"),
    }
    prepare = {
        "ok": True,
        "entity_generation": 7,
        "causal_turn_id": "turn-7-a",
        "turn_binding_digest": digest("turn-binding"),
        "boot_binding_digest": digest("boot-binding"),
        "workspace_digest": digest("workspace"),
        **cognition,
    }
    profile = {
        "profile_id": "mini-default",
        "_runtime_profile_snapshot": {
            "profile_id": "mini-default",
            "profile_hash": digest("profile"),
        },
        "inference": {
            "kind": "local_exec" if target == "BUNDLED_LOCAL_08B" else "claude_code",
            "model": "configured-target",
            "cognitive_engine_route": {
                "schema": route.ROUTE_SCHEMA,
                "target_engine_class": target,
                "jspace_mode": mode,
                **cognition,
            },
        },
    }
    return profile, prepare


class CognitiveEngineRouteTests(unittest.TestCase):
    def test_exact_local_route_is_bound_to_cognition_ancestry(self):
        profile, prepare = fixtures()
        resolved = route.resolve_engine_route(profile, prepare, expected_generation=7)
        self.assertTrue(resolved["ok"])
        self.assertEqual(resolved["target_engine_class"], "BUNDLED_LOCAL_08B")
        self.assertEqual(resolved["jspace_mode"], "FULL_LOCAL_LATENT")
        self.assertEqual(resolved["turn_binding_digest"], prepare["turn_binding_digest"])
        self.assertEqual(resolved["profile_hash"], profile["_runtime_profile_snapshot"]["profile_hash"])
        self.assertEqual(len(resolved["route_digest"]), 64)

    def test_provider_or_model_name_cannot_infer_route(self):
        profile, prepare = fixtures()
        profile["inference"].pop("cognitive_engine_route")
        profile["inference"]["kind"] = "openai_compatible_chat_json"
        profile["inference"]["model"] = "looks-hookable-but-is-not-authority"
        with self.assertRaisesRegex(
            route.CognitiveEngineRouteError, "EXPLICIT_COGNITIVE_ENGINE_ROUTE_REQUIRED"
        ):
            route.resolve_engine_route(profile, prepare, expected_generation=7)

    def test_cognition_digest_drift_fails_closed(self):
        profile, prepare = fixtures()
        profile["inference"]["cognitive_engine_route"]["jspace_profile_digest"] = digest("other-jspace")
        with self.assertRaisesRegex(
            route.CognitiveEngineRouteError,
            "COGNITION_ROUTE_BINDING_MISMATCH:jspace_profile_digest",
        ):
            route.resolve_engine_route(profile, prepare, expected_generation=7)

    def test_stale_generation_fails_closed(self):
        profile, prepare = fixtures()
        with self.assertRaisesRegex(route.CognitiveEngineRouteError, "STALE_GENERATION"):
            route.resolve_engine_route(profile, prepare, expected_generation=8)

    def test_claude_requires_compiled_external(self):
        profile, prepare = fixtures(target="CLAUDE_CODE", mode="FULL_LOCAL_LATENT")
        with self.assertRaisesRegex(
            route.CognitiveEngineRouteError, "CLAUDE_MUST_BE_COMPILED_EXTERNAL"
        ):
            route.resolve_engine_route(profile, prepare, expected_generation=7)

    def test_claude_compiled_external_is_explicitly_admitted(self):
        profile, prepare = fixtures(target="CLAUDE_CODE", mode="COMPILED_EXTERNAL")
        resolved = route.resolve_engine_route(profile, prepare, expected_generation=7)
        self.assertEqual(resolved["target_engine_class"], "CLAUDE_CODE")
        self.assertEqual(resolved["jspace_mode"], "COMPILED_EXTERNAL")

    def test_local_08b_cannot_claim_external_mode(self):
        profile, prepare = fixtures(target="BUNDLED_LOCAL_08B", mode="COMPILED_EXTERNAL")
        with self.assertRaisesRegex(
            route.CognitiveEngineRouteError, "LOCAL_08B_JSPACE_MODE_INVALID"
        ):
            route.resolve_engine_route(profile, prepare, expected_generation=7)


if __name__ == "__main__":
    unittest.main()
