#!/usr/bin/env python3
"""Bounded provider-independent search harness for direct HCU/J-Space activation steering.

The harness assumes a validated JSPACE_VECTOR_CONTROL_ABI/v1 packet has already been decoded
into the vector passed here. It can only claim a bounded *steering-search* result when the
executor returns a hook receipt that binds the exact applied vector, layer, alpha and seed.

Important evidence boundary: this module does not implement the full causal family required
for J-Space intervention promotion (clean + corrupted + target + sham + off-target controls).
Therefore even ``SearchResult.success`` is explicitly search-level only and can never mint
J-Space causal/model-runtime credit by itself.

The search-level discriminator includes sign-paired steering, a physical zero-vector no-op,
and caller-supplied equal-L2-norm random-direction controls. The latter distinguish a
specific steering direction from the counterhypothesis that any same-magnitude activation
perturbation produces the observed score change. They do not automatically promote to the
full canonical SHAM_CONTROL required by the J-Space causal gate.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from statistics import fmean
from typing import Callable, Protocol, Sequence

try:
    from .entry_canonicalization_v1 import canonicalize
except ImportError:
    from entry_canonicalization_v1 import canonicalize

HOOK_RECEIPT_SCHEMA = "HCU_ACTIVATION_STEERING_HOOK_RECEIPT/v1"
SEARCH_RESULT_SCHEMA = "HCU_JSPACE_ACTIVATION_STEERING_SEARCH/v1"
EVIDENCE_CLASS = "STEERING_SEARCH_ONLY_NOT_JSPACE_CAUSAL"
REQUIRED_CAUSAL_CONTROLS = (
    "BASELINE_CLEAN",
    "BASELINE_CORRUPTED",
    "INTERVENTION_TARGET",
    "SHAM_CONTROL",
    "OFF_TARGET_CONTROL",
)
# These search controls improve specificity but remain below the canonical causal family.
MISSING_CAUSAL_CONTROLS = (
    "BASELINE_CORRUPTED",
    "SHAM_CONTROL",
    "OFF_TARGET_CONTROL",
)
MAX_TRIALS = 4096


class ActivationSteeringError(ValueError):
    pass


@dataclass(frozen=True)
class HookReceipt:
    schema: str
    executor_id: str
    invocation_id: str
    layer_id: str
    seed: int
    alpha: float
    applied_vector_sha256: str
    pre_activation_sha256: str
    post_activation_sha256: str


@dataclass(frozen=True)
class SteeringObservation:
    output_text: str
    hook_receipt: HookReceipt | None


class SteerableExecutor(Protocol):
    def run(
        self,
        prompt: str,
        *,
        layer_id: str | None,
        vector: tuple[float, ...] | None,
        alpha: float,
        seed: int,
    ) -> SteeringObservation: ...


@dataclass(frozen=True)
class Candidate:
    layer_id: str
    alpha: float
    scores: tuple[float, ...]
    deltas: tuple[float, ...]
    mean_score: float
    mean_delta: float


@dataclass(frozen=True)
class RandomDirectionControl:
    applied_vector_sha256: str
    scores: tuple[float, ...]
    deltas: tuple[float, ...]
    mean_score: float
    mean_delta: float


@dataclass(frozen=True)
class SearchResult:
    schema: str
    evidence_class: str
    jspace_causal_credit: bool
    required_causal_controls: tuple[str, ...]
    missing_causal_controls: tuple[str, ...]
    vector_control_packet_sha256: str
    applied_vector_sha256: str
    baseline_scores: tuple[float, ...]
    candidates: tuple[Candidate, ...]
    best: Candidate
    sign_control: Candidate
    zero_control_mean_delta: float
    random_direction_controls: tuple[RandomDirectionControl, ...]
    random_control_max_abs_mean_delta: float | None
    random_specificity_gap: float | None
    min_delta: float
    min_directional_gap: float
    min_random_specificity_gap: float
    max_zero_drift: float
    success: bool


def _sha(value: str, field: str) -> str:
    if not isinstance(value, str) or len(value) != 64 or value.lower() != value or any(ch not in "0123456789abcdef" for ch in value):
        raise ActivationSteeringError(f"{field}:LOWERCASE_SHA256_REQUIRED")
    return value


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActivationSteeringError(f"{field}:FINITE_NUMBER_REQUIRED")
    value = float(value)
    if not math.isfinite(value):
        raise ActivationSteeringError(f"{field}:FINITE_NUMBER_REQUIRED")
    return value


def _l2_norm(vector: Sequence[float]) -> float:
    return math.sqrt(sum(value * value for value in vector))


def applied_vector_sha256(vector: Sequence[float]) -> str:
    if isinstance(vector, (str, bytes, bytearray)) or not isinstance(vector, Sequence) or not vector:
        raise ActivationSteeringError("vector:NONEMPTY_SEQUENCE_REQUIRED")
    normalized = tuple(_finite(value, f"vector[{index}]") for index, value in enumerate(vector))
    return hashlib.sha256(canonicalize(list(normalized))).hexdigest()


def _check_receipt(
    receipt: HookReceipt | None,
    *,
    layer_id: str,
    seed: int,
    alpha: float,
    vector_sha256: str,
    require_activation_change: bool = True,
) -> None:
    if not isinstance(receipt, HookReceipt):
        raise ActivationSteeringError("EXECUTOR_HOOK_RECEIPT_REQUIRED")
    if receipt.schema != HOOK_RECEIPT_SCHEMA:
        raise ActivationSteeringError("EXECUTOR_HOOK_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.layer_id != layer_id or receipt.seed != seed or receipt.alpha != alpha:
        raise ActivationSteeringError("EXECUTOR_HOOK_COORDINATE_MISMATCH")
    if _sha(receipt.applied_vector_sha256, "applied_vector_sha256") != vector_sha256:
        raise ActivationSteeringError("EXECUTOR_APPLIED_VECTOR_MISMATCH")
    for value, field in ((receipt.pre_activation_sha256, "pre_activation_sha256"), (receipt.post_activation_sha256, "post_activation_sha256")):
        _sha(value, field)
    if require_activation_change:
        if alpha != 0.0 and receipt.pre_activation_sha256 == receipt.post_activation_sha256:
            raise ActivationSteeringError("EXECUTOR_ACTIVATION_UNCHANGED")
    elif receipt.pre_activation_sha256 != receipt.post_activation_sha256:
        # An exact zero-vector control must be a physical no-op at the target activation.
        raise ActivationSteeringError("ZERO_VECTOR_CONTROL_CHANGED_ACTIVATION")


def _score(value: float) -> float:
    return _finite(value, "score")


def _normalize_random_controls(
    decoded_vector: tuple[float, ...],
    random_control_vectors: Sequence[Sequence[float]],
    *,
    norm_tolerance: float,
) -> tuple[tuple[float, ...], ...]:
    target_norm = _l2_norm(decoded_vector)
    if target_norm == 0.0:
        raise ActivationSteeringError("decoded_vector:NONZERO_NORM_REQUIRED")
    controls = []
    seen = set()
    neg_target = tuple(-value for value in decoded_vector)
    allowed_error = max(1.0, target_norm) * norm_tolerance
    for control_index, raw in enumerate(random_control_vectors):
        if isinstance(raw, (str, bytes, bytearray)) or not isinstance(raw, Sequence):
            raise ActivationSteeringError(f"random_control_vectors[{control_index}]:SEQUENCE_REQUIRED")
        control = tuple(_finite(value, f"random_control_vectors[{control_index}][{index}]") for index, value in enumerate(raw))
        if len(control) != len(decoded_vector):
            raise ActivationSteeringError("random_control_vectors:DIMENSION_MISMATCH")
        if control == decoded_vector or control == neg_target:
            raise ActivationSteeringError("random_control_vectors:TARGET_OR_SIGN_ALIAS_FORBIDDEN")
        if abs(_l2_norm(control) - target_norm) > allowed_error:
            raise ActivationSteeringError("random_control_vectors:EQUAL_L2_NORM_REQUIRED")
        digest = applied_vector_sha256(control)
        if digest in seen:
            raise ActivationSteeringError("random_control_vectors:UNIQUE_REQUIRED")
        seen.add(digest)
        controls.append(control)
    return tuple(controls)


def search_activation_steering(
    executor: SteerableExecutor,
    prompt: str,
    decoded_vector: Sequence[float],
    *,
    vector_control_packet_sha256: str,
    layer_ids: Sequence[str],
    alphas: Sequence[float],
    seeds: Sequence[int],
    score_fn: Callable[[SteeringObservation], float],
    random_control_vectors: Sequence[Sequence[float]] = (),
    min_delta: float = 0.1,
    min_directional_gap: float = 0.1,
    min_random_specificity_gap: float = 0.1,
    max_zero_drift: float = 1e-9,
    random_norm_tolerance: float = 1e-9,
) -> SearchResult:
    """Search layer/alpha coordinates with sign, zero, and equal-norm random controls.

    ``success`` means the bounded steering-search criteria passed. It deliberately does not
    mean J-Space causality. Current causal promotion separately requires the full clean /
    corrupted / target / sham / off-target family and exact model/runtime/loader/trace binding.

    At least one equal-L2-norm random-direction control is required for ``success``. Omitting
    random controls remains callable for compatibility but fails closed to ``success=False``.
    This is intentionally bounded; broader searches must remain below ``MAX_TRIALS``.
    """
    if not isinstance(prompt, str) or not prompt:
        raise ActivationSteeringError("prompt:NONEMPTY_STRING_REQUIRED")
    packet_sha = _sha(vector_control_packet_sha256, "vector_control_packet_sha256")
    vector = tuple(_finite(value, f"decoded_vector[{index}]") for index, value in enumerate(decoded_vector))
    if not vector:
        raise ActivationSteeringError("decoded_vector:NONEMPTY_REQUIRED")
    vector_sha = applied_vector_sha256(vector)
    layers = tuple(layer_ids)
    if not layers or any(not isinstance(layer, str) or not layer for layer in layers) or len(set(layers)) != len(layers):
        raise ActivationSteeringError("layer_ids:UNIQUE_NONEMPTY_STRINGS_REQUIRED")
    alpha_values = tuple(_finite(value, "alpha") for value in alphas)
    if not alpha_values or any(value == 0.0 for value in alpha_values) or len(set(alpha_values)) != len(alpha_values):
        raise ActivationSteeringError("alphas:UNIQUE_NONZERO_VALUES_REQUIRED")
    seed_values = tuple(seeds)
    if not seed_values or any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seed_values):
        raise ActivationSteeringError("seeds:NONNEGATIVE_INTEGERS_REQUIRED")
    if len(set(seed_values)) != len(seed_values):
        raise ActivationSteeringError("seeds:UNIQUE_REQUIRED")
    if any(-alpha not in alpha_values for alpha in alpha_values):
        raise ActivationSteeringError("alphas:SIGN_PAIRED_GRID_REQUIRED")

    random_norm_tolerance = _finite(random_norm_tolerance, "random_norm_tolerance")
    if random_norm_tolerance < 0:
        raise ActivationSteeringError("random_norm_tolerance:NONNEGATIVE_REQUIRED")
    random_vectors = _normalize_random_controls(
        vector,
        random_control_vectors,
        norm_tolerance=random_norm_tolerance,
    ) if random_control_vectors else ()

    trials = len(seed_values) * (1 + len(layers) * len(alpha_values) + 1 + len(random_vectors))
    if trials > MAX_TRIALS:
        raise ActivationSteeringError("SEARCH_TRIAL_BUDGET_EXCEEDED")

    min_delta = _finite(min_delta, "min_delta")
    min_directional_gap = _finite(min_directional_gap, "min_directional_gap")
    min_random_specificity_gap = _finite(min_random_specificity_gap, "min_random_specificity_gap")
    max_zero_drift = _finite(max_zero_drift, "max_zero_drift")
    if min_delta < 0 or min_directional_gap < 0 or min_random_specificity_gap < 0 or max_zero_drift < 0:
        raise ActivationSteeringError("thresholds:NONNEGATIVE_REQUIRED")

    baseline_scores = []
    for seed in seed_values:
        observation = executor.run(prompt, layer_id=None, vector=None, alpha=0.0, seed=seed)
        if observation.hook_receipt is not None:
            raise ActivationSteeringError("BASELINE_MUST_NOT_HAVE_STEERING_HOOK_RECEIPT")
        baseline_scores.append(_score(score_fn(observation)))

    candidates = []
    lookup = {}
    for layer in layers:
        for alpha in alpha_values:
            scores = []
            for seed in seed_values:
                observation = executor.run(prompt, layer_id=layer, vector=vector, alpha=alpha, seed=seed)
                _check_receipt(
                    observation.hook_receipt,
                    layer_id=layer,
                    seed=seed,
                    alpha=alpha,
                    vector_sha256=vector_sha,
                    require_activation_change=True,
                )
                scores.append(_score(score_fn(observation)))
            deltas = tuple(score - base for score, base in zip(scores, baseline_scores))
            candidate = Candidate(layer, alpha, tuple(scores), deltas, fmean(scores), fmean(deltas))
            candidates.append(candidate)
            lookup[(layer, alpha)] = candidate

    best = max(candidates, key=lambda item: (item.mean_delta, -abs(item.alpha), item.layer_id))
    sign_control = lookup[(best.layer_id, -best.alpha)]

    zero_vector = tuple(0.0 for _ in vector)
    zero_sha = applied_vector_sha256(zero_vector)
    zero_scores = []
    for seed in seed_values:
        observation = executor.run(prompt, layer_id=best.layer_id, vector=zero_vector, alpha=best.alpha, seed=seed)
        _check_receipt(
            observation.hook_receipt,
            layer_id=best.layer_id,
            seed=seed,
            alpha=best.alpha,
            vector_sha256=zero_sha,
            require_activation_change=False,
        )
        zero_scores.append(_score(score_fn(observation)))
    zero_delta = fmean(score - base for score, base in zip(zero_scores, baseline_scores))

    random_controls = []
    for control in random_vectors:
        control_sha = applied_vector_sha256(control)
        scores = []
        for seed in seed_values:
            observation = executor.run(prompt, layer_id=best.layer_id, vector=control, alpha=best.alpha, seed=seed)
            _check_receipt(
                observation.hook_receipt,
                layer_id=best.layer_id,
                seed=seed,
                alpha=best.alpha,
                vector_sha256=control_sha,
                require_activation_change=True,
            )
            scores.append(_score(score_fn(observation)))
        deltas = tuple(score - base for score, base in zip(scores, baseline_scores))
        random_controls.append(
            RandomDirectionControl(
                control_sha,
                tuple(scores),
                deltas,
                fmean(scores),
                fmean(deltas),
            )
        )

    directional_gap = best.mean_delta - sign_control.mean_delta
    random_max_abs_delta = (
        max(abs(control.mean_delta) for control in random_controls)
        if random_controls else None
    )
    random_specificity_gap = (
        best.mean_delta - random_max_abs_delta
        if random_max_abs_delta is not None else None
    )
    success = (
        bool(random_controls)
        and best.mean_delta >= min_delta
        and directional_gap >= min_directional_gap
        and random_specificity_gap is not None
        and random_specificity_gap >= min_random_specificity_gap
        and abs(zero_delta) <= max_zero_drift
    )
    return SearchResult(
        schema=SEARCH_RESULT_SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        jspace_causal_credit=False,
        required_causal_controls=REQUIRED_CAUSAL_CONTROLS,
        missing_causal_controls=MISSING_CAUSAL_CONTROLS,
        vector_control_packet_sha256=packet_sha,
        applied_vector_sha256=vector_sha,
        baseline_scores=tuple(baseline_scores),
        candidates=tuple(candidates),
        best=best,
        sign_control=sign_control,
        zero_control_mean_delta=zero_delta,
        random_direction_controls=tuple(random_controls),
        random_control_max_abs_mean_delta=random_max_abs_delta,
        random_specificity_gap=random_specificity_gap,
        min_delta=min_delta,
        min_directional_gap=min_directional_gap,
        min_random_specificity_gap=min_random_specificity_gap,
        max_zero_drift=max_zero_drift,
        success=success,
    )