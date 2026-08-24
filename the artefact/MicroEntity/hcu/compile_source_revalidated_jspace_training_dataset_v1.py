#!/usr/bin/env python3
"""Strict source-revalidated adapter for serious EntityOS/HCU J-Space training data.

The retained ``compile_admitted_jspace_training_dataset_v1`` path verifies dataset admission,
an exact admitted InferenceReceipt parent and non-BASELINE model-input-control delivery. Those
checks are necessary but a persisted ``JSpaceInferenceBinding`` and a persisted control
closure are still self-authenticating envelopes: digest consistency alone cannot prove they
were reconstructed from the canonical producer objects.

This adapter closes both rehydration boundaries by delegating to the existing single source
validators before any row can reach the retained compiler:

* ``revalidate_binding_against_sources`` rebuilds JSpaceInferenceBinding/v3 from the exact
  TrainingTrace, HCU InferenceReceipt/v4 and scheduler-owned GridPlan.
* ``revalidate_closure_against_canonical_sources`` rebuilds any supplied model-input-control
  closure from an already-admitted canonical MiniUnifiedDB control binding, exact consumed
  bytes, the same GridPlan/InferenceReceipt, and the revalidated J-Space binding.

No validator semantics are copied here and no missing canonical admission is minted by the
training path. BASELINE traces require binding-source rehydration but need no intervention-
delivery closure. Positive passage proves observable source/identity closure only; it does
not prove hidden-state causal use, model benefit, reward truth, runtime acceptance, or
training benefit.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Any, Iterable, Mapping

try:
    from .compile_admitted_jspace_training_dataset_v1 import (
        AdmittedTrainingDatasetError,
        compile_admitted_records,
    )
    from .grid10_scheduler_v1 import GridPlan
    from .inference_receipt_v1 import InferenceReceipt
    from .jspace_inference_binding_revalidation_v1 import revalidate_binding_against_sources
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError
    from .jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from .jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from .jspace_training_trace_v1 import JSpaceTrainingTraceError, TrainingTrace, trace_dict
    from .model_input_control_binding_v1 import ModelInputControlBinding
except ImportError:
    from compile_admitted_jspace_training_dataset_v1 import (
        AdmittedTrainingDatasetError,
        compile_admitted_records,
    )
    from grid10_scheduler_v1 import GridPlan
    from inference_receipt_v1 import InferenceReceipt
    from jspace_inference_binding_revalidation_v1 import revalidate_binding_against_sources
    from jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError
    from jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from jspace_training_trace_v1 import JSpaceTrainingTraceError, TrainingTrace, trace_dict
    from model_input_control_binding_v1 import ModelInputControlBinding

SCHEMA = "ENTITYOS_HCU_SOURCE_REVALIDATED_JSPACE_TRAINING_PIPELINE/v2"
BASELINE_CONTROL_CONDITION = "BASELINE"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class SourceRevalidatedTrainingDatasetError(ValueError):
    pass


@dataclass(frozen=True)
class InferenceBindingSourceBundle:
    """Exact producer objects required to rederive one persisted J-Space binding."""

    training_trace: TrainingTrace
    inference_receipt: InferenceReceipt
    grid_plan: GridPlan


@dataclass(frozen=True)
class ModelInputControlClosureSourceBundle:
    """Exact additional source objects required to rederive one control closure."""

    closure: JSpaceModelInputControlClosure
    control_binding: ModelInputControlBinding
    consumed_input_bytes: bytes


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise SourceRevalidatedTrainingDatasetError(f"{field}:MAPPING_REQUIRED")
    return value


def _sha256(value: Any, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64:
        raise SourceRevalidatedTrainingDatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise SourceRevalidatedTrainingDatasetError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise SourceRevalidatedTrainingDatasetError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise SourceRevalidatedTrainingDatasetError("current_generation:NONNEGATIVE_INTEGER_REQUIRED")
    if value > MAX_SAFE_INTEGER:
        raise SourceRevalidatedTrainingDatasetError("current_generation:IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _control_condition(trace: Mapping[str, Any]) -> str:
    value = trace.get("vector_control_condition")
    if not isinstance(value, str) or not value.strip():
        raise SourceRevalidatedTrainingDatasetError(
            "training_trace.vector_control_condition:NONEMPTY_STRING_REQUIRED"
        )
    normalized = value.strip().upper()
    if len(normalized) > 64:
        raise SourceRevalidatedTrainingDatasetError(
            "training_trace.vector_control_condition:TOO_LONG"
        )
    return normalized


def _require_exact_trace_source(
    serialized_trace: Mapping[str, Any],
    source_trace: TrainingTrace,
) -> None:
    """Bind caller-visible compiler bytes to the exact rehydration source object."""
    try:
        observed = trace_dict(source_trace)
    except JSpaceTrainingTraceError as exc:
        raise SourceRevalidatedTrainingDatasetError(
            f"TRAINING_TRACE_SOURCE_REVALIDATION_FAILED:{exc}"
        ) from exc
    if observed != dict(serialized_trace):
        raise SourceRevalidatedTrainingDatasetError("TRAINING_TRACE_SOURCE_BYTES_MISMATCH")


def compile_source_revalidated_records(
    records: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    canonical_db: sqlite3.Connection,
    current_generation: int,
    inference_binding_source_bundles: Mapping[str, InferenceBindingSourceBundle],
    model_input_control_source_bundles: Mapping[str, ModelInputControlClosureSourceBundle],
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
    """Compile only after exact-source rehydration of every persisted J-Space binding.

    Both source-bundle registries are keyed by the exact J-Space inference-binding SHA-256.
    Every trace, including BASELINE, requires an ``InferenceBindingSourceBundle``. A
    non-BASELINE trace additionally requires a ``ModelInputControlClosureSourceBundle``.
    Raw source bundles are never forwarded as admission evidence: only a closure freshly
    returned by the canonical-source revalidator can reach the retained serious compiler.
    """
    materialized = list(records)
    generation = _generation(current_generation)
    inference_sources = _mapping(
        inference_binding_source_bundles,
        "inference_binding_source_bundles",
    )
    control_sources = _mapping(
        model_input_control_source_bundles,
        "model_input_control_source_bundles",
    )
    bindings = _mapping(admitted_inference_bindings, "admitted_inference_bindings")
    revalidated_closures: dict[str, JSpaceModelInputControlClosure] = {}

    for record in materialized:
        if not isinstance(record, tuple) or len(record) != 2:
            raise SourceRevalidatedTrainingDatasetError("TRAINING_RECORD_PAIR_REQUIRED")
        trace = _mapping(record[0], "training_trace")
        trace_sha = _sha256(trace.get("trace_sha256"), "training_trace.trace_sha256")
        condition = _control_condition(trace)
        binding = bindings.get(trace_sha)
        if not isinstance(binding, JSpaceInferenceBinding):
            raise SourceRevalidatedTrainingDatasetError(
                "INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE"
            )
        binding_sha = _sha256(binding.binding_sha256, "inference_binding.binding_sha256")

        inference_source = inference_sources.get(binding_sha)
        if not isinstance(inference_source, InferenceBindingSourceBundle):
            raise SourceRevalidatedTrainingDatasetError(
                "INFERENCE_BINDING_SOURCE_BUNDLE_REQUIRED"
            )
        _require_exact_trace_source(trace, inference_source.training_trace)
        try:
            revalidate_binding_against_sources(
                binding,
                inference_source.training_trace,
                inference_source.inference_receipt,
                inference_source.grid_plan,
            )
        except JSpaceInferenceBindingError as exc:
            raise SourceRevalidatedTrainingDatasetError(
                f"JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_FAILED:{exc}"
            ) from exc

        control_source = control_sources.get(binding_sha)
        if control_source is None:
            if condition == BASELINE_CONTROL_CONDITION:
                continue
            raise SourceRevalidatedTrainingDatasetError(
                "CANONICAL_CONTROL_SOURCE_BUNDLE_REQUIRED_FOR_NON_BASELINE_TRAINING"
            )
        if not isinstance(control_source, ModelInputControlClosureSourceBundle):
            raise SourceRevalidatedTrainingDatasetError(
                "MODEL_INPUT_CONTROL_CLOSURE_SOURCE_BUNDLE_REQUIRED"
            )

        try:
            canonical_closure = revalidate_closure_against_canonical_sources(
                canonical_db,
                control_source.closure,
                control_source.control_binding,
                control_source.consumed_input_bytes,
                inference_source.grid_plan,
                inference_source.inference_receipt,
                binding,
                current_generation=generation,
            )
        except JSpaceModelInputControlClosureRevalidationError as exc:
            raise SourceRevalidatedTrainingDatasetError(
                f"MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED:{exc}"
            ) from exc
        revalidated_closures[binding_sha] = canonical_closure

    try:
        return compile_admitted_records(
            materialized,
            admitted_training_traces=admitted_training_traces,
            admitted_transition_traces=admitted_transition_traces,
            admitted_prototype_traces=admitted_prototype_traces,
            admitted_grid_plans=admitted_grid_plans,
            admitted_vector_control_packets=admitted_vector_control_packets,
            admitted_inference_bindings=admitted_inference_bindings,
            admitted_inference_receipts=admitted_inference_receipts,
            admitted_bases=admitted_bases,
            admitted_outcome_receipts=admitted_outcome_receipts,
            admitted_model_input_control_closures=revalidated_closures,
        )
    except AdmittedTrainingDatasetError as exc:
        raise SourceRevalidatedTrainingDatasetError(
            f"ADMITTED_TRAINING_PIPELINE_REJECTED:{exc}"
        ) from exc


__all__ = [
    "SCHEMA",
    "InferenceBindingSourceBundle",
    "ModelInputControlClosureSourceBundle",
    "SourceRevalidatedTrainingDatasetError",
    "compile_source_revalidated_records",
]
