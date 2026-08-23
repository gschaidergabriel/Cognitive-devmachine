#!/usr/bin/env python3
"""Fail-closed orchestration for serious EntityOS/HCU J-Space training data.

The lower-level compiler validates and renders TrainingTrace records into deterministic
family-split JSONL rows while requiring an externally admitted J-Space basis registry.
That alone is deliberately insufficient for serious training admission: a trace must also
survive DatasetAdmission, bind to the canonical HCU_INFERENCE_RECEIPT/v4 chain, and prove
that the referenced inference receipt itself exists byte/field-consistently in an external
admission registry.

A self-consistent JSpaceInferenceBinding is therefore necessary but not sufficient. This
module rejects "binding-only" evidence laundering where a caller re-hashes a plausible
binding around invented inference provenance. Serious train/validation/holdout ownership is
also derived from admitted upstream causal ancestry, never from the caller-controlled
``trace_family_id`` label alone. The DatasetAdmission call also receives the caller-owned
registry of exact canonical Vector-Control packet preimages, so a shared digest label cannot
be laundered into training rows without validation by the sole JSPACE_VECTOR_CONTROL_ABI/v1
implementation. It mints no truth, model authority, effect authority, runtime credit, or
paid-training permission.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import hashlib
from typing import Any, Iterable, Mapping

try:
    from .compile_jspace_bootstrap_dataset_v1 import compile_traces as compile_training_traces
    from .entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from .inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from .jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )
    from .jspace_dataset_family_split_v1 import split_for_family
    from .jspace_inference_binding_v1 import (
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from .jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA
except ImportError:
    from compile_jspace_bootstrap_dataset_v1 import compile_traces as compile_training_traces
    from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, CanonicalizationError, canonicalize
    from inference_receipt_v1 import (
        InferenceReceipt,
        SCHEMA as INFERENCE_RECEIPT_SCHEMA,
        STATUS as INFERENCE_RECEIPT_STATUS,
    )
    from jspace_dataset_admission_gate_v1 import (
        ADMISSION_SCHEMA,
        DatasetAdmission,
        JSpaceDatasetAdmissionError,
        admit_for_training_dataset,
    )
    from jspace_dataset_family_split_v1 import split_for_family
    from jspace_inference_binding_v1 import (
        SCHEMA as INFERENCE_BINDING_SCHEMA,
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        validate_binding,
    )
    from jspace_training_trace_v1 import TRACE_SCHEMA as TRAINING_TRACE_SCHEMA

PIPELINE_SCHEMA = "ENTITYOS_HCU_ADMITTED_JSPACE_TRAINING_PIPELINE/v1"
CAUSAL_FAMILY_SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_FAMILY/v1"


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
    declared_trace_family_id: str
    causal_family_sha256: str
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


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        return hashlib.sha256(canonicalize(value)).hexdigest()
    except CanonicalizationError as exc:
        raise AdmittedTrainingDatasetError(f"{field}:CANONICALIZATION_FAILED:{exc}") from exc


def _derive_causal_family_sha256(*, generation: int, causal: Mapping[str, str]) -> str:
    """Derive dataset-family authority only from admitted pre-control causal ancestry.

    Cell/role/basis/vector/outcome fields are deliberately excluded: baseline, lesion,
    shuffle, role-swap, rescue, and other counterfactual descendants of the same admitted
    Entry -> route -> GRID plan must remain in one dataset split even when those downstream
    properties differ. The digest is partition plumbing only, never canonical EntityOS state.
    """
    return _canonical_sha256(
        {
            "schema": CAUSAL_FAMILY_SCHEMA,
            "generation": generation,
            "entry_event_sha256": causal["entry_event_sha256"],
            "entry_admission_sha256": causal["entry_admission_sha256"],
            "route_decision_sha256": causal["route_decision_sha256"],
            "grid_plan_sha256": causal["grid_plan_sha256"],
        },
        "JSPACE_CAUSAL_FAMILY",
    )


def _normalize_admitted_inference_receipt(value: Any) -> dict[str, Any]:
    if isinstance(value, InferenceReceipt):
        receipt = asdict(value)
    elif isinstance(value, Mapping):
        receipt = dict(value)
    else:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_VALUE_INVALID")
    expected_fields = {field.name for field in fields(InferenceReceipt)}
    if set(receipt) != expected_fields:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_FIELD_SET_MISMATCH")
    return receipt


_RECEIPT_BINDING_FIELDS = {
    "entity_generation": "generation",
    "entry_admission_sha256": "entry_admission_sha256",
    "event_sha256": "entry_event_sha256",
    "decision_sha256": "route_decision_sha256",
    "engine_identity_sha256": "engine_identity_sha256",
    "resolved_engine_identity": "resolved_engine_identity",
    "resolved_engine_class": "resolved_engine_class",
    "resolved_engine_artifact_sha256": "resolved_engine_artifact_sha256",
    "engine_admission_receipt_sha256": "engine_admission_receipt_sha256",
    "engine_load_loader_binding_sha256": "engine_load_loader_binding_sha256",
    "engine_load_lease_sha256": "engine_load_lease_sha256",
    "engine_load_consumption_receipt_sha256": "engine_load_consumption_receipt_sha256",
    "engine_load_loader_id": "engine_load_loader_id",
    "model_execution_receipt_sha256": "model_execution_receipt_sha256",
    "model_execution_observation_sha256": "model_execution_observation_sha256",
    "model_execution_executor_id": "model_execution_executor_id",
    "model_execution_invocation_id": "model_execution_invocation_id",
    "grid_plan_sha256": "grid_plan_sha256",
    "output_producing_cell_id": "output_producing_cell_id",
    "model_execution_role": "model_execution_role",
    "input_sha256": "input_sha256",
    "input_size": "input_size",
    "model_call_id": "model_call_id",
    "output_ref": "output_ref",
    "output_sha256": "output_sha256",
    "output_size": "output_size",
}


def _require_admitted_inference_receipt(
    binding: JSpaceInferenceBinding,
    admitted_inference_receipts: Mapping[str, Any],
) -> dict[str, Any]:
    """Require exact admitted receipt content behind a binding's digest reference."""
    admitted_inference_receipts = _mapping(
        admitted_inference_receipts,
        "admitted_inference_receipts",
    )
    receipt_sha = _sha256(
        binding.inference_receipt_sha256,
        "inference_binding.inference_receipt_sha256",
    )
    raw_receipt = admitted_inference_receipts.get(receipt_sha)
    if raw_receipt is None:
        raise AdmittedTrainingDatasetError("INFERENCE_RECEIPT_NOT_ADMITTED_FOR_BINDING")
    receipt = _normalize_admitted_inference_receipt(raw_receipt)

    if receipt.get("schema") != INFERENCE_RECEIPT_SCHEMA or receipt.get("schema") != binding.inference_receipt_schema:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_SCHEMA_MISMATCH")
    if receipt.get("status") != INFERENCE_RECEIPT_STATUS:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_STATUS_UNSUPPORTED")
    for field in (
        "hash_serialization_schema",
        "engine_load_canonicalization_schema",
        "model_execution_canonicalization_schema",
    ):
        if receipt.get(field) != CANONICALIZATION_SCHEMA or receipt.get(field) != binding.canonicalization_schema:
            raise AdmittedTrainingDatasetError(f"ADMITTED_INFERENCE_RECEIPT_CANONICALIZATION_MISMATCH:{field}")

    observed_sha = _sha256(receipt.get("receipt_sha256"), "admitted_inference_receipt.receipt_sha256")
    if observed_sha != receipt_sha:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_KEY_IDENTITY_MISMATCH")
    material = dict(receipt)
    material.pop("receipt_sha256")
    if _canonical_sha256(material, "ADMITTED_INFERENCE_RECEIPT") != receipt_sha:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_DIGEST_MISMATCH")

    for receipt_field, binding_field in _RECEIPT_BINDING_FIELDS.items():
        if receipt.get(receipt_field) != getattr(binding, binding_field):
            raise AdmittedTrainingDatasetError(
                f"INFERENCE_RECEIPT_BINDING_MISMATCH:{receipt_field}"
            )

    model_lanes = receipt.get("model_lanes")
    if isinstance(model_lanes, (str, bytes, bytearray)) or not isinstance(model_lanes, (list, tuple)):
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_MODEL_LANES_INVALID")
    normalized_lanes = tuple(_text(value, "admitted_inference_receipt.model_lane", max_len=256) for value in model_lanes)
    if binding.role not in normalized_lanes:
        raise AdmittedTrainingDatasetError("ADMITTED_INFERENCE_RECEIPT_ROLE_NOT_IN_MODEL_LANES")
    return receipt


