#!/usr/bin/env python3
"""Successor-dynamic source-integrity gate for Trigger-2 Qwen3.5-0.8B candidates.

Separates five states that must never be conflated:

1. checkpoint snapshot identity,
2. observed loader smoke/load evidence,
3. exact loader-consumed bundle identity,
4. matched-baseline participation eligibility,
5. final checkpoint-winner eligibility.

Current VPS loader probes establish (2), not (3). Therefore a legacy
``selection_eligible=true`` registry flag is treated only as participation intent;
it cannot make a candidate selection-grade while consumed/input identity is unknown.

Source-integrity evidence only. No model/runtime/J-Space/HCU/EntityOS/training or
checkpoint-selection credit is minted here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_CANDIDATES/v3"
IDENTITY_SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_IDENTITY/v1"
LOADER_SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_LOADER_CONSUMPTION_AND_RESOURCE_PROBE/v1"
GATE_SCHEMA = "CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v3"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

BOUND_MEASURED = {
    "QWEN35_08B_BASE": {
        "role": "CONTROL",
        "identity": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_BASE_checkpoint_identity.json",
        "loader": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_BASE_loader_probe.json",
    },
    "QWEN35_08B_POSTTRAINED": {
        "role": "CONTROL",
        "identity": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_POSTTRAINED_checkpoint_identity.json",
        "loader": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_POSTTRAINED_loader_probe.json",
    },
    "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED": {
        "role": "TARGET_MEASURED",
        "identity": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_TARGET_MEASURED_checkpoint_identity.json",
        "loader": "research_entity/global/j-space/research/vps_run_receipts/2026-08-25_QWEN35_08B_TARGET_MEASURED_loader_probe.json",
    },
}
ROLES = {"CONTROL", "TARGET_MEASURED", "TARGET_EXTERNAL_UNMEASURED"}
ZERO_CREDIT_FIELDS = ("runtime_credit", "jspace_credit", "training_credit", "checkpoint_winner_credit")


def _load_json(path: str) -> dict[str, Any]:
    with (ROOT / path).open(encoding="utf-8") as fh:
        value = json.load(fh)
    if not isinstance(value, dict):
        raise ValueError(f"object required: {path}")
    return value


def load_bound_receipts() -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    identities: dict[str, dict[str, Any]] = {}
    loaders: dict[str, dict[str, Any]] = {}
    for cid, spec in BOUND_MEASURED.items():
        identities[cid] = _load_json(spec["identity"])
        loaders[cid] = _load_json(spec["loader"])
    return identities, loaders


def _manifest(identity: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    rows = identity.get("file_manifest")
    if not isinstance(rows, list):
        return result
    for row in rows:
        if not isinstance(row, dict):
            continue
        path = row.get("path")
        digest = row.get("sha256")
        size = row.get("size")
        if (
            isinstance(path, str)
            and isinstance(digest, str)
            and SHA256.fullmatch(digest)
            and isinstance(size, int)
            and size >= 0
        ):
            result[path] = {"path": path, "sha256": digest, "size": size}
    return result


def _normalized_architecture(identity: dict[str, Any]) -> dict[str, Any]:
    config = identity.get("config")
    if not isinstance(config, dict):
        config = {}
    text = config.get("text_config")
    if not isinstance(text, dict):
        text = {}
    dtype = text.get("dtype")
    if dtype is None:
        dtype = text.get("torch_dtype")
    return {
        "model_type": config.get("model_type"),
        "text_model_type": text.get("model_type"),
        "num_hidden_layers": text.get("num_hidden_layers"),
        "hidden_size": text.get("hidden_size"),
        "num_attention_heads": text.get("num_attention_heads"),
        "num_key_value_heads": text.get("num_key_value_heads"),
        "vocab_size": text.get("vocab_size"),
        "max_position_embeddings": text.get("max_position_embeddings"),
        "architectures": config.get("architectures"),
        "text_dtype": dtype,
    }


def _architecture_complete(arch: dict[str, Any]) -> bool:
    return all(
        arch.get(key) is not None
        for key in (
            "model_type",
            "text_model_type",
            "num_hidden_layers",
            "hidden_size",
            "num_attention_heads",
            "num_key_value_heads",
            "vocab_size",
            "max_position_embeddings",
            "architectures",
            "text_dtype",
        )
    )


def _template_status(identity: dict[str, Any]) -> dict[str, Any]:
    manifest = _manifest(identity)
    row = manifest.get("chat_template.jinja")
    if row is not None:
        return {"status": "STANDALONE_FILE_PRESENT", "sha256": row["sha256"]}
    return {
        "status": "NO_STANDALONE_CHAT_TEMPLATE_FILE_IN_BOUND_SNAPSHOT",
        "sha256": None,
        "runtime_resolved_template_identity": "UNRESOLVED_SELECTION_INPUT_ABI",
    }


def _weight_manifest(identity: dict[str, Any]) -> list[dict[str, Any]]:
    manifest = _manifest(identity)
    return [
        row
        for path, row in sorted(manifest.items())
        if path.endswith(".safetensors") or path.endswith(".safetensors.index.json")
    ]


def _is_snapshot_identity_complete(identity: dict[str, Any]) -> bool:
    revision = identity.get("requested_revision")
    arch = _normalized_architecture(identity)
    return bool(
        identity.get("identity_complete") is True
        and identity.get("revision_matches_pinned") is True
        and isinstance(revision, str)
        and SHA40.fullmatch(revision)
        and isinstance(identity.get("file_manifest_sha256"), str)
        and SHA256.fullmatch(identity["file_manifest_sha256"])
        and isinstance(identity.get("config_json_sha256"), str)
        and SHA256.fullmatch(identity["config_json_sha256"])
        and isinstance(identity.get("tokenizer_json_sha256"), str)
        and SHA256.fullmatch(identity["tokenizer_json_sha256"])
        and isinstance(identity.get("tokenizer_config_json_sha256"), str)
        and SHA256.fullmatch(identity["tokenizer_config_json_sha256"])
        and bool(_weight_manifest(identity))
        and _architecture_complete(arch)
    )


def adjudicate(
    x: Any,
    identities: dict[str, dict[str, Any]] | None = None,
    loaders: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    failures: list[str] = []
    warnings: list[str] = []
    normalized: dict[str, Any] = {}

    if identities is None or loaders is None:
        loaded_identities, loaded_loaders = load_bound_receipts()
        identities = loaded_identities if identities is None else identities
        loaders = loaded_loaders if loaders is None else loaders

    if not isinstance(x, dict):
        x = {}
        failures.append("OBJECT_REQUIRED")

    if x.get("schema") != REGISTRY_SCHEMA:
        failures.append("SCHEMA_MISMATCH")
    if x.get("selection_status") != "UNRESOLVED_TARGET_IDENTITY_AND_MATCHED_PILOT_REQUIRED":
        failures.append("SELECTION_STATUS_MUST_REMAIN_UNRESOLVED")
    if x.get("selected_candidate") is not None:
        failures.append("SOURCE_REGISTRY_CANNOT_SELECT_WINNER")

    candidates = x.get("candidates")
    seen: dict[str, dict[str, Any]] = {}
    if not isinstance(candidates, list):
        failures.append("CANDIDATES_REQUIRED")
        candidates = []

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

        for key in ZERO_CREDIT_FIELDS:
            if candidate.get(key) != 0:
                failures.append("CREDIT_MUST_BE_ZERO:" + cid + ":" + key)

        claims = candidate.get("external_claims")
        if claims is not None:
            if not isinstance(claims, dict):
                failures.append("EXTERNAL_CLAIMS_OBJECT_REQUIRED:" + cid)
            elif claims.get("clay_selection_credit") != 0:
                failures.append("MODEL_CARD_CLAIM_CANNOT_MINT_SELECTION_CREDIT:" + cid)

        if cid not in BOUND_MEASURED:
            if role != "TARGET_EXTERNAL_UNMEASURED":
                failures.append("UNBOUND_CANDIDATE_ROLE_INVALID:" + cid)
            if candidate.get("selection_eligible") is not False:
                failures.append("UNBOUND_CANDIDATE_CANNOT_REQUEST_MATCHED_BASELINE:" + cid)
            if candidate.get("loader_consumption_observed") is not False:
                failures.append("UNBOUND_CANDIDATE_CANNOT_CLAIM_LOADER_OBSERVATION:" + cid)
            if candidate.get("consumed_identity_match") is not None:
                failures.append("UNBOUND_CANDIDATE_CONSUMED_IDENTITY_MUST_BE_UNKNOWN:" + cid)
            normalized[cid] = {
                "legacy_participation_intent": False,
                "snapshot_registry_identity_complete": False,
                "loader_smoke_observed": False,
                "consumed_identity_match": None,
                "selection_input_identity_complete": False,
                "matched_baseline_participation_eligible": False,
                "winner_eligible": False,
                "reason": "EXTERNAL_UNMEASURED",
            }
            continue

        spec = BOUND_MEASURED[cid]
        if role != spec["role"]:
            failures.append("BOUND_ROLE_MISMATCH:" + cid)

        identity = identities.get(cid)
        loader = loaders.get(cid)
        if not isinstance(identity, dict):
            failures.append("IDENTITY_RECEIPT_REQUIRED:" + cid)
            continue
        if not isinstance(loader, dict):
            failures.append("LOADER_RECEIPT_REQUIRED:" + cid)
            continue

        if identity.get("schema") != IDENTITY_SCHEMA:
            failures.append("IDENTITY_RECEIPT_SCHEMA_MISMATCH:" + cid)
        if loader.get("schema") != LOADER_SCHEMA:
            failures.append("LOADER_RECEIPT_SCHEMA_MISMATCH:" + cid)
        if identity.get("candidate_id") != cid:
            failures.append("IDENTITY_RECEIPT_CANDIDATE_MISMATCH:" + cid)
        if loader.get("candidate_id") != cid:
            failures.append("LOADER_RECEIPT_CANDIDATE_MISMATCH:" + cid)

        revision = identity.get("requested_revision")
        if candidate.get("repo") != identity.get("repo"):
            failures.append("REGISTRY_RECEIPT_REPO_MISMATCH:" + cid)
        if candidate.get("immutable_revision") != revision:
            failures.append("REGISTRY_RECEIPT_REVISION_MISMATCH:" + cid)

        receipt_snapshot_complete = _is_snapshot_identity_complete(identity)
        if candidate.get("identity_complete") is not receipt_snapshot_complete:
            failures.append("SNAPSHOT_IDENTITY_COMPLETENESS_DECLARATION_MISMATCH:" + cid)

        digest_bindings = {
            "file_manifest_sha256": identity.get("file_manifest_sha256"),
            "config_sha256": identity.get("config_json_sha256"),
            "tokenizer_config_sha256": identity.get("tokenizer_config_json_sha256"),
            "tokenizer_json_sha256": identity.get("tokenizer_json_sha256"),
        }
        for registry_key, expected in digest_bindings.items():
            if candidate.get(registry_key) != expected:
                failures.append("REGISTRY_RECEIPT_DIGEST_MISMATCH:" + cid + ":" + registry_key)

        weight_manifest = _weight_manifest(identity)
        weight_digests = {row["sha256"] for row in weight_manifest}
        registry_weight = candidate.get("weights_sha256")
        if registry_weight is not None and registry_weight not in weight_digests:
            failures.append("REGISTRY_WEIGHT_NOT_IN_BOUND_MANIFEST:" + cid)

        template = _template_status(identity)
        registry_template = candidate.get("chat_template_sha256")
        if registry_template is not None and registry_template != template.get("sha256"):
            failures.append("REGISTRY_CHAT_TEMPLATE_MISMATCH:" + cid)
        elif registry_template is None and template.get("sha256") is not None:
            warnings.append("REGISTRY_CHAT_TEMPLATE_DENORMALIZED_NULL:" + cid)

        loader_observed = loader.get("loader_consumption_observed") is True
        if candidate.get("loader_consumption_observed") is not loader_observed:
            failures.append("LOADER_OBSERVATION_DECLARATION_MISMATCH:" + cid)

        consumed_identity_match = candidate.get("consumed_identity_match")
        if consumed_identity_match is not None:
            failures.append("CONSUMED_IDENTITY_MATCH_UNSUPPORTED_BY_CURRENT_RECEIPTS:" + cid)

        selection_input_identity_complete = False
        legacy_participation_intent = candidate.get("selection_eligible") is True
        matched_participation = bool(
            legacy_participation_intent
            and receipt_snapshot_complete
            and loader_observed
            and consumed_identity_match is True
            and selection_input_identity_complete
        )
        if legacy_participation_intent and not matched_participation:
            warnings.append("LEGACY_SELECTION_ELIGIBLE_BLOCKED_BY_SELECTION_IDENTITY:" + cid)

        arch = _normalized_architecture(identity)
        if not _architecture_complete(arch):
            failures.append("NESTED_QWEN35_ARCHITECTURE_INCOMPLETE:" + cid)
        observed_arch = candidate.get("architecture_observed")
        if isinstance(observed_arch, dict) and any(
            observed_arch.get(key) is None
            for key in (
                "num_hidden_layers",
                "hidden_size",
                "num_attention_heads",
                "num_key_value_heads",
                "vocab_size",
                "max_position_embeddings",
            )
        ):
            warnings.append("REGISTRY_ARCHITECTURE_DENORMALIZED_FROM_TOP_LEVEL_CONFIG:" + cid)

        normalized[cid] = {
            "legacy_participation_intent": legacy_participation_intent,
            "snapshot_registry_identity_complete": receipt_snapshot_complete,
            "loader_smoke_observed": loader_observed,
            "consumed_identity_match": None,
            "selection_input_identity_complete": selection_input_identity_complete,
            "matched_baseline_participation_eligible": matched_participation,
            "winner_eligible": False,
            "weight_manifest": weight_manifest,
            "chat_template": template,
            "architecture": arch,
        }

    for cid in BOUND_MEASURED:
        if cid not in seen:
            failures.append("MISSING_BOUND_MEASURED_CANDIDATE:" + cid)

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
            failures.append("SOURCE_REGISTRY_CANNOT_SELF_ATTEST_MATCHED_PILOT")

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
        if boundary.get("mode") != "FREE_ONLY":
            failures.append("FREE_ONLY_MODE_REQUIRED")

    failures = sorted(set(failures))
    warnings = sorted(set(warnings))
    return {
        "schema": GATE_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "warnings": warnings,
        "registry_source_integrity_valid": not failures,
        "selection_ready": False,
        "checkpoint_winner": None,
        "normalized_candidates": normalized,
        "runtime_credit_minted": False,
        "jspace_credit_minted": False,
        "training_credit_minted": False,
        "checkpoint_winner_credit_minted": False,
        "evidence_boundary": (
            "PASS means snapshot/loader-smoke source fields are consistent with bound receipts. "
            "All current matched-baseline participation remains blocked until exact consumed bundle "
            "identity AND exact model-visible input identity are bound. No winner exists."
        ),
    }


if __name__ == "__main__":
    registry_path = ROOT / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v2.json"
    with registry_path.open(encoding="utf-8") as fh:
        registry = json.load(fh)
    print(json.dumps(adjudicate(registry), indent=2, sort_keys=True))
