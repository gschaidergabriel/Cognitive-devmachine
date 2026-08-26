#!/usr/bin/env python3
"""Generation + A02 producer-auth + epistemic + replay Hyperposition proof composition v4.

Single retained positive-candidate proof order:

    generation provenance
      -> authority-pinned A02 discriminator producer authentication
      -> epistemic pre-update admission
      -> replay-bound state-history / retained Hyperposition semantics

No second labeler or truth/effect authority is introduced. PASS remains source/component
candidate evidence only and mints zero dataset/training/runtime/J-Space/HCU/EntityOS credit.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_HYPERPOSITION_STATE_HISTORY_GENERATION_A02_EPISTEMIC_BOUND_GATE/v4"


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
a02 = _load_sibling(
    "trigger2_a02_discriminator_producer_auth_gate_v1.py",
    "trigger2_a02_producer_auth_for_hp_v4",
)
epistemic = _load_sibling(
    "trigger2_hyperposition_epistemic_preupdate_guard_v1.py",
    "trigger2_epistemic_preupdate_for_hp_v4",
)
tokenizer_abi = _load_sibling(
    "trigger2_tokenizer_abi_gate_v1.py",
    "trigger2_tokenizer_abi_for_hp_v4",
)
hyperposition_replay = _load_sibling(
    "trigger2_hyperposition_state_history_proof_gate_v1.py",
    "trigger2_hyperposition_replay_for_hp_v4",
)
# NOTE: trigger2_family_provenance_gate_v1 is a BATCH-level gate (adjudicate(bundle)
# with bundle["rows"] = [...]) that validates cross-split lineage/anti-echo across a
# whole admission microbatch, not a single row. It cannot be wired into this per-row
# adjudicate() the same way tokenizer_abi is -- same structural reason the rendered
# nuisance gate can't be. It must be run separately over the full candidate batch
# before/alongside per-row adjudication, not embedded here.


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
    a02_result = None
    epistemic_result = None

    try:
        generation_result = generation.adjudicate(row)
    except Exception as exc:
        failures.append("GENERATION_PROVENANCE_EXCEPTION:" + type(exc).__name__)
    else:
        if not isinstance(generation_result, dict) or not generation_result.get("pass"):
            failures.extend(_failures_from("GENERATION:", generation_result))

    if not failures:
        try:
            a02_result = a02.adjudicate(row)
        except Exception as exc:
            failures.append("A02_PRODUCER_AUTH_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(a02_result, dict) or not a02_result.get("pass"):
                failures.extend(_failures_from("A02:", a02_result))

    if not failures:
        try:
            epistemic_result = epistemic.adjudicate(row)
        except Exception as exc:
            failures.append("EPISTEMIC_STATE_HISTORY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(epistemic_result, dict) or not epistemic_result.get("pass"):
                failures.extend(_failures_from("EPISTEMIC_STATE_HISTORY:", epistemic_result))

    tokenizer_abi_result = None
    if not failures:
        try:
            tokenizer_abi_result = tokenizer_abi.adjudicate(row)
        except Exception as exc:
            failures.append("TOKENIZER_ABI_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(tokenizer_abi_result, dict) or not tokenizer_abi_result.get("pass"):
                failures.extend(_failures_from("TOKENIZER_ABI:", tokenizer_abi_result))

    hyperposition_replay_result = None
    if not failures:
        try:
            hyperposition_replay_result = hyperposition_replay.adjudicate(row)
        except Exception as exc:
            failures.append("HYPERPOSITION_REPLAY_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(hyperposition_replay_result, dict) or not hyperposition_replay_result.get("pass"):
                failures.extend(_failures_from("HYPERPOSITION_REPLAY:", hyperposition_replay_result))

    failures = sorted(set(failures))
    return {
        "schema": SCHEMA,
        "pass": not failures,
        "candidate_pre_admission_pass": not failures,
        "failures": failures,
        "generation_provenance": generation_result,
        "a02_discriminator_producer_auth": a02_result,
        "epistemic_state_history_proof": epistemic_result,
        "tokenizer_abi": tokenizer_abi_result,
        "hyperposition_replay_state_history": hyperposition_replay_result,
        "family_provenance_note": "trigger2_family_provenance_gate_v1 is batch-level (adjudicate(bundle) "
            "over a whole admission microbatch's rows, anti-echo lineage across the batch) and is NOT "
            "invoked by this per-row adjudicate() -- run it separately over the full candidate batch, "
            "same treatment as the rendered nuisance gate",
        "required_order": [
            "GENERATION_PROVENANCE",
            "A02_DISCRIMINATOR_PRODUCER_AUTH",
            "EPISTEMIC_PREUPDATE_ADMISSION",
            "TOKENIZER_ABI",
            "REPLAY_STATE_HISTORY_RETAINED_HYPERPOSITION_SEMANTICS",
        ],
        "semantic_authority": "DELEGATED_TO_EXISTING_V3_REFERENCE_LABELER",
        "second_semantic_authority_created": False,
        "positive_D_E_promotion_ready": False,
        "remaining_p0": [
            "exact-current deterministic execution of the A02 mutation suite is required",
            "native seed must be rebound to this one retained successor before any pilot regeneration",
            "STALE-NOTE FIX 2026-08-26: the previous entry here claiming "
            "REPLAY_STATE_HISTORY_RETAINED_HYPERPOSITION_SEMANTICS was 'still not actually invoked' was "
            "WRONG and contradicted both the code below and this array's own closed_p0 entry -- "
            "hyperposition_replay.adjudicate(row) IS invoked as the 5th/final per-row check (see code); "
            "corrected during production DB_MATCH row-assembler build, see "
            "tests/test_trigger2_db_match_row_assembler_v1.py",
            "NEW P0 (found 2026-08-26 building the production DB_MATCH assembler): none of the 5 wired "
            "per-row checks bind or verify model_visible content -- 'prompt' text can be swapped after "
            "row assembly with zero detection, candidate_pre_admission_pass says nothing about prompt "
            "integrity; see tests/test_trigger2_db_match_row_assembler_v1.py::"
            "test_tampered_prompt_after_generation_receipt_fails_closed (tracked xfail, must close before "
            "real admission)",
            "rendered nuisance / full-cross-or-conditional-MI leakage remains a BATCH-level statistical "
            "check (trigger2_binding_router_visible_nuisance_gate_v1, executed once against a full "
            "blueprint on 2026-08-26, PASS) rather than a per-row check -- it is not and structurally "
            "cannot be wired into this per-row adjudicate() the same way; batch-level PASS must be "
            "re-verified whenever the generator/blueprint changes, it does not certify any individual row",
            "family-provenance: trigger2_family_provenance_gate_v1 EXISTS (closed concurrently by a "
            "separate authority, commit 87ededd26) and is also BATCH-level (bundle of rows, anti-echo "
            "lineage across model/checkpoint/generator/episode ancestry) -- same structural note as "
            "nuisance above; not wired into this per-row adjudicate(), must be run separately over the "
            "full candidate batch before/alongside per-row admission",
        ],
        "closed_p0": [
            "immutable genesis/ordered-history producer authority: trigger2_generation_provenance_gate_v1 "
            "now binds genesis_state + the full ordered event_history to the same trusted-generator "
            "authority as the single current event (T2_GP_PILOT_HIST_CHAIN_V1 case); a nonempty history "
            "not produced by an authorized case fails GENERATION_CASE_NOT_AUTHORIZED / subject-digest "
            "mismatch closed, proven by tests/test_trigger2_genesis_history_producer_authority_v1.py",
            "OBSERVED evidence producer authentication: trigger2_hyperposition_state_history_proof_gate_v1's "
            "_validate_observation_receipt now recomputes the expected receipt via "
            "trigger2_observed_evidence_producer_auth_gate_v1 against one pinned producer/policy/admission "
            "authority instead of trusting caller-typed source/provenance/receipt_id strings; a fully forged "
            "receipt now fails OBSERVED_PRODUCER_AUTH:OBSERVED_RECEIPT_NOT_EXACTLY_RECOMPUTED, proven by "
            "tests/test_trigger2_hyperposition_state_history_proof_gate_v1.py",
            "tokenizer-ABI: trigger2_tokenizer_abi_gate_v1 now resolves every claimed symbol against a "
            "real, measured atoms_index.json (46-atom alphabet, target checkpoint "
            "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1 rev 591852bda6e1979f59e4b0f5ee2919697b12e936, "
            "'or' explicitly excluded) instead of trusting a caller-declared token mapping; wired into this "
            "composer's adjudicate().",
            "replay-bound state-history / retained Hyperposition semantics: trigger2_hyperposition_state_history_proof_gate_v1.adjudicate(row) "
            "is now invoked as the 5th and final per-row check in this composer's adjudicate(); a row is no longer certified without "
            "passing the base genesis/history replay proof (required_order step 5).",
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
        "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
        "positive_D_E_promotion_ready": False,
    })
