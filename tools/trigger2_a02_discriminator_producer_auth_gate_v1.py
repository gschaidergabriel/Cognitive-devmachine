#!/usr/bin/env python3
"""Repository-authority-bound A02 discriminator producer-auth gate v1.

The gate closes the bounded Trigger-2 A02 hole where a candidate could carry a coherent
``admissible=true`` / ``executed=true`` discriminator receipt without proving that the
authority-selected deterministic synthetic producer actually produced it.

It does not create a second Hyperposition semantic authority. It verifies producer/policy
authority, reconstructs the exact receipt using the retained v3 test-order semantics, and
requires byte-structural equality with the transported receipt. PASS is candidate
pre-admission component evidence only and mints zero credit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTH_GATE/v1"
AUTHORITY_PATH = (
    "research_entity/global/j-space/research/"
    "TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"
)
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


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("JSON_OBJECT_REQUIRED")
    return value


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _jcs_module():
    return _load_module(
        _repo_root() / CANONICALIZER_PATH,
        "trigger2_jcs_for_a02_producer_auth_gate",
    )


def _jcs_sha256(value: Any) -> str:
    return sha256(_jcs_module().canonicalize(value)).hexdigest()


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "a02_producer_auth_pass": not failures,
        "candidate_pre_admission_pass": not failures,
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
        "row_producer_or_policy_fields_authoritative": False,
    }
    out.update(extra)
    return out


def adjudicate(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])
    failures: list[str] = []

    try:
        authority = _load_json(_repo_root() / AUTHORITY_PATH)
    except Exception as exc:
        return _result(["A02_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != "CLAY_TRIGGER2_A02_DISCRIMINATOR_PRODUCER_AUTHORITY/v1":
        failures.append("A02_AUTHORITY_SCHEMA_MISMATCH")

    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
        "runtime_credit_minted": 0,
        "jspace_runtime_credit_minted": 0,
        "hcu_runtime_credit_minted": 0,
        "entityos_runtime_credit_minted": 0,
    }
    if authority.get("authority_fences") != expected_fences:
        failures.append("A02_AUTHORITY_FENCES_INVALID")

    producer_auth = authority.get("producer")
    policy = authority.get("policy")
    generation_auth_ref = authority.get("generation_authority")
    if not isinstance(producer_auth, dict):
        return _result(failures + ["A02_PRODUCER_AUTHORITY_REQUIRED"])
    if not isinstance(policy, dict):
        return _result(failures + ["A02_POLICY_AUTHORITY_REQUIRED"])
    if not isinstance(generation_auth_ref, dict):
        return _result(failures + ["A02_GENERATION_AUTHORITY_REFERENCE_REQUIRED"])

    producer_repo_path = producer_auth.get("repo_path")
    if not isinstance(producer_repo_path, str) or not producer_repo_path:
        return _result(failures + ["A02_PRODUCER_PATH_REQUIRED"])
    producer_path = (_repo_root() / producer_repo_path).resolve()
    try:
        producer_path.relative_to(_repo_root().resolve())
    except ValueError:
        return _result(failures + ["A02_PRODUCER_PATH_ESCAPES_REPO"])
    if not producer_path.is_file():
        return _result(failures + ["A02_PRODUCER_FILE_MISSING"])

    actual_producer_sha = _source_sha256(producer_path)
    if actual_producer_sha != producer_auth.get("source_sha256"):
        failures.append("A02_PRODUCER_SOURCE_SHA256_MISMATCH")
    try:
        producer = _load_module(producer_path, "trigger2_a02_authority_selected_producer")
    except Exception as exc:
        return _result(failures + ["A02_PRODUCER_IMPORT_FAILED:" + type(exc).__name__])
    if getattr(producer, "PRODUCER_SCHEMA", None) != producer_auth.get("producer_schema_or_version"):
        failures.append("A02_PRODUCER_SCHEMA_MISMATCH")

    generation_authority_path = generation_auth_ref.get("repo_path")
    if not isinstance(generation_authority_path, str) or not generation_authority_path:
        return _result(failures + ["A02_GENERATION_AUTHORITY_PATH_REQUIRED"])
    try:
        generation_authority = _load_json(_repo_root() / generation_authority_path)
    except Exception as exc:
        return _result(failures + ["A02_GENERATION_AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if generation_authority.get("schema") != generation_auth_ref.get("schema"):
        failures.append("A02_GENERATION_AUTHORITY_SCHEMA_MISMATCH")

    case_id = row.get("generation_case_id_evaluator_only")
    if case_id != policy.get("allowed_case_id"):
        failures.append("A02_GENERATION_CASE_NOT_AUTHORIZED")
    cases = generation_authority.get("allowed_cases")
    case = cases.get(case_id) if isinstance(cases, dict) else None
    if not isinstance(case, dict):
        return _result(failures + ["A02_GENERATION_CASE_AUTHORITY_MISSING"])

    world = row.get("formal_task_world_evaluator_only")
    pre_state = row.get("hyperposition_state_before_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    history = row.get("synthetic_event_history_evaluator_only")
    if history != []:
        failures.append("A02_V1_REQUIRES_EMPTY_HISTORY_BOUNDED_PILOT")

    try:
        supplied_subject_hashes = {
            "formal_world_jcs_sha256": _jcs_sha256(world),
            "event_jcs_sha256": _jcs_sha256(event),
            "state_before_jcs_sha256": _jcs_sha256(pre_state),
        }
    except Exception as exc:
        supplied_subject_hashes = None
        failures.append("A02_SUBJECT_JCS_FAILED:" + type(exc).__name__)
    expected_subject_hashes = case.get("subjects")
    if not isinstance(expected_subject_hashes, dict):
        failures.append("A02_GENERATION_SUBJECT_HASH_AUTHORITY_REQUIRED")
    elif isinstance(supplied_subject_hashes, dict):
        for key, actual in supplied_subject_hashes.items():
            if actual != expected_subject_hashes.get(key):
                failures.append("A02_SUBJECT_NOT_AUTHORITY_RECONSTRUCTED:" + key)

    if isinstance(world, dict) and world.get("world_id") != policy.get("world_id"):
        failures.append("A02_WORLD_SCOPE_MISMATCH")
    if isinstance(pre_state, dict) and pre_state.get("query_id") != policy.get("query_id"):
        failures.append("A02_QUERY_SCOPE_MISMATCH")
    if isinstance(event, dict):
        if event.get("test_id") != policy.get("test_id"):
            failures.append("A02_TEST_SCOPE_MISMATCH")
        if event.get("epistemic_type") != policy.get("epistemic_type"):
            failures.append("A02_EPISTEMIC_SCOPE_MISMATCH")

    expected_binding = {
        "repo_path": producer_repo_path,
        "source_sha256": actual_producer_sha,
        "producer_schema_or_version": producer_auth.get("producer_schema_or_version"),
        "policy_id": policy.get("policy_id"),
        "policy_version": policy.get("policy_version"),
        "formal_discriminator_spec_jcs_sha256": policy.get(
            "formal_discriminator_spec_jcs_sha256"
        ),
    }
    claimed_binding = row.get("discriminator_producer_binding_evaluator_only")
    if claimed_binding != expected_binding:
        failures.append("A02_ROW_PRODUCER_BINDING_NOT_EXACT_AUTHORITY")

    expected_receipt = None
    if not failures:
        try:
            expected_receipt = producer.produce(
                world=world,
                pre_state=pre_state,
                event=event,
                generation_case_id=case_id,
                policy=policy,
            )
        except Exception as exc:
            failures.append("A02_PRODUCER_EXECUTION_FAILED:" + type(exc).__name__ + ":" + str(exc))

    receipts = row.get("discriminator_execution_receipts_evaluator_only")
    claimed_receipt = None
    if not isinstance(receipts, list):
        failures.append("A02_DISCRIMINATOR_RECEIPTS_LIST_REQUIRED")
    elif isinstance(event, dict):
        matching = [
            r for r in receipts
            if isinstance(r, dict) and r.get("event_id") == event.get("event_id")
        ]
        if len(matching) != 1:
            failures.append("A02_REQUIRES_EXACTLY_ONE_CURRENT_EVENT_RECEIPT")
        else:
            claimed_receipt = matching[0]

    if expected_receipt is not None and claimed_receipt != expected_receipt:
        failures.append("A02_DISCRIMINATOR_RECEIPT_NOT_EXACTLY_AUTHORITY_DERIVED")

    return _result(
        failures,
        expected_producer_binding=expected_binding,
        expected_discriminator_receipt=expected_receipt,
        supplied_subject_hashes=supplied_subject_hashes,
        bounded_generation_case_id=case_id,
        producer_source_verified=actual_producer_sha == producer_auth.get("source_sha256"),
        producer_invocation_completed=expected_receipt is not None,
        semantic_authority="RETAINED_V3_U_TEST_ORDER_VIA_AUTHORITY_PINNED_PRODUCER",
        producer_execution_scope="SYNTHETIC_PROOF_ONLY_NONCANONICAL",
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_CANDIDATE_PRE_ADMISSION",
        "canonical_dataset_admission": False,
        "training_credit_minted": 0,
    })
