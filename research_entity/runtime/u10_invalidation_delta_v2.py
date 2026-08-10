"""U10 depth-3 structural invalidation V2: anchor-mask hot path.

Research candidate only. V1 proved the reverse<=2 invalidation law but materialized all
prepared refs before intersecting with active anchors. V2 intersects the prepared bitmask
with an anchor-only bitmask first, so read cost scales with affected anchors rather than the
entire prepared semantic neighborhood.

The full support-count index is optional at the architecture level. A low-memory reverse-BFS
fallback is intentionally provided because differential-maintenance memory can dominate on
hubbed/high-churn graphs. Selection between prepared-mask and BFS must be measured on the
actual ClayGraph workload.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Iterable

from semantic_reachability_delta_v1 import BoundedReachability2, ReachabilityDeltaReceipt


@dataclass(frozen=True)
class U10InvalidationV2Receipt:
    operation: str
    forward_source_ref: str
    forward_target_ref: str
    affected_anchor_refs: tuple[str, ...]
    affected_anchor_count: int
    total_active_anchors: int
    reusable_anchor_count: int
    selector_mode: str
    reachability_delta: ReachabilityDeltaReceipt | None
    authority: str = "DERIVED_INVALIDATION_ONLY"


class U10Depth3InvalidationIndexV2:
    """Exact no-false-negative structural invalidation for U10 max_depth=3.

    Prepared mode maintains exact reverse <=2 support-count reachability and intersects its
    bitmask directly with active-anchor bits. BFS mode keeps only reverse adjacency and
    computes the same <=2 predecessor set on demand. Both use pre-mutation reachability for
    edge removals.
    """

    def __init__(
        self,
        *,
        source_epoch: int,
        graph_epoch: int,
        semantic_refs: Iterable[str],
        forward_edges: Iterable[tuple[str, str]],
        active_anchor_refs: Iterable[str],
        mode: str = "PREPARED_MASK",
    ) -> None:
        refs = tuple(dict.fromkeys(str(r) for r in semantic_refs))
        self.refs = refs
        self.ref_to_idx = {ref: i for i, ref in enumerate(refs)}
        anchors = tuple(sorted(set(map(str, active_anchor_refs))))
        unknown = [a for a in anchors if a not in self.ref_to_idx]
        if unknown:
            raise KeyError(f"active anchors missing from semantic_refs: {unknown[:5]}")
        if mode not in {"PREPARED_MASK", "ON_DEMAND_BFS"}:
            raise ValueError("mode must be PREPARED_MASK or ON_DEMAND_BFS")
        self.mode = mode
        self.active_anchors = frozenset(anchors)
        self.anchor_mask = 0
        for ref in anchors:
            self.anchor_mask |= 1 << self.ref_to_idx[ref]

        edges = tuple((str(u), str(v)) for u, v in forward_edges)
        self.forward_adj: dict[int, set[int]] = {}
        self.forward_rev: dict[int, set[int]] = {}
        for uref, vref in edges:
            u = self.ref_to_idx[uref]
            v = self.ref_to_idx[vref]
            if u == v:
                continue
            self.forward_adj.setdefault(u, set()).add(v)
            self.forward_rev.setdefault(v, set()).add(u)

        self.source_epoch = int(source_epoch)
        self.graph_epoch = int(graph_epoch)
        self.reverse: BoundedReachability2 | None = None
        if mode == "PREPARED_MASK":
            self.reverse = BoundedReachability2(
                source_epoch=source_epoch,
                graph_epoch=graph_epoch,
                semantic_refs=refs,
                edges=((v, u) for u, v in edges),
            )

    def _check_basis(self, source_epoch: int, graph_epoch: int) -> None:
        if int(source_epoch) != self.source_epoch or int(graph_epoch) != self.graph_epoch:
            raise ValueError(
                f"stale invalidation basis source={source_epoch}/graph={graph_epoch}; "
                f"current={self.source_epoch}/{self.graph_epoch}"
            )

    @staticmethod
    def _iter_mask(mask: int):
        while mask:
            bit = mask & -mask
            yield bit.bit_length() - 1
            mask -= bit

    def _prepared_affected(self, source_ref: str) -> tuple[str, ...]:
        assert self.reverse is not None
        source_idx = self.reverse.ref_to_idx[source_ref]
        masked = self.reverse.masks[source_idx] & self.anchor_mask
        return tuple(self.refs[i] for i in self._iter_mask(masked))

    def _bfs_affected(self, source_ref: str) -> tuple[str, ...]:
        source = self.ref_to_idx[source_ref]
        seen = {source}
        frontier = {source}
        for _ in range(2):
            nxt: set[int] = set()
            for node in frontier:
                nxt.update(self.forward_rev.get(node, ()))
            nxt -= seen
            seen |= nxt
            frontier = nxt
            if not frontier:
                break
        return tuple(sorted(self.refs[i] for i in seen if ((self.anchor_mask >> i) & 1)))

    def affected_anchors_before_edge_mutation(
        self,
        forward_source_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
    ) -> tuple[str, ...]:
        self._check_basis(basis_source_epoch, basis_graph_epoch)
        if self.mode == "PREPARED_MASK":
            return self._prepared_affected(forward_source_ref)
        return self._bfs_affected(forward_source_ref)

    def _advance_epochs(self, source_epoch: int, graph_epoch: int) -> None:
        self.source_epoch = int(source_epoch)
        self.graph_epoch = int(graph_epoch)

    def add_forward_edge(
        self,
        forward_source_ref: str,
        forward_target_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
    ) -> U10InvalidationV2Receipt:
        affected = self.affected_anchors_before_edge_mutation(
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
        )
        u = self.ref_to_idx[forward_source_ref]
        v = self.ref_to_idx[forward_target_ref]
        delta = None
        if self.reverse is not None:
            delta = self.reverse.add_edge(
                forward_target_ref,
                forward_source_ref,
                basis_source_epoch=basis_source_epoch,
                basis_graph_epoch=basis_graph_epoch,
                result_source_epoch=result_source_epoch,
                result_graph_epoch=result_graph_epoch,
            )
        self.forward_adj.setdefault(u, set()).add(v)
        self.forward_rev.setdefault(v, set()).add(u)
        self._advance_epochs(result_source_epoch, result_graph_epoch)
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
    ) -> U10InvalidationV2Receipt:
        affected = self.affected_anchors_before_edge_mutation(
            forward_source_ref,
            basis_source_epoch=basis_source_epoch,
            basis_graph_epoch=basis_graph_epoch,
        )
        u = self.ref_to_idx[forward_source_ref]
        v = self.ref_to_idx[forward_target_ref]
        delta = None
        if self.reverse is not None:
            delta = self.reverse.remove_edge(
                forward_target_ref,
                forward_source_ref,
                basis_source_epoch=basis_source_epoch,
                basis_graph_epoch=basis_graph_epoch,
                result_source_epoch=result_source_epoch,
                result_graph_epoch=result_graph_epoch,
            )
        if v in self.forward_adj.get(u, ()):
            self.forward_adj[u].remove(v)
        if u in self.forward_rev.get(v, ()):
            self.forward_rev[v].remove(u)
        self._advance_epochs(result_source_epoch, result_graph_epoch)
        return self._receipt("REMOVE", forward_source_ref, forward_target_ref, affected, delta)

    def _receipt(
        self,
        operation: str,
        source: str,
        target: str,
        affected: tuple[str, ...],
        delta: ReachabilityDeltaReceipt | None,
    ) -> U10InvalidationV2Receipt:
        total = len(self.active_anchors)
        return U10InvalidationV2Receipt(
            operation=operation,
            forward_source_ref=source,
            forward_target_ref=target,
            affected_anchor_refs=affected,
            affected_anchor_count=len(affected),
            total_active_anchors=total,
            reusable_anchor_count=total - len(affected),
            selector_mode=self.mode,
            reachability_delta=delta,
        )
