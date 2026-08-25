#!/usr/bin/env python3
"""Generation-bound successor wrapper for Trigger-2 Hyperposition state-history proof v2.

This is the single retained positive-candidate proof composition:
generation provenance -> replay-bound state history/discriminator proof.
It delegates semantic transition authority to the existing v3 reference labeler through
state-history proof v1 and adds no competing labeler/truth/effect authority.

PASS is candidate pre-admission component evidence only and mints zero dataset/training/
runtime/J-Space/HCU/EntityOS credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_BOUND_GATE/v2"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generation = _load_sibling("trigger2_generation_provenance_gate_v1.py", "trigger2_generation_provenance_for_hp_v2")
history = _load_sibling("trigger2_hyperposition_state_history_proof_gate_v1.py", "trigger2_state_history_for_hp_v2")


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        generation_result = None
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not generation_result.get("pass"):
            failures.extend("GENERATION:" + str(x) for x in generation_result.get("failures", []))

    history_result = None
    if not failures:
        try:
            history_result = history.adjudicate(row)
        except Exception as exc:
            failures.append("STATE_HISTORY_PROOF_EXCEPTION:" + type(exc).__name__)
        else:
            if not history_result.get("pass"):
                failures.extend("STATE_HISTORY:" + str(x) for x in history_result.get("failures", []))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "generation_provenance": generation_result,
        "state_history_proof": history_result,
        "semantic_authority": "DELEGATED_TO_EXISTING_V3_REFERENCE_LABELER_VIA_RETAINED_GATES",
        "second_semantic_authority_created": False,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }
