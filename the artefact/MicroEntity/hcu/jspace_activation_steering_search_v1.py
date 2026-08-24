#!/usr/bin/env python3
"""Bounded provider-independent search harness for direct HCU/J-Space activation steering.

The harness assumes a validated JSPACE_VECTOR_CONTROL_ABI/v1 packet has already been decoded
into the vector passed here. It can only claim a bounded *steering-search* result when the
executor returns a hook receipt that binds the exact applied vector, layer, alpha and seed.

Important supervisor-8.68 evidence boundary: this module does not implement the full causal
family required for J-Space intervention promotion (clean + corrupted + target + sham +
off-target controls). Therefore even ``SearchResult.success`` is explicitly search-level only
and can never mint J-Space causal/model-runtime credit by itself.
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
# This v1 search has a baseline, directional target intervention, sign control and physical
# zero-vector control. Those are useful discriminators, but they are not substitutes for the
# three missing controls below under the current HCU J-Space intervention gate.
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
    min_delta: float
    min_directional_gap: float
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
        # Allowing a changed post hash here would make implementation drift look like a
        # harmless zero control and weaken the causal discriminator.
        raise ActivationSteeringError("ZERO_VECTOR_CONTROL_CHANGED_ACTIVATION")


def _score(value: float) -> float:
    return _finite(value, "score")


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
    min_delta: float = 0.1,
    min_directional_gap: float = 0.1,
    max_zero_drift: float = 1e-9,
) -> SearchResult:
    """Search layer/alpha coordinates with sign + zero controls.

    ``success`` means the bounded steering-search criteria passed. It deliberately does not
    mean J-Space causality. Current causal promotion separately requires the full clean /
    corrupted / target / sham / off-target family and exact model/runtime/loader/trace binding.

    This is intentionally bounded. A caller wanting broader search must explicitly provide a
    larger finite grid while remaining below MAX_TRIALS.
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
    trials = len(seed_values) * (1 + len(layers) * len(alpha_values) + 1)
    if trials > MAX_TRIALS:
        raise ActivationSteeringError("SEARCH_TRIAL_BUDGET_EXCEEDED")

    min_delta = _finite(min_delta, "min_delta")
    min_directional_gap = _finite(min_directional_gap, "min_directional_gap")
    max_zero_drift = _finite(max_zero_drift, "max_zero_drift")
    if min_delta < 0 or min_directional_gap < 0 or max_zero_drift < 0:
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

    directional_gap = best.mean_delta - sign_control.mean_delta
    success = (
        best.mean_delta >= min_delta
        and directional_gap >= min_directional_gap
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
        min_delta=min_delta,
        min_directional_gap=min_directional_gap,
        max_zero_drift=max_zero_drift,
        success=success,
    )
