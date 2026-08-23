#!/usr/bin/env python3
from __future__ import annotations

import re
import unittest
from pathlib import Path

SRC_PATH = Path(__file__).with_name("BLOGPOST_ENTITY.clay")
SRC = SRC_PATH.read_text(encoding="utf-8")

EXPECTED_RUN_ARGS = ["entity_db", "source_db", "secret_file", "invocation"]


def run_args(source: str) -> list[str]:
    match = re.search(r"fn\s+run\((.*?)\)\s*->\s*Map", source, re.S)
    if not match:
        return []
    return [
        item.strip().split(":", 1)[0].strip()
        for item in match.group(1).split(",")
        if item.strip()
    ]


def validate_selector_path(source: str) -> list[str]:
    errors: list[str] = []
    if run_args(source) != EXPECTED_RUN_ARGS:
        errors.append("INVOCATION_SELECTOR_BOUNDARY_MISSING")
    if 'map_set(cognition_data,"invocation",invocation)' not in source:
        errors.append("INVOCATION_SELECTOR_ADMISSION_BINDING_MISSING")
    if 'map_set(infer,"invocation"' in source:
        errors.append("INVOCATION_SELECTOR_DIRECT_INFERENCE_BYPASS")
    forbidden_authority = (
        "invocation.zero_identity",
        "invocation.grf",
        "invocation.hyperposition",
        "invocation.model",
        "invocation.tokenizer",
        "invocation.jspace",
        "invocation.workspace",
        "invocation.policy",
    )
    if any(token in source for token in forbidden_authority):
        errors.append("INVOCATION_SELECTOR_AUTHORITY_EXPANSION")
    return errors


class CognitiveInvocationSelectorPathTests(unittest.TestCase):
    def test_canonical_path_threads_only_bounded_selector_into_admission(self):
        self.assertEqual(validate_selector_path(SRC), [])

    def test_legacy_three_argument_path_fails_selector_contract(self):
        # The macrocycle discriminator: the old shape could look canonically ordered while
        # starving admission of the exact already-bound turn selector required by MiniUnifiedDB.
        legacy = SRC.replace(
            "fn run(entity_db:String, source_db:String, secret_file:String, invocation:Map)->Map",
            "fn run(entity_db:String, source_db:String, secret_file:String)->Map",
            1,
        ).replace('  map_set(cognition_data,"invocation",invocation)\n', "", 1)
        errors = validate_selector_path(legacy)
        self.assertIn("INVOCATION_SELECTOR_BOUNDARY_MISSING", errors)
        self.assertIn("INVOCATION_SELECTOR_ADMISSION_BINDING_MISSING", errors)

    def test_selector_cannot_be_forwarded_as_raw_inference_input(self):
        poisoned = SRC.replace(
            "  let generated = effect(\"inference_generate\",infer)",
            '  map_set(infer,"invocation",invocation)\n  let generated = effect("inference_generate",infer)',
            1,
        )
        self.assertIn("INVOCATION_SELECTOR_DIRECT_INFERENCE_BYPASS", validate_selector_path(poisoned))

    def test_selector_cannot_expand_into_cognition_authority_fields(self):
        poisoned = SRC.replace(
            '  map_set(cognition_data,"invocation",invocation)',
            '  map_set(cognition_data,"invocation",invocation)\n  map_set(cognition_data,"jspace",invocation.jspace)',
            1,
        )
        self.assertIn("INVOCATION_SELECTOR_AUTHORITY_EXPANSION", validate_selector_path(poisoned))


if __name__ == "__main__":
    unittest.main()
