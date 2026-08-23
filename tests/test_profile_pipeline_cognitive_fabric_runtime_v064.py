#!/usr/bin/env python3
from __future__ import annotations

import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import clay_profile_pipeline_runtime as runtime_module

HEX_A = "a" * 64
HEX_B = "b" * 64


class ProfilePipelineCognitiveFabricRuntimeV064Tests(unittest.TestCase):
    def make_runtime(self, root: Path, **kwargs):
        return runtime_module.ProfilePipelineRuntime(root=root, **kwargs)

    def test_pipeline_init_installs_cognition_schema_inside_canonical_db(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = self.make_runtime(root)
            result = runtime.effect("pipeline_init", {"entity_db": "entity.db"})
            self.assertTrue(result["ok"], result)
            expected = {
                "mini_cognition_objects",
                "mini_cognition_object_admissions",
                "mini_cognition_boot_bindings",
                "mini_cognition_turn_bindings",
                "mini_cognition_active_turns",
            }
            with sqlite3.connect(root / "entity.db") as db:
                found = {
                    str(row[0])
                    for row in db.execute(
                        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'mini_cognition_%'"
                    ).fetchall()
                }
            self.assertTrue(expected.issubset(found))

    def test_admission_uses_same_db_generation_and_canonical_compositor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = self.make_runtime(root)
            self.assertTrue(runtime.effect("pipeline_init", {"entity_db": "entity.db"})["ok"])
            compiled = {"canonical_state_hash": HEX_A, "packet_hash": HEX_B}
            admitted = {
                "ok": True,
                "generation": 0,
                "canonical_state_hash": HEX_A,
                "packet_hash": HEX_B,
                "inference_packet_digest": "c" * 64,
                "cognitive_fabric_receipt_digest": "d" * 64,
                "inference": {"kind": "mock"},
                "system": "system",
                "user": "user",
            }
            with mock.patch.object(
                runtime_module.cognitive_fabric_admission,
                "build_pre_inference_admission",
                return_value=admitted,
            ) as compositor:
                result = runtime.effect(
                    "pipeline_cognitive_fabric_admit",
                    {
                        "entity_db": "entity.db",
                        "source_db": "source.db",
                        "profile": {},
                        "previous": {"generation": 0},
                        "data": {
                            "compiled": compiled,
                            "prompt": {"system": "system", "user": "{}"},
                            "invocation": {"selector": "bounded"},
                        },
                    },
                )
            self.assertTrue(result["ok"], result)
            self.assertEqual(compositor.call_count, 1)
            kwargs = compositor.call_args.kwargs
            self.assertEqual(kwargs["entity_generation"], 0)
            self.assertEqual(kwargs["compiled"], compiled)
            self.assertEqual(kwargs["origin"], runtime_module.VERSION)

    def test_admission_rejects_stale_generation_before_compositor(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            runtime = self.make_runtime(root)
            self.assertTrue(runtime.effect("pipeline_init", {"entity_db": "entity.db"})["ok"])
            with mock.patch.object(
                runtime_module.cognitive_fabric_admission,
                "build_pre_inference_admission",
            ) as compositor:
                result = runtime.effect(
                    "pipeline_cognitive_fabric_admit",
                    {
                        "entity_db": "entity.db",
                        "source_db": "source.db",
                        "profile": {},
                        "previous": {"generation": 1},
                        "data": {
                            "compiled": {"canonical_state_hash": HEX_A, "packet_hash": HEX_B},
                            "prompt": {},
                            "invocation": {},
                        },
                    },
                )
            self.assertFalse(result["ok"])
            self.assertIn("STALE_GENERATION", result["error"])
            compositor.assert_not_called()

    def test_inference_requires_and_propagates_admission_identities(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            seen = {}

            def provider(request):
                seen.update(request)
                return {"candidate": True}

            runtime = self.make_runtime(root, provider_override=provider)
            denied = runtime.effect(
                "inference_generate",
                {"inference": {"kind": "mock"}, "system": "s", "user": "u"},
            )
            self.assertFalse(denied["ok"])
            self.assertIn("inference_packet_digest", denied["error"])

            result = runtime.effect(
                "inference_generate",
                {
                    "inference": {"kind": "mock"},
                    "system": "s",
                    "user": "u",
                    "inference_packet_digest": HEX_A,
                    "cognitive_fabric_admission_receipt_digest": HEX_B,
                },
            )
            self.assertTrue(result["ok"], result)
            self.assertEqual(result["inference_packet_digest"], HEX_A)
            self.assertEqual(result["cognitive_fabric_admission_receipt_digest"], HEX_B)
            self.assertEqual(seen["inference_packet_digest"], HEX_A)
            self.assertEqual(seen["cognitive_fabric_admission_receipt_digest"], HEX_B)

    def test_postcommit_finalizer_never_fabricates_final_ucf_receipt(self):
        with tempfile.TemporaryDirectory() as td:
            runtime = self.make_runtime(Path(td))
            result = runtime.effect(
                "pipeline_cognitive_fabric_finalize",
                {
                    "entity_db": "entity.db",
                    "source_db": "source.db",
                    "profile": {},
                    "previous": {"generation": 0},
                    "data": {
                        "admitted": {
                            "ok": True,
                            "inference_packet_digest": HEX_A,
                            "cognitive_fabric_receipt_digest": HEX_B,
                        },
                        "generated": {
                            "ok": True,
                            "inference_packet_digest": HEX_A,
                            "cognitive_fabric_admission_receipt_digest": HEX_B,
                        },
                        "gated": {"ok": True},
                        "committed": {"ok": True, "output_id": "o1", "generation": 1},
                    },
                },
            )
            self.assertFalse(result["ok"])
            self.assertEqual(result["error"], "UCF_FINAL_RECEIPT_SOURCE_RUNTIME_IDENTITY_UNBOUND")
            self.assertTrue(result["retry_commit_forbidden"])
            self.assertNotIn("ucf_runtime_receipt_digest", result)


if __name__ == "__main__":
    unittest.main()
