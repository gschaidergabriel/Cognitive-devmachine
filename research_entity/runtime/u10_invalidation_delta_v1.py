"""Targeted structural invalidation helper for the Clay U10 Possibility Compiler.

RESEARCH CANDIDATE. The current U10 compiler uses max_depth=3. Any compiled anchor field
that can change after mutation of forward edge u->v must reach u in <=2 hops before the
mutation. Therefore an exact <=2-hop index over the *reversed* graph gives a conservative
and complete affected-anchor set without rebuilding every active anchor field.

This helper does not decide whether a field's weighted ranking actually changes. It provides
an exact no-false-negative structural invalidation frontier; U10 still recompiles/verifies
those affected fields and retains its truncation/epoch/LKG safeguards.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from semantic_reachability_delta_v1 import BoundedReachability2, ReachabilityDeltaReceipt


@dataclass(frozen=True)
class U10InvalidationReceipt:
    operation: str
    forward_source_ref: str
    forward_target_ref: str
    affected_anchor_refs: tuple[str, ...]
    affected_anchor_count: int
    total_active_anchors: int
    reusable_anchor_count: int
    reachability_delta: ReachabilityDeltaReceipt
    completeness_contract: str = "ALL_DEPTH3_PATHS_USING_EDGE_START_AT_ANCHOR_WITHIN_PREMUTATION_LE2_OF_SOURCE"
    authority: str = "DERIVED_INVALIDATION_ONLY"


class U10Depth3InvalidationIndex:
    """Exact structural invalidation frontier for U10's current depth-3 compiler."""

    def __init__(
        self,
        *,
        source_epoch: int,
        graph_epoch: int,
        semantic_refs: Iterable[str],
        forward_edges: Iterable[tuple[str, str]],
        active_anchor_refs: Iterable[str],
    ) -> None:
        refs = tuple(dict.fromkeys(str(r) for r in semantic_refs))
        refset = set(refs)
        anchors = tuple(sorted(set(map(str, active_anchor_refs))))
        unknown = [a for a in anchors if a not in refset]
        if unknown:
            raise KeyError(f"active anchors missing from semantic_refs: {unknown[:5]}")
        edges = tuple((str(u), str(v)) for u, v in forward_edges)
        self.active_anchors = frozenset(anchors)
        self.reverse = BoundedReachability2(
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            semantic_refs=refs,
            edges=((v, u) for u, v in edges),
        )

    @property
    def source_epoch(self) -> int:
        return self.reverse.source_epoch

    @property
    def graph_epoch(self) -> int:
        return self.reverse.graph_epoch

    def affected_anchors_before_edge_mutation(
        self,
        forward_source_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
    ) -> tuple[str, ...]:
        possible_predecessors = self.reverse.prepared_refs(
            [forward_source_ref],
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
        )
        return tuple(sorted(self.active_anchors.intersection(possible_predecessors)))

    def add_forward_edge(
        self,
        forward_source_ref: str,
        forward_target_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
    ) -> U10InvalidationReceipt:
        affected = self.affected_anchors_before_edge_mutation(
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
        )
        # Forward u->v is reverse v->u.
        delta = self.reverse.add_edge(
            forward_target_ref,
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
            result_source_epoch=result_source_epoch,
            result_graph_epoch=result_graph_epoch,
        )
        return self._receipt("ADD", forward_source_ref, forward_target_ref, affected, delta)

    def remove_forward_edge(
        self,
        forward_source_ref: str,
        forward_target_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
    ) -> U10InvalidationReceipt:
        # Must be measured before removal: every old depth-3 path using u->v begins at an
        # anchor that reached u within <=2 hops in the pre-mutation graph.
        affected = self.affected_anchors_before_edge_mutation(
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
        )
        delta = self.reverse.remove_edge(
            forward_target_ref,
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
            result_source_epoch=result_source_epoch,
            result_graph_epoch=result_graph_epoch,
        )
        return self._receipt("REMOVE", forward_source_ref, forward_target_ref, affected, delta)

    def _receipt(
        self,
        operation: str,
        source: str,
        target: str,
        affected: tuple[str, ...],
        delta: ReachabilityDeltaReceipt,
    ) -> U10InvalidationReceipt:
        total = len(self.active_anchors)
        return U10InvalidationReceipt(
            operation=operation,
            forward_source_ref=str(source),
            forward_target_ref=str(target),
            affected_anchor_refs=affected,
            affected_anchor_count=len(affected),
            total_active_anchors=total,
            reusable_anchor_count=total - len(affected),
            reachability_delta=delta,
        )
