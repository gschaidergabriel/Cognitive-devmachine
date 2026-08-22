#!/usr/bin/env python3
from __future__ import annotations

import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import clay_profile_pipeline_runtime as runtime_mod


REQUIRED_EFFECTS = {
    "pipeline_init",
    "pipeline_profile_read",
    "pipeline_state_read",
    "pipeline_collect",
    "pipeline_compile",
    "pipeline_build_prompt",
    "inference_generate",
    "pipeline_gate",
    "pipeline_commit",
}


def minimal_profile() -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "test-neutral",
        "inference": {
            "kind": "fixture",
            "model": "fixture-model",
            "response_pointer": "/choices/0/message/content",
        },
        "personality": {
            "system_prompt": "neutral",
            "public_style": "neutral",
            "output_contract": {},
        },
        "sources": [],
        "state_metrics": [],
        "gate": {},
    }


class ReferenceEffectSurfaceConvergenceTests(unittest.TestCase):
    def test_effect_surface_matches_current_pipeline_exactly(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rt = runtime_mod.ProfilePipelineRuntime(root=td)
            self.assertEqual(rt.allowed_effects, REQUIRED_EFFECTS)
            self.assertNotIn("profile_load", rt.allowed_effects)
            self.assertNotIn("provider_chat_json", rt.allowed_effects)

    def test_db_profile_import_read_and_digest_tamper_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            db_path = Path(td) / "entity.db"
            rt = runtime_mod.ProfilePipelineRuntime(root=td)
            imported = rt.import_profile(str(db_path), minimal_profile())
            self.assertTrue(imported["ok"])

            read = rt.effect("pipeline_profile_read", {"entity_db": str(db_path)})
            self.assertTrue(read["ok"], read)
            self.assertEqual(read["profile"]["profile_id"], "test-neutral")
            self.assertEqual(read["profile"]["inference"]["kind"], "fixture")
            self.assertEqual(read["profile_hash"], imported["profile_hash"])

            with sqlite3.connect(db_path) as db:
                row = db.execute(
                    "SELECT profile_json FROM eos_pipeline_profile WHERE singleton=1"
                ).fetchone()
                profile = json.loads(row[0])
                profile["profile_id"] = "tampered"
                db.execute(
                    "UPDATE eos_pipeline_profile SET profile_json=? WHERE singleton=1",
                    (json.dumps(profile, sort_keys=True, separators=(",", ":")),),
                )

            tampered = rt.effect("pipeline_profile_read", {"entity_db": str(db_path)})
            self.assertFalse(tampered["ok"])
            self.assertIn("PROFILE_INTEGRITY_MISMATCH", tampered["error"])

    def test_missing_profile_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            rt = runtime_mod.ProfilePipelineRuntime(root=td)
            result = rt.effect(
                "pipeline_profile_read",
                {"entity_db": str(Path(td) / "fresh.db")},
            )
            self.assertFalse(result["ok"])
            self.assertIn("NO_ACTIVE_PROFILE", result["error"])

    def test_inference_generate_keeps_provider_helper_private(self) -> None:
        seen = {}

        def fixture(request: dict) -> dict:
            seen.update(request)
            return {"fixture": True}

        with tempfile.TemporaryDirectory() as td:
            rt = runtime_mod.ProfilePipelineRuntime(root=td, provider_override=fixture)
            result = rt.effect(
                "inference_generate",
                {
                    "inference": {"kind": "fixture", "model": "fixture-model"},
                    "system": "s",
                    "user": "u",
                    "secret_file": "",
                },
            )
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["payload"], {"fixture": True})
            self.assertEqual(seen["provider"]["kind"], "fixture")
            with self.assertRaises(Exception):
                rt.effect("provider_chat_json", {})

    def test_json_pointer_accepts_shipped_v2_pointer_shape(self) -> None:
        payload = {"choices": [{"message": {"content": "ok"}}]}
        self.assertEqual(
            runtime_mod.ProfilePipelineRuntime._pointer(
                payload, "/choices/0/message/content"
            ),
            "ok",
        )


if __name__ == "__main__":
    unittest.main()