def validate_pipeline_evidence(
    training_trace: Mapping[str, Any],
    admission: DatasetAdmission,
    inference_binding: JSpaceInferenceBinding,
) -> PipelineEvidence:
    """Cross-bind one compiler input to its admission and inference-binding evidence."""
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
            "inference_binding": _sha256(inference_binding.training_trace_sha256, "inference_binding.training_trace_sha256"),
        },
        "TRAINING_TRACE_BINDING",
    )
    prototype_sha = _same(
        {
            "trace": _sha256(training_trace.get("prototype_trace_sha256"), "training_trace.prototype_trace_sha256"),
            "admission": _sha256(admission.prototype_trace_sha256, "admission.prototype_trace_sha256"),
            "inference_binding": _sha256(inference_binding.prototype_trace_sha256, "inference_binding.prototype_trace_sha256"),
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
                "inference_binding": _sha256(getattr(inference_binding, field), f"inference_binding.{field}"),
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
            "trace": _sha256(training_trace.get("vector_control_packet_sha256"), "training_trace.vector_control_packet_sha256"),
            "admission": _sha256(admission.vector_control_packet_sha256, "admission.vector_control_packet_sha256"),
            "inference_binding": _sha256(inference_binding.vector_control_packet_sha256, "inference_binding.vector_control_packet_sha256"),
        },
        "VECTOR_CONTROL_PACKET_BINDING",
    )

    declared_trace_family_id = _text(
        training_trace.get("trace_family_id"),
        "training_trace.trace_family_id",
        max_len=256,
    )
    causal_family_sha256 = _derive_causal_family_sha256(
        generation=generation,
        causal=causal,
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
        transition_trace_sha256=_sha256(admission.transition_trace_sha256, "admission.transition_trace_sha256"),
        prototype_trace_sha256=prototype_sha,
        inference_binding_sha256=_sha256(inference_binding.binding_sha256, "inference_binding.binding_sha256"),
        inference_receipt_sha256=_sha256(inference_binding.inference_receipt_sha256, "inference_binding.inference_receipt_sha256"),
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
        declared_trace_family_id=declared_trace_family_id,
        causal_family_sha256=causal_family_sha256,
        credit_label=credit_label,
        outcome_receipt_sha256=trace_outcome,
    )


