#!/usr/bin/env python3
from __future__ import annotations

import copy
import tempfile
import unittest

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


class PersistedStringScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.runtime = ProfilePipelineRuntime(root=self.tmp.name)
        self.profile = {
            "personality": {
                "output_contract": {
                    "title_field": "title",
                    "intro_field": "intro",
                    "sections_field": "sections",
                    "continuity_field": "continuity",
                    "autobiographical_hypotheses_field": "autobiographical_hypotheses",
                    "section_text_field": "text",
                    "section_evidence_field": "evidence_refs",
                    "section_claims_field": "state_claims",
                }
            },
            "gate": {
                "require_hash_echo": True,
                "require_evidence_per_section": True,
                "leak_patterns": [r"SENTINEL_LEAK"],
            },
        }
        self.compiled = {
            "canonical_state_hash": "canonical-hash",
            "packet_hash": "packet-hash",
            "allowed_evidence_refs": ["e:1"],
            "personality_state": {},
        }
        self.clean = {
            "canonical_state_hash_seen": "canonical-hash",
            "packet_hash_seen": "packet-hash",
            "title": "clean title",
            "intro": "clean intro",
            "sections": [
                {"text": "clean section", "evidence_refs": ["e:1"], "state_claims": {}}
            ],
            "continuity": "clean continuity",
            "autobiographical_hypotheses": ["clean hypothesis"],
            "additional_self_report": {"nested": ["clean value"]},
        }

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def gate(self, payload: dict) -> dict:
        return self.runtime._pipeline_gate(
            {
                "profile": self.profile,
                "data": {"generated": {"payload": payload}, "compiled": self.compiled},
            }
        )

    def test_clean_nested_payload_passes(self) -> None:
        self.assertTrue(self.gate(copy.deepcopy(self.clean))["ok"])

    def test_leak_pattern_is_rejected_in_every_persisted_value_region(self) -> None:
        variants = []
        p = copy.deepcopy(self.clean); p["continuity"] = "SENTINEL_LEAK"; variants.append(p)
        p = copy.deepcopy(self.clean); p["autobiographical_hypotheses"] = ["SENTINEL_LEAK"]; variants.append(p)
        p = copy.deepcopy(self.clean); p["additional_self_report"] = {"deep": [{"value": "SENTINEL_LEAK"}]}; variants.append(p)
        for payload in variants:
            with self.subTest(payload=payload):
                result = self.gate(payload)
                self.assertFalse(result["ok"])
                self.assertEqual("LEAK_PATTERN", result["error"])

    def test_active_secret_is_rejected_in_every_persisted_value_region(self) -> None:
        self.runtime._active_secrets = ["SECRET_SENTINEL"]
        variants = []
        p = copy.deepcopy(self.clean); p["continuity"] = "SECRET_SENTINEL"; variants.append(p)
        p = copy.deepcopy(self.clean); p["autobiographical_hypotheses"] = ["SECRET_SENTINEL"]; variants.append(p)
        p = copy.deepcopy(self.clean); p["additional_self_report"] = {"deep": [{"value": "SECRET_SENTINEL"}]}; variants.append(p)
        for payload in variants:
            with self.subTest(payload=payload):
                result = self.gate(payload)
                self.assertFalse(result["ok"])
                self.assertEqual("SECRET_LEAK", result["error"])

    def test_object_keys_are_not_treated_as_persisted_string_values(self) -> None:
        payload = copy.deepcopy(self.clean)
        payload["additional_self_report"] = {"SENTINEL_LEAK": "clean value"}
        self.assertTrue(self.gate(payload)["ok"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
