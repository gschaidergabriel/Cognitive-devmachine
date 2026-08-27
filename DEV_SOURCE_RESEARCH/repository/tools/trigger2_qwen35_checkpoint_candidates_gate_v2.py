#!/usr/bin/env python3
from __future__ import annotations

import re
from typing import Any

SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_CANDIDATES/v2"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

CONTROL_EXPECTED = {
    "QWEN35_08B_BASE": {
        "repo": "Qwen/Qwen3.5-0.8B-Base",
        "revision": "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68",
        "weights_sha256": "c2b1e5a17d9c1e27685d92ed9b382911ebb99955ecd89052d1721241adfbab6c",
        "tokenizer_sha256": "fe000e3ed39ed12b8d2481d527d44f93c65d37e87645d2dcc80d1bf9d50d2927",
    },
    "QWEN35_08B_POSTTRAINED": {
        "repo": "Qwen/Qwen3.5-0.8B",
        "revision": "2fc06364715b967f1860aea9cf38778875588b17",
        "weights_sha256": "04b1c301231dd422b8860db31311ab2721511346a32cb1e079c4c4e5f1fe4696",
        "tokenizer_sha256": "5f9e4d4901a92b997e463c1f46055088b6cca5ca61a6522d1b9f64c4bb81cb42",
    },
}
MEASURED_TARGET = {
    "candidate_id": "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED",
    "repo": "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1",
    "revision": "591852bda6e1979f59e4b0f5ee2919697b12e936",
}
ROLES = {"CONTROL", "TARGET_MEASURED", "TARGET_EXTERNAL_UNMEASURED"}
IDENTITY_DIGEST_FIELDS = (
    "weights_sha256",
    "tokenizer_sha256",
    "chat_template_sha256",
    "config_sha256",
    "file_manifest_sha256",
)


def _has_complete_identity(candidate: dict[str, Any]) -> bool:
    revision = candidate.get("immutable_revision")
    if not isinstance(revision, str) or not SHA40.fullmatch(revision):
        return False
    return all(
        isinstance(candidate.get(field), str)
        and bool(SHA256.fullmatch(candidate[field]))
        for field in IDENTITY_DIGEST_FIELDS
    )


