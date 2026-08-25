#!/usr/bin/env python3
"""Generation + producer-auth + epistemic + replay-bound Trigger-2 proof composition v4.

Successor to v3 for the bounded SYNTHETIC_PROOF pilot. The single retained positive-candidate
order is now:

    generation provenance
      -> repository-authority discriminator producer authentication
      -> typed epistemic pre-update admission
      -> replay-bound state-history proof

The producer-auth layer does not create a second Hyperposition semantic oracle: discriminator
coverage is recomputed through the retained v3 reference semantics used by the state-history
gate. PASS remains candidate pre-admission source evidence only and mints zero dataset,
training, runtime, J-Space, HCU, EntityOS, truth, or effect credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_EPISTEMIC_PRODUCER_BOUND_GATE/v4"


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
    "trigger2_generation_provenance_for_hp_v4",
)
producer_auth = _load_sibling(
    "trigger2_discriminator_producer_auth_gate_v1.py",
    "trigger2_discriminator_producer_auth_for_hp_v4",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_hp_v4",
)


def _failures_from(prefix: str, result: Any) -> list[str]:
    if not isinstance(result, dict):
        return [prefix + "RESULT_INVALID"]
    failures = result.get("failures")
    if isinstance(failures, list) and failures:
        return [prefix + str(x) for x in failures]
    return [prefix + "REJECTED"]


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    generation_result = None
    producer_auth_result = None
    epistemic_result = None
    sanitized_row = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or not generation_result.get("pass"):
            failures.extend(_failures_from("GENERATION:", generation_result))

    # No producer policy/execution is considered until generation provenance is green.
    if not failures:
        try:
            producer_auth_result = producer_auth.authenticate_after_generation(row)
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_AUTH_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(producer_auth_result, dict) or not producer_auth_result.get("pass"):
                failures.extend(_failures_from("DISCRIMINATOR_PRODUCER_AUTH:", producer_auth_result))
            else:
                sanitized_row = producer_auth_result.get("sanitized_row_evaluator_only")
                if not isinstance(sanitized_row, dict):
                    failures.append("DISCRIMINATOR_PRODUCER_AUTH:SANITIZED_ROW_REQUIRED")

    # No epistemic/state transition may occur until producer-authenticated execution proof passes.
    if not failures:
        try:
            epistemic_result = epistemic.adjudicate(sanitized_row)
        except Exception as exc:
            failures.append("EPISTEMIC_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or not epistemic_result.get("pass"):
                failures.extend(_failures_from("EPISTEMIC_STATE_HISTORY:", epistemic_result))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "generation_provenance": generation_result,
        "discriminator_producer_auth": producer_auth_result,
        "epistemic_state_history_proof": epistemic_result,
        "required_order": [
            "GENERATION_PROVENANCE",
            "REPOSITORY_AUTHORITY_DISCRIMINATOR_PRODUCER_AUTH",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPLAY_STATE_HISTORY_DISCRIMINATOR_OBSERVATION_PROOF",
        ],
        "semantic_authority": "DELEGATED_TO_EXISTING_V3_REFERENCE_LABELER_VIA_RETAINED_STATE_HISTORY_GATE",
        "second_semantic_authority_created": False,
        "positive_D_E_promotion_ready": False,
        "remaining_p0": [
            "exact-current deterministic execution receipt for this v4 chain remains required",
            "nonempty histories still require independently authority-bound genesis/ordered-history production",
            "OBSERVED events still require producer-authenticated observation evidence",
            "rendered model-visible nuisance/family/provenance split and tokenizer/ABI gates remain required",
            "abliterated approximately-0.8B target winner selection remains orthogonal and unresolved",
        ],
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


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION_A02_SUCCESSOR",
        "positive_D_E_promotion_ready": False,
    })
