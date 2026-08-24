#!/usr/bin/env python3
"""Matched PERMUTED-null control for EntityOS/HCU activation steering.

This module strengthens the existing provider-independent
``jspace_activation_steering_search_v1`` harness without creating a second J-Space
wire. Every counted permuted null is derived from, and re-encoded through, the
single canonical ``JSPACE_VECTOR_CONTROL_ABI/v1`` packet path.

It is source/component instrumentation only. A PASS here cannot mint model,
J-Space, HCU, EntityOS, training, state, truth, or effect authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import math
from statistics import fmean
from typing import Callable, Sequence

try:
    from .entry_canonicalization_v1 import canonicalize
    from .jspace_activation_steering_search_v1 import (
        ActivationSteeringError,
        MAX_TRIALS,
        SearchResult,
        SteerableExecutor,
        SteeringObservation,
        _check_receipt,
        _score,
        applied_vector_sha256,
        search_activation_steering,
    )
    from .jspace_vector_control_v1 import (
        VectorControlPacket,
        decode_vector,
        encode_vector,
        reconstruction_metrics,
        validate_packet,
    )
except ImportError:
    from entry_canonicalization_v1 import canonicalize
    from jspace_activation_steering_search_v1 import (
        ActivationSteeringError,
        MAX_TRIALS,
        SearchResult,
        SteerableExecutor,
        SteeringObservation,
        _check_receipt,
        _score,
        applied_vector_sha256,
        search_activation_steering,
    )
    from jspace_vector_control_v1 import (
        VectorControlPacket,
        decode_vector,
        encode_vector,
        reconstruction_metrics,
        validate_packet,
    )

SCHEMA = "HCU_JSPACE_ACTIVATION_STEERING_MATCHED_PERMUTED_SEARCH/v1"
EVIDENCE_CLASS = "STEERING_SEARCH_WITH_MATCHED_PERMUTED_NULL_ONLY_NOT_JSPACE_CAUSAL"
PERMUTATION_DERIVATION_SCHEMA = "HCU_JSPACE_PERMUTED_NULL_DERIVATION/v1"
MAX_PERMUTATION_ATTEMPTS = 128


@dataclass(frozen=True)
class PermutedNullControl:
    """One deterministic ABI-bound magnitude-preserving null direction."""

    seed: int
    derivation_attempt: int
    permutation: tuple[int, ...]
    permutation_sha256: str
    source_packet_sha256: str
    packet: VectorControlPacket
    applied_vector: tuple[float, ...]
    applied_vector_sha256: str


@dataclass(frozen=True)
class PermutedNullObservation:
    seed: int
    permutation_sha256: str
    packet_sha256: str
    applied_vector_sha256: str
    scores: tuple[float, ...]
    deltas: tuple[float, ...]
    mean_delta: float


@dataclass(frozen=True)
class MatchedPermutedSearchResult:
    schema: str
    evidence_class: str
    jspace_causal_credit: bool
    remaining_causal_controls: tuple[str, ...]
    base: SearchResult
    permuted_controls: tuple[PermutedNullObservation, ...]
    max_permuted_mean_delta: float
    directional_vs_permuted_gap: float
    min_permuted_gap: float
    success: bool


def _nonnegative_int(value: int, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ActivationSteeringError(f"{field}:NONNEGATIVE_INTEGER_REQUIRED")
    return value


def _finite_nonnegative(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ActivationSteeringError(f"{field}:FINITE_NONNEGATIVE_REQUIRED")
    value = float(value)
    if not math.isfinite(value) or value < 0.0:
        raise ActivationSteeringError(f"{field}:FINITE_NONNEGATIVE_REQUIRED")
    return value


def _permutation_for_seed(
    *,
    source_packet_sha256: str,
    seed: int,
    dimension: int,
    attempt: int,
) -> tuple[int, ...]:
    """Derive a deterministic permutation without host RNG state."""
    ranked: list[tuple[bytes, int]] = []
    for index in range(dimension):
        material = {
            "schema": PERMUTATION_DERIVATION_SCHEMA,
            "source_packet_sha256": source_packet_sha256,
            "seed": seed,
            "attempt": attempt,
            "index": index,
        }
        ranked.append((hashlib.sha256(canonicalize(material)).digest(), index))
    ranked.sort()
    return tuple(index for _, index in ranked)


def _permutation_sha256(
    *,
    source_packet_sha256: str,
    seed: int,
    attempt: int,
    permutation: Sequence[int],
) -> str:
    return hashlib.sha256(canonicalize({
        "schema": PERMUTATION_DERIVATION_SCHEMA,
        "source_packet_sha256": source_packet_sha256,
        "seed": seed,
        "attempt": attempt,
        "permutation": list(permutation),
    })).hexdigest()


def derive_permuted_null_control(
    source_packet: VectorControlPacket,
    *,
    current_generation: int,
    expected_basis_id: str,
    expected_basis_sha256: str,
    expected_role: str,
    seed: int,
    expected_source_control_condition: str = "BASELINE",
) -> PermutedNullControl:
    """Derive one nontrivial ``PERMUTED`` control through the canonical ABI.

    The source packet is first validated/decoded at exact generation/basis/role.
    We then search deterministically for a coordinate permutation that changes
    the applied coordinate sequence. The permuted vector is re-encoded using the
    same canonical ABI with ``control_condition=PERMUTED``.

    The re-encoded packet must preserve the exact q8 coordinate multiset and
    reconstruction scale. This proves the control is magnitude matched at the
    currently admitted q8 packet representation rather than merely carrying a
    ``PERMUTED`` label.
    """
    seed = _nonnegative_int(seed, "seed")
    validate_packet(source_packet)
    source_vector = decode_vector(
        source_packet,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
        expected_control_condition=expected_source_control_condition,
    )
    if len(source_vector) < 2:
        raise ActivationSteeringError("PERMUTED_CONTROL_DIMENSION_AT_LEAST_TWO_REQUIRED")

    source_indices = tuple(range(len(source_vector)))
    for attempt in range(MAX_PERMUTATION_ATTEMPTS):
        permutation = _permutation_for_seed(
            source_packet_sha256=source_packet.packet_sha256,
            seed=seed,
            dimension=len(source_vector),
            attempt=attempt,
        )
        if permutation == source_indices:
            continue
        permuted_vector = tuple(source_vector[index] for index in permutation)
        if permuted_vector == source_vector:
            continue

        packet = encode_vector(
            permuted_vector,
            basis_id=source_packet.basis_id,
            basis_sha256=source_packet.basis_sha256,
            generation=source_packet.generation,
            role=source_packet.role,
            control_condition="PERMUTED",
        )
        validate_packet(packet)
        applied = decode_vector(
            packet,
            current_generation=current_generation,
            expected_basis_id=expected_basis_id,
            expected_basis_sha256=expected_basis_sha256,
            expected_role=expected_role,
            expected_control_condition="PERMUTED",
        )

        if sorted(packet.q8_values) != sorted(source_packet.q8_values):
            raise ActivationSteeringError("PERMUTED_CONTROL_Q8_MULTISET_NOT_PRESERVED")
        if (
            packet.scale_numerator != source_packet.scale_numerator
            or packet.scale_denominator != source_packet.scale_denominator
        ):
            raise ActivationSteeringError("PERMUTED_CONTROL_SCALE_NOT_PRESERVED")
        if reconstruction_metrics(permuted_vector, applied)["normalized_max_error"] > (1.0 / 254.0 + 1e-15):
            raise ActivationSteeringError("PERMUTED_CONTROL_RECONSTRUCTION_BOUND_EXCEEDED")

        permutation_sha = _permutation_sha256(
            source_packet_sha256=source_packet.packet_sha256,
            seed=seed,
            attempt=attempt,
            permutation=permutation,
        )
        return PermutedNullControl(
            seed=seed,
            derivation_attempt=attempt,
            permutation=permutation,
            permutation_sha256=permutation_sha,
            source_packet_sha256=source_packet.packet_sha256,
            packet=packet,
            applied_vector=applied,
            applied_vector_sha256=applied_vector_sha256(applied),
        )

    raise ActivationSteeringError("PERMUTED_CONTROL_NONTRIVIAL_DERIVATION_UNAVAILABLE")


def search_activation_steering_with_permuted_nulls(
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
    min_permuted_gap: float = 0.1,
    expected_source_control_condition: str = "BASELINE",
) -> MatchedPermutedSearchResult:
    """Run the existing steering search plus ABI-bound PERMUTED nulls.

    The base search remains authoritative for baseline/sign/zero controls. The
    selected target coordinate is then challenged with deterministic, exact-q8
    magnitude-matched ``PERMUTED`` controls at the *same* layer and alpha.

    This is a deliberately conservative bounded discriminator: the target must
    beat the strongest observed permuted mean delta by ``min_permuted_gap``.
    Statistical/holdout promotion remains governed by the higher-level causal
    steering acceptance protocol. A matched PERMUTED pass remains search-level
    evidence and does not satisfy the required corrupted/sham/off-target family.
    """
    min_permuted_gap = _finite_nonnegative(min_permuted_gap, "min_permuted_gap")
    permutation_seed_values = tuple(
        _nonnegative_int(seed, "permutation_seed") for seed in permutation_seeds
    )
    if not permutation_seed_values:
        raise ActivationSteeringError("permutation_seeds:NONEMPTY_REQUIRED")
    if len(set(permutation_seed_values)) != len(permutation_seed_values):
        raise ActivationSteeringError("permutation_seeds:UNIQUE_REQUIRED")

    source_vector = decode_vector(
        source_packet,
        current_generation=current_generation,
        expected_basis_id=expected_basis_id,
        expected_basis_sha256=expected_basis_sha256,
        expected_role=expected_role,
        expected_control_condition=expected_source_control_condition,
    )
    base = search_activation_steering(
        executor,
        prompt,
        source_vector,
        vector_control_packet_sha256=source_packet.packet_sha256,
        layer_ids=layer_ids,
        alphas=alphas,
        seeds=seeds,
        score_fn=score_fn,
        min_delta=min_delta,
        min_directional_gap=min_directional_gap,
        max_zero_drift=max_zero_drift,
    )

    seed_values = tuple(seeds)
    base_trials = len(seed_values) * (1 + len(layer_ids) * len(alphas) + 1)
    extra_trials = len(permutation_seed_values) * len(seed_values)
    if base_trials + extra_trials > MAX_TRIALS:
        raise ActivationSteeringError("PERMUTED_CONTROL_TRIAL_BUDGET_EXCEEDED")

    controls: list[PermutedNullObservation] = []
    packet_identities: set[str] = set()
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
        if control.packet.packet_sha256 in packet_identities:
            raise ActivationSteeringError("PERMUTED_CONTROL_DUPLICATE_PACKET_IDENTITY")
        packet_identities.add(control.packet.packet_sha256)

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

        deltas = tuple(score - baseline for score, baseline in zip(scores, base.baseline_scores))
        controls.append(PermutedNullObservation(
            seed=permutation_seed,
            permutation_sha256=control.permutation_sha256,
            packet_sha256=control.packet.packet_sha256,
            applied_vector_sha256=control.applied_vector_sha256,
            scores=tuple(scores),
            deltas=deltas,
            mean_delta=fmean(deltas),
        ))

    max_permuted = max(control.mean_delta for control in controls)
    gap = base.best.mean_delta - max_permuted
    return MatchedPermutedSearchResult(
        schema=SCHEMA,
        evidence_class=EVIDENCE_CLASS,
        jspace_causal_credit=False,
        remaining_causal_controls=base.missing_causal_controls,
        base=base,
        permuted_controls=tuple(controls),
        max_permuted_mean_delta=max_permuted,
        directional_vs_permuted_gap=gap,
        min_permuted_gap=min_permuted_gap,
        success=base.success and gap >= min_permuted_gap,
    )
