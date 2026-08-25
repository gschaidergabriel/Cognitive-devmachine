#!/usr/bin/env python3
"""Generation + producer-auth + epistemic + replay-bound Trigger-2 proof composition v3.

This retained successor composition enforces the current positive-candidate proof order:

    generation provenance
      -> repository-authorized deterministic discriminator production
      -> epistemic pre-update admission
      -> replay-bound state-history / discriminator / typed-observation proof

The producer-auth step resolves producer identity and policy from repository authority,
executes the retained u_test_order path, derives admissibility/execution from that invocation,
and replaces row-carried discriminator assertions with authenticated deterministic output.
The epistemic guard then delegates to the retained state-history gate and existing v3
reference labeler. No second semantic authority, truth store, effect path, or model authority
is created.

PASS is candidate pre-admission component evidence only. It mints zero dataset, training,
runtime, J-Space, HCU, EntityOS, BASE, canonical-truth, or direct-effect credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_EPISTEMIC_BOUND_GATE/v3"


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
producer_auth = _load_sibling(
    "trigger2_discriminator_producer_auth_v1.py",
    "trigger2_discriminator_producer_auth_for_hp_v3",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_hp_v3",
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

    # Ordering invariant 1: producer execution cannot run until exact generation
    # provenance has passed. This prevents row-supplied world/event/state substitution
    # from reaching the deterministic discriminator producer.
    if not failures:
        try:
            producer_auth_result, sanitized_row = producer_auth.authenticate_and_sanitize(
                row, generation_result
            )
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_AUTH_EXCEPTION:" + type(exc).__name__)
        else:
            if (
                not isinstance(producer_auth_result, dict)
                or not producer_auth_result.get("pass")
                or not isinstance(sanitized_row, dict)
            ):
                failures.extend(
                    _failures_from("DISCRIMINATOR_PRODUCER_AUTH:", producer_auth_result)
                )

    # Ordering invariant 2: no epistemic/state update path is called until both
    # generation provenance and producer-authenticated discriminator production pass.
    # The epistemic guard rejects non-evidence-bearing types before delegating to
    # replay/u_state.
    if not failures and isinstance(sanitized_row, dict):
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
            "REPOSITORY_AUTHORIZED_DETERMINISTIC_DISCRIMINATOR_PRODUCTION",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPLAY_STATE_HISTORY_DISCRIMINATOR_OBSERVATION_PROOF",
        ],
        "semantic_authority": "DELEGATED_TO_EXISTING_V3_REFERENCE_LABELER_VIA_RETAINED_STATE_HISTORY_GATE",
        "discriminator_execution_authority": "REPOSITORY_AUTHORITY_PLUS_DETERMINISTIC_PRODUCER_OUTPUT",
        "row_carried_admissible_or_executed_is_authority": False,
        "second_semantic_authority_created": False,
        "positive_D_E_promotion_ready": False,
        "remaining_p0": [
            "nonempty history requires authority-bound ordered-history generation/commitment",
            "OBSERVED events require producer-authenticated observation evidence authority",
            "exact-current admitted execution plus rendered nuisance/family/tokenizer/checkpoint gates remain required before positive dataset admission",
        ],
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "base_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
    }


if __name__ == "__main__":
    print(
        {
            "schema": SCHEMA,
            "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
            "positive_D_E_promotion_ready": False,
        }
    )
