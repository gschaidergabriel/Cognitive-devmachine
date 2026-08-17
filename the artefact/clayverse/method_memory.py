from __future__ import annotations

import json
import math
from typing import Any


METHOD_KINDS = frozenset(
    {
        "framework_candidate",
        "framework",
        "heuristic_candidate",
        "heuristic",
        "failure_pattern",
        "counterexample",
        "method_receipt",
    }
)
CANDIDATE_KINDS = frozenset({"framework_candidate", "heuristic_candidate"})
REUSABLE_KINDS = frozenset({"framework_candidate", "framework", "heuristic_candidate", "heuristic"})
PROMOTED_KINDS = frozenset({"framework", "heuristic"})
LIFECYCLE_STATUSES = frozenset({"CANDIDATE", "PROMOTED", "DEMOTED", "RETIRED"})
RECEIPT_ACTIONS = frozenset({"ABSTRACT", "PROMOTE", "DEMOTE", "RETIRE", "USE", "EVALUATE"})


class MethodMemoryValidationError(ValueError):
    """Raised when method memory is malformed or crosses its epistemic contract."""


def is_method_kind(kind: str) -> bool:
    return kind in METHOD_KINDS


def _fail(field: str, detail: str) -> None:
    raise MethodMemoryValidationError(f"{field}: {detail}")


