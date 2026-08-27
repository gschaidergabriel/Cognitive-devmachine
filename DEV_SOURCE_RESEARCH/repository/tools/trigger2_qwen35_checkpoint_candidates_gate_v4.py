#!/usr/bin/env python3
"""Receipt-bound Trigger-2 Qwen3.5-0.8B checkpoint registry gate.

This is a deterministic source-integrity gate. It separates:
- matched evaluation participation,
- target-role eligibility,
- actual winner-selection readiness,
- observed loader activity,
- consumed-byte identity attestation.

A loader-probe v1 receipt can prove that loading was observed for an exact pinned
checkout path; it does NOT by itself prove that the loader consumed bytes matching
the complete checkpoint manifest. This gate therefore keeps consumed identity,
checkpoint winner, J-Space and training credit closed.
"""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
import re
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v4.json"

SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_CANDIDATES/v4"
GATE_SCHEMA = "CLAY_TRIGGER2_QWEN35_CHECKPOINT_CANDIDATES_GATE/v4"
IDENTITY_SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_CHECKPOINT_IDENTITY/v1"
LOADER_SCHEMA = "CLAY_TRIGGER2_QWEN35_08B_LOADER_CONSUMPTION_AND_RESOURCE_PROBE/v1"
SHA1 = re.compile(r"^[0-9a-f]{40}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")

REQUIRED_MEASURED = {
    "QWEN35_08B_BASE": ("CONTROL", "Qwen/Qwen3.5-0.8B-Base", "dc7cdfe2ee4154fa7e30f5b51ca41bfa40174e68", False),
    "QWEN35_08B_POSTTRAINED": ("CONTROL", "Qwen/Qwen3.5-0.8B", "2fc06364715b967f1860aea9cf38778875588b17", False),
    "QWEN35_08B_JOSIEFIED_GABLITERATED_MEASURED": (
        "TARGET_MEASURED",
        "Goekdeniz-Guelmez/Josiefied-Qwen3.5-0.8B-gabliterated-v1",
        "591852bda6e1979f59e4b0f5ee2919697b12e936",
        True,
    ),
}
EXTERNAL_ROLE = "TARGET_EXTERNAL_UNMEASURED"
ARCH_FIELDS = (
    "num_hidden_layers",
    "hidden_size",
    "num_attention_heads",
    "num_key_value_heads",
    "vocab_size",
    "max_position_embeddings",
)


class GateError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def git_blob_sha1(data: bytes) -> str:
    header = f"blob {len(data)}\0".encode("utf-8")
    return hashlib.sha1(header + data).hexdigest()


def load_bound_json(rel_path: str, expected_blob_sha1: str) -> dict[str, Any]:
    if not isinstance(rel_path, str) or not rel_path:
        raise GateError("BOUND_PATH_REQUIRED")
    if not isinstance(expected_blob_sha1, str) or not SHA1.fullmatch(expected_blob_sha1):
        raise GateError("BOUND_BLOB_SHA1_REQUIRED")
    path = ROOT / rel_path
    data = path.read_bytes()
    actual_blob = git_blob_sha1(data)
    if actual_blob != expected_blob_sha1:
        raise GateError(f"BOUND_BLOB_SHA1_MISMATCH:{rel_path}")
    obj = json.loads(data)
    if type(obj) is not dict:
        raise GateError(f"BOUND_OBJECT_REQUIRED:{rel_path}")
    return obj


def manifest_index(receipt: dict[str, Any]) -> dict[str, dict[str, Any]]:
    manifest = receipt.get("file_manifest")
    if not isinstance(manifest, list) or not manifest:
        raise GateError("IDENTITY_FILE_MANIFEST_REQUIRED")
    out: dict[str, dict[str, Any]] = {}
    for item in manifest:
        if type(item) is not dict:
            raise GateError("IDENTITY_MANIFEST_ITEM_OBJECT_REQUIRED")
        path = item.get("path")
        digest = item.get("sha256")
        size = item.get("size")
        if not isinstance(path, str) or not path:
            raise GateError("IDENTITY_MANIFEST_PATH_REQUIRED")
        if path in out:
            raise GateError("IDENTITY_MANIFEST_DUPLICATE_PATH:" + path)
        if not isinstance(digest, str) or not SHA256.fullmatch(digest):
            raise GateError("IDENTITY_MANIFEST_SHA256_INVALID:" + path)
        if not isinstance(size, int) or size < 0:
            raise GateError("IDENTITY_MANIFEST_SIZE_INVALID:" + path)
        out[path] = item
    return out


