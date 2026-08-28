#!/usr/bin/env python3
"""Deterministic source-bound CompletionGate validator for Frankenstein 2.0.

This module is deliberately NOT an effect executor, canonical truth store, or
CompletionGate authority. It is a pure validator primitive intended to harden
the existing effect lifecycle by accepting only explicitly typed success
receipts that all bind the same invocation/source/generation lineage.

Runtime/effect/completion credit requires a caller that actually wires and
executes this validator at the authoritative boundary.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
from typing import Any

SCHEMA = "FRANKENSTEIN2_COMPLETION_VERIFIER/v2"
ADMISSION_SCHEMA = "FRANKENSTEIN2_ADMISSION_RECEIPT/v2"
ENFORCEMENT_SCHEMA = "FRANKENSTEIN2_ENFORCEMENT_RECEIPT/v2"
EXECUTION_SCHEMA = "FRANKENSTEIN2_EXECUTION_RECEIPT/v2"
WORLD_SCHEMA = "FRANKENSTEIN2_WORLD_VERIFICATION_RECEIPT/v2"
REENTRY_SCHEMA = "FRANKENSTEIN2_RESULT_REENTRY_RECEIPT/v2"
TEST_SCHEMA = "FRANKENSTEIN2_TEST_RECEIPT/v2"

SUCCESS_ADMISSION = frozenset({"ALLOW"})
SUCCESS_ENFORCEMENT = frozenset({"ALLOW"})
SUCCESS_EXECUTION = frozenset({"SUCCEEDED"})
SUCCESS_WORLD = frozenset({"SUCCEEDED"})
SUCCESS_TEST = frozenset({"PASS"})
UNIQUE_DUPLICATE_STATE = "UNIQUE"


def _cj(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_cj(value).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ExpectedInvocation:
    invocation_id: str
    request_digest: str
    task_id: str
    turn_id: str
    causal_id: str
    generation: int
    source_digest: str


@dataclass(frozen=True)
class AdmissionReceipt:
    schema: str
    invocation_id: str
    request_digest: str
    generation: int
    decision: str


@dataclass(frozen=True)
class EnforcementReceipt:
    schema: str
    invocation_id: str
    request_digest: str
    generation: int
    decision: str
    dispatch_permitted: bool
    boundary_id: str


@dataclass(frozen=True)
class ExecutionReceipt:
    schema: str
    invocation_id: str
    request_digest: str
    generation: int
    source_digest: str
    executable_id: str
    environment_id: str
    status: str
    exit_code: int
    result_digest: str
    duplicate_state: str


@dataclass(frozen=True)
class WorldVerificationReceipt:
    schema: str
    invocation_id: str
    generation: int
    result_digest: str
    outcome: str
    evidence_digest: str | None


@dataclass(frozen=True)
class ResultReentryReceipt:
    schema: str
    invocation_id: str
    generation: int
    result_digest: str
    task_id: str
    turn_id: str
    causal_id: str


@dataclass(frozen=True)
class TestReceipt:
    schema: str
    invocation_id: str
    generation: int
    source_digest: str
    status: str
    assertions_total: int
    assertions_passed: int
    test_result_digest: str
    # These bindings are append-only to preserve construction compatibility while
    # making legacy/unbound receipts fail closed whenever a TestReceipt is supplied.
    request_digest: str = ""
    result_digest: str = ""
    test_plan_digest: str = ""
    executable_id: str = ""
    environment_id: str = ""


@dataclass(frozen=True)
class CompletionDecision:
    schema: str
    closable: bool
    reasons: tuple[str, ...]
    validation_digest: str | None


def _basic_expected_errors(expected: ExpectedInvocation) -> list[str]:
    reasons: list[str] = []
    if not expected.invocation_id:
        reasons.append("MISSING_INVOCATION_ID")
    if not expected.request_digest:
        reasons.append("MISSING_REQUEST_DIGEST")
    if not expected.task_id or not expected.turn_id or not expected.causal_id:
        reasons.append("MISSING_CAUSAL_LINEAGE")
    if expected.generation < 0:
        reasons.append("INVALID_GENERATION")
    if not expected.source_digest:
        reasons.append("MISSING_SOURCE_DIGEST")
    return reasons


def _bind_identity(
    *,
    expected: ExpectedInvocation,
    label: str,
    invocation_id: str,
    generation: int,
) -> list[str]:
    reasons: list[str] = []
    if invocation_id != expected.invocation_id:
        reasons.append(f"{label}_INVOCATION_MISMATCH")
    if generation != expected.generation:
        reasons.append(f"{label}_GENERATION_MISMATCH")
    return reasons


def verify_completion(
    expected: ExpectedInvocation,
    *,
    admission: AdmissionReceipt,
    enforcement: EnforcementReceipt,
    execution: ExecutionReceipt,
    world: WorldVerificationReceipt,
    reentry: ResultReentryReceipt,
    test_receipt: TestReceipt | None = None,
    require_test_receipt: bool = False,
    require_world_evidence: bool = True,
) -> CompletionDecision:
    """Fail closed unless every supplied receipt is an explicitly typed bound success.

    The returned digest attests only to this deterministic validation decision.
    It is not runtime evidence and cannot by itself mint canonical completion.
    """
    reasons = _basic_expected_errors(expected)

    if admission.schema != ADMISSION_SCHEMA:
        reasons.append("ADMISSION_SCHEMA_MISMATCH")
    if enforcement.schema != ENFORCEMENT_SCHEMA:
        reasons.append("ENFORCEMENT_SCHEMA_MISMATCH")
    if execution.schema != EXECUTION_SCHEMA:
        reasons.append("EXECUTION_SCHEMA_MISMATCH")
    if world.schema != WORLD_SCHEMA:
        reasons.append("WORLD_SCHEMA_MISMATCH")
    if reentry.schema != REENTRY_SCHEMA:
        reasons.append("REENTRY_SCHEMA_MISMATCH")
    if test_receipt is not None and test_receipt.schema != TEST_SCHEMA:
        reasons.append("TEST_SCHEMA_MISMATCH")

    reasons += _bind_identity(expected=expected, label="ADMISSION", invocation_id=admission.invocation_id, generation=admission.generation)
    reasons += _bind_identity(expected=expected, label="ENFORCEMENT", invocation_id=enforcement.invocation_id, generation=enforcement.generation)
    reasons += _bind_identity(expected=expected, label="EXECUTION", invocation_id=execution.invocation_id, generation=execution.generation)
    reasons += _bind_identity(expected=expected, label="WORLD", invocation_id=world.invocation_id, generation=world.generation)
    reasons += _bind_identity(expected=expected, label="REENTRY", invocation_id=reentry.invocation_id, generation=reentry.generation)
    if test_receipt is not None:
        reasons += _bind_identity(expected=expected, label="TEST", invocation_id=test_receipt.invocation_id, generation=test_receipt.generation)

    if admission.request_digest != expected.request_digest:
        reasons.append("ADMISSION_REQUEST_MISMATCH")
    if enforcement.request_digest != expected.request_digest:
        reasons.append("ENFORCEMENT_REQUEST_MISMATCH")
    if execution.request_digest != expected.request_digest:
        reasons.append("EXECUTION_REQUEST_MISMATCH")

    if admission.decision not in SUCCESS_ADMISSION:
        reasons.append(f"ADMISSION_NOT_SUCCESS:{admission.decision}")
    if enforcement.decision not in SUCCESS_ENFORCEMENT or not enforcement.dispatch_permitted:
        reasons.append("ENFORCEMENT_NOT_SUCCESS")
    if not enforcement.boundary_id:
        reasons.append("MISSING_ENFORCEMENT_BOUNDARY")

    if execution.source_digest != expected.source_digest:
        reasons.append("EXECUTION_SOURCE_DRIFT")
    if not execution.executable_id or not execution.environment_id:
        reasons.append("MISSING_EXECUTION_PROVENANCE")
    if execution.status not in SUCCESS_EXECUTION:
        reasons.append(f"EXECUTION_NOT_SUCCESS:{execution.status}")
    if execution.exit_code != 0:
        reasons.append(f"EXECUTION_EXIT_NONZERO:{execution.exit_code}")
    if not execution.result_digest:
        reasons.append("MISSING_EXECUTION_RESULT_DIGEST")
    if execution.duplicate_state != UNIQUE_DUPLICATE_STATE:
        reasons.append(f"EXECUTION_DUPLICATE_UNRESOLVED:{execution.duplicate_state}")

    if world.result_digest != execution.result_digest:
        reasons.append("WORLD_RESULT_MISMATCH")
    if world.outcome not in SUCCESS_WORLD:
        reasons.append(f"WORLD_NOT_SUCCESS:{world.outcome}")
    if require_world_evidence and not world.evidence_digest:
        reasons.append("MISSING_WORLD_EVIDENCE")

    if reentry.result_digest != execution.result_digest:
        reasons.append("REENTRY_RESULT_MISMATCH")
    if (
        reentry.task_id != expected.task_id
        or reentry.turn_id != expected.turn_id
        or reentry.causal_id != expected.causal_id
    ):
        reasons.append("REENTRY_CAUSAL_LINEAGE_MISMATCH")

    if require_test_receipt and test_receipt is None:
        reasons.append("MISSING_REQUIRED_TEST_RECEIPT")
    if test_receipt is not None:
        if test_receipt.source_digest != expected.source_digest:
            reasons.append("TEST_SOURCE_DRIFT")
        if test_receipt.request_digest != expected.request_digest:
            reasons.append("TEST_REQUEST_MISMATCH")
        if test_receipt.result_digest != execution.result_digest:
            reasons.append("TEST_RESULT_TRANSPLANT")
        if not test_receipt.test_plan_digest:
            reasons.append("MISSING_TEST_PLAN_DIGEST")
        if not test_receipt.executable_id or not test_receipt.environment_id:
            reasons.append("MISSING_TEST_PROVENANCE")
        if test_receipt.status not in SUCCESS_TEST:
            reasons.append(f"TEST_NOT_SUCCESS:{test_receipt.status}")
        if test_receipt.assertions_total <= 0:
            reasons.append("TEST_ZERO_OR_NEGATIVE_ASSERTIONS")
        elif test_receipt.assertions_passed != test_receipt.assertions_total:
            reasons.append("TEST_ASSERTION_COUNT_MISMATCH")
        if not test_receipt.test_result_digest:
            reasons.append("MISSING_TEST_RESULT_DIGEST")

    unique_reasons = tuple(dict.fromkeys(reasons))
    closable = not unique_reasons
    validation_digest = None
    if closable:
        payload = {
            "schema": SCHEMA,
            "expected": asdict(expected),
            "admission": asdict(admission),
            "enforcement": asdict(enforcement),
            "execution": asdict(execution),
            "world": asdict(world),
            "reentry": asdict(reentry),
            "test_receipt": None if test_receipt is None else asdict(test_receipt),
            "require_test_receipt": bool(require_test_receipt),
            "require_world_evidence": bool(require_world_evidence),
        }
        validation_digest = _digest(payload)
    return CompletionDecision(SCHEMA, closable, unique_reasons, validation_digest)
