#!/usr/bin/env python3
"""Source-aware revalidation for persisted J-Space inference bindings.

`validate_binding()` proves the persisted binding is structurally valid, internally
cross-bound and digest-consistent. It cannot, from the flattened binding alone, prove
that a caller did not consistently relabel multiple correlated summary fields and then
recompute the binding digest.

This guard closes that rehydration boundary by rebuilding the binding from the exact
TrainingTrace, HCU InferenceReceipt and scheduler-owned GridPlan sources and requiring
byte-semantic equality with the persisted binding.

This is deterministic research-evidence plumbing only. It grants no canonical truth,
runtime acceptance, model credit, training credit, capability or effects.
"""
from __future__ import annotations

from dataclasses import asdict

try:
    from .grid10_scheduler_v1 import GridPlan
    from .inference_receipt_v1 import InferenceReceipt
    from .jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        bind_training_trace_to_inference,
        validate_binding,
    )
    from .jspace_training_trace_v1 import TrainingTrace
except ImportError:
    from grid10_scheduler_v1 import GridPlan
    from inference_receipt_v1 import InferenceReceipt
    from jspace_inference_binding_v1 import (
        JSpaceInferenceBinding,
        JSpaceInferenceBindingError,
        bind_training_trace_to_inference,
        validate_binding,
    )
    from jspace_training_trace_v1 import TrainingTrace


SOURCE_REVALIDATION_SCHEMA = "ENTITYOS_HCU_JSPACE_INFERENCE_SOURCE_REVALIDATION/v1"


def revalidate_binding_against_sources(
    binding: JSpaceInferenceBinding,
    training_trace: TrainingTrace,
    inference_receipt: InferenceReceipt,
    grid_plan: GridPlan,
) -> None:
    """Fail closed unless a persisted binding exactly re-derives from its sources.

    The source validators are intentionally reached through
    `bind_training_trace_to_inference()`: TrainingTrace, InferenceReceipt and GridPlan
    must each pass their existing exact identity/canonicalization gates before an
    expected binding can be reconstructed.
    """
    validate_binding(binding)
    expected = bind_training_trace_to_inference(
        training_trace,
        inference_receipt,
        grid_plan,
    )
    validate_binding(expected)

    if asdict(binding) != asdict(expected):
        raise JSpaceInferenceBindingError(
            "JSPACE_INFERENCE_BINDING_SOURCE_REVALIDATION_MISMATCH"
        )