def _annotate_rows(
    compiled: Mapping[str, list[dict[str, Any]]],
    evidence: PipelineEvidence,
) -> dict[str, list[dict[str, Any]]]:
    """Annotate and repartition lower-level rows using admitted causal-family authority."""
    out = {"train": [], "validation": [], "holdout": []}
    causal_split = split_for_family(evidence.causal_family_sha256)
    evidence_metadata = {
        "pipeline_schema": evidence.schema,
        "dataset_admission_transition_trace_sha256": evidence.transition_trace_sha256,
        "dataset_admission_prototype_trace_sha256": evidence.prototype_trace_sha256,
        "inference_binding_sha256": evidence.inference_binding_sha256,
        "inference_receipt_sha256": evidence.inference_receipt_sha256,
        "engine_load_consumption_receipt_sha256": evidence.engine_load_consumption_receipt_sha256,
        "model_output_sha256": evidence.output_sha256,
        "declared_trace_family_id": evidence.declared_trace_family_id,
        "causal_family_schema": CAUSAL_FAMILY_SCHEMA,
        "causal_family_sha256": evidence.causal_family_sha256,
        "causal_family_split": causal_split,
    }
    for declared_split in out:
        rows = compiled.get(declared_split)
        if not isinstance(rows, list):
            raise AdmittedTrainingDatasetError(f"LOWER_LEVEL_COMPILER_SPLIT_INVALID:{declared_split}")
        for row in rows:
            if not isinstance(row, dict) or not isinstance(row.get("metadata"), dict):
                raise AdmittedTrainingDatasetError("LOWER_LEVEL_COMPILER_ROW_INVALID")
            metadata = dict(row["metadata"])
            row_family = metadata.get("trace_family_id")
            if row_family is not None and _text(
                row_family,
                "lower_level.metadata.trace_family_id",
                max_len=256,
            ) != evidence.declared_trace_family_id:
                raise AdmittedTrainingDatasetError("LOWER_LEVEL_COMPILER_TRACE_FAMILY_MISMATCH")
            copied = dict(row)
            copied["metadata"] = {
                **metadata,
                **evidence_metadata,
                "declared_family_split": declared_split,
            }
            out[causal_split].append(copied)
    return out


