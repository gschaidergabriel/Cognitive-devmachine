#!/usr/bin/env python3
"""Trigger-2 deterministic generation-provenance gate v1.

Closes the row-controlled evaluator-subject provenance root for a bounded pilot by resolving
the trusted generator identity from a repository authority manifest, verifying its exact
source bytes, deterministically reconstructing evaluator-only subjects, canonicalizing them
with the admitted RFC8785/JCS implementation, and comparing a recomputed generation receipt.

This is a provenance component only. PASS does not mint canonical truth/effect/runtime/
J-Space/HCU/EntityOS/training credit and does not admit dataset tokens.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_GENERATION_PROVENANCE_GATE/v1"
RECEIPT_SCHEMA = "XENO_SYNTHETIC_GENERATION_RECEIPT/v1"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY_V1.json"
CANONICALIZER_PATH = "the artefact/MicroEntity/hcu/entry_canonicalization_v1.py"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _authority() -> dict[str, Any]:
    return json.loads((_repo_root() / AUTHORITY_PATH).read_text(encoding="utf-8"))


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _jcs_module():
    return _load_module(_repo_root() / CANONICALIZER_PATH, "trigger2_jcs_for_generation_provenance")


def _jcs_sha256(value: Any) -> str:
    canonicalize = _jcs_module().canonicalize
    return sha256(canonicalize(value)).hexdigest()


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "generation_provenance_pass": not failures,
        "failures": failures,
        "canonical_dataset_admission": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
        "canonical_truth_minted": False,
        "direct_effect_authority_minted": False,
        "row_declared_generator_path_is_authority": False,
    }
    out.update(extra)
    return out


def _reconstructed_subjects(generator: Any, case_id: str, parameters: Any) -> dict[str, Any]:
    bundle = generator.build_subjects(case_id, deepcopy(parameters))
    return {
        "formal_world": bundle["formal_world"],
        "event_dependence_registry": bundle["event_dependence_registry"],
        "event": bundle["event"],
        "state_before": bundle["state_before"],
    }


def _subject_hashes(subjects: dict[str, Any]) -> dict[str, str]:
    return {
        "formal_world_jcs_sha256": _jcs_sha256(subjects["formal_world"]),
        "event_dependence_registry_jcs_sha256": _jcs_sha256(subjects["event_dependence_registry"]),
        "event_jcs_sha256": _jcs_sha256(subjects["event"]),
        "state_before_jcs_sha256": _jcs_sha256(subjects["state_before"]),
    }


def _invocation_id(generator_commit: str, case_id: str, params_hash: str, materials_hash: str) -> str:
    preimage = {
        "generator_git_commit_sha": generator_commit,
        "generation_case_id": case_id,
        "deterministic_parameters_jcs_sha256": params_hash,
        "materials_manifest_jcs_sha256": materials_hash,
    }
    return "t2gp:" + _jcs_sha256(preimage)


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    try:
        authority = _authority()
    except Exception as exc:
        return _result(["AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY/v1":
        failures.append("GENERATOR_AUTHORITY_SCHEMA_MISMATCH")
    fences = authority.get("authority_fences")
    if not isinstance(fences, dict) or fences != {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }:
        failures.append("GENERATOR_AUTHORITY_FENCES_INVALID")

    generator_authority = authority.get("generator")
    if not isinstance(generator_authority, dict):
        return _result(failures + ["GENERATOR_AUTHORITY_OBJECT_REQUIRED"])
    expected_path = generator_authority.get("repo_path")
    if not isinstance(expected_path, str) or not expected_path:
        return _result(failures + ["EXPECTED_GENERATOR_PATH_REQUIRED"])
    generator_path = (_repo_root() / expected_path).resolve()
    try:
        generator_path.relative_to(_repo_root().resolve())
    except ValueError:
        return _result(failures + ["EXPECTED_GENERATOR_PATH_ESCAPES_REPO"])
    if not generator_path.is_file():
        return _result(failures + ["EXPECTED_GENERATOR_FILE_MISSING"])

    actual_source_sha = _source_sha256(generator_path)
    if actual_source_sha != generator_authority.get("source_sha256"):
        failures.append("EXPECTED_GENERATOR_SOURCE_SHA256_MISMATCH")

    try:
        generator = _load_module(generator_path, "trigger2_trusted_generator_for_provenance_gate")
    except Exception as exc:
        return _result(failures + ["EXPECTED_GENERATOR_IMPORT_FAILED:" + type(exc).__name__])
    if getattr(generator, "GENERATOR_SCHEMA", None) != generator_authority.get("generator_schema_or_version"):
        failures.append("EXPECTED_GENERATOR_SCHEMA_MISMATCH")

    source_binding = row.get("source_binding")
    if not isinstance(source_binding, dict) or source_binding.get("generator_path") != expected_path:
        failures.append("ROW_GENERATOR_PATH_NOT_CURRENT_AUTHORITY")
    if isinstance(source_binding, dict) and source_binding.get("generator_sha256") != actual_source_sha:
        failures.append("ROW_GENERATOR_SHA256_NOT_CURRENT_AUTHORITY")

    case_id = row.get("generation_case_id_evaluator_only")
    cases = authority.get("allowed_cases")
    if not isinstance(cases, dict) or case_id not in cases:
        return _result(failures + ["GENERATION_CASE_NOT_AUTHORIZED"], expected_generator_path=expected_path)
    case = cases[case_id]
    parameters = row.get("generation_parameters_evaluator_only")
    if parameters != case.get("deterministic_parameters"):
        failures.append("GENERATION_PARAMETERS_NOT_AUTHORIZED")
    try:
        params_hash = _jcs_sha256(parameters)
    except Exception as exc:
        failures.append("GENERATION_PARAMETERS_JCS_FAILED:" + type(exc).__name__)
        params_hash = None
    if params_hash != case.get("deterministic_parameters_jcs_sha256"):
        failures.append("GENERATION_PARAMETERS_DIGEST_MISMATCH")

    materials = case.get("materials_manifest")
    try:
        materials_hash = _jcs_sha256(materials)
    except Exception as exc:
        failures.append("MATERIALS_MANIFEST_JCS_FAILED:" + type(exc).__name__)
        materials_hash = None
    if materials_hash != case.get("materials_manifest_jcs_sha256"):
        failures.append("MATERIALS_MANIFEST_DIGEST_MISMATCH")

    reconstructed = None
    reconstructed_hashes = None
    try:
        reconstructed = _reconstructed_subjects(generator, case_id, parameters)
        reconstructed_hashes = _subject_hashes(reconstructed)
    except Exception as exc:
        failures.append("DETERMINISTIC_SUBJECT_RECONSTRUCTION_FAILED:" + type(exc).__name__)

    supplied_subjects = {
        "formal_world": row.get("formal_task_world_evaluator_only"),
        "event_dependence_registry": (
            row.get("formal_task_world_evaluator_only", {}).get("event_dependence_registry")
            if isinstance(row.get("formal_task_world_evaluator_only"), dict) else None
        ),
        "event": row.get("synthetic_test_event_evaluator_only"),
        "state_before": row.get("hyperposition_state_before_evaluator_only"),
    }
    supplied_hashes = None
    try:
        supplied_hashes = _subject_hashes(supplied_subjects)
    except Exception as exc:
        failures.append("SUPPLIED_SUBJECT_JCS_FAILED:" + type(exc).__name__)

    if reconstructed_hashes != case.get("subjects"):
        failures.append("AUTHORITY_SUBJECT_DIGEST_DOES_NOT_MATCH_RECONSTRUCTION")
    if supplied_hashes != reconstructed_hashes:
        failures.append("SUPPLIED_SUBJECT_DIGEST_OR_RECONSTRUCTION_MISMATCH")
    if isinstance(reconstructed, dict):
        for key in ("formal_world", "event_dependence_registry", "event", "state_before"):
            if supplied_subjects.get(key) != reconstructed.get(key):
                failures.append("SUPPLIED_SUBJECT_BYTES_NOT_RECONSTRUCTED:" + key)

    scope = case.get("semantic_scope")
    if not isinstance(scope, dict):
        failures.append("SEMANTIC_SCOPE_AUTHORITY_REQUIRED")
    else:
        if supplied_subjects.get("formal_world", {}).get("world_id") != scope.get("world_id"):
            failures.append("WORLD_ID_SCOPE_MISMATCH")
        if supplied_subjects.get("state_before", {}).get("query_id") != scope.get("query_id"):
            failures.append("QUERY_ID_SCOPE_MISMATCH")
        if supplied_subjects.get("event", {}).get("event_id") != scope.get("event_id"):
            failures.append("EVENT_ID_SCOPE_MISMATCH")

    generator_commit = generator_authority.get("git_commit_sha")
    invocation_id = (
        _invocation_id(generator_commit, case_id, params_hash, materials_hash)
        if all(isinstance(x, str) and x for x in (generator_commit, params_hash, materials_hash))
        else None
    )
    expected_receipt = {
        "schema": RECEIPT_SCHEMA,
        "generator": {
            "repo_path": expected_path,
            "source_sha256": actual_source_sha,
            "git_commit_sha": generator_commit,
            "generator_schema_or_version": generator_authority.get("generator_schema_or_version"),
        },
        "invocation": {
            "invocation_id": invocation_id,
            "generation_case_id": case_id,
            "deterministic_parameters_jcs_sha256": params_hash,
            "materials_manifest_jcs_sha256": materials_hash,
        },
        "subjects": reconstructed_hashes,
        "semantic_scope": deepcopy(scope),
        "authority_fences": {
            "canonical_truth_allowed": False,
            "direct_effect_authority": False,
            "training_eligible": False,
            "accepted_dataset_tokens_minted": 0,
            "training_credit_minted": 0,
        },
        "canonicalization": "RFC8785_JCS_IJSON/v1",
        "digest": "SHA256",
    }
    claimed_receipt = row.get("generation_receipt_evaluator_only")
    if claimed_receipt != expected_receipt:
        failures.append("GENERATION_RECEIPT_NOT_EXACTLY_RECOMPUTED")

    return _result(
        failures,
        expected_generator_path=expected_path,
        expected_generator_source_sha256=actual_source_sha,
        expected_generation_receipt=expected_receipt,
        reconstructed_subject_hashes=reconstructed_hashes,
        supplied_subject_hashes=supplied_hashes,
        deterministic_reconstruction_performed=reconstructed is not None,
        jcs_key_order_invariant_by_canonicalizer=True,
    )
