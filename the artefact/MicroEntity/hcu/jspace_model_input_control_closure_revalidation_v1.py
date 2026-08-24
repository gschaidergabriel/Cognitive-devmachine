#!/usr/bin/env python3
"""Semantically revalidate a persisted J-Space model-input-control closure.

``ENTITYOS_HCU_JSPACE_MODEL_INPUT_CONTROL_CLOSURE/v1`` is self-authenticating, but a
self-consistent digest alone cannot prove that a deserialized closure was produced from the
canonical source objects. This boundary re-derives the canonical ModelInputControlAdmission
from the existing MiniUnifiedDB admission store, revalidates the supplied J-Space binding,
and reconstructs the closure from the exact producer evidence before accepting equality.

No new database, truth/effect authority, inference path, J-Space authority, model runtime
credit, or training credit is created here. The function is deterministic and idempotent over
already-admitted evidence.
"""
from __future__ import annotations

from dataclasses import asdict
import sqlite3
from typing import Any

try:
    from .grid10_scheduler_v1 import GridPlan
    from .inference_receipt_v1 import InferenceReceipt
    from .jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from .jspace_model_input_control_closure_v1 import (
        JSpaceModelInputControlClosure,
        JSpaceModelInputControlClosureError,
        close_model_input_control_into_jspace,
        validate_closure,
    )
    from .model_input_control_admission_store_v1 import (
        ModelInputControlAdmissionStoreError,
        admit_model_input_control_binding,
    )
    from .model_input_control_binding_v1 import ModelInputControlBinding
except ImportError:
    from grid10_scheduler_v1 import GridPlan
    from inference_receipt_v1 import InferenceReceipt
    from jspace_inference_binding_v1 import JSpaceInferenceBinding, JSpaceInferenceBindingError, validate_binding
    from jspace_model_input_control_closure_v1 import (
        JSpaceModelInputControlClosure,
        JSpaceModelInputControlClosureError,
        close_model_input_control_into_jspace,
        validate_closure,
    )
    from model_input_control_admission_store_v1 import (
        ModelInputControlAdmissionStoreError,
        admit_model_input_control_binding,
    )
    from model_input_control_binding_v1 import ModelInputControlBinding


class JSpaceModelInputControlClosureRevalidationError(ValueError):
    pass


def _same_record(observed: Any, expected: Any, label: str) -> None:
    try:
        observed_record = asdict(observed)
        expected_record = asdict(expected)
    except TypeError as exc:
        raise JSpaceModelInputControlClosureRevalidationError(
            f"{label}:DATACLASS_REQUIRED"
        ) from exc
    if observed_record != expected_record:
        raise JSpaceModelInputControlClosureRevalidationError(f"{label}:SOURCE_MISMATCH")


def revalidate_closure_against_canonical_sources(
    db: sqlite3.Connection,
    closure: JSpaceModelInputControlClosure,
    control_binding: ModelInputControlBinding,
    consumed_input_bytes: bytes,
    grid_plan: GridPlan,
    inference_receipt: InferenceReceipt,
    jspace_binding: JSpaceInferenceBinding,
    *,
    current_generation: int,
) -> JSpaceModelInputControlClosure:
    """Re-derive one persisted closure from canonical admitted source evidence.

    The existing admission store is deliberately reused rather than copied: exact replay is
    idempotent, divergent replay fails closed, and the store re-reads the already-admitted
    model-execution observation from the caller-supplied canonical MiniUnifiedDB connection.
    The returned closure is the freshly reconstructed canonical record.
    """
    try:
        validate_closure(closure)
        validate_binding(jspace_binding)
        canonical_admission = admit_model_input_control_binding(
            db,
            control_binding,
            consumed_input_bytes,
            grid_plan,
            current_generation=current_generation,
        )
        expected = close_model_input_control_into_jspace(
            control_binding,
            canonical_admission,
            consumed_input_bytes,
            grid_plan,
            inference_receipt,
            jspace_binding,
        )
    except (
        JSpaceModelInputControlClosureError,
        JSpaceInferenceBindingError,
        ModelInputControlAdmissionStoreError,
    ) as exc:
        raise JSpaceModelInputControlClosureRevalidationError(
            f"CLOSURE_SOURCE_REVALIDATION_FAILED:{exc}"
        ) from exc

    _same_record(closure, expected, "JSPACE_MODEL_INPUT_CONTROL_CLOSURE")
    return expected
