#!/usr/bin/env python3
from __future__ import annotations

import re
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")

EXPECTED_SEQUENCE = [
    "pipeline_init",
    "pipeline_profile_read",
    "pipeline_state_read",
    "pipeline_collect",
    "pipeline_compile",
    "pipeline_build_prompt",
    "pipeline_cognitive_fabric_admit",
    "inference_generate",
    "pipeline_gate",
    "pipeline_commit",
    "pipeline_cognitive_fabric_finalize",
]


def literal_calls(source: str) -> list[str]:
    executable = re.sub(r"//[^\n]*", "", source)
    return [
        match.group(1)
        for match in re.finditer(r"\b(?:phase|effect)\(\s*\"([^\"]+)\"", executable)
    ]


def validate_path(source: str) -> list[str]:
    errors: list[str] = []
    calls = literal_calls(source)
    if calls != EXPECTED_SEQUENCE:
        errors.append("CANONICAL_PHASE_SEQUENCE_MISMATCH")
    if calls.count("pipeline_cognitive_fabric_admit") != 1:
        errors.append("COGNITIVE_FABRIC_ADMISSION_ARITY")
    if calls.count("pipeline_cognitive_fabric_finalize") != 1:
        errors.append("COGNITIVE_FABRIC_FINALIZATION_ARITY")

    required = {
        'map_set(infer,"inference",admitted.inference)': "ADMITTED_INFERENCE_ENGINE_MISSING",
        'map_set(infer,"system",admitted.system)': "ADMITTED_SYSTEM_CONTEXT_MISSING",
        'map_set(infer,"user",admitted.user)': "ADMITTED_USER_CONTEXT_MISSING",
        'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)': "INFERENCE_PACKET_BINDING_MISSING",
        'map_set(infer,"cognitive_fabric_admission_receipt_digest",admitted.cognitive_fabric_receipt_digest)': "COGNITIVE_FABRIC_ADMISSION_BINDING_MISSING",
        'map_set(gate_data,"cognitive_fabric_admission",admitted)': "GATE_FABRIC_REENTRY_MISSING",
        'map_set(commit_data,"cognitive_fabric_admission",admitted)': "COMMIT_FABRIC_REENTRY_MISSING",
        'map_set(finalize_data,"admitted",admitted)': "FINALIZE_ADMISSION_BINDING_MISSING",
        'map_set(finalize_data,"generated",generated)': "FINALIZE_CANDIDATE_BINDING_MISSING",
        'map_set(finalize_data,"gated",gated)': "FINALIZE_GATE_BINDING_MISSING",
        'map_set(finalize_data,"committed",committed)': "FINALIZE_COMMIT_BINDING_MISSING",
        'map_set(result,"ucf_runtime_receipt_digest",finalized.ucf_runtime_receipt_digest)': "FINAL_RUNTIME_RECEIPT_RESULT_MISSING",
    }
    for token, error in required.items():
        if token not in source:
            errors.append(error)

    forbidden = {
        'map_set(infer,"inference",profile.inference)': "RAW_PROFILE_INFERENCE_BYPASS",
        'map_set(infer,"system",prompt.system)': "RAW_SYSTEM_PROMPT_BYPASS",
        'map_set(infer,"user",prompt.user)': "RAW_USER_PROMPT_BYPASS",
        'map_set(infer,"ucf_runtime_receipt_digest"': "PREINFERENCE_FINAL_RUNTIME_RECEIPT",
        'map_set(infer,"cognitive_fabric_receipt_digest"': "AMBIGUOUS_PREINFERENCE_RUNTIME_RECEIPT_BINDING",
    }
    for token, error in forbidden.items():
        if token in source:
            errors.append(error)
    return errors


class CanonicalCognitiveFabricPathTests(unittest.TestCase):
    def test_canonical_pipeline_has_pre_admission_and_post_commit_finalization(self):
        self.assertEqual(validate_path(SRC), [])

    def test_direct_prompt_to_inference_lesion_fails_closed(self):
        start = SRC.index("  // PRE-INFERENCE ADMISSION")
        end = SRC.index("  // Inference is replaceable candidate cognition", start)
        lesioned = SRC[:start] + SRC[end:]
        lesioned = lesioned.replace("admitted.inference", "profile.inference")
        lesioned = lesioned.replace("admitted.system", "prompt.system")
        lesioned = lesioned.replace("admitted.user", "prompt.user")
        errors = validate_path(lesioned)
        self.assertIn("CANONICAL_PHASE_SEQUENCE_MISMATCH", errors)
        self.assertIn("COGNITIVE_FABRIC_ADMISSION_ARITY", errors)

    def test_digest_decorated_raw_inference_bypass_is_rejected(self):
        # Regression-only source poison: leave admission/packet digests present so the path
        # looks provenance-aware, but secretly restore raw profile/prompt inference inputs.
        poisoned = SRC.replace(
            'map_set(infer,"inference",admitted.inference)',
            'map_set(infer,"inference",profile.inference)',
        ).replace(
            'map_set(infer,"system",admitted.system)',
            'map_set(infer,"system",prompt.system)',
        ).replace(
            'map_set(infer,"user",admitted.user)',
            'map_set(infer,"user",prompt.user)',
        )
        errors = validate_path(poisoned)
        self.assertIn("RAW_PROFILE_INFERENCE_BYPASS", errors)
        self.assertIn("RAW_SYSTEM_PROMPT_BYPASS", errors)
        self.assertIn("RAW_USER_PROMPT_BYPASS", errors)
        self.assertNotIn("INFERENCE_PACKET_BINDING_MISSING", errors)
        self.assertNotIn("COGNITIVE_FABRIC_ADMISSION_BINDING_MISSING", errors)

    def test_precommit_final_runtime_receipt_poison_is_rejected(self):
        # Regression-only temporal poison. The user-triggered GO's unusual experiment was
        # already consumed by the authority-routing poison recorded on current main.
        poisoned = SRC.replace(
            'let committed = phase("pipeline_commit"',
            'let committed = phase("__TEMP_FINALIZE__"',
            1,
        ).replace(
            'let finalized = phase("pipeline_cognitive_fabric_finalize"',
            'let finalized = phase("pipeline_commit"',
            1,
        ).replace(
            'let committed = phase("__TEMP_FINALIZE__"',
            'let committed = phase("pipeline_cognitive_fabric_finalize"',
            1,
        )
        errors = validate_path(poisoned)
        self.assertIn("CANONICAL_PHASE_SEQUENCE_MISMATCH", errors)

    def test_final_runtime_receipt_is_not_passed_into_inference(self):
        start = SRC.index("  let infer = map_new()")
        end = SRC.index('  let generated = effect("inference_generate"', start)
        infer_block = SRC[start:end]
        self.assertNotIn("ucf_runtime_receipt_digest", infer_block)
        self.assertNotIn('map_set(infer,"cognitive_fabric_receipt_digest"', infer_block)
        self.assertIn("cognitive_fabric_admission_receipt_digest", infer_block)


if __name__ == "__main__":
    unittest.main()
