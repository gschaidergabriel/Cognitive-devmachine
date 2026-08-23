#!/usr/bin/env python3
"""Launch-facing admission bridge for the EntityOS/HCU J-Space training dataset.

This module deliberately owns no new dataset semantics. The existing
``compile_jspace_training_dataset_v1`` module remains the deterministic JSONL serializer,
and ``jspace_dataset_admission_gate_v1`` remains the evidence-admission authority. This
bridge composes them so a launch-facing caller cannot obtain serious-training rows from a
self-consistent but unadmitted training trace.

Direct use of the serializer is therefore component/bootstrap work only; it is not
sufficient evidence for the owner-authorized one-shot training launch.
"""
from __future__ import annotations

from dataclasses import asdict
from typing import Any, Iterable, Mapping

try:
    from .compile_jspace_training_dataset_v1 import compile_traces
    from .jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )
except ImportError:
    from compile_jspace_training_dataset_v1 import compile_traces
    from jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )

BRIDGE_SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_DATASET_ADMISSION_BRIDGE/v1"


class JSpaceTrainingDatasetAdmissionBridgeError(ValueError):
    pass


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise JSpaceTrainingDatasetAdmissionBridgeError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise JSpaceTrainingDatasetAdmissionBridgeError(f"{field}:NONEMPTY_STRING_REQUIRED")
    return value.strip()


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise JSpaceTrainingDatasetAdmissionBridgeError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _verify_admission_echo(
    admission: DatasetAdmission,
    training_trace: Mapping[str, Any],
    transition_trace: Mapping[str, Any],
) -> None:
    if not isinstance(admission, DatasetAdmission) or admission.schema != ADMISSION_SCHEMA:
        raise JSpaceTrainingDatasetAdmissionBridgeError("DATASET_ADMISSION_REQUIRED")
    if admission.training_trace_sha256 != _sha256(
        training_trace.get("trace_sha256"), "training_trace.trace_sha256"
    ):
        raise JSpaceTrainingDatasetAdmissionBridgeError("ADMISSION_TRAINING_TRACE_MISMATCH")
    if admission.transition_trace_sha256 != _sha256(
        transition_trace.get("trace_sha256"), "transition_trace.trace_sha256"
    ):
        raise JSpaceTrainingDatasetAdmissionBridgeError("ADMISSION_TRANSITION_TRACE_MISMATCH")


def compile_admitted_traces(
    trace_pairs: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
    admitted_transition_traces: Mapping[str, Mapping[str, Any]],
    admitted_prototype_traces: Mapping[str, Mapping[str, Any]],
    admitted_outcome_receipts: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Gate every training/transition pair before delegating to the serializer.

    The return shape keeps ``splits`` separate from the admission receipts so a later
    Together preflight can hash-bind both. A duplicate exact pair is idempotent. Reusing
    one training trace with a different transition is rejected rather than silently
    selecting one causal family.
    """
    accepted: list[dict[str, Any]] = []
    admissions: list[dict[str, Any]] = []
    seen: dict[str, str] = {}

    for ordinal, pair in enumerate(trace_pairs):
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise JSpaceTrainingDatasetAdmissionBridgeError(
                f"trace_pairs[{ordinal}]:TRAINING_TRANSITION_PAIR_REQUIRED"
            )
        training_trace = dict(_mapping(pair[0], f"trace_pairs[{ordinal}].training_trace"))
        transition_trace = dict(_mapping(pair[1], f"trace_pairs[{ordinal}].transition_trace"))
        training_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")
        transition_sha = _sha256(transition_trace.get("trace_sha256"), "transition_trace.trace_sha256")

        prior_transition = seen.get(training_sha)
        if prior_transition is not None:
            if prior_transition != transition_sha:
                raise JSpaceTrainingDatasetAdmissionBridgeError(
                    "TRAINING_TRACE_BOUND_TO_MULTIPLE_TRANSITIONS"
                )
            continue

        try:
            admission = admit_for_training_dataset(
                training_trace,
                transition_trace,
                admitted_training_traces=admitted_training_traces,
                admitted_transition_traces=admitted_transition_traces,
                admitted_prototype_traces=admitted_prototype_traces,
                admitted_outcome_receipts=admitted_outcome_receipts,
            )
        except JSpaceDatasetAdmissionError as exc:
            raise JSpaceTrainingDatasetAdmissionBridgeError(
                f"DATASET_ADMISSION_REJECTED:{exc}"
            ) from exc

        _verify_admission_echo(admission, training_trace, transition_trace)
        seen[training_sha] = transition_sha
        accepted.append(training_trace)
        admissions.append(asdict(admission))

    if not accepted:
        raise JSpaceTrainingDatasetAdmissionBridgeError("NO_ADMITTED_TRAINING_TRACES")

    return {
        "schema": BRIDGE_SCHEMA,
        "splits": compile_traces(accepted),
        "admissions": admissions,
    }