def normalize_identity(candidate: dict[str, Any], receipt: dict[str, Any]) -> dict[str, Any]:
    cid = candidate["candidate_id"]
    if receipt.get("schema") != IDENTITY_SCHEMA:
        raise GateError("IDENTITY_SCHEMA_MISMATCH:" + cid)
    for left, right, code in (
        (receipt.get("candidate_id"), cid, "IDENTITY_CANDIDATE_MISMATCH"),
        (receipt.get("repo"), candidate.get("repo"), "IDENTITY_REPO_MISMATCH"),
        (receipt.get("requested_revision"), candidate.get("immutable_revision"), "IDENTITY_REVISION_MISMATCH"),
    ):
        if left != right:
            raise GateError(code + ":" + cid)
    if receipt.get("revision_matches_pinned") is not True:
        raise GateError("IDENTITY_REVISION_NOT_PINNED:" + cid)
    if receipt.get("identity_complete") is not True:
        raise GateError("IDENTITY_RECEIPT_NOT_COMPLETE:" + cid)

    revision = receipt.get("requested_revision")
    if not isinstance(revision, str) or not SHA1.fullmatch(revision):
        raise GateError("IDENTITY_REVISION_FORMAT_INVALID:" + cid)

    files = manifest_index(receipt)
    manifest_sha = receipt.get("file_manifest_sha256")
    if not isinstance(manifest_sha, str) or not SHA256.fullmatch(manifest_sha):
        raise GateError("IDENTITY_MANIFEST_AGGREGATE_INVALID:" + cid)

    config_item = files.get("config.json")
    tokenizer_item = files.get("tokenizer.json")
    if config_item is None or tokenizer_item is None:
        raise GateError("IDENTITY_REQUIRED_ARTIFACT_MISSING:" + cid)
    if receipt.get("config_json_sha256") != config_item["sha256"]:
        raise GateError("IDENTITY_CONFIG_DIGEST_DRIFT:" + cid)
    if receipt.get("tokenizer_json_sha256") != tokenizer_item["sha256"]:
        raise GateError("IDENTITY_TOKENIZER_DIGEST_DRIFT:" + cid)

    chat_item = files.get("chat_template.jinja")
    if chat_item is None:
        chat_template = {"state": "ABSENT_IN_MANIFEST", "sha256": None}
        if receipt.get("chat_template_jinja_sha256") not in (None, ""):
            raise GateError("IDENTITY_CHAT_TEMPLATE_DECLARED_BUT_ABSENT:" + cid)
    else:
        chat_digest = receipt.get("chat_template_jinja_sha256")
        if chat_digest != chat_item["sha256"]:
            raise GateError("IDENTITY_CHAT_TEMPLATE_DIGEST_DRIFT:" + cid)
        chat_template = {"state": "PRESENT", "sha256": chat_digest}

    weight_files = [
        {"path": p, "size": item["size"], "sha256": item["sha256"]}
        for p, item in sorted(files.items())
        if p.endswith(".safetensors")
    ]
    if not weight_files:
        raise GateError("IDENTITY_WEIGHT_FILES_REQUIRED:" + cid)
    weights_aggregate = sha256_json(weight_files)

    config = receipt.get("config")
    if type(config) is not dict:
        raise GateError("IDENTITY_CONFIG_OBJECT_REQUIRED:" + cid)
    text = config.get("text_config")
    if type(text) is not dict:
        raise GateError("QWEN35_TEXT_CONFIG_REQUIRED:" + cid)
    architecture: dict[str, Any] = {"model_type": text.get("model_type")}
    if architecture["model_type"] != "qwen3_5_text":
        raise GateError("QWEN35_TEXT_MODEL_TYPE_MISMATCH:" + cid)
    for field in ARCH_FIELDS:
        value = text.get(field)
        if not isinstance(value, int) or value <= 0:
            raise GateError("QWEN35_TEXT_ARCH_FIELD_INVALID:" + cid + ":" + field)
        architecture[field] = value

    return {
        "candidate_id": cid,
        "repo": candidate["repo"],
        "immutable_revision": revision,
        "identity_complete": True,
        "file_manifest_sha256": manifest_sha,
        "weights": {
            "files": weight_files,
            "aggregate_sha256": weights_aggregate,
        },
        "tokenizer_sha256": tokenizer_item["sha256"],
        "config_sha256": config_item["sha256"],
        "chat_template": chat_template,
        "architecture": architecture,
    }