def _nonempty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        _fail(field, "must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field: str, *, nonempty: bool = False) -> list[str]:
    if not isinstance(value, list):
        _fail(field, "must be a list")
    if nonempty and not value:
        _fail(field, "must not be empty")
    result: list[str] = []
    for item in value:
        result.append(_nonempty_string(item, field))
    return result


def _nonnegative_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        _fail(field, "must be a non-negative integer")
    return value


def _finite_number(value: Any, field: str, *, minimum: float | None = None, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        _fail(field, "must be a finite number")
    number = float(value)
    if not math.isfinite(number):
        _fail(field, "must be finite")
    if minimum is not None and number < minimum:
        _fail(field, f"must be >= {minimum}")
    if maximum is not None and number > maximum:
        _fail(field, f"must be <= {maximum}")
    return number


def _json_safe(value: Any, field: str) -> None:
    try:
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise MethodMemoryValidationError(f"{field}: must be deterministic JSON data") from exc


def _problem_signature(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or not value:
        _fail("problem_signature", "must be a non-empty object")
    for key in value:
        _nonempty_string(key, "problem_signature key")
    _json_safe(value, "problem_signature")
    return value


def _status(record: dict[str, Any], kind: str) -> str:
    status = _nonempty_string(record.get("status"), "status").upper()
    if status not in LIFECYCLE_STATUSES:
        _fail("status", f"must be one of {sorted(LIFECYCLE_STATUSES)}")
    if kind in CANDIDATE_KINDS and status != "CANDIDATE":
        _fail("status", f"{kind} must remain CANDIDATE")
    if kind in PROMOTED_KINDS and status == "CANDIDATE":
        _fail("status", f"{kind} cannot carry CANDIDATE status")
    return status


def _validate_common_method_record(kind: str, record: dict[str, Any]) -> None:
    _nonempty_string(record.get("name"), "name")
    _problem_signature(record.get("problem_signature"))
    _string_list(record.get("source_episode_ids"), "source_episode_ids", nonempty=True)
    _string_list(record.get("supporting_memory_ids"), "supporting_memory_ids")
    _string_list(record.get("counterexample_memory_ids"), "counterexample_memory_ids")
    version = record.get("abstraction_version")
    if isinstance(version, int) and not isinstance(version, bool):
        if version < 1:
            _fail("abstraction_version", "must be >= 1")
    else:
        _nonempty_string(version, "abstraction_version")
    _status(record, kind)


def _validate_reusable(kind: str, record: dict[str, Any]) -> None:
    _validate_common_method_record(kind, record)
    _string_list(record.get("preconditions"), "preconditions")
    goal_shape = record.get("goal_shape")
    if not isinstance(goal_shape, (str, dict)):
        _fail("goal_shape", "must be a non-empty string or object")
    if isinstance(goal_shape, str):
        _nonempty_string(goal_shape, "goal_shape")
    else:
        if not goal_shape:
            _fail("goal_shape", "must not be empty")
        _json_safe(goal_shape, "goal_shape")
    _string_list(record.get("method_steps"), "method_steps", nonempty=True)
    _string_list(record.get("invariants"), "invariants")
    _string_list(record.get("expected_observations"), "expected_observations")
    _string_list(record.get("falsifiers"), "falsifiers", nonempty=True)
    _string_list(record.get("failure_modes"), "failure_modes")
    _string_list(record.get("scope_limits"), "scope_limits", nonempty=True)
    support_count = _nonnegative_int(record.get("support_count"), "support_count")
    success_count = _nonnegative_int(record.get("success_count"), "success_count")
    failure_count = _nonnegative_int(record.get("failure_count"), "failure_count")
    if success_count + failure_count > support_count:
        _fail("support_count", "must cover success_count + failure_count")
    _finite_number(record.get("calibration"), "calibration", minimum=0.0, maximum=1.0)
    last_validated = record.get("last_validated_at")
    if kind in PROMOTED_KINDS:
        _finite_number(last_validated, "last_validated_at", minimum=0.0)
    elif last_validated is not None:
        _finite_number(last_validated, "last_validated_at", minimum=0.0)


def _validate_failure_pattern(record: dict[str, Any]) -> None:
    _validate_common_method_record("failure_pattern", record)
    _string_list(record.get("conditions"), "conditions", nonempty=True)
    _nonempty_string(record.get("failure_mode"), "failure_mode")
    _string_list(record.get("scope_limits"), "scope_limits", nonempty=True)
    _string_list(record.get("failed_method_ids"), "failed_method_ids")
    last_validated = record.get("last_validated_at")
    if last_validated is not None:
        _finite_number(last_validated, "last_validated_at", minimum=0.0)


def _validate_counterexample(record: dict[str, Any]) -> None:
    _validate_common_method_record("counterexample", record)
    _string_list(record.get("conditions"), "conditions", nonempty=True)
    _nonempty_string(record.get("contradiction"), "contradiction")
    _string_list(record.get("target_method_ids"), "target_method_ids", nonempty=True)
    last_validated = record.get("last_validated_at")
    if last_validated is not None:
        _finite_number(last_validated, "last_validated_at", minimum=0.0)


def _validate_receipt(record: dict[str, Any]) -> None:
    action = _nonempty_string(record.get("action"), "action").upper()
    if action not in RECEIPT_ACTIONS:
        _fail("action", f"must be one of {sorted(RECEIPT_ACTIONS)}")
    _nonempty_string(record.get("method_memory_id"), "method_memory_id")
    _nonempty_string(record.get("causal_id"), "causal_id")
    _nonempty_string(record.get("episode_id"), "episode_id")
    generation = record.get("generation")
    if isinstance(generation, bool) or not isinstance(generation, int) or generation < 1:
        _fail("generation", "must be an integer >= 1")
    _nonempty_string(record.get("result"), "result")
    _json_safe(record.get("details", {}), "details")


def validate_method_record(kind: str, record: Any) -> dict[str, Any]:
    """Validate one durable method record without granting it factual authority.

    The validator checks structure only. Promotion truth, access rights, and factual
    correctness remain outside this module and must be established by their own
    evidence/authority paths.
    """
    if kind not in METHOD_KINDS:
        raise MethodMemoryValidationError(f"unsupported method-memory kind: {kind!r}")
    if not isinstance(record, dict):
        raise MethodMemoryValidationError("record must be an object")
    if kind in REUSABLE_KINDS:
        _validate_reusable(kind, record)
    elif kind == "failure_pattern":
        _validate_failure_pattern(record)
    elif kind == "counterexample":
        _validate_counterexample(record)
    else:
        _validate_receipt(record)
    _json_safe(record, "record")
    return record


def canonical_method_json(kind: str, record: Any) -> str:
    validate_method_record(kind, record)
    return json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def decode_method_json(kind: str, value: str) -> dict[str, Any]:
    if kind not in METHOD_KINDS:
        raise MethodMemoryValidationError(f"unsupported method-memory kind: {kind!r}")
    try:
        record = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise MethodMemoryValidationError("stored method memory is not valid JSON") from exc
    return validate_method_record(kind, record)
