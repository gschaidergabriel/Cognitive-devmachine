#!/usr/bin/env python3
"""Fail-closed source guard for the canonical Mini Entity cognitive causal path."""
from __future__ import annotations

import pathlib
import re
import unittest

CLAY_PATH = pathlib.Path(__file__).resolve().with_name("BLOGPOST_ENTITY.clay")


def executable_source(text: str) -> str:
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


def cognitive_path_errors(text: str) -> list[str]:
    src = executable_source(text)
    prompt = src.find('phase("pipeline_build_prompt"')
    fabric = src.find('phase("pipeline_cognitive_fabric_admit"')
    inference = src.find('effect("inference_generate"')
    errors: list[str] = []

    if not (0 <= prompt < fabric < inference):
        errors.append("COGNITIVE_FABRIC_NOT_ON_PROMPT_TO_INFERENCE_PATH")

    required = (
        'map_set(infer,"inference",admitted.inference)',
        'map_set(infer,"system",admitted.system)',
        'map_set(infer,"user",admitted.user)',
        'map_set(infer,"inference_packet_digest",admitted.inference_packet_digest)',
        'map_set(infer,"cognitive_fabric_receipt_digest",admitted.cognitive_fabric_receipt_digest)',
        'map_set(gate_data,"cognitive_fabric",admitted)',
        'map_set(commit_data,"cognitive_fabric",admitted)',
    )
    for marker in required:
        if marker not in src:
            errors.append("MISSING_ADMITTED_BINDING:" + marker)

    bypasses = (
        'map_set(infer,"inference",profile.inference)',
        'map_set(infer,"system",prompt.system)',
        'map_set(infer,"user",prompt.user)',
    )
    for marker in bypasses:
        if marker in src:
            errors.append("RAW_PROMPT_OR_PROFILE_BYPASS:" + marker)

    return errors


class CanonicalCognitiveFabricPathTests(unittest.TestCase):
    def test_canonical_path_routes_inference_through_admitted_fabric(self):
        clay = CLAY_PATH.read_text(encoding="utf-8")
        self.assertEqual(cognitive_path_errors(clay), [])

    def test_raw_profile_inference_poison_fails_closed(self):
        """Regression for the GO source-level bypass poison discriminator."""
        clay = CLAY_PATH.read_text(encoding="utf-8")
        poisoned = clay.replace(
            'map_set(infer,"inference",admitted.inference)',
            'map_set(infer,"inference",profile.inference)',
            1,
        )
        errors = cognitive_path_errors(poisoned)
        self.assertTrue(any(item.startswith("RAW_PROMPT_OR_PROFILE_BYPASS:") for item in errors))
        self.assertTrue(any(item.startswith("MISSING_ADMITTED_BINDING:") for item in errors))


if __name__ == "__main__":
    unittest.main()
