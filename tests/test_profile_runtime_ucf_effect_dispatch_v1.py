#!/usr/bin/env python3
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import clay_profile_pipeline_runtime as runtime_mod


PACKET = "1" * 64
ADMISSION = "2" * 64
OTHER_PACKET = "3" * 64


class RuntimeUcfEffectDispatchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = runtime_mod.ProfilePipelineRuntime(
            root=self.tmp.name,
            provider_override=lambda request: {"candidate": True},
        )

    def tearDown(self):
        self.tmp.cleanup()

    def test_admission_effect_delegates_to_single_merged_binding(self):
        payload = {"entity_db": "mini.db", "profile": {}, "data": {}}
        admitted = {
            "ok": True,
            "inference_packet_digest": PACKET,
            "cognitive_fabric_receipt_digest": ADMISSION,
        }
        with mock.patch.object(
            runtime_mod.cognitive_fabric_binding,
            "admit_profile_runtime_payload",
            return_value=admitted,
        ) as bridge:
            out = self.runtime.effect("pipeline_cognitive_fabric_admit", payload)
        self.assertEqual(out, admitted)
        bridge.assert_called_once_with(self.runtime, payload)
        self.assertEqual(self.runtime.effect_trace[-1]["kind"], "pipeline_cognitive_fabric_admit")
        self.assertTrue(self.runtime.effect_trace[-1]["ok"])

    def test_inference_requires_and_preserves_pre_admission_identity(self):
        out = self.runtime.effect(
            "inference_generate",
            {
                "inference": {"kind": "mock", "model": "fixture"},
                "system": "s",
                "user": "u",
                "inference_packet_digest": PACKET,
                "cognitive_fabric_admission_receipt_digest": ADMISSION,
            },
        )
        self.assertTrue(out["ok"])
        self.assertEqual(out["inference_packet_digest"], PACKET)
        self.assertEqual(out["cognitive_fabric_admission_receipt_digest"], ADMISSION)

    def test_inference_rejects_missing_or_placeholder_identity_before_provider(self):
        provider = mock.Mock(return_value={"candidate": True})
        runtime = runtime_mod.ProfilePipelineRuntime(root=self.tmp.name, provider_override=provider)
        for packet in (None, "0" * 64):
            with self.subTest(packet=packet):
                out = runtime.effect(
                    "inference_generate",
                    {
                        "inference": {"kind": "mock"},
                        "system": "s",
                        "user": "u",
                        "inference_packet_digest": packet,
                        "cognitive_fabric_admission_receipt_digest": ADMISSION,
                    },
                )
                self.assertFalse(out["ok"])
        provider.assert_not_called()

    def test_gate_rejects_generated_identity_substitution_before_content_gate(self):
        out = self.runtime.effect(
            "pipeline_gate",
            {
                "profile": {"personality": {"output_contract": {}}, "gate": {}},
                "data": {
                    "compiled": {},
                    "generated": {
                        "ok": True,
                        "payload": {},
                        "inference_packet_digest": OTHER_PACKET,
                        "cognitive_fabric_admission_receipt_digest": ADMISSION,
                    },
                    "cognitive_fabric_admission": {
                        "ok": True,
                        "inference_packet_digest": PACKET,
                        "cognitive_fabric_receipt_digest": ADMISSION,
                    },
                },
            },
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "INFERENCE_PACKET_ANCESTRY_MISMATCH")

    def test_finalize_effect_is_explicit_post_commit_failure_not_fake_receipt(self):
        out = self.runtime.effect(
            "pipeline_cognitive_fabric_finalize",
            {
                "data": {
                    "admitted": {
                        "ok": True,
                        "inference_packet_digest": PACKET,
                        "cognitive_fabric_receipt_digest": ADMISSION,
                    },
                    "generated": {
                        "ok": True,
                        "inference_packet_digest": PACKET,
                        "cognitive_fabric_admission_receipt_digest": ADMISSION,
                    },
                    "gated": {"ok": True},
                    "committed": {"ok": True, "output_id": "o1", "generation": 8},
                }
            },
        )
        self.assertFalse(out["ok"])
        self.assertEqual(out["error"], "UCF_FINAL_RUNTIME_RECEIPT_NOT_IMPLEMENTED")
        self.assertEqual(out["committed_output_id"], "o1")
        self.assertNotIn("ucf_runtime_receipt_digest", out)
        self.assertFalse(self.runtime.effect_trace[-1]["ok"])


if __name__ == "__main__":
    unittest.main()
