#!/usr/bin/env python3
"""Fail-closed native cvec positional-scope gate for Trigger-1.

The legacy PyTorch witness changed only hidden[:, -1, :], while llama.cpp control
vectors are broadcast over the token dimension of the current decode graph. This gate
does not pretend the earlier multi-token-prefill native intervention was causally
identical. Instead it admits only native observations where the prompt is tokenized
once, every token except the original final token is decoded with cvec disabled, cvec
is enabled only after that prefill, and exactly that original final prompt token is
decoded in a one-token batch.

Cross-runtime numeric/mechanistic identity is intentionally not claimed. The native Q8
experiment must stand on its own causal evidence.
"""
from __future__ import annotations

from typing import Any

SCHEMA = "CLAY_TRIGGER1_NATIVE_SINGLE_TOKEN_SCOPE_GATE/v1"
EVIDENCE_SCHEMA = "CLAY_TRIGGER1_NATIVE_SINGLE_TOKEN_CVEC_SCOPE_EVIDENCE/v1"
OBS_SCHEMA = "CLAY_LLAMA_CPP_SINGLE_TOKEN_CVEC_OBSERVATION/v1"
CONTROLS = (
    "BASELINE", "+VECTOR", "SIGN_FLIP", "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM", "PERMUTED_SAME_NORM",
)
PINNED_LLAMA_CPP = "bb4caa7540188872173c44d161602d9271386413"
PINNED_GGUF_SHA256 = "9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031"
INJECTION_LAYER = 20
PRIMARY_LAYER = 21
DOWNSTREAM_LAYER = 24
SCOPE = "POST_UNSTEERED_PREFILL_ORIGINAL_LAST_PROMPT_TOKEN_ONLY"


def _sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
    except ValueError:
        return False
    return value == value.lower()


def validate(candidate: dict[str, Any]) -> dict[str, Any]:
    failures: list[str] = []
    evidence = candidate.get("native_single_token_scope_evidence")
    if not isinstance(evidence, dict) or evidence.get("schema") != EVIDENCE_SCHEMA:
        failures.append("NATIVE_SINGLE_TOKEN_SCOPE_EVIDENCE_REQUIRED")
        evidence = {}

    if evidence.get("llama_cpp_commit") != PINNED_LLAMA_CPP:
        failures.append("LLAMA_CPP_COMMIT_MISMATCH")
    if evidence.get("gguf_sha256") != PINNED_GGUF_SHA256:
        failures.append("GGUF_SHA256_MISMATCH")
    harness_sha = evidence.get("harness_source_sha256")
    if not _sha256(harness_sha):
        failures.append("HARNESS_SOURCE_SHA256_REQUIRED")

    rows = evidence.get("rows")
    if not isinstance(rows, list) or not rows:
        failures.append("NONEMPTY_NATIVE_SCOPE_ROWS_REQUIRED")
        rows = []

    by_case: dict[str, list[dict[str, Any]]] = {}
    for i, row in enumerate(rows):
        prefix = f"ROW_{i}"
        if not isinstance(row, dict):
            failures.append(f"{prefix}_OBJECT_REQUIRED")
            continue
        if row.get("schema") != OBS_SCHEMA:
            failures.append(f"{prefix}_OBSERVATION_SCHEMA_INVALID")
        case_id = row.get("case_id")
        if not isinstance(case_id, str) or not case_id:
            failures.append(f"{prefix}_CASE_ID_REQUIRED")
            continue
        control = row.get("control")
        if control not in CONTROLS:
            failures.append(f"{prefix}_CONTROL_INVALID")
        if row.get("prefill_cvec_applied") is not False:
            failures.append(f"{prefix}_PREFILL_MUST_BE_UNSTEERED")
        if row.get("cvec_active_decode_n_tokens") != 1:
            failures.append(f"{prefix}_CVEC_ACTIVE_DECODE_MUST_HAVE_ONE_TOKEN")
        if row.get("probe_is_original_last_prompt_token") is not True:
            failures.append(f"{prefix}_PROBE_MUST_BE_ORIGINAL_LAST_PROMPT_TOKEN")
        full = row.get("full_prompt_tokens")
        prefill = row.get("prefill_tokens")
        if not isinstance(full, int) or not isinstance(prefill, int) or full < 2 or prefill != full - 1:
            failures.append(f"{prefix}_PREFILL_TOKEN_COUNT_MISMATCH")
        if row.get("intervention_position_scope") != SCOPE:
            failures.append(f"{prefix}_INTERVENTION_SCOPE_INVALID")
        if row.get("il_start") != INJECTION_LAYER or row.get("il_end") != INJECTION_LAYER:
            failures.append(f"{prefix}_INJECTION_LAYER_MISMATCH")
        if row.get("primary_layer_inp") != PRIMARY_LAYER:
            failures.append(f"{prefix}_PRIMARY_LAYER_MISMATCH")
        if row.get("downstream_layer_inp") != DOWNSTREAM_LAYER:
            failures.append(f"{prefix}_DOWNSTREAM_LAYER_MISMATCH")
        if row.get("harness_source_sha256") != harness_sha:
            failures.append(f"{prefix}_HARNESS_SHA256_MISMATCH")
        if not _sha256(row.get("runtime_receipt_sha256")):
            failures.append(f"{prefix}_RUNTIME_RECEIPT_SHA256_REQUIRED")
        if control == "BASELINE":
            if row.get("cvec_applied") is not False:
                failures.append(f"{prefix}_BASELINE_MUST_NOT_APPLY_CVEC")
        elif control in CONTROLS:
            if row.get("cvec_applied") is not True or row.get("cvec_rc") != 0:
                failures.append(f"{prefix}_TREATMENT_CVEC_NOT_SUCCESSFULLY_APPLIED")
        by_case.setdefault(case_id, []).append(row)

    for case_id, case_rows in sorted(by_case.items()):
        if {row.get("control") for row in case_rows} != set(CONTROLS) or len(case_rows) != len(CONTROLS):
            failures.append(f"CASE_CONTROL_UNIVERSE_INVALID:{case_id}")
        prompt_hashes = {row.get("prompt_sha256") for row in case_rows}
        probe_ids = {row.get("probe_token_id") for row in case_rows}
        full_counts = {row.get("full_prompt_tokens") for row in case_rows}
        if len(prompt_hashes) != 1 or not all(_sha256(x) for x in prompt_hashes):
            failures.append(f"CASE_PROMPT_IDENTITY_NOT_MATCHED:{case_id}")
        if len(probe_ids) != 1 or None in probe_ids:
            failures.append(f"CASE_PROBE_TOKEN_NOT_MATCHED:{case_id}")
        if len(full_counts) != 1:
            failures.append(f"CASE_FULL_PROMPT_TOKEN_COUNT_NOT_MATCHED:{case_id}")

    return {
        "schema": SCHEMA,
        "pass": not failures,
        "failures": sorted(set(failures)),
        "native_single_token_position_scope_candidate": not failures,
        "legacy_multitoken_prefill_cvec_causally_identical_to_last_token_witness": False,
        "cross_runtime_numeric_identity_claimed": False,
        "cross_runtime_mechanistic_identity_claimed": False,
        "native_q8_must_stand_on_own_causal_evidence": True,
        "runtime_credit_minted": False,
        "jspace_model_credit_minted": False,
        "canonical_semantics_promotion": False,
        "evidence_boundary": (
            "PASS proves only that the admitted native cvec-active decode graph contained exactly the original "
            "last prompt token after an unsteered prefill, with exact runtime identity and six-control matching. "
            "It does not prove PyTorch/llama.cpp numerical identity or semantic J-Space success."
        ),
    }
