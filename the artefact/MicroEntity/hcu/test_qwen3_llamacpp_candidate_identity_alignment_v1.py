#!/usr/bin/env python3
"""Source regression for Qwen3 / llama.cpp / J-Space bridge identity alignment.

This test is deterministic source plumbing only. It does not download a model, execute
llama.cpp, establish loader consumption, inference, hidden-state causality, or runtime credit.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

from jspace_llamacpp_cvec_bridge_v1 import (
    QWEN3_06B_CHECKPOINT_SHA256,
    QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT,
)


HERE = Path(__file__).resolve().parent
MODEL_CANDIDATE = HERE / "LOCAL_08B_QWEN3_06B_Q8_GGUF_CANDIDATE.json"
RUNTIME_CANDIDATE = HERE / "LOCAL_RUNTIME_LLAMA_CPP_B10566_UBUNTU_X64_CANDIDATE.json"


class QwenLlamaCppCandidateIdentityAlignmentTests(unittest.TestCase):
    def load_json(self, path: Path) -> dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def test_checkpoint_identity_matches_bridge(self):
        model = self.load_json(MODEL_CANDIDATE)
        self.assertEqual(
            model["upstream_model_artifact"]["sha256"],
            QWEN3_06B_CHECKPOINT_SHA256,
        )
        self.assertEqual(
            model["single_file_role_mapping"]["checkpoint_expected_sha256"],
            QWEN3_06B_CHECKPOINT_SHA256,
        )

    def test_runtime_source_identity_matches_model_candidate_and_bridge(self):
        model = self.load_json(MODEL_CANDIDATE)
        runtime = self.load_json(RUNTIME_CANDIDATE)
        runtime_source = runtime["upstream"]["source_repository_digest"]
        self.assertEqual(
            model["documented_local_runtime_family"]["exact_runtime_source_commit"],
            runtime_source,
        )
        self.assertEqual(QWEN3_06B_LLAMA_CPP_SOURCE_COMMIT, runtime_source)

    def test_runtime_candidate_remains_non_promoted(self):
        model = self.load_json(MODEL_CANDIDATE)
        runtime = self.load_json(RUNTIME_CANDIDATE)
        self.assertEqual(model["status"], "CANDIDATE_ONLY_NO_RUNTIME_CREDIT")
        self.assertEqual(
            runtime["status"],
            "ATTESTED_DISTRIBUTION_CANDIDATE_ONLY_NO_RUNTIME_CREDIT",
        )
        self.assertEqual(runtime["credit_boundary"]["local_runtime_credit"], 0)
        self.assertEqual(runtime["credit_boundary"]["model_runtime_credit"], 0)
        self.assertEqual(runtime["credit_boundary"]["jspace_model_runtime_credit"], 0)
        self.assertEqual(runtime["credit_boundary"]["training_credit"], 0)


if __name__ == "__main__":
    unittest.main()
