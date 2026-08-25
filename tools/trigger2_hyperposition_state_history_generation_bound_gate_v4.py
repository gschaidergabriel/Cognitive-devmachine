#!/usr/bin/env python3
"""Generation + epistemic + producer-authenticated state-history composition v4.

Bounded Trigger-2 positive-pilot path:

    generation provenance
      -> epistemic pre-update admission
      -> repository-bound discriminator producer
      -> retained replay/state-history/derivation proof

The composition deliberately remains nonpromoting.  It closes the row-carried discriminator
``admissible/executed/execution_receipt_id`` source-authenticity exploit for the already
source-pinned empty-history SYNTHETIC_PROOF pilot, but exact-current deterministic execution,
general history authority, OBSERVED producer authenticity and rendered leakage/split/tokenizer
gates remain required before positive training admission.
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
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v2.py",
    "trigger2_epistemic_preupdate_v2_for_hp_v4",
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
    epistemic_result = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or not generation_result.get("pass"):
            failures.extend(_failures_from("GENERATION:", generation_result))

    # Critical ordering: unbound generation never reaches epistemic/state mutation; unsafe
    # epistemic types never reach the producer-bound replay path.
    if not failures:
        try:
            epistemic_result = epistemic.adjudicate(row)
        except Exception as exc:
            failures.append("EPISTEMIC_PRODUCER_BOUND_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or not epistemic_result.get("pass"):
                failures.extend(_failures_from("EPISTEMIC_PRODUCER_BOUND_STATE_HISTORY:", epistemic_result))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "generation_provenance": generation_result,
        "epistemic_producer_bound_state_history_proof": epistemic_result,
        "required_order": [
            "GENERATION_PROVENANCE",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPOSITORY_BOUND_DISCRIMINATOR_PRODUCER",
            "REPLAY_STATE_HISTORY_DERIVATION_PROOF",
        ],
        "semantic_authority": "DELEGATED_TO_EXISTING_V3_REFERENCE_LABELER_VIA_RETAINED_STATE_HISTORY_GATE",
        "second_semantic_authority_created": False,
        "row_carried_discriminator_execution_assertions_authoritative": False,
        "bounded_empty_history_synthetic_pilot_source_closure": not failures,
        "positive_D_E_promotion_ready": False,
        "remaining_p0": [
            "exact-current repository-bound deterministic execution receipt for this v4 chain",
            "immutable ordered-history commitment before non-empty-history positive supervision",
            "producer-authenticated OBSERVED evidence before OBSERVED positive supervision",
            "rendered nuisance/family/provenance split + tokenizer/ABI leakage gates",
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
        "status": "SOURCE_ONLY_BOUNDED_PILOT_SUCCESSOR",
        "positive_D_E_promotion_ready": False,
    })
