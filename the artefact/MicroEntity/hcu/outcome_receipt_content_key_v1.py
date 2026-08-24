#!/usr/bin/env python3
"""Acyclic content-key plumbing for EntityOS/HCU J-Space outcome receipts.

This module is NOT a dataset-admission, truth, reward, effect, or state authority.
It only defines the deterministic content key needed to avoid the current hash cycle:

    OutcomeReceipt(full bytes) -> TrainingTrace SHA -> OutcomeReceipt(full bytes)

The content key deliberately excludes exactly the late-bound ``training_trace_sha256``
back-reference while binding every other currently admitted outcome-family field.  The
canonical dataset-admission gate must still verify the final receipt's exact training-trace
back-reference and causal fields before granting any dataset credit.
"""
from __future__ import annotations

import hashlib
from typing import Any, Mapping

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

CONTENT_KEY_SCHEMA = "ENTITYOS_HCU_JSPACE_OUTCOME_RECEIPT_CONTENT_KEY/v1"
CREDIT_LABELS = frozenset({"UNKNOWN", "POSITIVE", "NEGATIVE", "NEUTRAL"})
_CONTENT_FIELDS = frozenset(
    {
        "status",
        "credit_label",
        "transition_trace_sha256",
        "generation",
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
        "cell_id",
        "role",
    }
)
_FINAL_FIELDS = frozenset(set(_CONTENT_FIELDS) | {"training_trace_sha256"})


class OutcomeReceiptContentKeyError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OutcomeReceiptContentKeyError(f"{field}:MAPPING_REQUIRED")
    return value


def _canonical_text(value: Any, field: str, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value:
        raise OutcomeReceiptContentKeyError(f"{field}:NONEMPTY_STRING_REQUIRED")
    if value != value.strip():
        raise OutcomeReceiptContentKeyError(f"{field}:NONCANONICAL_TEXT")
    if len(value) > max_len:
        raise OutcomeReceiptContentKeyError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _canonical_text(value, field, 64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise OutcomeReceiptContentKeyError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise OutcomeReceiptContentKeyError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str = "generation") -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise OutcomeReceiptContentKeyError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise OutcomeReceiptContentKeyError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _field_set(receipt: Mapping[str, Any]) -> frozenset[str]:
    fields = frozenset(receipt)
    if fields not in {_CONTENT_FIELDS, _FINAL_FIELDS}:
        raise OutcomeReceiptContentKeyError("OUTCOME_RECEIPT_FIELD_SET_MISMATCH")
    return fields


def outcome_receipt_content_material(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Return canonical content-key material from a provisional or final receipt.

    The provisional form omits ``training_trace_sha256``; the final form contains it.
    Both yield the same content material.  No other omitted or extra field is accepted.
    """
    receipt = _mapping(receipt, "outcome_receipt")
    _field_set(receipt)

    status = _canonical_text(receipt.get("status"), "outcome_receipt.status", 32).upper()
    if status != "VERIFIED":
        raise OutcomeReceiptContentKeyError("OUTCOME_RECEIPT_NOT_VERIFIED")
    credit = _canonical_text(receipt.get("credit_label"), "outcome_receipt.credit_label", 32).upper()
    if credit not in CREDIT_LABELS:
        raise OutcomeReceiptContentKeyError("OUTCOME_CREDIT_LABEL_UNSUPPORTED")

    material = {
        "schema": CONTENT_KEY_SCHEMA,
        "status": status,
        "credit_label": credit,
        "transition_trace_sha256": _sha256(
            receipt.get("transition_trace_sha256"),
            "outcome_receipt.transition_trace_sha256",
        ),
        "generation": _generation(receipt.get("generation"), "outcome_receipt.generation"),
        "entry_event_sha256": _sha256(
            receipt.get("entry_event_sha256"),
            "outcome_receipt.entry_event_sha256",
        ),
        "entry_admission_sha256": _sha256(
            receipt.get("entry_admission_sha256"),
            "outcome_receipt.entry_admission_sha256",
        ),
        "route_decision_sha256": _sha256(
            receipt.get("route_decision_sha256"),
            "outcome_receipt.route_decision_sha256",
        ),
        "grid_plan_sha256": _sha256(
            receipt.get("grid_plan_sha256"),
            "outcome_receipt.grid_plan_sha256",
        ),
        "cell_id": _canonical_text(receipt.get("cell_id"), "outcome_receipt.cell_id", 256),
        "role": _canonical_text(receipt.get("role"), "outcome_receipt.role", 256),
    }
    return material


def outcome_receipt_content_key(receipt: Mapping[str, Any]) -> str:
    """Return the RFC8785/JCS content key, excluding only the training-trace back-reference."""
    material = outcome_receipt_content_material(receipt)
    try:
        return hashlib.sha256(canonicalize(material)).hexdigest()
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise OutcomeReceiptContentKeyError("OUTCOME_CONTENT_KEY_CANONICALIZATION_FAILED") from exc


def finalize_outcome_receipt(
    provisional_receipt: Mapping[str, Any],
    training_trace_sha256: str,
) -> dict[str, Any]:
    """Add the late training-trace back-reference without changing the content key."""
    provisional_receipt = _mapping(provisional_receipt, "provisional_outcome_receipt")
    if frozenset(provisional_receipt) != _CONTENT_FIELDS:
        raise OutcomeReceiptContentKeyError("PROVISIONAL_OUTCOME_RECEIPT_FIELD_SET_MISMATCH")
    outcome_receipt_content_material(provisional_receipt)
    final_receipt = dict(provisional_receipt)
    final_receipt["training_trace_sha256"] = _sha256(
        training_trace_sha256,
        "training_trace_sha256",
    )
    outcome_receipt_content_material(final_receipt)
    return final_receipt


def verify_outcome_receipt_content_key(
    receipt: Mapping[str, Any],
    claimed_content_key: str,
    *,
    expected_training_trace_sha256: str | None = None,
) -> None:
    """Verify content-key identity and, for final receipts, the exact late back-reference.

    A content-key match alone is intentionally insufficient for final admission.  When the
    canonical dataset gate verifies a final receipt it MUST supply the expected training SHA.
    """
    receipt = _mapping(receipt, "outcome_receipt")
    claimed = _sha256(claimed_content_key, "claimed_content_key")
    observed = outcome_receipt_content_key(receipt)
    if observed != claimed:
        raise OutcomeReceiptContentKeyError("OUTCOME_RECEIPT_CONTENT_KEY_MISMATCH")

    if expected_training_trace_sha256 is None:
        return
    if frozenset(receipt) != _FINAL_FIELDS:
        raise OutcomeReceiptContentKeyError("FINAL_OUTCOME_RECEIPT_REQUIRED")
    expected = _sha256(expected_training_trace_sha256, "expected_training_trace_sha256")
    actual = _sha256(receipt.get("training_trace_sha256"), "outcome_receipt.training_trace_sha256")
    if actual != expected:
        raise OutcomeReceiptContentKeyError("OUTCOME_TRAINING_TRACE_MISMATCH")
