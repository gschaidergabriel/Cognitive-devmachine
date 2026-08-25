#!/usr/bin/env python3
"""Repository-authorized discriminator producer authenticity gate for Trigger-2 A02.

This gate closes the bounded pilot exploit where discriminator receipts could carry
``admissible=true``, ``executed=true`` and an arbitrary receipt identifier. It resolves
producer/policy authority from repository source, verifies exact producer bytes, binds
the already generation-pinned world/state/event subjects, invokes the deterministic
producer, and requires the transported receipt to equal the recomputed producer result.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints zero dataset/training/runtime/J-Space/
HCU/EntityOS/canonical-truth/direct-effect credit.
"""
from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_DISCRIMINATOR_PRODUCER_AUTH_GATE/v1"
AUTHORITY_PATH = "research_entity/global/j-space/research/TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_PRODUCER_AUTHORITY_V1.json"


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


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _event_semantic_payload(event: Any) -> dict[str, Any] | None:
    if not isinstance(event, dict):
        return None
    keys = (
        "schema",
        "event_id",
        "correlation_ancestry_id",
        "independence_group",
        "payload_key",
        "provenance",
        "epistemic_type",
        "test_id",
        "observed_outcome",
        "canonical_truth_allowed",
        "direct_effect_authority",
    )
    if any(key not in event for key in keys):
        return None
    return {key: event[key] for key in keys}


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "producer_authenticity_pass": not failures,
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
        "row_carried_admissible_is_authority": False,
        "row_carried_executed_is_authority": False,
        "row_carried_execution_receipt_id_is_authority": False,
    }
    out.update(extra)
    return out