def _evidence_identity(evidence: PipelineEvidence) -> tuple[str, str, str, str]:
    return (
        evidence.transition_trace_sha256,
        evidence.inference_binding_sha256,
        evidence.inference_receipt_sha256,
        evidence.causal_family_sha256,
    )


def compile_admitted_records(
    records: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    admitted_training_traces: Mapping[str, Mapping[str, Any]],
    admitted_transition_traces: Mapping[str, Mapping[str, Any]],
    admitted_prototype_traces: Mapping[str, Mapping[str, Any]],
    admitted_grid_plans: Mapping[str, Mapping[str, Any]],
    admitted_vector_control_packets: Mapping[str, Any],
    admitted_inference_bindings: Mapping[str, JSpaceInferenceBinding],
    admitted_inference_receipts: Mapping[str, Any],
    admitted_bases: Mapping[str, str],
    admitted_outcome_receipts: Mapping[str, Any] | None = None,
) -> dict[str, list[dict[str, Any]]]:
    """Compile only traces with external basis, trace, GRID, vector, binding, and receipt admission."""
    out = {"train": [], "validation": [], "holdout": []}
    seen: dict[str, tuple[str, str, str, str]] = {}
    admitted_grid_plans = _mapping(admitted_grid_plans, "admitted_grid_plans")
    admitted_vector_control_packets = _mapping(
        admitted_vector_control_packets,
        "admitted_vector_control_packets",
    )
    admitted_inference_bindings = _mapping(admitted_inference_bindings, "admitted_inference_bindings")
    admitted_inference_receipts = _mapping(admitted_inference_receipts, "admitted_inference_receipts")
    admitted_bases = _mapping(admitted_bases, "admitted_bases")

    for record in records:
        if not isinstance(record, tuple) or len(record) != 2:
            raise AdmittedTrainingDatasetError("TRAINING_RECORD_PAIR_REQUIRED")
        training_trace = _mapping(record[0], "training_trace")
        transition_trace = _mapping(record[1], "transition_trace")
        training_sha = _sha256(training_trace.get("trace_sha256"), "training_trace.trace_sha256")

        try:
            admission = admit_for_training_dataset(
                training_trace,
                transition_trace,
                admitted_training_traces=admitted_training_traces,
                admitted_transition_traces=admitted_transition_traces,
                admitted_prototype_traces=admitted_prototype_traces,
                admitted_grid_plans=admitted_grid_plans,
                admitted_vector_control_packets=admitted_vector_control_packets,
                admitted_outcome_receipts=admitted_outcome_receipts,
            )
        except JSpaceDatasetAdmissionError as exc:
            raise AdmittedTrainingDatasetError(f"DATASET_ADMISSION_REJECTED:{exc}") from exc

        inference_binding = admitted_inference_bindings.get(training_sha)
        if not isinstance(inference_binding, JSpaceInferenceBinding):
            raise AdmittedTrainingDatasetError("INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE")
        _require_admitted_inference_receipt(inference_binding, admitted_inference_receipts)
        evidence = validate_pipeline_evidence(training_trace, admission, inference_binding)
        evidence_identity = _evidence_identity(evidence)
        previous_identity = seen.get(training_sha)
        if previous_identity is not None:
            if previous_identity != evidence_identity:
                raise AdmittedTrainingDatasetError("TRAINING_TRACE_ANCESTRY_CONFLICT")
            continue

        compiled = compile_training_traces([dict(training_trace)], admitted_bases=admitted_bases)
        annotated = _annotate_rows(compiled, evidence)
        for split in out:
            out[split].extend(annotated[split])
        seen[training_sha] = evidence_identity

    if not seen:
        raise AdmittedTrainingDatasetError("NO_ADMITTED_TRAINING_TRACES")
    return out
