#!/usr/bin/env python3
"""Fail-closed adapter for current variable-grid workspace re-entry fixtures.

This utility is deliberately *not* a second causal-reentry contract. Positive
matched-control promotion belongs to GLOBAL_WORKSPACE_REENTRY_RECEIPT_CONTRACT/v1
(PR #1980 donor lane until fused). This adapter has one narrow job: prevent
stubbed, synthetic, or otherwise unmeasured WORKSPACE_REENTRY/v1 packets from
being reused as causal evidence merely because a fixture wrote TRUE.

It can grant packet-binding evidence only. It can never grant observable
workspace-reentry, Claude runtime, model-internal, or Global J-Space credit.
"""
from __future__ import annotations

import copy
from typing import Any

REENTRY_SCHEMA = "WORKSPACE_REENTRY/v1"
ALLOWED_CHANGE = {"TRUE", "FALSE", "UNKNOWN"}
POSITIVE_RECEIPT_CONTRACT = "GLOBAL_WORKSPACE_REENTRY_RECEIPT_CONTRACT/v1"


class ReentryEvidenceError(ValueError):
    pass


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ReentryEvidenceError(message)


def _is_synthetic(source_metadata: dict[str, Any]) -> bool:
    runtime_credit = source_metadata.get("runtime_credit")
    return bool(
        source_metadata.get("stubbed")
        or source_metadata.get("synthetic_fixture_return")
        or runtime_credit in {
            0,
            "SYNTHETIC_REFERENCE_FIXTURE_ONLY",
            "REFERENCE_FIXTURE_COMPONENT_ONLY",
        }
    )


def normalize_reentry_evidence(
    reentry: dict[str, Any],
    *,
    source_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Downgrade an unmeasured re-entry packet to its actual evidence ceiling.

    The raw claimed change is preserved for diagnosis, but the admitted evidence
    view is UNKNOWN/NONE. A future positive promotion must occur through the
    separate matched-control receipt contract, never through this adapter.
    """
    need(isinstance(reentry, dict), "REENTRY_OBJECT_REQUIRED")
    need(reentry.get("schema") == REENTRY_SCHEMA, "REENTRY_SCHEMA_MISMATCH")
    for field in (
        "source_result_id",
        "source_process_id",
        "causal_event_id",
        "from_workspace_epoch",
        "to_workspace_epoch",
        "reentry_payload_ref",
        "reentry_digest",
    ):
        need(field in reentry, f"REENTRY_FIELD_REQUIRED:{field}")

    claimed = str(reentry.get("observed_downstream_change", "UNKNOWN"))
    need(claimed in ALLOWED_CHANGE, "OBSERVED_DOWNSTREAM_CHANGE_INVALID")
    source_metadata = dict(source_metadata or {})

    out = copy.deepcopy(reentry)
    out["raw_observed_downstream_change"] = claimed
    out["observed_downstream_change"] = "UNKNOWN"
    out["causal_credit"] = "NONE"
    out["global_jspace_causal_credit"] = 0
    out["positive_promotion_contract"] = POSITIVE_RECEIPT_CONTRACT

    if _is_synthetic(source_metadata):
        out["credit_scope"] = "PACKET_BINDING_ONLY"
        out["evidence_class"] = "SYNTHETIC_OR_STUBBED_NO_CAUSAL_MEASUREMENT"
        out["normalization_reason"] = (
            "SYNTHETIC_OR_STUBBED_SOURCE_CANNOT_OBSERVE_DOWNSTREAM_CAUSAL_CHANGE"
        )
    else:
        out["credit_scope"] = "REENTRY_PRESENT_UNMEASURED"
        out["evidence_class"] = "MATCHED_CONTROL_RECEIPT_REQUIRED_FOR_POSITIVE_CREDIT"
        out["normalization_reason"] = (
            "REENTRY_PRESENCE_TEXT_COHERENCE_OR_UNBOUND_TRUE_FALSE_IS_NOT_CAUSAL_EVIDENCE"
        )

    return out
