#!/usr/bin/env python3
"""Strict source-revalidated adapter for serious EntityOS/HCU J-Space training data.

The retained ``compile_admitted_jspace_training_dataset_v1`` path now requires a
``JSpaceModelInputControlClosure`` for non-BASELINE intervention traces.  A closure is
self-authenticating, however, and its digest alone does not prove that the closure was
reconstructed from canonical MiniUnifiedDB model-execution/control-admission evidence.

This adapter closes that remaining parent-evidence boundary without creating another truth,
effect, inference, or dataset authority.  Any closure admitted to the existing compiler is
first revalidated by ``revalidate_closure_against_canonical_sources`` and, critically, the
control binding must already exist in the caller-supplied canonical MiniUnifiedDB.  The
adapter never uses source revalidation to bootstrap a missing control admission merely so a
training row can pass.

BASELINE traces remain compatible with the existing compiler and need no intervention-
delivery closure.  Positive passage proves exact observable source/identity closure only; it
does not prove hidden-state causal use, model benefit, reward truth, runtime acceptance, or
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
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding
    from .jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from .jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from .model_input_control_binding_v1 import ModelInputControlBinding
except ImportError:
    from compile_admitted_jspace_training_dataset_v1 import (
        AdmittedTrainingDatasetError,
        compile_admitted_records,
    )
    from grid10_scheduler_v1 import GridPlan
    from inference_receipt_v1 import InferenceReceipt
    from jspace_inference_binding_v1 import JSpaceInferenceBinding
    from jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from model_input_control_binding_v1 import ModelInputControlBinding

SCHEMA = "ENTITYOS_HCU_SOURCE_REVALIDATED_JSPACE_TRAINING_PIPELINE/v1"
BASELINE_CONTROL_CONDITION = "BASELINE"
MAX_SAFE_INTEGER = 9_007_199_254_740_991


class SourceRevalidatedTrainingDatasetError(ValueError):
    pass


@dataclass(frozen=True)
class ModelInputControlClosureSourceBundle:
    """Exact source objects required to rederive one admitted control closure."""

    closure: JSpaceModelInputControlClosure
    control_binding: ModelInputControlBinding
    consumed_input_bytes: bytes
    grid_plan: GridPlan
    inference_receipt: InferenceReceipt


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


def _require_existing_control_admission(
    db: sqlite3.Connection,
    binding: ModelInputControlBinding,
) -> None:
    """Require source admission to predate training compilation.

    ``revalidate_closure_against_canonical_sources`` intentionally reuses the canonical
    admission-store operation because exact replay is idempotent.  Without this predecessor
    check, however, a training compiler could accidentally create a missing control admission
    while trying to validate its own evidence.  Training promotion must consume prior
    canonical evidence, not manufacture that prerequisite.
    """
    if not isinstance(db, sqlite3.Connection):
        raise SourceRevalidatedTrainingDatasetError("CANONICAL_MINIUNIFIEDDB_CONNECTION_REQUIRED")
    if not isinstance(binding, ModelInputControlBinding):
        raise SourceRevalidatedTrainingDatasetError("MODEL_INPUT_CONTROL_BINDING_REQUIRED")
    binding_sha = _sha256(binding.binding_sha256, "control_binding.binding_sha256")
    try:
        row = db.execute(
            "SELECT binding_sha256 FROM hcu_model_input_control_bindings WHERE binding_sha256=?",
            (binding_sha,),
        ).fetchone()
        invocation = db.execute(
            "SELECT binding_sha256 FROM hcu_model_input_control_invocations "
            "WHERE executor_id=? AND invocation_id=?",
            (binding.executor_id, binding.invocation_id),
        ).fetchone()
    except sqlite3.Error as exc:
        raise SourceRevalidatedTrainingDatasetError(
            "MODEL_INPUT_CONTROL_ADMISSION_STORE_REQUIRED_BEFORE_TRAINING"
        ) from exc
    if row is None or row[0] != binding_sha:
        raise SourceRevalidatedTrainingDatasetError(
            "MODEL_INPUT_CONTROL_BINDING_NOT_PREVIOUSLY_ADMITTED"
        )
    if invocation is None or invocation[0] != binding_sha:
        raise SourceRevalidatedTrainingDatasetError(
            "MODEL_INPUT_CONTROL_INVOCATION_NOT_PREVIOUSLY_ADMITTED"
        )


def compile_source_revalidated_records(
    records: Iterable[tuple[Mapping[str, Any], Mapping[str, Any]]],
    *,
    canonical_db: sqlite3.Connection,
    current_generation: int,
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
    """Compile with canonical-source revalidation for every used control closure.

    ``model_input_control_source_bundles`` is keyed by the exact J-Space inference-binding
    SHA-256.  The raw bundle is never forwarded as admission evidence.  Only the freshly
    reconstructed closure returned by the canonical-source revalidator can reach the retained
    serious-training compiler.
    """
    materialized = list(records)
    generation = _generation(current_generation)
    bundles = _mapping(model_input_control_source_bundles, "model_input_control_source_bundles")
    bindings = _mapping(admitted_inference_bindings, "admitted_inference_bindings")
    revalidated: dict[str, JSpaceModelInputControlClosure] = {}

    for record in materialized:
        if not isinstance(record, tuple) or len(record) != 2:
            raise SourceRevalidatedTrainingDatasetError("TRAINING_RECORD_PAIR_REQUIRED")
        trace = _mapping(record[0], "training_trace")
        trace_sha = _sha256(trace.get("trace_sha256"), "training_trace.trace_sha256")
        condition = _control_condition(trace)
        binding = bindings.get(trace_sha)
        if not isinstance(binding, JSpaceInferenceBinding):
            # Preserve a fail-closed error at this stricter boundary rather than attempting
            # source revalidation without the admitted child identity.
            raise SourceRevalidatedTrainingDatasetError(
                "INFERENCE_BINDING_NOT_ADMITTED_FOR_TRAINING_TRACE"
            )
        binding_sha = _sha256(binding.binding_sha256, "inference_binding.binding_sha256")
        bundle = bundles.get(binding_sha)

        if bundle is None:
            if condition == BASELINE_CONTROL_CONDITION:
                continue
            raise SourceRevalidatedTrainingDatasetError(
                "CANONICAL_SOURCE_BUNDLE_REQUIRED_FOR_NON_BASELINE_TRAINING"
            )
        if not isinstance(bundle, ModelInputControlClosureSourceBundle):
            raise SourceRevalidatedTrainingDatasetError(
                "MODEL_INPUT_CONTROL_CLOSURE_SOURCE_BUNDLE_REQUIRED"
            )

        _require_existing_control_admission(canonical_db, bundle.control_binding)
        try:
            canonical_closure = revalidate_closure_against_canonical_sources(
                canonical_db,
                bundle.closure,
                bundle.control_binding,
                bundle.consumed_input_bytes,
                bundle.grid_plan,
                bundle.inference_receipt,
                binding,
                current_generation=generation,
            )
        except JSpaceModelInputControlClosureRevalidationError as exc:
            raise SourceRevalidatedTrainingDatasetError(
                f"MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED:{exc}"
            ) from exc
        revalidated[binding_sha] = canonical_closure

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
            admitted_model_input_control_closures=revalidated,
        )
    except AdmittedTrainingDatasetError as exc:
        raise SourceRevalidatedTrainingDatasetError(
            f"ADMITTED_TRAINING_PIPELINE_REJECTED:{exc}"
        ) from exc


__all__ = [
    "SCHEMA",
    "ModelInputControlClosureSourceBundle",
    "SourceRevalidatedTrainingDatasetError",
    "compile_source_revalidated_records",
]
