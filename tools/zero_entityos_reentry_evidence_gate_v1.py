#!/usr/bin/env python3
"""Fail-closed workspace re-entry evidence gate.

Separates packet/re-entry presence from measured downstream causal use.
This gate cannot grant model-internal or Global J-Space causal credit.
"""
from __future__ import annotations

import copy
from typing import Any

REENTRY_SCHEMA = "WORKSPACE_REENTRY/v1"
MEASUREMENT_SCHEMA = "WORKSPACE_REENTRY_CAUSAL_MEASUREMENT/v1"
ALLOWED_CHANGE = {"TRUE", "FALSE", "UNKNOWN"}


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
    measurement: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a fail-closed evidence view of a WORKSPACE_REENTRY packet.

    A stub/synthetic/unmeasured re-entry can prove packet binding and provenance,
    but it cannot prove downstream causal use. TRUE/FALSE is retained only for an
    explicitly bound matched observable-interface measurement.
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

    source_metadata = dict(source_metadata or {})
    out = copy.deepcopy(reentry)
    claimed = str(out.get("observed_downstream_change", "UNKNOWN"))
    need(claimed in ALLOWED_CHANGE, "OBSERVED_DOWNSTREAM_CHANGE_INVALID")

    if _is_synthetic(source_metadata):
        out["observed_downstream_change"] = "UNKNOWN"
        out["causal_credit"] = 0
        out["credit_scope"] = "PACKET_BINDING_ONLY"
        out["evidence_class"] = "SYNTHETIC_OR_STUBBED_NO_CAUSAL_MEASUREMENT"
        out["normalization_reason"] = (
            "SYNTHETIC_OR_STUBBED_SOURCE_CANNOT_OBSERVE_DOWNSTREAM_CAUSAL_CHANGE"
        )
        out["global_jspace_causal_credit"] = 0
        return out

    if measurement is None:
        out["observed_downstream_change"] = "UNKNOWN"
        out["causal_credit"] = 0
        out["credit_scope"] = "REENTRY_PRESENT_UNMEASURED"
        out["evidence_class"] = "NO_MATCHED_DOWNSTREAM_MEASUREMENT"
        out["normalization_reason"] = (
            "REENTRY_PRESENCE_OR_TEXT_COHERENCE_IS_NOT_CAUSAL_EVIDENCE"
        )
        out["global_jspace_causal_credit"] = 0
        return out

    need(isinstance(measurement, dict), "MEASUREMENT_OBJECT_REQUIRED")
    need(measurement.get("schema") == MEASUREMENT_SCHEMA, "MEASUREMENT_SCHEMA_MISMATCH")
    required = (
        "measurement_id",
        "source_result_id",
        "causal_event_id",
        "reentry_digest",
        "intervention_id",
        "matched_control_id",
        "metric_id",
        "baseline_value",
        "intervention_value",
        "observed_downstream_change",
        "off_target_result",
        "observation_surface",
    )
    for field in required:
        need(field in measurement, f"MEASUREMENT_FIELD_REQUIRED:{field}")

    need(
        measurement["source_result_id"] == reentry["source_result_id"],
        "MEASUREMENT_SOURCE_RESULT_MISMATCH",
    )
    need(
        measurement["causal_event_id"] == reentry["causal_event_id"],
        "MEASUREMENT_CAUSAL_EVENT_MISMATCH",
    )
    need(
        measurement["reentry_digest"] == reentry["reentry_digest"],
        "MEASUREMENT_REENTRY_DIGEST_MISMATCH",
    )
    need(bool(measurement["intervention_id"]), "INTERVENTION_ID_REQUIRED")
    need(bool(measurement["matched_control_id"]), "MATCHED_CONTROL_ID_REQUIRED")
    need(bool(measurement["metric_id"]), "METRIC_ID_REQUIRED")
    need(
        measurement["off_target_result"] in {"PASS", "FAIL", "UNKNOWN"},
        "OFF_TARGET_RESULT_INVALID",
    )
    change = measurement["observed_downstream_change"]
    need(change in ALLOWED_CHANGE, "MEASUREMENT_CHANGE_INVALID")

    out["observed_downstream_change"] = change
    out["measurement_id"] = measurement["measurement_id"]
    out["evidence_class"] = "MATCHED_OBSERVABLE_INTERFACE_MEASUREMENT"
    out["global_jspace_causal_credit"] = 0
    if change == "UNKNOWN":
        out["causal_credit"] = 0
        out["credit_scope"] = "OBSERVABLE_WORKSPACE_REENTRY_UNRESOLVED"
    else:
        out["causal_credit"] = 1
        out["credit_scope"] = "OBSERVABLE_WORKSPACE_REENTRY_ONLY"
    return out
