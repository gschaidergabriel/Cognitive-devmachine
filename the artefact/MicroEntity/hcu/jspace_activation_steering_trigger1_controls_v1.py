#!/usr/bin/env python3
"""Trigger-1 search wrapper with explicit ORTHOGONAL_SAME_NORM + PERMUTED controls.

This is an integration wrapper around the retained single J-Space steering donor.
It does not create a second packet wire or causal authority. It closes the owner-
required search-control gap while remaining strictly below model/J-Space causal
promotion: BASELINE_CORRUPTED, SHAM_CONTROL, OFF_TARGET_CONTROL, disjoint frozen
holdout, exact model/runtime identity, and invocation-owned intervention receipts
remain separate promotion gates.

The wrapper deliberately passes the deterministic orthogonal vector into the base
search as its equal-L2 control. That removes the impossible-success edge where the
matched-permuted wrapper called ``search_activation_steering`` with no random/equal-
norm control even though base ``SearchResult.success`` requires at least one.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from statistics import fmean
from typing import Callable, Sequence

try:
    from .jspace_activation_steering_search_v1 import (
        ActivationSteeringError,
        MAX_TRIALS,
        SearchResult,
        SteerableExecutor,
        SteeringObservation,
        _check_receipt,
        _score,
        search_activation_steering,
    )
    from .jspace_activation_steering_matched_permuted_v1 import (
        PermutedNullObservation,
        derive_permuted_null_control,
    )
    from .jspace_matched_orthogonal_control_v1 import (
        MatchedOrthogonalDirection,
        derive_matched_orthogonal_direction,
    )
    from .jspace_vector_control_v1 import VectorControlPacket, decode_vector
except ImportError:
    from jspace_activation_steering_search_v1 import (
        ActivationSteeringError,
        MAX_TRIALS,
        SearchResult,
        SteerableExecutor,
        SteeringObservation,
        _check_receipt,
        _score,
        search_activation_steering,
    )
    from jspace_activation_steering_matched_permuted_v1 import (
        PermutedNullObservation,
        derive_permuted_null_control,
    )
    from jspace_matched_orthogonal_control_v1 import (
        MatchedOrthogonalDirection,
        derive_matched_orthogonal_direction,
    )
    from jspace_vector_control_v1 import VectorControlPacket, decode_vector

SCHEMA = "HCU_JSPACE_TRIGGER1_MATCHED_CONTROL_SEARCH/v1"
EVIDENCE_CLASS = "TRIGGER1_SEARCH_CONTROLS_ONLY_NOT_JSPACE_CAUSAL"
CONTROL_LABELS = (
    "BASELINE",
    "+VECTOR",
    "SIGN_FLIP",
    "NULL_VECTOR",
    "ORTHOGONAL_SAME_NORM",
    "PERMUTED_SAME_NORM",
)


@dataclass(frozen=True)
class Trigger1MatchedControlSearchResult:
    schema: str
    evidence_class: str
    jspace_causal_credit: bool
    control_labels: tuple[str, ...]
    remaining_promotion_gates: tuple[str, ...]
    base: SearchResult
    orthogonal_control: MatchedOrthogonalDirection
    orthogonal_mean_delta: float
    directional_vs_orthogonal_gap: float
    permuted_controls: tuple[PermutedNullObservation, ...]
    max_abs_permuted_mean_delta: float
    directional_vs_permuted_gap: float
    min_orthogonal_gap: float
    min_permuted_gap: float
    success: bool


def _finite_nonnegative(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActivationSteeringError(f"{field}:FINITE_NONNEGATIVE_REQUIRED")
    number = float(value)
    if not math.isfinite(number) or number < 0.0:
        raise ActivationSteeringError(f"{field}:FINITE_NONNEGATIVE_REQUIRED")
    return number


def _nonnegative_unique_seeds(values: Sequence[int], field: str) -> tuple[int, ...]:
    seeds = tuple(values)
    if not seeds:
        raise ActivationSteeringError(f"{field}:NONEMPTY_REQUIRED")
    if any(isinstance(seed, bool) or not isinstance(seed, int) or seed < 0 for seed in seeds):
        raise ActivationSteeringError(f"{field}:NONNEGATIVE_INTEGERS_REQUIRED")
    if len(set(seeds)) != len(seeds):
        raise ActivationSteeringError(f"{field}:UNIQUE_REQUIRED")
    return seeds


def search_trigger1_matched_controls(
    executor: SteerableExecutor,
    prompt: str,
    source_packet: VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    layer_ids: Sequence[str],
    alphas: Sequence[float],
    seeds: Sequence[int],
    permutation_seeds: Sequence[int],
    score_fn: Callable[[SteeringObservation], float],
    min_delta: float = 0.1,
    min_directional_gap: float = 0.1,
    max_zero_drift: float = 1e-9,
    min_orthogonal_gap: float = 0.1,
    min_permuted_gap: float = 0.1,
    expected_source_control_condition: str = "BASELINE",
) -> Trigger1MatchedControlSearchResult:
    """Search on calibration coordinates with explicit matched controls.

    This function intentionally does *not* implement holdout selection. It is a
    calibration/search discriminator only. A caller must freeze ``base.best`` and
    evaluate a disjoint holdout family before any Trigger-1 promotion candidate.
    """
    seed_values = _nonnegative_unique_seeds(seeds, "seeds")
    permutation_seed_values = _nonnegative_unique_seeds(
        permutation_seeds, "permutation_seeds"
    )
    min_orthogonal_gap = _finite_nonnegative(min_orthogonal_gap, "min_orthogonal_gap")
    min_permuted_gap = _finite_nonnegative(min_permuted_gap, "min_permuted_gap")

    source_vector = decode_vector(
        source_packet,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
        expected_control_condition=expected_source_control_condition,
    )
    orthogonal = derive_matched_orthogonal_direction(source_vector)

    # The base search already knows how to bind an equal-L2 executed control to
    # exact hook receipts. Supplying the explicit orthogonal vector here makes its
    # random/equal-norm specificity slot an owner-required orthogonal control.
    base = search_activation_steering(
        executor,
        prompt,
        source_vector,
        vector_control_packet_sha256=source_packet.packet_sha256,
        layer_ids=layer_ids,
        alphas=alphas,
        seeds=seed_values,
        score_fn=score_fn,
        random_control_vectors=(orthogonal.vector,),
        min_delta=min_delta,
        min_directional_gap=min_directional_gap,
        min_random_specificity_gap=min_orthogonal_gap,
        max_zero_drift=max_zero_drift,
    )
    if len(base.random_direction_controls) != 1:
        raise ActivationSteeringError("ORTHOGONAL_CONTROL_EXECUTION_RECEIPT_REQUIRED")
    executed_orthogonal = base.random_direction_controls[0]
    if executed_orthogonal.applied_vector_sha256 != orthogonal.matched_vector_sha256:
        # ``matched_vector_sha256`` uses the canonicalized vector bytes, the same
        # identity domain used by ``applied_vector_sha256`` in the base harness.
        raise ActivationSteeringError("ORTHOGONAL_CONTROL_VECTOR_IDENTITY_MISMATCH")

    # Base trial accounting already includes the orthogonal control.
    base_trials = len(seed_values) * (
        1 + len(tuple(layer_ids)) * len(tuple(alphas)) + 1 + 1
    )
    extra_trials = len(permutation_seed_values) * len(seed_values)
    if base_trials + extra_trials > MAX_TRIALS:
        raise ActivationSteeringError("TRIGGER1_MATCHED_CONTROL_TRIAL_BUDGET_EXCEEDED")

    permuted_observations: list[PermutedNullObservation] = []
    packet_ids: set[str] = set()
    for permutation_seed in permutation_seed_values:
        control = derive_permuted_null_control(
            source_packet,
            current_generation=current_generation,
            expected_basis_id=expected_basis_id,
            expected_basis_sha256=expected_basis_sha256,
            expected_role=expected_role,
            seed=permutation_seed,
            expected_source_control_condition=expected_source_control_condition,
        )
        if control.packet.packet_sha256 in packet_ids:
            raise ActivationSteeringError("PERMUTED_CONTROL_DUPLICATE_PACKET_IDENTITY")
        packet_ids.add(control.packet.packet_sha256)

        scores: list[float] = []
        for seed in seed_values:
            observation = executor.run(
                prompt,
                layer_id=base.best.layer_id,
                vector=control.applied_vector,
                alpha=base.best.alpha,
                seed=seed,
            )
            _check_receipt(
                observation.hook_receipt,
                layer_id=base.best.layer_id,
                seed=seed,
                alpha=base.best.alpha,
                vector_sha256=control.applied_vector_sha256,
                require_activation_change=True,
            )
            scores.append(_score(score_fn(observation)))
        deltas = tuple(
            score - baseline for score, baseline in zip(scores, base.baseline_scores)
        )
        permuted_observations.append(PermutedNullObservation(
            seed=permutation_seed,
            permutation_sha256=control.permutation_sha256,
            packet_sha256=control.packet.packet_sha256,
            applied_vector_sha256=control.applied_vector_sha256,
            scores=tuple(scores),
            deltas=deltas,
            mean_delta=fmean(deltas),
        ))

    orthogonal_mean_delta = executed_orthogonal.mean_delta
    orthogonal_gap = base.best.mean_delta - abs(orthogonal_mean_delta)
    max_abs_permuted = max(abs(item.mean_delta) for item in permuted_observations)
    permuted_gap = base.best.mean_delta - max_abs_permuted

    return Trigger1MatchedControlSearchResult(
        schema=SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        jspace_causal_credit=False,
        control_labels=CONTROL_LABELS,
        remaining_promotion_gates=(
            "DISJOINT_CALIBRATION_TO_FROZEN_HOLDOUT",
            "BASELINE_CORRUPTED",
            "SHAM_CONTROL",
            "OFF_TARGET_CONTROL",
            "EXACT_MODEL_RUNTIME_AND_INTERVENTION_RECEIPTS",
        ),
        base=base,
        orthogonal_control=orthogonal,
        orthogonal_mean_delta=orthogonal_mean_delta,
        directional_vs_orthogonal_gap=orthogonal_gap,
        permuted_controls=tuple(permuted_observations),
        max_abs_permuted_mean_delta=max_abs_permuted,
        directional_vs_permuted_gap=permuted_gap,
        min_orthogonal_gap=min_orthogonal_gap,
        min_permuted_gap=min_permuted_gap,
        success=(
            base.success
            and orthogonal_gap >= min_orthogonal_gap
            and permuted_gap >= min_permuted_gap
        ),
    )


__all__ = [
    "SCHEMA",
    "EVIDENCE_CLASS",
    "CONTROL_LABELS",
    "Trigger1MatchedControlSearchResult",
    "search_trigger1_matched_controls",
]
