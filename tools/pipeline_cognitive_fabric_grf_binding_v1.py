#!/usr/bin/env python3
"""Thin GRF Brain binding in front of the one canonical Cognitive Fabric compositor.

This module owns no turn allocation, truth, durable state, routing, model execution,
GWT selection, effects, or post-turn finalization. It resolves the active prepare once,
binds one sealed GRF Brain trace to that exact prepare, freezes the resolved prepare for
the canonical compositor, delegates, then cross-checks the returned candidate-only
admission. No second turn loop or second admission authority is created.
"""
from __future__ import annotations

import importlib.util
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

BINDING_VERSION = "pipeline-cognitive-fabric-grf-binding/v1"
ADMISSION_SCHEMA = "mini-entity-cognitive-fabric-admission/v1"
_ROOT = Path(__file__).resolve().parents[1]
_IMPL = _ROOT / "research_entity" / "global" / "j-space" / "implementations"
_GRF_BRAIN = _IMPL / "grf_brain_v1.py"
_GRF_BINDING = _IMPL / "grf_zero_binding_v1.py"


class CognitiveFabricGRFBindingError(ValueError):
    pass


def _need(condition: bool, message: str) -> None:
    if not condition:
        raise CognitiveFabricGRFBindingError(message)


def _load_module(path: Path, name: str) -> Any:
    _need(path.is_file(), f"GRF_MODULE_MISSING:{path.name}")
    spec = importlib.util.spec_from_file_location(name, path)
    _need(spec is not None and spec.loader is not None, f"GRF_IMPORT_SPEC_FAILED:{name}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise CognitiveFabricGRFBindingError(
            f"GRF_IMPORT_EXEC_FAILED:{name}:{type(exc).__name__}:{exc}"
        ) from exc
    return module


def load_default_grf_binding_module() -> Any:
    brain = _load_module(_GRF_BRAIN, "grf_brain_v1")
    previous = sys.modules.get("grf_brain_v1")
    sys.modules["grf_brain_v1"] = brain
    try:
        binding = _load_module(_GRF_BINDING, "grf_zero_binding_v1")
    finally:
        if previous is None:
            sys.modules.pop("grf_brain_v1", None)
        else:
            sys.modules["grf_brain_v1"] = previous
    _need(getattr(brain, "SCHEMA", None) == "OMEGA_GRF_BRAIN_TRACE/v1", "GRF_BRAIN_V1_REQUIRED")
    _need(getattr(binding, "SCHEMA", None) == "OMEGA_GRF_ZERO_BINDING/v1", "GRF_ZERO_BINDING_V1_REQUIRED")
    return binding


def _validate_result(result: Any, *, prepare: Mapping[str, Any], binding_receipt: Mapping[str, Any]) -> dict[str, Any]:
    _need(type(result) is dict and result.get("ok") is True, "CANONICAL_ADMISSION_FAILED")
    _need(result.get("schema") == ADMISSION_SCHEMA, "ADMISSION_SCHEMA_MISMATCH")
    _need(result.get("generation") == prepare.get("entity_generation"), "ADMISSION_GENERATION_DRIFT")
    _need(result.get("causal_turn_id") == prepare.get("causal_turn_id"), "ADMISSION_TURN_DRIFT")
    _need(result.get("turn_binding_digest") == prepare.get("turn_binding_digest"), "ADMISSION_TURN_BINDING_DRIFT")
    _need(result.get("boot_binding_digest") == prepare.get("boot_binding_digest"), "ADMISSION_BOOT_BINDING_DRIFT")

    receipt = result.get("admission_receipt")
    _need(isinstance(receipt, Mapping), "ADMISSION_RECEIPT_OBJECT_REQUIRED")
    _need(receipt.get("authority") == "CANDIDATE_INFERENCE_ONLY", "ADMISSION_AUTHORITY_ESCALATION")
    _need(receipt.get("real_effect_executed") is False, "PREINFERENCE_EFFECT_EXECUTION_FORBIDDEN")
    _need(receipt.get("grf_digest") == binding_receipt.get("framework_digest"), "ADMISSION_GRF_DIGEST_DRIFT")
    _need(
        "ucf_runtime_receipt_digest" not in result
        and "ucf_runtime_receipt_digest" not in receipt,
        "PREINFERENCE_FINAL_UCF_RECEIPT_FORBIDDEN",
    )
    return result


