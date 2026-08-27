#!/usr/bin/env python3
"""Trigger-2 model-visible prompt content-binding gate v1.

Closes a gap found 2026-08-26 while building the production DB_MATCH row
assembler: none of the previously wired v4 per-row checks (generation
provenance, A02 discriminator-producer auth, epistemic pre-update,
tokenizer-ABI, hyperposition replay/state-history proof) bind or verify
row['prompt'] -- the literal text listed in model_visible_fields, i.e. what a
model trained on this row would actually see. A row could pass full
candidate_pre_admission_pass with row['prompt'] swapped to arbitrary
unauthorized text after assembly.

Same recompute-don't-trust pattern as A02's producer.produce(): this gate
does NOT trust a caller-declared prompt or a caller-declared hash of it. It
independently re-renders the expected prompt from the pinned generator
authority (trigger2_trusted_hyperposition_pilot_generator_v1.render_prompt)
using only generation_case_id_evaluator_only + generation_parameters_evaluator_only,
and fails closed on any mismatch.

Source/content-binding validation only. PASS does not mint canonical
truth/effect/runtime/J-Space/HCU/EntityOS/training credit and does not admit
dataset tokens.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_PROMPT_CONTENT_BINDING_GATE/v1"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generator = _load_sibling(
    "trigger2_trusted_hyperposition_pilot_generator_v1.py",
    "trigger2_trusted_hyperposition_pilot_generator_for_prompt_binding_v1",
)


def _sha256_text(text: str) -> str:
    return sha256(text.encode("utf-8")).hexdigest()


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {"schema": SCHEMA, "pass": False, "failures": ["ROW_NOT_DICT"]}

    failures: list[str] = []

    prompt = row.get("prompt")
    if not isinstance(prompt, str) or not prompt:
        failures.append("PROMPT_MISSING_OR_NOT_STRING")

    case_id = row.get("generation_case_id_evaluator_only")
    parameters = row.get("generation_parameters_evaluator_only")
    if not isinstance(case_id, str) or not case_id:
        failures.append("GENERATION_CASE_ID_EVALUATOR_ONLY_MISSING")
    if not isinstance(parameters, dict):
        failures.append("GENERATION_PARAMETERS_EVALUATOR_ONLY_MISSING")

    if failures:
        return {"schema": SCHEMA, "pass": False, "failures": sorted(set(failures))}

    try:
        expected_prompt = generator.render_prompt(case_id, parameters)
    except Exception as exc:
        return {
            "schema": SCHEMA,
            "pass": False,
            "failures": ["RENDER_PROMPT_EXCEPTION:" + type(exc).__name__ + ":" + str(exc)],
        }

    expected_sha256 = _sha256_text(expected_prompt)
    actual_sha256 = _sha256_text(prompt)

    if prompt != expected_prompt:
        failures.append("PROMPT_DOES_NOT_MATCH_RENDERED_AUTHORITY")
    if actual_sha256 != expected_sha256:
        failures.append("PROMPT_SHA256_MISMATCH")

    binding = row.get("prompt_binding_evaluator_only")
    if not isinstance(binding, dict):
        failures.append("PROMPT_BINDING_EVALUATOR_ONLY_MISSING")
    else:
        claimed_sha256 = binding.get("prompt_sha256")
        if claimed_sha256 != expected_sha256:
            failures.append("PROMPT_BINDING_SHA256_NOT_EXACTLY_RECOMPUTED")
        if binding.get("render_source") != (
            "trigger2_trusted_hyperposition_pilot_generator_v1.render_prompt"
        ):
            failures.append("PROMPT_BINDING_RENDER_SOURCE_MISMATCH")

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": failures,
        "expected_prompt_sha256": expected_sha256,
        "actual_prompt_sha256": actual_sha256,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
