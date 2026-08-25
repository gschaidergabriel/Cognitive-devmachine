#!/usr/bin/env python3
"""Repository-authorized discriminator-producer authenticity gate for Trigger-2.

Bounded to T2_GP_PILOT_DB_MATCH_V1. The gate resolves producer, deterministic ordering
semantics and policy from repository authority, verifies exact source identities, reconstructs
world/state/event from the already trusted generator authority, invokes the deterministic
producer, and requires the transported discriminator receipt to equal the recomputed receipt
exactly.

SOURCE/CANDIDATE PRE-ADMISSION ONLY. PASS mints zero canonical truth/effect/runtime/J-Space/
HCU/EntityOS/dataset-token/training credit.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha1, sha256
import importlib.util
import json
from pathlib import Path
from typing import Any

SCHEMA = "CLAY_TRIGGER2_DISCRIMINATOR_PRODUCER_AUTH_GATE/v1"
AUTHORITY_PATH = (
    "research_entity/global/j-space/research/"
    "TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY_V1.json"
)
EXPECTED_AUTHORITY_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_DISCRIMINATOR_AUTHORITY/v1"
EXPECTED_GENERATOR_AUTHORITY_SCHEMA = "CLAY_TRIGGER2_TRUSTED_SYNTHETIC_GENERATOR_AUTHORITY/v1"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _load_module(path: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_json(relative_path: str) -> dict[str, Any]:
    return json.loads((_repo_root() / relative_path).read_text(encoding="utf-8"))


def _producer_authority() -> dict[str, Any]:
    return _load_json(AUTHORITY_PATH)


def _source_sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _git_blob_sha1(path: Path) -> str:
    data = path.read_bytes()
    return sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def _digest(value: Any) -> str:
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _result(failures: list[str], **extra: Any) -> dict[str, Any]:
    failures = sorted(set(failures))
    out = {
        "schema": SCHEMA,
        "pass": not failures,
        "producer_authenticity_pass": not failures,
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
        "row_declared_producer_is_authority": False,
        "row_declared_policy_is_authority": False,
        "row_declared_admissible_is_authority": False,
        "row_declared_executed_is_authority": False,
        "row_declared_execution_receipt_id_is_authority": False,
    }
    out.update(extra)
    return out


def _resolve_repo_file(relative_path: Any, *, missing_code: str, escape_code: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path:
        raise ValueError(missing_code)
    path = (_repo_root() / relative_path).resolve()
    try:
        path.relative_to(_repo_root().resolve())
    except ValueError as exc:
        raise ValueError(escape_code) from exc
    if not path.is_file():
        raise FileNotFoundError(missing_code)
    return path


def _trusted_subjects(
    case_id: str, producer_authority: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    generator_authority_path = producer_authority.get("generator_authority_path")
    if not isinstance(generator_authority_path, str) or not generator_authority_path:
        raise ValueError("GENERATOR_AUTHORITY_PATH_REQUIRED")
    generator_authority = _load_json(generator_authority_path)
    if generator_authority.get("schema") != EXPECTED_GENERATOR_AUTHORITY_SCHEMA:
        raise ValueError("GENERATOR_AUTHORITY_SCHEMA_MISMATCH")

    generator_binding = generator_authority.get("generator")
    if not isinstance(generator_binding, dict):
        raise ValueError("GENERATOR_BINDING_REQUIRED")
    generator_path = _resolve_repo_file(
        generator_binding.get("repo_path"),
        missing_code="GENERATOR_FILE_REQUIRED",
        escape_code="GENERATOR_PATH_ESCAPES_REPO",
    )
    actual_generator_sha = _source_sha256(generator_path)
    if actual_generator_sha != generator_binding.get("source_sha256"):
        raise ValueError("GENERATOR_SOURCE_SHA256_MISMATCH")
    generator = _load_module(
        generator_path, "trigger2_trusted_generator_for_discriminator_producer_auth"
    )
    if getattr(generator, "GENERATOR_SCHEMA", None) != generator_binding.get(
        "generator_schema_or_version"
    ):
        raise ValueError("GENERATOR_SCHEMA_MISMATCH")

    cases = generator_authority.get("allowed_cases")
    if not isinstance(cases, dict) or case_id not in cases:
        raise ValueError("GENERATION_CASE_NOT_AUTHORIZED")
    case = cases[case_id]
    parameters = case.get("deterministic_parameters")
    bundle = generator.build_subjects(case_id, deepcopy(parameters))
    trusted = {
        "world": deepcopy(bundle["formal_world"]),
        "state_before": deepcopy(bundle["state_before"]),
        "event": deepcopy(bundle["event"]),
        "parameters": deepcopy(parameters),
    }
    return trusted, {
        "repo_path": generator_binding.get("repo_path"),
        "source_sha256": actual_generator_sha,
        "generator_schema_or_version": generator_binding.get("generator_schema_or_version"),
    }


def _ordering_binding(authority: dict[str, Any]) -> dict[str, Any]:
    expected = authority.get("ordering_semantics")
    if not isinstance(expected, dict):
        raise ValueError("ORDERING_SEMANTICS_BINDING_REQUIRED")
    path = _resolve_repo_file(
        expected.get("repo_path"),
        missing_code="ORDERING_SEMANTICS_FILE_REQUIRED",
        escape_code="ORDERING_SEMANTICS_PATH_ESCAPES_REPO",
    )
    actual_blob = _git_blob_sha1(path)
    if actual_blob != expected.get("git_blob_sha1"):
        raise ValueError("ORDERING_SEMANTICS_GIT_BLOB_MISMATCH")
    module = _load_module(path, "trigger2_bound_ordering_semantics_for_producer_auth")
    if getattr(module, "SCHEMA", None) != expected.get("schema_or_version"):
        raise ValueError("ORDERING_SEMANTICS_SCHEMA_MISMATCH")
    return {
        "repo_path": expected.get("repo_path"),
        "git_blob_sha1": actual_blob,
        "source_sha256": _source_sha256(path),
        "schema_or_version": expected.get("schema_or_version"),
    }


def expected_receipt(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        raise ValueError("ROW_OBJECT_REQUIRED")
    authority = _producer_authority()
    if authority.get("schema") != EXPECTED_AUTHORITY_SCHEMA:
        raise ValueError("PRODUCER_AUTHORITY_SCHEMA_MISMATCH")
    expected_fences = {
        "canonical_truth_allowed": False,
        "direct_effect_authority": False,
        "training_eligible": False,
        "accepted_dataset_tokens_minted": 0,
        "training_credit_minted": 0,
    }
    if authority.get("authority_fences") != expected_fences:
        raise ValueError("PRODUCER_AUTHORITY_FENCES_INVALID")

    producer_binding_authority = authority.get("producer")
    if not isinstance(producer_binding_authority, dict):
        raise ValueError("PRODUCER_BINDING_REQUIRED")
    producer_path = _resolve_repo_file(
        producer_binding_authority.get("repo_path"),
        missing_code="PRODUCER_FILE_REQUIRED",
        escape_code="PRODUCER_PATH_ESCAPES_REPO",
    )
    actual_producer_sha = _source_sha256(producer_path)
    if actual_producer_sha != producer_binding_authority.get("source_sha256"):
        raise ValueError("PRODUCER_SOURCE_SHA256_MISMATCH")
    producer = _load_module(producer_path, "trigger2_trusted_discriminator_producer")
    if getattr(producer, "PRODUCER_SCHEMA", None) != producer_binding_authority.get(
        "producer_schema_or_version"
    ):
        raise ValueError("PRODUCER_SCHEMA_MISMATCH")

    ordering_binding = _ordering_binding(authority)

    case_id = row.get("generation_case_id_evaluator_only")
    cases = authority.get("allowed_cases")
    if not isinstance(cases, dict) or case_id not in cases:
        raise ValueError("DISCRIMINATOR_PRODUCER_CASE_NOT_AUTHORIZED")
    case = cases[case_id]
    policy = case.get("policy")
    if not isinstance(policy, dict):
        raise ValueError("DISCRIMINATOR_POLICY_REQUIRED")
    if _digest(policy) != case.get("policy_sha256"):
        raise ValueError("DISCRIMINATOR_POLICY_DIGEST_MISMATCH")

    trusted, generator_binding = _trusted_subjects(case_id, authority)
    if row.get("generation_parameters_evaluator_only") != trusted["parameters"]:
        raise ValueError("ROW_GENERATION_PARAMETERS_NOT_TRUSTED")
    if row.get("formal_task_world_evaluator_only") != trusted["world"]:
        raise ValueError("ROW_WORLD_NOT_TRUSTED_GENERATOR_OUTPUT")
    if row.get("hyperposition_state_before_evaluator_only") != trusted["state_before"]:
        raise ValueError("ROW_STATE_BEFORE_NOT_TRUSTED_GENERATOR_OUTPUT")
    if row.get("synthetic_test_event_evaluator_only") != trusted["event"]:
        raise ValueError("ROW_EVENT_NOT_TRUSTED_GENERATOR_OUTPUT")

    producer_binding = {
        "repo_path": producer_binding_authority.get("repo_path"),
        "source_sha256": actual_producer_sha,
        "producer_schema_or_version": producer_binding_authority.get("producer_schema_or_version"),
    }
    receipt = producer.produce(
        trusted["world"],
        trusted["state_before"],
        trusted["event"],
        case_id=case_id,
        policy=deepcopy(policy),
        producer_binding=deepcopy(producer_binding),
        labeler_binding=deepcopy(ordering_binding),
    )
    return {
        "receipt": receipt,
        "producer_binding": producer_binding,
        "ordering_semantics_binding": ordering_binding,
        "generator_binding": generator_binding,
        "policy_sha256": case.get("policy_sha256"),
    }


def adjudicate(row: Any, *, generation_result: Any = None) -> dict[str, Any]:
    failures: list[str] = []
    if generation_result is not None:
        if not isinstance(generation_result, dict) or generation_result.get("pass") is not True:
            failures.append("UPSTREAM_GENERATION_PROVENANCE_PASS_REQUIRED")

    expected = None
    try:
        expected = expected_receipt(row)
    except Exception as exc:
        failures.append(
            "TRUSTED_PRODUCER_RECOMPUTE_FAILED:" + type(exc).__name__ + ":" + str(exc)
        )

    claimed = None
    if isinstance(row, dict):
        receipts = row.get("discriminator_execution_receipts_evaluator_only")
        if not isinstance(receipts, list):
            failures.append("DISCRIMINATOR_RECEIPTS_LIST_REQUIRED")
        else:
            event_id = (
                row.get("synthetic_test_event_evaluator_only", {}).get("event_id")
                if isinstance(row.get("synthetic_test_event_evaluator_only"), dict)
                else None
            )
            matches = [
                receipt
                for receipt in receipts
                if isinstance(receipt, dict) and receipt.get("event_id") == event_id
            ]
            if len(matches) != 1:
                failures.append("PINNED_EVENT_REQUIRES_EXACTLY_ONE_DISCRIMINATOR_RECEIPT")
            else:
                claimed = matches[0]

    if isinstance(expected, dict):
        expected_receipt_value = expected["receipt"]
        if expected_receipt_value.get("admissible") is not True:
            failures.append("TRUSTED_PRODUCER_DID_NOT_DERIVE_ADMISSIBLE")
        if expected_receipt_value.get("executed") is not True:
            failures.append("TRUSTED_PRODUCER_DID_NOT_EXECUTE")
        if claimed != expected_receipt_value:
            failures.append("DISCRIMINATOR_RECEIPT_NOT_EXACT_TRUSTED_PRODUCER_OUTPUT")

    return _result(
        failures,
        expected_discriminator_receipt=(expected["receipt"] if isinstance(expected, dict) else None),
        producer_binding=(expected["producer_binding"] if isinstance(expected, dict) else None),
        ordering_semantics_binding=(
            expected["ordering_semantics_binding"] if isinstance(expected, dict) else None
        ),
        generator_binding=(expected["generator_binding"] if isinstance(expected, dict) else None),
        policy_sha256=(expected["policy_sha256"] if isinstance(expected, dict) else None),
        trusted_producer_invocation_performed=isinstance(expected, dict),
        synthetic_noncanonical=True,
    )


if __name__ == "__main__":
    print(
        {
            "schema": SCHEMA,
            "status": "SOURCE_ONLY_PINNED_PILOT_PRODUCER_AUTH",
            "training_credit_minted": 0,
        }
    )