def adjudicate(x: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(x, dict):
        x = {}
        failures.append("OBJECT_REQUIRED")

    if x.get("schema") != SCHEMA:
        failures.append("SCHEMA_MISMATCH")
    if x.get("selection_status") != "UNRESOLVED_TARGET_IDENTITY_AND_MATCHED_PILOT_REQUIRED":
        failures.append("SELECTION_STATUS_MUST_REMAIN_UNRESOLVED")
    if x.get("selected_candidate") is not None:
        failures.append("SOURCE_REGISTRY_CANNOT_SELECT_WINNER")

    candidates = x.get("candidates")
    seen: dict[str, dict[str, Any]] = {}
    measured_seen = False
    if not isinstance(candidates, list):
        failures.append("CANDIDATES_REQUIRED")
    else:
        for candidate in candidates:
            if not isinstance(candidate, dict):
                failures.append("CANDIDATE_OBJECT_REQUIRED")
                continue
            cid = candidate.get("candidate_id")
            if not isinstance(cid, str):
                failures.append("CANDIDATE_ID_REQUIRED")
                continue
            if cid in seen:
                failures.append("DUPLICATE_CANDIDATE:" + cid)
                continue
            seen[cid] = candidate

            role = candidate.get("candidate_role")
            if role not in ROLES:
                failures.append("ROLE_INVALID:" + cid)
                continue

            if role == "CONTROL":
                expected = CONTROL_EXPECTED.get(cid)
                if expected is None:
                    failures.append("UNKNOWN_CONTROL:" + cid)
                    continue
                if candidate.get("repo") != expected["repo"]:
                    failures.append("CONTROL_REPO_MISMATCH:" + cid)
                if candidate.get("immutable_revision") != expected["revision"]:
                    failures.append("CONTROL_REVISION_MISMATCH:" + cid)
                if candidate.get("weights_sha256") != expected["weights_sha256"]:
                    failures.append("CONTROL_WEIGHTS_SHA_MISMATCH:" + cid)
                if candidate.get("tokenizer_sha256") != expected["tokenizer_sha256"]:
                    failures.append("CONTROL_TOKENIZER_SHA_MISMATCH:" + cid)
                if candidate.get("selection_eligible") is not False:
                    failures.append("CONTROL_CANNOT_SATISFY_TARGET_ROLE:" + cid)

            if role == "TARGET_MEASURED":
                if (
                    cid != MEASURED_TARGET["candidate_id"]
                    or candidate.get("repo") != MEASURED_TARGET["repo"]
                    or candidate.get("immutable_revision") != MEASURED_TARGET["revision"]
                ):
                    failures.append("MEASURED_TARGET_IDENTITY_MISMATCH:" + cid)
                else:
                    measured_seen = True
                if candidate.get("model_specific_measurements_observed") is not True:
                    failures.append("MEASURED_TARGET_MEASUREMENTS_REQUIRED:" + cid)

            identity_complete = _has_complete_identity(candidate)
            declared_complete = candidate.get("identity_complete")
            if declared_complete is not identity_complete:
                failures.append("IDENTITY_COMPLETENESS_DECLARATION_MISMATCH:" + cid)
            if not identity_complete and candidate.get("selection_eligible") is not False:
                failures.append("INCOMPLETE_IDENTITY_CANNOT_BE_SELECTION_ELIGIBLE:" + cid)

            if candidate.get("loader_consumption_observed") is not False:
                failures.append("LOADER_CONSUMPTION_MUST_REMAIN_UNOBSERVED:" + cid)
            if candidate.get("consumed_identity_match") is not None:
                failures.append("CONSUMED_IDENTITY_MATCH_MUST_REMAIN_UNKNOWN:" + cid)

            claims = candidate.get("external_claims")
            if claims is not None:
                if not isinstance(claims, dict):
                    failures.append("EXTERNAL_CLAIMS_OBJECT_REQUIRED:" + cid)
                elif claims.get("clay_selection_credit") != 0:
                    failures.append("MODEL_CARD_CLAIM_CANNOT_MINT_SELECTION_CREDIT:" + cid)

            for key in ("runtime_credit", "jspace_credit", "training_credit", "checkpoint_winner_credit"):
                if candidate.get(key) != 0:
                    failures.append("CREDIT_MUST_BE_ZERO:" + cid + ":" + key)

    for control_id in CONTROL_EXPECTED:
        if control_id not in seen:
            failures.append("MISSING_CONTROL:" + control_id)
    if not measured_seen:
        failures.append("MEASURED_ABLITERATED_TARGET_REQUIRED")

    contract = x.get("matched_pilot_contract")
    if not isinstance(contract, dict):
        failures.append("MATCHED_PILOT_CONTRACT_REQUIRED")
    else:
        for key in (
            "same_training_token_budget",
            "same_example_budget",
            "same_optimizer_family",
            "same_hyperparameter_search_budget",
            "same_corpus_revision",
            "same_calibration_validation_split",
            "separate_low_refusal_and_cognition_retention_axes",
            "separate_jspace_causal_axis",
        ):
            if contract.get(key) is not True:
                failures.append("MATCHING_REQUIRED:" + key)
        if contract.get("holdout_seen_during_selection") is not False:
            failures.append("HOLDOUT_LEAK_FORBIDDEN")
        if contract.get("matched_pilot_executed") is not False:
            failures.append("MATCHED_PILOT_MUST_REMAIN_UNEXECUTED_IN_SOURCE_REGISTRY")

    boundary = x.get("execution_boundary")
    if not isinstance(boundary, dict):
        failures.append("EXECUTION_BOUNDARY_REQUIRED")
    else:
        for key in (
            "provider_preflight_performed",
            "provider_credentials_consumed",
            "training_performed",
            "paid_job_authorized",
            "together_job_authorized",
        ):
            if boundary.get(key) is not False:
                failures.append("EXECUTION_MUST_REMAIN_FALSE:" + key)

    failures = sorted(set(failures))
    complete_targets = [
        c["candidate_id"]
        for c in seen.values()
        if c.get("candidate_role") in {"TARGET_MEASURED", "TARGET_EXTERNAL_UNMEASURED"}
        and _has_complete_identity(c)
        and c.get("selection_eligible") is True
    ]
    return {
        "schema": "CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v2",
        "pass": not failures,
        "failures": failures,
        "registry_valid": not failures,
        "selection_ready": False,
        "identity_complete_selection_eligible_targets": complete_targets,
        "checkpoint_winner": None,
        "runtime_credit_minted": False,
        "jspace_credit_minted": False,
        "training_credit_minted": False,
        "checkpoint_winner_credit_minted": False,
        "evidence_boundary": (
            "Role-typed source registry only. A complete target identity does not select a winner; "
            "matched FREE_ONLY pilot, loader-consumed identity and frozen holdout remain required."
        ),
    }