def build_grf_bound_pre_inference_admission(
    db: Any,
    *,
    entity_generation: int,
    grf_trace: Mapping[str, Any],
    invocation: Mapping[str, Any],
    compiled: Mapping[str, Any],
    prompt: Mapping[str, Any],
    profile: Mapping[str, Any],
    expected_activation_digest: str | None = None,
    active_turn_module: Any | None = None,
    compositor_module: Any | None = None,
    grf_binding_module: Any | None = None,
    capsule_module: Any | None = None,
    packet_module: Any | None = None,
    capability_module: Any | None = None,
) -> dict[str, Any]:
    """Bind a sealed GRF trace and delegate exactly that prepare to canonical admission."""
    _need(type(entity_generation) is int and entity_generation >= 0, "GENERATION_INVALID")
    _need(isinstance(grf_trace, Mapping), "GRF_TRACE_OBJECT_REQUIRED")
    _need(isinstance(invocation, Mapping), "INVOCATION_OBJECT_REQUIRED")
    _need(isinstance(compiled, Mapping), "COMPILED_OBJECT_REQUIRED")
    _need(isinstance(prompt, Mapping), "PROMPT_OBJECT_REQUIRED")
    _need(isinstance(profile, Mapping), "PROFILE_OBJECT_REQUIRED")

    if active_turn_module is None:
        import miniunifieddb_active_turn_v1 as active_turn_module  # type: ignore[no-redef]
    prepare = active_turn_module.resolve_active_prepare(
        db,
        entity_generation=entity_generation,
        expected_activation_digest=expected_activation_digest,
    )
    _need(type(prepare) is dict and prepare.get("ok") is True, "ACTIVE_PREPARE_RESOLUTION_FAILED")
    _need(prepare.get("entity_generation") == entity_generation, "STALE_PREPARE_GENERATION")

    binding_module = grf_binding_module or load_default_grf_binding_module()
    try:
        binding_receipt = binding_module.bind_trace_to_prepare(grf_trace, prepare)
        binding_module.validate_binding(binding_receipt)
    except Exception as exc:
        raise CognitiveFabricGRFBindingError(
            f"GRF_PREPARE_BINDING_FAILED:{type(exc).__name__}:{exc}"
        ) from exc

    frozen_prepare = dict(prepare)

    class FrozenActiveTurn:
        @staticmethod
        def resolve_active_prepare(_db: Any, *, entity_generation: int, expected_activation_digest: str | None = None):
            _need(entity_generation == frozen_prepare.get("entity_generation"), "FROZEN_PREPARE_GENERATION_DRIFT")
            if expected_activation_digest is not None:
                _need(
                    expected_activation_digest == frozen_prepare.get("activation_digest"),
                    "FROZEN_PREPARE_ACTIVATION_DRIFT",
                )
            return dict(frozen_prepare)

    if compositor_module is None:
        import pipeline_cognitive_fabric_admission_v1 as compositor_module  # type: ignore[no-redef]

    result = compositor_module.build_pre_inference_admission(
        db,
        entity_generation=entity_generation,
        invocation=invocation,
        compiled=compiled,
        prompt=prompt,
        profile=profile,
        expected_activation_digest=expected_activation_digest,
        origin=BINDING_VERSION,
        active_turn_module=FrozenActiveTurn,
        capsule_module=capsule_module,
        packet_module=packet_module,
        capability_module=capability_module,
    )
    result = _validate_result(result, prepare=frozen_prepare, binding_receipt=binding_receipt)
    out = dict(result)
    out["grf_binding_digest"] = binding_receipt["binding_digest"]
    out["grf_binding_receipt"] = dict(binding_receipt)
    out["grf_binding_version"] = BINDING_VERSION
    return out


__all__ = [
    "ADMISSION_SCHEMA",
    "BINDING_VERSION",
    "CognitiveFabricGRFBindingError",
    "build_grf_bound_pre_inference_admission",
    "load_default_grf_binding_module",
]