def adjudicate(row: Any) -> dict[str, Any]:
    failures: list[str] = []
    if not isinstance(row, dict):
        return _result(["ROW_OBJECT_REQUIRED"])

    try:
        authority = _authority()
    except Exception as exc:
        return _result(["AUTHORITY_LOAD_FAILED:" + type(exc).__name__])
    if authority.get("schema") != "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_PRODUCER_AUTHORITY/v1":
        failures.append("PRODUCER_AUTHORITY_SCHEMA_MISMATCH")

    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
    if authority.get("authority_fences") != expected_fences:
        failures.append("PRODUCER_AUTHORITY_FENCES_INVALID")

    producer_authority = authority.get("producer")
    if not isinstance(producer_authority, dict):
        return _result(failures + ["PRODUCER_AUTHORITY_OBJECT_REQUIRED"])
    expected_path = producer_authority.get("repo_path")
    if not isinstance(expected_path, str) or not expected_path:
        return _result(failures + ["EXPECTED_PRODUCER_PATH_REQUIRED"])
    producer_path = (_repo_root() / expected_path).resolve()
    try:
        producer_path.relative_to(_repo_root().resolve())
    except ValueError:
        return _result(failures + ["EXPECTED_PRODUCER_PATH_ESCAPES_REPO"])
    if not producer_path.is_file():
        return _result(failures + ["EXPECTED_PRODUCER_FILE_MISSING"])

    actual_source_sha = _source_sha256(producer_path)
    if actual_source_sha != producer_authority.get("source_sha256"):
        failures.append("EXPECTED_PRODUCER_SOURCE_SHA256_MISMATCH")
    try:
        producer = _load_module(
            producer_path,
            "trigger2_trusted_synthetic_discriminator_for_a02",
        )
    except Exception as exc:
        return _result(failures + ["EXPECTED_PRODUCER_IMPORT_FAILED:" + type(exc).__name__])
    if getattr(producer, "PRODUCER_SCHEMA", None) != producer_authority.get("producer_schema_or_version"):
        failures.append("EXPECTED_PRODUCER_SCHEMA_MISMATCH")

    case_id = row.get("generation_case_id_evaluator_only")
    cases = authority.get("allowed_cases")
    if not isinstance(cases, dict) or case_id not in cases:
        return _result(failures + ["DISCRIMINATOR_CASE_NOT_AUTHORIZED"])
    case = cases[case_id]

    world = row.get("formal_task_world_evaluator_only")
    state_before = row.get("hyperposition_state_before_evaluator_only")
    event = row.get("synthetic_test_event_evaluator_only")
    if not isinstance(world, dict) or not isinstance(state_before, dict) or not isinstance(event, dict):
        return _result(failures + ["BOUND_SUBJECT_OBJECTS_REQUIRED"])

    world_sha = _digest(world)
    state_sha = _digest(state_before)
    event_full_sha = _digest(event)
    semantic_payload = _event_semantic_payload(event)
    event_semantic_sha = _digest(semantic_payload) if semantic_payload is not None else None
    test_id = event.get("test_id")
    test_spec = world.get("tests", {}).get(test_id) if isinstance(world.get("tests"), dict) else None
    policy = authority.get("policy")
    spec_sha = _digest({
        "test_id": test_id,
        "test_spec": test_spec,
        "policy": policy,
    })

    expected_pairs = {
        "WORLD_ID_NOT_AUTHORIZED": (world.get("world_id"), case.get("world_id")),
        "EVENT_ID_NOT_AUTHORIZED": (event.get("event_id"), case.get("event_id")),
        "TEST_ID_NOT_AUTHORIZED": (test_id, case.get("test_id")),
        "EPISTEMIC_TYPE_NOT_AUTHORIZED": (event.get("epistemic_type"), case.get("epistemic_type")),
        "WORLD_SHA256_NOT_AUTHORIZED": (world_sha, case.get("world_sha256")),
        "STATE_BEFORE_SHA256_NOT_AUTHORIZED": (state_sha, case.get("state_before_sha256")),
        "EVENT_FULL_SHA256_NOT_AUTHORIZED": (event_full_sha, case.get("full_event_sha256")),
        "EVENT_SEMANTIC_SHA256_NOT_AUTHORIZED": (event_semantic_sha, case.get("event_semantic_sha256")),
        "DISCRIMINATOR_SPEC_SHA256_NOT_AUTHORIZED": (spec_sha, case.get("discriminator_spec_sha256")),
    }
    for failure, (actual, expected) in expected_pairs.items():
        if actual != expected:
            failures.append(failure)

    producer_result = None
    expected_receipt = None
    if not failures:
        try:
            producer_result = producer.produce(world, state_before, event, policy)
        except Exception as exc:
            failures.append("PRODUCER_INVOCATION_EXCEPTION:" + type(exc).__name__)
        else:
            if not isinstance(producer_result, dict) or not producer_result.get("pass"):
                inner = producer_result.get("failures", []) if isinstance(producer_result, dict) else []
                failures.extend("PRODUCER:" + str(item) for item in (inner or ["REJECTED"]))
            else:
                expected_receipt = producer_result.get("receipt")
                if not isinstance(expected_receipt, dict):
                    failures.append("PRODUCER_RECEIPT_OBJECT_REQUIRED")

    transported = row.get("discriminator_execution_receipts_evaluator_only")
    matches = []
    if not isinstance(transported, list):
        failures.append("DISCRIMINATOR_RECEIPTS_LIST_REQUIRED")
    else:
        matches = [
            rec for rec in transported
            if isinstance(rec, dict) and rec.get("event_id") == event.get("event_id")
        ]
        if len(matches) != 1:
            failures.append("EXACTLY_ONE_CURRENT_EVENT_DISCRIMINATOR_RECEIPT_REQUIRED")
    if expected_receipt is not None and len(matches) == 1 and matches[0] != expected_receipt:
        failures.append("TRANSPORTED_DISCRIMINATOR_RECEIPT_NOT_EXACT_PRODUCER_RESULT")

    return _result(
        failures,
        expected_producer_path=expected_path,
        expected_producer_source_sha256=actual_source_sha,
        producer_invoked=producer_result is not None,
        producer_result=producer_result,
        expected_discriminator_receipt=expected_receipt,
        bound_world_sha256=world_sha,
        bound_state_before_sha256=state_sha,
        bound_event_semantic_sha256=event_semantic_sha,
        bound_discriminator_spec_sha256=spec_sha,
        synthetic_execution_only=True,
    )


if __name__ == "__main__":
    print({
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_A02_CANDIDATE_PRE_ADMISSION",
    })
