#!/usr/bin/env python3
"""Fail-closed identity gate for one EntityOS/HCU local J-Space causal control family.

This module does not execute a model and does not decide that a causal effect exists.
It validates that the minimum clean/corrupted/target/sham/off-target family is complete,
uses one exact model/runtime/loader/activation-site identity, binds the exact consumed
model-input content for every trial, and does not relabel one execution/trace/output as
multiple controls.

A PASS from this gate is identity/provenance readiness only:
``CAUSAL_FAMILY_IDENTITY_COMPLETE_NOT_JSPACE_CAUSAL_PASS``.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
from typing import Any, Sequence

try:
    from .entry_canonicalization_v1 import CanonicalizationError, canonicalize
except ImportError:
    from entry_canonicalization_v1 import CanonicalizationError, canonicalize

SCHEMA = "ENTITYOS_HCU_JSPACE_CAUSAL_FAMILY_IDENTITY_GATE/v1"
EVIDENCE_CLASS = "CAUSAL_FAMILY_IDENTITY_COMPLETE_NOT_JSPACE_CAUSAL_PASS"
REQUIRED_CONDITIONS = (
    "BASELINE_CLEAN",
    "BASELINE_CORRUPTED",
    "INTERVENTION_TARGET",
    "SHAM_CONTROL",
    "OFF_TARGET_CONTROL",
)
BASELINE_CONDITIONS = frozenset({"BASELINE_CLEAN", "BASELINE_CORRUPTED"})
INTERVENTION_CONDITIONS = frozenset({
    "INTERVENTION_TARGET",
    "SHAM_CONTROL",
    "OFF_TARGET_CONTROL",
})
MAX_SAFE_IJSON_INT = 9_007_199_254_740_991


class CausalFamilyIdentityError(ValueError):
    pass


@dataclass(frozen=True)
class CausalTrialIdentity:
    condition: str
    family_id: str
    input_variant_id: str
    model_input_content_schema: str
    model_input_content_sha256: str
    generation: int
    checkpoint_sha256: str
    tokenizer_sha256: str
    runtime_build_sha256: str
    loader_consumption_sha256: str
    model_execution_sha256: str
    inference_receipt_sha256: str
    trace_sha256: str
    output_sha256: str
    activation_site_id: str
    pre_activation_sha256: str
    post_activation_sha256: str
    intervention_sha256: str | None


@dataclass(frozen=True)
class CausalFamilyIdentityResult:
    schema: str
    evidence_class: str
    jspace_causal_credit: bool
    family_id: str
    generation: int
    required_conditions: tuple[str, ...]
    present_conditions: tuple[str, ...]
    checkpoint_sha256: str
    tokenizer_sha256: str
    runtime_build_sha256: str
    loader_consumption_sha256: str
    activation_site_id: str
    model_input_content_schema: str
    clean_model_input_content_sha256: str
    corrupted_model_input_content_sha256: str
    trial_identity_sha256: tuple[str, ...]
    family_identity_sha256: str


def _text(value: Any, field: str, *, max_len: int = 512) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CausalFamilyIdentityError(f"{field}:NONEMPTY_STRING_REQUIRED")
    value = value.strip()
    if len(value) > max_len:
        raise CausalFamilyIdentityError(f"{field}:TOO_LONG")
    return value


def _sha(value: Any, field: str) -> str:
    value = _text(value, field, max_len=64)
    if len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise CausalFamilyIdentityError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    if value in {"0" * 64, "f" * 64}:
        raise CausalFamilyIdentityError(f"{field}:PLACEHOLDER_SHA256_FORBIDDEN")
    return value


def _generation(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= MAX_SAFE_IJSON_INT:
        raise CausalFamilyIdentityError("generation:NONNEGATIVE_IJSON_SAFE_INTEGER_REQUIRED")
    return value


def _canonical_sha256(value: Any, field: str) -> str:
    try:
        encoded = canonicalize(value)
    except (CanonicalizationError, TypeError, ValueError) as exc:
        raise CausalFamilyIdentityError(f"{field}:CANONICALIZATION_FAILED") from exc
    return hashlib.sha256(encoded).hexdigest()


def _validated_trial(trial: CausalTrialIdentity) -> CausalTrialIdentity:
    if not isinstance(trial, CausalTrialIdentity):
        raise CausalFamilyIdentityError("trial:CAUSAL_TRIAL_IDENTITY_REQUIRED")
    if trial.condition not in REQUIRED_CONDITIONS:
        raise CausalFamilyIdentityError("condition:UNSUPPORTED")
    family_id = _text(trial.family_id, "family_id")
    input_variant_id = _text(trial.input_variant_id, "input_variant_id")
    model_input_content_schema = _text(
        trial.model_input_content_schema,
        "model_input_content_schema",
        max_len=256,
    )
    activation_site_id = _text(trial.activation_site_id, "activation_site_id")
    generation = _generation(trial.generation)

    hashes = {}
    for field in (
        "model_input_content_sha256",
        "checkpoint_sha256",
        "tokenizer_sha256",
        "runtime_build_sha256",
        "loader_consumption_sha256",
        "model_execution_sha256",
        "inference_receipt_sha256",
        "trace_sha256",
        "output_sha256",
        "pre_activation_sha256",
        "post_activation_sha256",
    ):
        hashes[field] = _sha(getattr(trial, field), field)

    intervention = trial.intervention_sha256
    if trial.condition in BASELINE_CONDITIONS:
        if intervention is not None:
            raise CausalFamilyIdentityError(
                f"{trial.condition}:BASELINE_INTERVENTION_MUST_BE_NONE"
            )
    else:
        intervention = _sha(intervention, "intervention_sha256")

    return CausalTrialIdentity(
        condition=trial.condition,
        family_id=family_id,
        input_variant_id=input_variant_id,
        model_input_content_schema=model_input_content_schema,
        generation=generation,
        activation_site_id=activation_site_id,
        intervention_sha256=intervention,
        **hashes,
    )


def _require_same(trials: Sequence[CausalTrialIdentity], field: str) -> Any:
    values = {getattr(trial, field) for trial in trials}
    if len(values) != 1:
        raise CausalFamilyIdentityError(f"{field}:CROSS_CONTROL_MISMATCH")
    return next(iter(values))


def _require_unique(trials: Sequence[CausalTrialIdentity], field: str) -> None:
    values = [getattr(trial, field) for trial in trials]
    if len(values) != len(set(values)):
        raise CausalFamilyIdentityError(f"{field}:CROSS_CONTROL_REUSE_FORBIDDEN")


def _validate_model_input_topology(
    by_condition: dict[str, CausalTrialIdentity],
) -> tuple[CausalTrialIdentity, CausalTrialIdentity]:
    clean = by_condition["BASELINE_CLEAN"]
    corrupted = by_condition["BASELINE_CORRUPTED"]
    if clean.input_variant_id == corrupted.input_variant_id:
        raise CausalFamilyIdentityError(
            "input_variant_id:BASELINE_CLEAN_CORRUPTED_REUSE_FORBIDDEN"
        )
    if clean.model_input_content_sha256 == corrupted.model_input_content_sha256:
        raise CausalFamilyIdentityError(
            "model_input_content_sha256:BASELINE_CLEAN_CORRUPTED_REUSE_FORBIDDEN"
        )
    for condition in INTERVENTION_CONDITIONS:
        trial = by_condition[condition]
        if trial.input_variant_id != corrupted.input_variant_id:
            raise CausalFamilyIdentityError(
                f"{condition}:INTERVENTION_BASE_INPUT_VARIANT_MISMATCH"
            )
        if trial.model_input_content_sha256 != corrupted.model_input_content_sha256:
            raise CausalFamilyIdentityError(
                f"{condition}:INTERVENTION_BASE_INPUT_CONTENT_MISMATCH"
            )
    return clean, corrupted


def validate_causal_family_identity(
    trials: Sequence[CausalTrialIdentity],
) -> CausalFamilyIdentityResult:
    """Validate minimum causal-family identity without granting causal/model credit."""
    if isinstance(trials, (str, bytes, bytearray)) or not isinstance(trials, Sequence):
        raise CausalFamilyIdentityError("trials:SEQUENCE_REQUIRED")
    validated = tuple(_validated_trial(trial) for trial in trials)
    if len(validated) != len(REQUIRED_CONDITIONS):
        raise CausalFamilyIdentityError("trials:EXACT_MINIMUM_CAUSAL_FAMILY_REQUIRED")

    by_condition = {trial.condition: trial for trial in validated}
    if len(by_condition) != len(validated):
        raise CausalFamilyIdentityError("condition:DUPLICATE_CONTROL_FORBIDDEN")
    if set(by_condition) != set(REQUIRED_CONDITIONS):
        missing = sorted(set(REQUIRED_CONDITIONS) - set(by_condition))
        extra = sorted(set(by_condition) - set(REQUIRED_CONDITIONS))
        raise CausalFamilyIdentityError(
            f"condition:FAMILY_INCOMPLETE:missing={','.join(missing)}:extra={','.join(extra)}"
        )

    ordered = tuple(by_condition[name] for name in REQUIRED_CONDITIONS)
    family_id = _require_same(ordered, "family_id")
    generation = _require_same(ordered, "generation")
    checkpoint = _require_same(ordered, "checkpoint_sha256")
    tokenizer = _require_same(ordered, "tokenizer_sha256")
    runtime_build = _require_same(ordered, "runtime_build_sha256")
    loader_consumption = _require_same(ordered, "loader_consumption_sha256")
    activation_site = _require_same(ordered, "activation_site_id")
    model_input_content_schema = _require_same(ordered, "model_input_content_schema")
    clean_input, corrupted_input = _validate_model_input_topology(by_condition)

    # A control family is not five independent controls if the same execution, downstream
    # receipt, trace, or output identity can be relabeled into several conditions.
    for field in (
        "model_execution_sha256",
        "inference_receipt_sha256",
        "trace_sha256",
        "output_sha256",
    ):
        _require_unique(ordered, field)

    # Each intervention-bearing control must have its own exact intervention identity.
    intervention_ids = [
        by_condition[name].intervention_sha256 for name in REQUIRED_CONDITIONS
        if name in INTERVENTION_CONDITIONS
    ]
    if len(intervention_ids) != len(set(intervention_ids)):
        raise CausalFamilyIdentityError(
            "intervention_sha256:CROSS_CONTROL_REUSE_FORBIDDEN"
        )

    trial_digests = tuple(
        _canonical_sha256(asdict(trial), f"trial:{trial.condition}")
        for trial in ordered
    )
    family_material = {
        "schema": SCHEMA,
        "evidence_class": EVIDENCE_CLASS,
        "jspace_causal_credit": False,
        "family_id": family_id,
        "generation": generation,
        "required_conditions": list(REQUIRED_CONDITIONS),
        "trial_identity_sha256": list(trial_digests),
        "checkpoint_sha256": checkpoint,
        "tokenizer_sha256": tokenizer,
        "runtime_build_sha256": runtime_build,
        "loader_consumption_sha256": loader_consumption,
        "activation_site_id": activation_site,
        "model_input_content_schema": model_input_content_schema,
        "clean_model_input_content_sha256": clean_input.model_input_content_sha256,
        "corrupted_model_input_content_sha256": corrupted_input.model_input_content_sha256,
    }
    family_digest = _canonical_sha256(family_material, "causal_family")

    return CausalFamilyIdentityResult(
        schema=SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        jspace_causal_credit=False,
        family_id=family_id,
        generation=generation,
        required_conditions=REQUIRED_CONDITIONS,
        present_conditions=REQUIRED_CONDITIONS,
        checkpoint_sha256=checkpoint,
        tokenizer_sha256=tokenizer,
        runtime_build_sha256=runtime_build,
        loader_consumption_sha256=loader_consumption,
        activation_site_id=activation_site,
        model_input_content_schema=model_input_content_schema,
        clean_model_input_content_sha256=clean_input.model_input_content_sha256,
        corrupted_model_input_content_sha256=corrupted_input.model_input_content_sha256,
        trial_identity_sha256=trial_digests,
        family_identity_sha256=family_digest,
    )


__all__ = [
    "SCHEMA",
    "EVIDENCE_CLASS",
    "REQUIRED_CONDITIONS",
    "CausalFamilyIdentityError",
    "CausalTrialIdentity",
    "CausalFamilyIdentityResult",
    "validate_causal_family_identity",
]
