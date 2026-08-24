#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from trigger1_v4_postlease_pipeline import (
    EXPECTED_EXPERIMENT,
    PipelineBlocked,
    sanitized_environment,
    validate_postlease_environment,
)


def valid_env() -> dict[str, str]:
    return {
        "TRIGGER1_LEASE_ADMITTED": "true",
        "TRIGGER1_TRIGGER_KEY": "rid_" + "a" * 64,
        "TRIGGER1_EXPERIMENT_NAME": EXPECTED_EXPERIMENT,
        "TRIGGER1_CLAIM_SHA256": "b" * 64,
        "TRIGGER1_CLAIM_PATH": "research_entity/continuity/go_experiment_claims/rid_example.json",
        "TRIGGER1_CLAIMANT_ORGAN": "unit-test-organ",
        "TRIGGER1_SOURCE_HEAD": "c" * 40,
        "TRIGGER1_SOURCE_TREE": "d" * 40,
        "TRIGGER1_SOURCE_DIRTY": "false",
    }


class Trigger1V4PostleasePipelineTests(unittest.TestCase):
    def test_valid_canonical_postlease_identity_is_admitted(self):
        admitted = validate_postlease_environment(valid_env())
        self.assertEqual("rid_" + "a" * 64, admitted["trigger_key"])
        self.assertEqual(EXPECTED_EXPERIMENT, admitted["experiment_name"])
        self.assertEqual("c" * 40, admitted["source_head"])

    def test_missing_lease_fails_before_intervention(self):
        env = valid_env()
        env["TRIGGER1_LEASE_ADMITTED"] = "false"
        with self.assertRaisesRegex(PipelineBlocked, "CANONICAL_ATOMIC_LEASE_NOT_ADMITTED"):
            validate_postlease_environment(env)

    def test_old_experiment_alias_cannot_reuse_new_pipeline(self):
        env = valid_env()
        env["TRIGGER1_EXPERIMENT_NAME"] = "CLAY_TRIGGER1_LOCAL_QWEN06_MIDLAYER_CAUSAL_EXPERIMENT/v1"
        with self.assertRaisesRegex(PipelineBlocked, "LEASE_EXPERIMENT_IDENTITY_MISMATCH"):
            validate_postlease_environment(env)

    def test_noncanonical_trigger_key_fails_closed(self):
        env = valid_env()
        env["TRIGGER1_TRIGGER_KEY"] = "go-2026-08-24"
        with self.assertRaisesRegex(PipelineBlocked, "TRIGGER_KEY_NONCANONICAL"):
            validate_postlease_environment(env)

    def test_dirty_source_claim_fails_closed(self):
        env = valid_env()
        env["TRIGGER1_SOURCE_DIRTY"] = "true"
        with self.assertRaisesRegex(PipelineBlocked, "LEASE_SOURCE_NOT_CLEAN"):
            validate_postlease_environment(env)

    def test_provider_credentials_are_not_forwarded(self):
        env = valid_env() | {
            "OPENAI_API_KEY": "secret-a",
            "ANTHROPIC_API_KEY": "secret-b",
            "GROQ3_API_KEY": "secret-c",
            "NVIDIA_NIM_API_KEY": "secret-d",
            "OPENROUTER_API_KEY": "secret-e",
            "TOGETHER_API_KEY": "secret-f",
            "HF_TOKEN": "secret-g",
            "HUGGING_FACE_HUB_TOKEN": "secret-h",
            "ORDINARY_VALUE": "keep-me",
        }
        with tempfile.TemporaryDirectory() as td:
            clean = sanitized_environment(env, Path(td))
        for name in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "GROQ3_API_KEY",
            "NVIDIA_NIM_API_KEY",
            "OPENROUTER_API_KEY",
            "TOGETHER_API_KEY",
            "HF_TOKEN",
            "HUGGING_FACE_HUB_TOKEN",
        ):
            self.assertNotIn(name, clean)
        self.assertEqual("keep-me", clean["ORDINARY_VALUE"])
        self.assertEqual("1", clean["HF_HUB_DISABLE_IMPLICIT_TOKEN"])
        self.assertTrue(clean["HF_TOKEN_PATH"].endswith("no-hf-token"))


if __name__ == "__main__":
    unittest.main()
