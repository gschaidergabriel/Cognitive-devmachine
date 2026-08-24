#!/usr/bin/env python3
"""Provider-independent orchestrator for one bounded EntityOS/HCU J-Space causal family.

This module closes a source-level integration gap between the existing five-condition
causal-family identity gate and future real local model backends. It does not execute a
provider, grant model/J-Space runtime credit, or decide that a causal effect exists.

The orchestrator fixes the required condition order, binds every invocation to a
predeclared input/intervention plan, rejects callback relabeling or consumed-input drift,
and then delegates exact model/runtime/loader/activation/trace identity closure to
``validate_causal_family_identity``.

``model_input_sha256`` is the exact content identity already exposed by the canonical
``VerifiedModelExecution.input_sha256`` / executor-I/O evidence path. It is not a new input
authority. The v2 plan requires the intervention target, sham, and off-target controls to
consume the exact corrupted-baseline model input. A backend that needs a different input
transformation must use a future explicitly versioned plan rather than silently changing
bytes under a stable ``input_variant_id`` label.

A successful return means only:
``CAUSAL_FAMILY_ORCHESTRATED_IDENTITY_COMPLETE_NOT_JSPACE_CAUSAL_PASS``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Protocol, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from .jspace_causal_family_identity_gate_v1 import (
        CausalFamilyIdentityError,
        CausalFamilyIdentityResult,
        CausalTrialIdentity,
        REQUIRED_CONDITIONS,
        validate_causal_family_identity,
    )
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize
    from jspace_causal_family_identity_gate_v1 import (
        CausalFamilyIdentityError,
        CausalFamilyIdentityResult,
        CausalTrialIdentity,
        REQUIRED_CONDITIONS,
        validate_causal_family_identity,
    )

SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_FAMILY_ORCHESTRATOR/v2"
PLAN_SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_FAMILY_PLAN/v2"
EVIDENCE_CLASS = "CAUSAL_FAMILY_ORCHESTRATED_IDENTITY_COMPLETE_NOT_JSPACE_CAUSAL_PASS"
BASELINE_CONDITIONS = frozenset({"BASELINE_CLEAN", "BASELINE_CORRUPTED"})
INTERVENTION_CONDITIONS = frozenset({"INTERVENTION_TARGET", "SHAM_CONTROL", "OFF_TARGET_CONTROL"})
MAX_SAFE_IJSON_INT = 9_007_199_254_740_991


class CausalFamilyOrchestratorError(ValueError):
    pass


@dataclass(frozen=True)
class CausalTrialSpec:
    condition: str
    input_variant_id: str
    model_input_sha256: str
    intervention_sha256: str | None


@dataclass(frozen=True)
class CausalFamilyPlan:
    schema: str
    family_id: str
    generation: int
    trials: tuple[CausalTrialSpec, ...]


@dataclass(frozen=True)
class CausalFamilyRunResult:
    schema: str
    evidence_class: str
    jspace_causal_credit: bool
    plan_sha256: str
    family_identity_sha256: str
    invocation_count: int
    trial_identity_sha256: tuple[str, ...]
    identity_result: CausalFamilyIdentityResult


class CausalFamilyExecutor(Protocol):
    """Future local/model backend boundary.

    Implementations may perform real local model work only under then-current execution
    authority. They must return the exact observed identity for the requested trial,
    including the exact model input content digest observed by the canonical executor path.
    """

    def run_causal_trial(self, spec: CausalTrialSpec, *, family_id: str, generation: int) -> CausalTrialIdentity: ...


def _text(value: object, field: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CausalFamilyOrchestratorError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise CausalFamilyOrchestratorError(f"{field}:TOO_LONG")
    return value


def _generation(value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SAFE_IJSON_INT:
        raise CausalFamilyOrchestratorError("generation:NONNEGATIVE_IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _sha(value: object, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise CausalFamilyOrchestratorError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise CausalFamilyOrchestratorError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _canonical_sha256(value: object, field: str) -> str:
    try:
        encoded = canonicalize(value)
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise CausalFamilyOrchestratorError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


def validate_causal_family_plan(plan: CausalFamilyPlan) -> tuple[CausalTrialSpec, ...]:
    """Validate the pre-execution five-condition plan and return canonical order."""
    if not isinstance(plan, CausalFamilyPlan):
        raise CausalFamilyOrchestratorError("plan:CAUSAL_FAMILY_PLAN_REQUIRED")
    if plan.schema != PLAN_SCHEMA:
        raise CausalFamilyOrchestratorError("plan.schema:UNSUPPORTED")
    family_id = _text(plan.family_id, "family_id")
    _generation(plan.generation)
    if isinstance(plan.trials, (str, bytes, bytearray)) or not isinstance(plan.trials, Sequence):
        raise CausalFamilyOrchestratorError("trials:SEQUENCE_REQUIRED")
    if len(plan.trials) != len(REQUIRED_CONDITIONS):
        raise CausalFamilyOrchestratorError("trials:EXACT_MINIMUM_CAUSAL_FAMILY_REQUIRED")

    by_condition: dict[str, CausalTrialSpec] = {}
    for spec in plan.trials:
        if not isinstance(spec, CausalTrialSpec):
            raise CausalFamilyOrchestratorError("trial_spec:CAUSAL_TRIAL_SPEC_REQUIRED")
        if spec.condition not in REQUIRED_CONDITIONS:
            raise CausalFamilyOrchestratorError("condition:UNSUPPORTED")
        if spec.condition in by_condition:
            raise CausalFamilyOrchestratorError("condition:DUPLICATE_CONTROL_FORBIDDEN")
        input_variant_id = _text(spec.input_variant_id, "input_variant_id")
        model_input_sha256 = _sha(spec.model_input_sha256, "model_input_sha256")
        intervention = spec.intervention_sha256
        if spec.condition in BASELINE_CONDITIONS:
            if intervention is not None:
                raise CausalFamilyOrchestratorError(f"{spec.condition}:BASELINE_INTERVENTION_MUST_BE_NONE")
        else:
            intervention = _sha(intervention, "intervention_sha256")
        by_condition[spec.condition] = CausalTrialSpec(
            spec.condition,
            input_variant_id,
            model_input_sha256,
            intervention,
        )

    if set(by_condition) != set(REQUIRED_CONDITIONS):
        raise CausalFamilyOrchestratorError("condition:FAMILY_INCOMPLETE")

    intervention_ids = [
        by_condition[name].intervention_sha256
        for name in REQUIRED_CONDITIONS
        if name in INTERVENTION_CONDITIONS
    ]
    if len(intervention_ids) != len(set(intervention_ids)):
        raise CausalFamilyOrchestratorError("intervention_sha256:CROSS_CONTROL_REUSE_FORBIDDEN")

    clean = by_condition["BASELINE_CLEAN"]
    corrupted = by_condition["BASELINE_CORRUPTED"]
    if clean.input_variant_id == corrupted.input_variant_id:
        raise CausalFamilyOrchestratorError("input_variant_id:BASELINE_VARIANT_COLLISION_FORBIDDEN")
    if clean.model_input_sha256 == corrupted.model_input_sha256:
        raise CausalFamilyOrchestratorError("model_input_sha256:BASELINE_CONTENT_COLLISION_FORBIDDEN")
    for condition in INTERVENTION_CONDITIONS:
        control = by_condition[condition]
        if control.input_variant_id != corrupted.input_variant_id:
            raise CausalFamilyOrchestratorError(f"{condition}:CORRUPTED_BASE_INPUT_VARIANT_REQUIRED")
        if control.model_input_sha256 != corrupted.model_input_sha256:
            raise CausalFamilyOrchestratorError(f"{condition}:CORRUPTED_BASE_MODEL_INPUT_REQUIRED")

    # Keep the family id observed by canonicalization so whitespace aliases cannot create
    # distinct-looking plans at the executor boundary.
    if family_id != plan.family_id:
        raise CausalFamilyOrchestratorError("family_id:NONCANONICAL_WHITESPACE_FORBIDDEN")
    return tuple(by_condition[name] for name in REQUIRED_CONDITIONS)


def causal_family_plan_sha256(plan: CausalFamilyPlan) -> str:
    ordered = validate_causal_family_plan(plan)
    material = {
        "schema": PLAN_SCHEMA,
        "family_id": plan.family_id,
        "generation": plan.generation,
        "trials": [asdict(spec) for spec in ordered],
    }
    return _canonical_sha256(material, "causal_family_plan")


def run_causal_family(executor: CausalFamilyExecutor, plan: CausalFamilyPlan) -> CausalFamilyRunResult:
    """Execute exactly one predeclared causal family through one callback boundary.

    This function intentionally has no provider selection, credential access, network I/O,
    effect authority, or fallback path. A backend is responsible for its own then-current
    execution admission and must return exact observed trial identities.
    """
    if executor is None or not callable(getattr(executor, "run_causal_trial", None)):
        raise CausalFamilyOrchestratorError("executor:RUN_CAUSAL_TRIAL_REQUIRED")
    ordered = validate_causal_family_plan(plan)
    plan_sha = causal_family_plan_sha256(plan)

    observed: list[CausalTrialIdentity] = []
    for spec in ordered:
        trial = executor.run_causal_trial(spec, family_id=plan.family_id, generation=plan.generation)
        if not isinstance(trial, CausalTrialIdentity):
            raise CausalFamilyOrchestratorError(f"{spec.condition}:CAUSAL_TRIAL_IDENTITY_REQUIRED")
        if trial.condition != spec.condition:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_CONDITION_RELABEL_FORBIDDEN")
        if trial.family_id != plan.family_id:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_FAMILY_ID_MISMATCH")
        if trial.generation != plan.generation:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_GENERATION_MISMATCH")
        if trial.input_variant_id != spec.input_variant_id:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_INPUT_VARIANT_MISMATCH")
        if trial.model_input_sha256 != spec.model_input_sha256:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_MODEL_INPUT_IDENTITY_MISMATCH")
        if trial.intervention_sha256 != spec.intervention_sha256:
            raise CausalFamilyOrchestratorError(f"{spec.condition}:EXECUTOR_INTERVENTION_IDENTITY_MISMATCH")
        observed.append(trial)

    try:
        identity = validate_causal_family_identity(tuple(observed))
    except CausalFamilyIdentityError as exc:
        raise CausalFamilyOrchestratorError(f"IDENTITY_GATE_REJECTED:{exc}") from exc

    return CausalFamilyRunResult(
        schema=SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        jspace_causal_credit=False,
        plan_sha256=plan_sha,
        family_identity_sha256=identity.family_identity_sha256,
        invocation_count=len(observed),
        trial_identity_sha256=identity.trial_identity_sha256,
        identity_result=identity,
    )


__all__ = [
    "SCHEMA",
    "PLAN_SCHEMA",
    "EVIDENCE_CLASS",
    "CausalFamilyOrchestratorError",
    "CausalTrialSpec",
    "CausalFamilyPlan",
    "CausalFamilyRunResult",
    "CausalFamilyExecutor",
    "validate_causal_family_plan",
    "causal_family_plan_sha256",
    "run_causal_family",
]
