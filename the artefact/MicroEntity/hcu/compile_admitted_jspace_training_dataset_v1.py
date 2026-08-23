#!/usr/bin/env python3
"""Fail-closed orchestration for serious EntityOS/HCU J-Space training data.

The lower-level ``compile_jspace_training_dataset_v1`` module can validate and render a
TrainingTrace into deterministic JSONL rows. That alone is deliberately insufficient for
serious training admission: a self-consistent trace must also survive the cross-trace
DatasetAdmission gate and be bound to the canonical HCU_INFERENCE_RECEIPT/v3 loader/output
chain.

This module is the orchestration boundary that requires both before rows are emitted. It
mints no truth, model authority, effect authority, runtime credit, or paid-training
permission. Current FREE_ONLY supervisor policy can still forbid provider execution after
this source gate passes.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

try:
    from .compile_jspace_training_dataset_v1 import compile_traces as compile_training_traces
    from .jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )
    from .jspace_inference_binding_v1 import (
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from .jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
except ImportError:
    from compile_jspace_training_dataset_v1 import compile_traces as compile_training_traces
    from jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )
    from jspace_inference_binding_v1 import (
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA

PIPELINE_SCHEMA = "ENTITYOS_HCU_ADMITTED_JSPACE_TRAINING_PIPELINE/v1"


class AdmittedTrainingDatasetError(ValueError):
    pass


@dataclass(frozen=True)
class PipelineEvidence:
    schema: str
    training_trace_sha256: str
    transition_trace_sha256: str
    prototype_trace_sha256: str
    inference_binding_sha256: str
    inference_receipt_sha256: str
    engine_load_consumption_receipt_sha256: str
    output_sha256: str
    generation: int
    entry_event_sha256: str
    entry_admission_sha256: str
    route_decision_sha256: str
    grid_plan_sha256: str
    cell_id: str
    role: str
    credit_label: str
    outcome_receipt_sha256: str | None


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise AdmittedTrainingDatasetError(f"{field}:MAPPING_REQUIRED")
    return value


def _text(value: Any, field: str, *, max_len: int = 1024) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AdmittedTrainingDatasetError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise AdmittedTrainingDatasetError(f"{field}:TOO_LONG")
    return value


def _sha256(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise AdmittedTrainingDatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise AdmittedTrainingDatasetError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise AdmittedTrainingDatasetError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    if value > 9_007_199_254_740_991:
        raise AdmittedTrainingDatasetError(f"{field}:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _same(observed: Mapping[str, Any], field: str) -> Any:
    first = object()
    current: Any = first
    for label, value in observed.items():
        if current is first:
            current = value
        elif value != current:
            raise AdmittedTrainingDatasetError(f"{field}:MISMATCH:{label}")
    return None if current is first else current


def validate_pipeline_evidence(
    training_trace: Mapping[str, Any],
    admission: DatasetAdmission,
    inference_binding: JSpaceInferenceBinding,
) -> PipelineEvidence:
    """Cross-bind one compiler input to its admission and real-inference evidence."""
    training_trace = _mapping(training_trace, "training_trace")
    if training_trace.get("schema_version") != TRAINING_TRACE_SCHEMA:
        raise AdmittedTrainingDatasetError("TRAINING_TRACE_SCHEMA_UNSUPPORTED")
    if not isinstance(admission, DatasetAdmission) or admission.schema != ADMISSION_SCHEMA:
        raise AdmittedTrainingDatasetError("DATASET_ADMISSION_REQUIRED")
    if not isinstance(inference_binding, JSpaceInferenceBinding):
        raise AdmittedTrainingDatasetError("JSPACE_INFERENCE_BINDING_REQUIRED")
    try:
        validate_binding(inference_binding)
    except JSpaceInferenceBindingError as exc:
        raise AdmittedTrainingDatasetError(f"JSPACE_INFERENCE_BINDING_REJECTED:{exc}") from exc
    if inference_binding.schema != INFERENCE_BINDING_SCHEMA:
        raise AdmittedTrainingDatasetError("JSPACE_INFERENCE_BINDING_SCHEMA_UNSUPPORTED")
    if inference_binding.training_trace_schema != TRAINING_TRACE_SCHEMA:
        raise AdmittedTrainingDatasetError("JSPACE_INFERENCE_BINDING_TRACE_SCHEMA_MISMATCH")

    training_sha = _same(
        {
            "trace": _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256"),
            "admission": _sha256(admission.training_trace_sha256, "admission.training_trace_sha256"),
            "inference_binding": _sha256(
                inference_binding.training_trace_sha256,
                "inference_binding.training_trace_sha256",
            ),
        },
        "TRAINING_TRACE_BINDING",
    )
    prototype_sha = _same(
        {
            "trace": _sha256(training_trace.get("prototype_trace_sha256"), "training_trace.prototype_trace_sha256"),
            "admission": _sha256(admission.prototype_trace_sha256, "admission.prototype_trace_sha256"),
            "inference_binding": _sha256(
                inference_binding.prototype_trace_sha256,
                "inference_binding.prototype_trace_sha256",
            ),
        },
        "PROTOTYPE_TRACE_BINDING",
    )
    generation = _same(
        {
            "trace": _generation(training_trace.get("generation"), "training_trace.generation"),
            "admission": _generation(admission.generation, "admission.generation"),
            "inference_binding": _generation(inference_binding.generation, "inference_binding.generation"),
        },
        "GENERATION_BINDING",
    )

    causal: dict[str, str] = {}
    for field in (
        "entry_event_sha256",
        "entry_admission_sha256",
        "route_decision_sha256",
        "grid_plan_sha256",
    ):
        causal[field] = _same(
            {
                "trace": _sha256(training_trace.get(field), f"training_trace.{field}"),
                "admission": _sha256(getattr(admission, field), f"admission.{field}"),
                "inference_binding": _sha256(
                    getattr(inference_binding, field),
                    f"inference_binding.{field}",
                ),
            },
            f"CAUSAL_BINDING:{field}",
        )

    cell_id = _same(
        {
            "trace": _text(training_trace.get("cell_id"), "training_trace.cell_id", max_len=256),
            "admission": _text(admission.cell_id, "admission.cell_id", max_len=256),
            "inference_binding": _text(inference_binding.cell_id, "inference_binding.cell_id", max_len=256),
        },
        "CELL_BINDING",
    )
    role = _same(
        {
            "trace": _text(training_trace.get("role"), "training_trace.role", max_len=256),
            "admission": _text(admission.role, "admission.role", max_len=256),
            "inference_binding": _text(inference_binding.role, "inference_binding.role", max_len=256),
        },
        "ROLE_BINDING",
    )
    _same(
        {
            "trace": _sha256(
                training_trace.get("vector_control_packet_sha256"),
                "training_trace.vector_control_packet_sha256",
            ),
            "inference_binding": _sha256(
                inference_binding.vector_control_packet_sha256,
                "inference_binding.vector_control_packet_sha256",
            ),
        },
        "VECTOR_CONTROL_PACKET_BINDING",
    )

    credit_label = _same(
        {
            "trace": _text(training_trace.get("credit_label"), "training_trace.credit_label", max_len=32).upper(),
            "admission": _text(admission.credit_label, "admission.credit_label", max_len=32).upper(),
        },
        "CREDIT_LABEL_BINDING",
    )
    trace_outcome = training_trace.get("outcome_receipt_sha256")
    if trace_outcome is not None:
        trace_outcome = _sha256(trace_outcome, "training_trace.outcome_receipt_sha256")
    admission_outcome = admission.outcome_receipt_sha256
    if admission_outcome is not None:
        admission_outcome = _sha256(admission_outcome, "admission.outcome_receipt_sha256")
    if trace_outcome != admission_outcome:
        raise AdmittedTrainingDatasetError("OUTCOME_RECEIPT_BINDING_MISMATCH")

    return PipelineEvidence(
        schema=PIPELINE_SCHEMA,
        training_trace_sha256=training_sha,
        transition_trace_sha256=_sha256(
            admission.transition_trace_sha256,
            "admission.transition_trace_sha256",
        ),
        prototype_trace_sha256=prototype_sha,
        inference_binding_sha256=_sha256(
            inference_binding.binding_sha256,
            "inference_binding.binding_sha256",
        ),
        inference_receipt_sha256=_sha256(
            inference_binding.inference_receipt_sha256,
            "inference_binding.inference_receipt_sha256",
        ),
        engine_load_consumption_receipt_sha256=_sha256(
            inference_binding.engine_load_consumption_receipt_sha256,
            "inference_binding.engine_load_consumption_receipt_sha256",
        ),
        output_sha256=_sha256(inference_binding.output_sha256, "inference_binding.output_sha256"),
        generation=generation,
        entry_event_sha256=causal["entry_event_sha256"],
        entry_admission_sha256=causal["entry_admission_sha256"],
        route_decision_sha256=causal["route_decision_sha256"],
        grid_plan_sha256=causal["grid_plan_sha256"],
        cell_id=cell_id,
        role=role,
        credit_label=credit_label,
        outcome_receipt_sha256=trace_outcome,
    )


def _annotate_rows(
    compiled: Mapping[str, list[dict[str, Any]]],
    evidence: PipelineEvidence,
) -> dict[str, list[dict[str, Any]]]:
    out = {"train": [], "validation": [], "holdout": []}
    evidence_metadata = {
        "pipeline_schema": evidence.schema,
        "dataset_admission_transition_trace_sha256": evidence.transition_trace_sha256,
        "dataset_admission_prototype_trace_sha256": evidence.prototype_trace_sha256,
        "inference_binding_sha256": evidence.inference_binding_sha256,
        "inference_receipt_sha256": evidence.inference_receipt_sha256,
        "engine_load_consumption_receipt_sha256": evidence.engine_load_consumption_receipt_sha256,
        "model_output_sha256": evidence.output_sha256,
    }
    for split in out:
        rows = compiled.get(split)
        if not isinstance(rows, list):
            raise AdmittedTrainingDatasetError(f"LOWER_LEVEL_COMPILER_SPLIT_INVALID:{split}")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("metadata"), dict):
                raise AdmittedTrainingDatasetError("LOWER_LEVEL_COMPILER_ROW_INVALID")
            copied = dict(row)
            copied["metadata"] = {**dict(row["metadata"]), **evidence_metadata}
            out[split].append(copied)
    return out


def compile_admitted_records(
    records: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
    admitted_transition_traces: Mapping[str, Mapping[str, Any]],
    admitted_prototype_traces: Mapping[str, Mapping[str, Any]],
    admitted_inference_bindings: Mapping[str, JSpaceInferenceBinding],
    admitted_outcome_receipts: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Compile only traces that pass both cross-trace admission and inference binding.

    ``records`` contains ``(training_trace, transition_trace)`` pairs. The admission gate
    uses caller-owned registries rather than rebuilding trust from each row. The matching
    inference binding is looked up by training-trace SHA and must validate cryptographically
    under the selected RFC8785/JCS identity rules before the lower-level row compiler is
    called.
    """
    out = {"train": [], "validation": [], "holdout": []}
    seen: set[str] = set()
    admitted_inference_bindings = _mapping(
        admitted_inference_bindings,
        "admitted_inference_bindings",
    )

    for record in records:
        if not isinstance(record, tuple) or len(record) != 2:
            raise AdmittedTrainingDatasetError("TRAINING_RECORD_PAIR_REQUIRED")
        training_trace = _mapping(record[0], "training_trace")
        transition_trace = _mapping(record[1], "transition_trace")
        training_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")
        if training_sha in seen:
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
            raise AdmittedTrainingDatasetError(f"DATASET_ADMISSION_REJECTED:{exc}") from exc

        inference_binding = admitted_inference_bindings.get(training_sha)
        if not isinstance(inference_binding, JSpaceInferenceBinding):
            raise AdmittedTrainingDatasetError("INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE")
        evidence = validate_pipeline_evidence(training_trace, admission, inference_binding)
        compiled = compile_training_traces([dict(training_trace)])
        annotated = _annotate_rows(compiled, evidence)
        for split in out:
            out[split].extend(annotated[split])
        seen.add(training_sha)

    if not seen:
        raise AdmittedTrainingDatasetError("NO_ADMITTED_TRAINING_TRACES")
    return out