def normalize_loader(candidate: dict[str, Any], identity_receipt: dict[str, Any], loader: dict[str, Any]) -> dict[str, Any]:
    cid = candidate["candidate_id"]
    if loader.get("schema") != LOADER_SCHEMA:
        raise GateError("LOADER_SCHEMA_MISMATCH:" + cid)
    if loader.get("candidate_id") != cid:
        raise GateError("LOADER_CANDIDATE_MISMATCH:" + cid)
    if loader.get("loader_consumption_observed") is not True:
        raise GateError("LOADER_OBSERVATION_REQUIRED:" + cid)
    expected_local_dir = identity_receipt.get("local_dir")
    if loader.get("local_dir") != expected_local_dir:
        raise GateError("LOADER_LOCAL_DIR_IDENTITY_MISMATCH:" + cid)
    revision = candidate.get("immutable_revision")
    if not isinstance(revision, str) or not str(loader.get("local_dir", "")).rstrip("/").endswith("/" + revision):
        raise GateError("LOADER_LOCAL_DIR_REVISION_MISMATCH:" + cid)
    return {
        "loader_consumption_observed": True,
        "consumed_identity_match": "UNPROVEN_BY_LOADER_PROBE_V1",
        "reason": (
            "The bound v1 loader probe observes loading from the pinned snapshot path but does not "
            "attest the exact bytes actually consumed against the complete identity manifest."
        ),
        "runtime": loader.get("runtime"),
        "resource_benchmark": loader.get("resource_benchmark"),
    }


def adjudicate(registry: Any) -> dict[str, Any]:
    failures: list[str] = []
    normalized: list[dict[str, Any]] = []
    if type(registry) is not dict:
        return {"schema": GATE_SCHEMA, "pass": False, "failures": ["OBJECT_REQUIRED"]}

    if registry.get("schema") != SCHEMA:
        failures.append("SCHEMA_MISMATCH")
    if registry.get("selected_candidate") is not None:
        failures.append("SOURCE_REGISTRY_CANNOT_SELECT_WINNER")
    if registry.get("selection_status") != "UNRESOLVED_MATCHED_BASELINE_AND_CONSUMED_IDENTITY_ATTESTATION_REQUIRED":
        failures.append("SELECTION_STATUS_MUST_REMAIN_UNRESOLVED")

    candidates = registry.get("candidates")
    if not isinstance(candidates, list):
        failures.append("CANDIDATES_REQUIRED")
        candidates = []

    seen: set[str] = set()
    for candidate in candidates:
        if type(candidate) is not dict:
            failures.append("CANDIDATE_OBJECT_REQUIRED")
            continue
        cid = candidate.get("candidate_id")
        if not isinstance(cid, str) or not cid:
            failures.append("CANDIDATE_ID_REQUIRED")
            continue
        if cid in seen:
            failures.append("DUPLICATE_CANDIDATE:" + cid)
            continue
        seen.add(cid)

        credits = candidate.get("credits")
        if not isinstance(credits, dict) or any(credits.get(k) != 0 for k in ("runtime", "jspace", "training", "checkpoint_winner")):
            failures.append("CANDIDATE_CREDIT_MUST_BE_ZERO:" + cid)
        if candidate.get("winner_selection_ready") is not False:
            failures.append("WINNER_SELECTION_READY_MUST_REMAIN_FALSE:" + cid)

        expected = REQUIRED_MEASURED.get(cid)
        role = candidate.get("candidate_role")
        if expected is not None:
            exp_role, exp_repo, exp_rev, exp_winner_role = expected
            if role != exp_role:
                failures.append("MEASURED_ROLE_MISMATCH:" + cid)
            if candidate.get("repo") != exp_repo:
                failures.append("MEASURED_REPO_MISMATCH:" + cid)
            if candidate.get("immutable_revision") != exp_rev:
                failures.append("MEASURED_REVISION_MISMATCH:" + cid)
            if candidate.get("matched_evaluation_participant") is not True:
                failures.append("MEASURED_PARTICIPANT_REQUIRED:" + cid)
            if candidate.get("winner_role_eligible") is not exp_winner_role:
                failures.append("WINNER_ROLE_ELIGIBILITY_MISMATCH:" + cid)
            try:
                identity = load_bound_json(candidate["identity_receipt_path"], candidate["identity_receipt_blob_sha1"])
                loader = load_bound_json(candidate["loader_receipt_path"], candidate["loader_receipt_blob_sha1"])
                n_identity = normalize_identity(candidate, identity)
                n_loader = normalize_loader(candidate, identity, loader)
                normalized.append({
                    **n_identity,
                    **n_loader,
                    "candidate_role": role,
                    "matched_evaluation_participant": True,
                    "winner_role_eligible": exp_winner_role,
                    "winner_selection_ready": False,
                })
            except (KeyError, OSError, json.JSONDecodeError, GateError) as exc:
                failures.append("BOUND_RECEIPT_FAILURE:" + cid + ":" + str(exc))
        else:
            if role != EXTERNAL_ROLE:
                failures.append("UNKNOWN_CANDIDATE_OR_ROLE:" + cid)
            if candidate.get("matched_evaluation_participant") is not False:
                failures.append("UNMEASURED_CANNOT_PARTICIPATE:" + cid)
            if candidate.get("winner_role_eligible") is not True:
                failures.append("UNMEASURED_TARGET_ROLE_EXPECTED:" + cid)
            for key in ("immutable_revision", "identity_receipt_path", "identity_receipt_blob_sha1", "loader_receipt_path", "loader_receipt_blob_sha1"):
                if candidate.get(key) is not None:
                    failures.append("UNMEASURED_BOUND_IDENTITY_MUST_BE_NULL:" + cid + ":" + key)

    for cid in REQUIRED_MEASURED:
        if cid not in seen:
            failures.append("MISSING_REQUIRED_MEASURED_CANDIDATE:" + cid)

    contract = registry.get("matched_pilot_contract")
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

    boundary = registry.get("execution_boundary")
    if not isinstance(boundary, dict):
        failures.append("EXECUTION_BOUNDARY_REQUIRED")
    else:
        for key in ("provider_preflight_performed", "provider_credentials_consumed", "training_performed", "paid_job_authorized", "together_job_authorized"):
            if boundary.get(key) is not False:
                failures.append("EXECUTION_MUST_REMAIN_FALSE:" + key)
        if boundary.get("mode") != "FREE_ONLY":
            failures.append("FREE_ONLY_REQUIRED")

    credit = registry.get("credit_boundary")
    if not isinstance(credit, dict) or any(v != 0 for v in credit.values()):
        failures.append("REGISTRY_CREDIT_BOUNDARY_MUST_BE_ZERO")

    failures = sorted(set(failures))
    return {
        "schema": GATE_SCHEMA,
        "pass": not failures,
        "failures": failures,
        "registry_valid": not failures,
        "selection_ready": False,
        "checkpoint_winner": None,
        "normalized_measured_candidates": sorted(normalized, key=lambda x: x["candidate_id"]),
        "credit": {
            "checkpoint_selection": 0,
            "jspace": 0,
            "training": 0,
            "whole_hcu_runtime": 0,
            "whole_entityos_runtime": 0,
        },
        "evidence_boundary": (
            "Exact receipt binding and nested Qwen3.5 architecture normalization are source-integrity evidence only. "
            "Loader-probe v1 proves observed loading but not exact consumed-byte identity; no winner is selected."
        ),
    }


