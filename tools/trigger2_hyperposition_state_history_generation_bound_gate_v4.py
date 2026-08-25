#!/usr/bin/env python3
"""A02 producer-authenticated Trigger-2 Hyperposition proof composition v4.

Exact order:
  trusted generation provenance
    -> repository-authorized discriminator producer/policy/ordering semantics
    -> exact trusted-producer receipt equality
    -> epistemic pre-update admission
    -> retained replay/state-history proof

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints zero canonical truth/effect/runtime/J-Space/
HCU/EntityOS/dataset-token/training credit.
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


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "row_carried_producer_identity_is_authority": False,
        "row_carried_policy_is_authority": False,
        "row_carried_admissible_boolean_is_authority": False,
        "row_carried_executed_boolean_is_authority": False,
        "row_carried_execution_receipt_id_is_authority": False,
        "positive_D_E_promotion_ready": False,
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
    out.update(extra)
    return out


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    failures: list[str] = []
    generation_result = None
    producer_auth_result = None
    epistemic_result = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or generation_result.get("pass") is not True:
            failures.extend(_failures_from("GENERATION:", generation_result))

    if not failures:
        try:
            producer_auth_result = producer_auth.adjudicate(
                row, generation_result=generation_result
            )
        except Exception as exc:
            failures.append("DISCRIMINATOR_PRODUCER_AUTH_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(producer_auth_result, dict) or producer_auth_result.get("pass") is not True:
                failures.extend(_failures_from("PRODUCER_AUTH:", producer_auth_result))

    if not failures:
        try:
            epistemic_result = epistemic.adjudicate(row)
        except Exception as exc:
            failures.append("EPISTEMIC_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or epistemic_result.get("pass") is not True:
                failures.extend(_failures_from("EPISTEMIC_STATE_HISTORY:", epistemic_result))

    return _result(
        failures,
        generation_provenance=generation_result,
        discriminator_producer_auth=producer_auth_result,
        epistemic_state_history_proof=epistemic_result,
        exact_order=[
            "GENERATION_PROVENANCE",
            "REPOSITORY_PRODUCER_POLICY_AND_ORDERING_AUTHORITY",
            "TRUSTED_PRODUCER_INVOCATION",
            "EXACT_DISCRIMINATOR_RECEIPT_MATCH",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "REPLAY_STATE_HISTORY_PROOF",
        ],
        a02_contract_status=(
            "SOURCE_IMPLEMENTED_DEPENDENCY_BOUND_EXECUTION_UNOBSERVED"
            if not failures
            else "SOURCE_CANDIDATE_REJECTED"
        ),
        remaining_p0=[
            "exact-current repository-bound deterministic execution of the A02 mutation suite",
            "immutable genesis/ordered-history authority before any nonempty-history positive case",
            "producer-authenticated OBSERVED evidence before OBSERVED positive supervision",
            "final rendered nuisance/full-cross-or-conditional-MI/family-provenance/tokenizer-ABI gates",
        ],
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_A02_DEPENDENCY_BOUND_IMPLEMENTATION_CANDIDATE",
        "positive_D_E_promotion_ready": False,
    })
