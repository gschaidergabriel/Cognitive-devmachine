"""Proof-gated bounded dependency pulse adapter for U12 segmented generations.

U12 intentionally does not treat generic EDGE_ADD as safe incremental topology change.
For the current U10 compiler contract max_depth=3, however, a new forward edge u->v can
only change seeds that reached u within <=2 hops before the mutation. This module binds that
structural proof to source/graph epochs and lets U12 use its existing LOCAL_REWRITE path for
that *specific proven bounded add*. Generic edge additions remain full-fallback territory.

Removals use U12's native EDGE_REMOVE class. U12 still owns immutable segment reuse,
generation verification, atomic head publication and last-known-good recovery.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
from typing import Callable, Sequence

from semantic_access_pulse_v12 import AccessPath, PulsePlan, PulseReceipt, SegmentedPulseProjection
from u10_invalidation_delta_v2 import U10Depth3InvalidationIndexV2


PROOF_CLASS = "EXACT_PREMUTATION_REVERSE_LE2_FOR_U10_DEPTH3"


class BoundedImpactProofError(ValueError):
    pass


@dataclass(frozen=True)
class BoundedEdgeImpactProof:
    event_id: str
    operation: str
    forward_source_ref: str
    forward_target_ref: str
    basis_source_epoch: int
    basis_graph_epoch: int
    result_source_epoch: int
    result_graph_epoch: int
    compiler_max_depth: int
    affected_seed_ids: tuple[str, ...]
    proof_class: str
    proof_hash: str


@dataclass(frozen=True)
class BoundedEdgePulseReceipt:
    original_operation: str
    u12_change_class: str
    proof_hash: str
    affected_seed_ids: tuple[str, ...]
    pulse: PulseReceipt
    authority: str = "DERIVED_ACCESS_PROJECTION_ONLY"


def _stable(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value) -> str:
    return sha256(_stable(value).encode()).hexdigest()


def _proof_payload(
    *, event_id: str, operation: str, forward_source_ref: str, forward_target_ref: str,
    basis_source_epoch: int, basis_graph_epoch: int, result_source_epoch: int,
    result_graph_epoch: int, compiler_max_depth: int, affected_seed_ids: Sequence[str],
) -> dict:
    return {
        "event_id": event_id,
        "operation": operation,
        "forward_source_ref": forward_source_ref,
        "forward_target_ref": forward_target_ref,
        "basis_source_epoch": int(basis_source_epoch),
        "basis_graph_epoch": int(basis_graph_epoch),
        "result_source_epoch": int(result_source_epoch),
        "result_graph_epoch": int(result_graph_epoch),
        "compiler_max_depth": int(compiler_max_depth),
        "affected_seed_ids": sorted(set(map(str, affected_seed_ids))),
        "proof_class": PROOF_CLASS,
    }


def build_bounded_edge_impact_proof(
    index: U10Depth3InvalidationIndexV2,
    *,
    event_id: str,
    operation: str,
    forward_source_ref: str,
    forward_target_ref: str,
    basis_source_epoch: int,
    basis_graph_epoch: int,
    result_source_epoch: int,
    result_graph_epoch: int,
    compiler_max_depth: int = 3,
) -> BoundedEdgeImpactProof:
    operation = operation.upper()
    if operation not in {"ADD", "REMOVE"}:
        raise BoundedImpactProofError("operation must be ADD or REMOVE")
    if compiler_max_depth != 3:
        raise BoundedImpactProofError("V1 proof is valid only for current U10 max_depth=3")
    if result_source_epoch < basis_source_epoch or result_graph_epoch < basis_graph_epoch:
        raise BoundedImpactProofError("result epoch may not regress")
    if result_source_epoch == basis_source_epoch and result_graph_epoch == basis_graph_epoch:
        raise BoundedImpactProofError("result must advance source or graph epoch")

    affected = index.affected_anchors_before_edge_mutation(
        forward_source_ref,
        basis_source_epoch=basis_source_epoch,
        basis_graph_epoch=basis_graph_epoch,
    )
    payload = _proof_payload(
        event_id=event_id,
        operation=operation,
        forward_source_ref=forward_source_ref,
        forward_target_ref=forward_target_ref,
        basis_source_epoch=basis_source_epoch,
        basis_graph_epoch=basis_graph_epoch,
        result_source_epoch=result_source_epoch,
        result_graph_epoch=result_graph_epoch,
        compiler_max_depth=compiler_max_depth,
        affected_seed_ids=affected,
    )
    return BoundedEdgeImpactProof(
        event_id=event_id,
        operation=operation,
        forward_source_ref=forward_source_ref,
        forward_target_ref=forward_target_ref,
        basis_source_epoch=int(basis_source_epoch),
        basis_graph_epoch=int(basis_graph_epoch),
        result_source_epoch=int(result_source_epoch),
        result_graph_epoch=int(result_graph_epoch),
        compiler_max_depth=compiler_max_depth,
        affected_seed_ids=tuple(payload["affected_seed_ids"]),
        proof_class=PROOF_CLASS,
        proof_hash=_hash(payload),
    )


def verify_bounded_edge_impact_proof(proof: BoundedEdgeImpactProof) -> None:
    if proof.proof_class != PROOF_CLASS or proof.compiler_max_depth != 3:
        raise BoundedImpactProofError("unsupported proof contract")
    payload = _proof_payload(
        event_id=proof.event_id,
        operation=proof.operation,
        forward_source_ref=proof.forward_source_ref,
        forward_target_ref=proof.forward_target_ref,
        basis_source_epoch=proof.basis_source_epoch,
        basis_graph_epoch=proof.basis_graph_epoch,
        result_source_epoch=proof.result_source_epoch,
        result_graph_epoch=proof.result_graph_epoch,
        compiler_max_depth=proof.compiler_max_depth,
        affected_seed_ids=proof.affected_seed_ids,
    )
    if _hash(payload) != proof.proof_hash:
        raise BoundedImpactProofError("impact proof hash mismatch")


def advance_invalidation_index(
    index: U10Depth3InvalidationIndexV2,
    proof: BoundedEdgeImpactProof,
):
    """Advance the structural index after the caller has accepted the pre-mutation proof."""
    verify_bounded_edge_impact_proof(proof)
    kwargs = dict(
        basis_source_epoch=proof.basis_source_epoch,
        basis_graph_epoch=proof.basis_graph_epoch,
        result_source_epoch=proof.result_source_epoch,
        result_graph_epoch=proof.result_graph_epoch,
    )
    if proof.operation == "ADD":
        return index.add_forward_edge(proof.forward_source_ref, proof.forward_target_ref, **kwargs)
    return index.remove_forward_edge(proof.forward_source_ref, proof.forward_target_ref, **kwargs)


def apply_u12_bounded_edge_pulse(
    projection: SegmentedPulseProjection,
    proof: BoundedEdgeImpactProof,
    *,
    recompute_seed: Callable[[str], Sequence[AccessPath]],
    recompute_all_seeds: Callable[[], Sequence[str]],
    incremental_fraction_limit: float = 0.25,
) -> BoundedEdgePulseReceipt:
    """Apply a proven bounded edge mutation to U12 without weakening generic U12 safety.

    ADD maps to U12 LOCAL_REWRITE only after exact proof verification. REMOVE uses the native
    EDGE_REMOVE class. The proof remains explicit in the returned receipt so provenance never
    misrepresents a topology expansion as an ordinary local value rewrite.
    """
    verify_bounded_edge_impact_proof(proof)
    head = projection.head_basis()
    if head is None:
        raise BoundedImpactProofError("U12 projection has no current head")
    if (head[0], head[1]) != (proof.basis_source_epoch, proof.basis_graph_epoch):
        raise BoundedImpactProofError(
            f"U12 head basis {head[:2]} does not match proof basis "
            f"{(proof.basis_source_epoch, proof.basis_graph_epoch)}"
        )

    u12_class = "EDGE_REMOVE" if proof.operation == "REMOVE" else "LOCAL_REWRITE"
    plan = PulsePlan(
        event_id=proof.event_id,
        change_class=u12_class,
        changed_logical_ids=(proof.forward_source_ref, proof.forward_target_ref),
        impact_seed_ids=proof.affected_seed_ids,
        impact_complete=True,
        to_source_epoch=proof.result_source_epoch,
        to_graph_epoch=proof.result_graph_epoch,
    )
    pulse = projection.apply_pulse(
        plan,
        recompute_seed=recompute_seed,
        recompute_all_seeds=recompute_all_seeds,
        incremental_fraction_limit=incremental_fraction_limit,
    )
    return BoundedEdgePulseReceipt(
        original_operation=proof.operation,
        u12_change_class=u12_class,
        proof_hash=proof.proof_hash,
        affected_seed_ids=proof.affected_seed_ids,
        pulse=pulse,
    )
