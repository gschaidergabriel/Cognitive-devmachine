#!/usr/bin/env python3
"""Require canonical-source revalidation for persisted control-delivery closures.

A JSpaceModelInputControlClosure is self-authenticating, but its digest cannot prove that
its control-admission/binding identities were derived from the canonical MiniUnifiedDB
admission store. This adapter deliberately reuses the existing read-only canonical source
revalidator and gives the serious training compiler one narrow fail-closed entry point.

The context is request-scoped evidence plumbing. It is not a second store, capability,
truth/effect authority, model authority, training authority, or runtime-credit source.
"""
from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from typing import Mapping

try:
    from .grid10_scheduler_v1 import GridPlan
    from .inference_receipt_v1 import InferenceReceipt
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from .jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from .jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from .model_input_control_binding_v1 import ModelInputControlBinding
except ImportError:
    from grid10_scheduler_v1 import GridPlan
    from inference_receipt_v1 import InferenceReceipt
    from jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from jspace_model_input_control_closure_revalidation_v1 import (
        JSpaceModelInputControlClosureRevalidationError,
        revalidate_closure_against_canonical_sources,
    )
    from jspace_model_input_control_closure_v1 import JSpaceModelInputControlClosure
    from model_input_control_binding_v1 import ModelInputControlBinding


SCHEMA = "ENTITYOS_HCU_JSPACE_TRAINING_CONTROL_SOURCE_REVALIDATION/v1"


class JSpaceTrainingControlSourceRevalidationError(ValueError):
    pass


@dataclass(frozen=True)
class TrainingControlSourceContext:
    """Exact already-observed producer sources for one J-Space binding."""

    db: sqlite3.Connection
    control_binding: ModelInputControlBinding
    consumed_input_bytes: bytes
    grid_plan: GridPlan
    inference_receipt: InferenceReceipt
    current_generation: int


def require_source_revalidated_model_input_control_closure(
    inference_binding: JSpaceInferenceBinding,
    closure: JSpaceModelInputControlClosure | None,
    source_contexts: Mapping[str, TrainingControlSourceContext] | None,
) -> JSpaceModelInputControlClosure | None:
    """Return a source-revalidated closure, or fail closed before training promotion.

    ``None`` remains ``None`` so the existing training-delivery gate can retain its sole
    BASELINE-vs-intervention policy. Whenever a closure is actually supplied and therefore
    can become training metadata/evidence, canonical-source revalidation is mandatory.
    """
    if closure is None:
        return None
    if not isinstance(inference_binding, JSpaceInferenceBinding):
        raise JSpaceTrainingControlSourceRevalidationError(
            "JSPACE_INFERENCE_BINDING_REQUIRED"
        )
    try:
        validate_binding(inference_binding)
    except JSpaceInferenceBindingError as exc:
        raise JSpaceTrainingControlSourceRevalidationError(
            f"JSPACE_INFERENCE_BINDING_REJECTED:{exc}"
        ) from exc

    if not isinstance(source_contexts, Mapping):
        raise JSpaceTrainingControlSourceRevalidationError(
            "MODEL_INPUT_CONTROL_SOURCE_CONTEXTS_REQUIRED"
        )
    context = source_contexts.get(inference_binding.binding_sha256)
    if not isinstance(context, TrainingControlSourceContext):
        raise JSpaceTrainingControlSourceRevalidationError(
            "MODEL_INPUT_CONTROL_SOURCE_CONTEXT_REQUIRED_FOR_JSPACE_BINDING"
        )
    if isinstance(context.current_generation, bool) or not isinstance(
        context.current_generation, int
    ):
        raise JSpaceTrainingControlSourceRevalidationError(
            "MODEL_INPUT_CONTROL_SOURCE_GENERATION_INVALID"
        )
    if context.current_generation != inference_binding.generation:
        raise JSpaceTrainingControlSourceRevalidationError(
            "MODEL_INPUT_CONTROL_SOURCE_GENERATION_MISMATCH"
        )

    try:
        return revalidate_closure_against_canonical_sources(
            context.db,
            closure,
            context.control_binding,
            context.consumed_input_bytes,
            context.grid_plan,
            context.inference_receipt,
            inference_binding,
            current_generation=context.current_generation,
        )
    except JSpaceModelInputControlClosureRevalidationError as exc:
        raise JSpaceTrainingControlSourceRevalidationError(
            f"MODEL_INPUT_CONTROL_CLOSURE_SOURCE_REVALIDATION_FAILED:{exc}"
        ) from exc


__all__ = [
    "SCHEMA",
    "JSpaceTrainingControlSourceRevalidationError",
    "TrainingControlSourceContext",
    "require_source_revalidated_model_input_control_closure",
]
