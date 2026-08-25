#!/usr/bin/env python3
"""Trigger-2 generation-bound + epistemic-preupdate + state-history proof composition v3.

This successor fixes the composition omission in v2: generation provenance alone must not
route a non-evidentiary HYPOTHESIS/PREDICTION/UNKNOWN/etc. directly into the retained
state-history gate and its ``u_state`` path.

Exact order:
    deterministic generation provenance
      -> epistemic pre-update guard
      -> retained state-history/discriminator proof (delegated by the guard)

No second semantic authority is created. PASS is candidate pre-admission component evidence
only and mints zero dataset/training/runtime/J-Space/HCU/EntityOS/truth/effect credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_BOUND_GATE/v3"


def _load_sibling(filename: str, module_name: str):
    path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {filename}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


generation = _load_sibling(
    "trigger2_generation_provenance_gate_v1.py",
    "trigger2_generation_provenance_for_hp_v3",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_hp_v3",
)


def _result(failures: list[str], *, generation_result: Any = None, epistemic_result: Any = None) -> dict[str, Any]:
    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "generation_provenance": generation_result,
        "epistemic_preupdate_state_history_proof": epistemic_result,
        "proof_order": [
            "GENERATION_PROVENANCE",
            "EPISTEMIC_PREUPDATE_GUARD",
            "STATE_HISTORY_PROOF_VIA_GUARD",
        ],
        "direct_state_history_bypass_allowed": False,
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


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        generation_result = None
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict):
            failures.append("GENERATION_PROVENANCE_RESULT_INVALID")
        elif not generation_result.get("pass"):
            failures.extend("GENERATION:" + str(x) for x in generation_result.get("failures", []))

    epistemic_result = None
    if not failures:
        try:
            epistemic_result = epistemic.adjudicate(row)
        except Exception as exc:
            failures.append("EPISTEMIC_PREUPDATE_GUARD_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict):
                failures.append("EPISTEMIC_PREUPDATE_GUARD_RESULT_INVALID")
            elif not epistemic_result.get("pass"):
                failures.extend("EPISTEMIC:" + str(x) for x in epistemic_result.get("failures", []))

    return _result(
        failures,
        generation_result=generation_result,
        epistemic_result=epistemic_result,
    )