def self_test(registry: dict[str, Any]) -> dict[str, Any]:
    checks: dict[str, bool] = {}
    base = adjudicate(registry)
    checks["CURRENT_V4_REGISTRY_PASSES"] = base["pass"]

    m = copy.deepcopy(registry)
    m["schema"] = "STALE"
    checks["STALE_SCHEMA_FAILS"] = not adjudicate(m)["pass"]

    m = copy.deepcopy(registry)
    m["candidates"][0]["candidate_role"] = "TARGET_MEASURED"
    checks["ROLE_MUTATION_FAILS"] = not adjudicate(m)["pass"]

    m = copy.deepcopy(registry)
    m["candidates"][0]["identity_receipt_blob_sha1"] = "0" * 40
    checks["IDENTITY_RECEIPT_BINDING_MUTATION_FAILS"] = not adjudicate(m)["pass"]

    m = copy.deepcopy(registry)
    m["candidates"][0]["matched_evaluation_participant"] = False
    checks["PARTICIPATION_MUTATION_FAILS"] = not adjudicate(m)["pass"]

    try:
        c = registry["candidates"][0]
        identity = load_bound_json(c["identity_receipt_path"], c["identity_receipt_blob_sha1"])
        broken = copy.deepcopy(identity)
        broken["config"]["text_config"]["hidden_size"] = None
        normalize_identity(c, broken)
        checks["NESTED_ARCH_NULL_FAILS"] = False
    except GateError:
        checks["NESTED_ARCH_NULL_FAILS"] = True

    return {"pass": all(checks.values()), "checks": checks}


def main() -> int:
    registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
    result = adjudicate(registry)
    result["self_test"] = self_test(registry)
    result["pass"] = bool(result["pass"] and result["self_test"]["pass"])
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
