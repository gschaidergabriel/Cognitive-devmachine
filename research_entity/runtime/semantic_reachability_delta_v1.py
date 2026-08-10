"""Exact bounded semantic reachability delta compiler for Clay's possibility preprocessor.

RESEARCH CANDIDATE. This is derived acceleration state only.
Canonical state/provenance/authority remain in UnifiedDB and current ClayGraph epochs.

The V1 horizon is deliberately fixed at <=2 hops. That bounded contract permits exact
incremental add *and remove/revocation* updates using sparse support counts. A reachable
pair stays materialized while at least one direct/2-hop support path remains. Identity
reachability is structural and does not depend on graph support.

The component is intended to sit below the existing query-conditioned possibility compiler:
known/hot semantic cues can consume prepared neighborhoods; cold/missing/exploratory queries
may still fall back to FTS/BM25 + relation-aware ClayGraph expansion.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable


class StaleReachabilityEpoch(ValueError):
    pass


@dataclass(frozen=True)
class ReachabilityDeltaReceipt:
    operation: str
    source_ref: str
    target_ref: str
    basis_source_epoch: int
    basis_graph_epoch: int
    result_source_epoch: int
    result_graph_epoch: int
    affected_refs: tuple[str, ...]
    support_updates: int
    exact_horizon: int = 2
    authority: str = "DERIVED_NON_AUTHORITATIVE"


class BoundedReachability2:
    """Prepared <=2-hop reachability with exact sparse support-count deltas.

    One support count is stored for every direct path and every 2-edge path. Addition or
    removal of one edge changes only paths containing that edge, so for horizon=2 the exact
    delta is local:
      u->v              direct support for (u,v)
      u->v->w           for each current successor w of v
      p->u->v           for each current predecessor p of u

    This avoids global graph rebuild and, unlike OR-only bitmap deltas, makes revocation
    exact when alternative paths still support the same prepared relation.
    """

    HORIZON = 2

    def __init__(
        self,
        *,
        source_epoch: int,
        graph_epoch: int,
        semantic_refs: Iterable[str],
        edges: Iterable[tuple[str, str]],
    ) -> None:
        refs = tuple(dict.fromkeys(str(ref) for ref in semantic_refs))
        if not refs:
            raise ValueError("semantic_refs must be non-empty")
        self.source_epoch = int(source_epoch)
        self.graph_epoch = int(graph_epoch)
        self.refs = refs
        self.ref_to_idx = {ref: idx for idx, ref in enumerate(refs)}
        self.adj: dict[int, set[int]] = defaultdict(set)
        self.rev: dict[int, set[int]] = defaultdict(set)

        for source_ref, target_ref in edges:
            u = self._idx(source_ref)
            v = self._idx(target_ref)
            if u == v or v in self.adj[u]:
                continue
            self.adj[u].add(v)
            self.rev[v].add(u)

        # support[s][t] counts non-identity paths with length 1 or 2.
        self.support: list[dict[int, int]] = [defaultdict(int) for _ in refs]
        for u in range(len(refs)):
            for v in self.adj.get(u, ()):
                self.support[u][v] += 1
                for w in self.adj.get(v, ()):
                    self.support[u][w] += 1
        self.masks = [self._mask_from_support(u) for u in range(len(refs))]

    def _idx(self, semantic_ref: str) -> int:
        try:
            return self.ref_to_idx[str(semantic_ref)]
        except KeyError as exc:
            raise KeyError(f"unknown semantic ref: {semantic_ref}") from exc

    def _mask_from_support(self, source: int) -> int:
        mask = 1 << source
        for target, count in self.support[source].items():
            if count > 0:
                mask |= 1 << target
        return mask

    def _brute_mask(self, source: int) -> int:
        mask = 1 << source
        for mid in self.adj.get(source, ()):
            mask |= 1 << mid
            for target in self.adj.get(mid, ()):
                mask |= 1 << target
        return mask

    def _check_basis(self, basis_source_epoch: int, basis_graph_epoch: int) -> None:
        if int(basis_source_epoch) != self.source_epoch or int(basis_graph_epoch) != self.graph_epoch:
            raise StaleReachabilityEpoch(
                f"basis source={basis_source_epoch}/graph={basis_graph_epoch}; "
                f"current source={self.source_epoch}/graph={self.graph_epoch}"
            )

    def _change_support(self, source: int, target: int, delta: int) -> None:
        supports = self.support[source]
        old = supports.get(target, 0)
        new = old + delta
        if new < 0:
            raise AssertionError(
                f"negative support count source={self.refs[source]} target={self.refs[target]} "
                f"old={old} delta={delta}"
            )
        if new == 0:
            supports.pop(target, None)
            if target != source:
                self.masks[source] &= ~(1 << target)
        else:
            supports[target] = new
            self.masks[source] |= 1 << target
        # A cue always reaches its own semantic identity.
        self.masks[source] |= 1 << source

    def prepared_refs(
        self,
        cue_refs: Iterable[str],
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
    ) -> tuple[str, ...]:
        self._check_basis(basis_source_epoch, basis_graph_epoch)
        mask = 0
        for ref in cue_refs:
            mask |= self.masks[self._idx(ref)]
        out: list[str] = []
        while mask:
            bit = mask & -mask
            out.append(self.refs[bit.bit_length() - 1])
            mask -= bit
        return tuple(out)

    def add_edge(
        self,
        source_ref: str,
        target_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
    ) -> ReachabilityDeltaReceipt:
        self._check_basis(basis_source_epoch, basis_graph_epoch)
        u = self._idx(source_ref)
        v = self._idx(target_ref)
        if u == v or v in self.adj.get(u, ()):
            return self._finish_receipt(
                "ADD_NOOP", source_ref, target_ref, basis_source_epoch, basis_graph_epoch,
                result_source_epoch, result_graph_epoch, (), 0
            )

        predecessors = tuple(self.rev.get(u, ()))
        successors = tuple(self.adj.get(v, ()))
        updates = 0

        self._change_support(u, v, +1)
        updates += 1
        for w in successors:
            self._change_support(u, w, +1)
            updates += 1
        for p in predecessors:
            self._change_support(p, v, +1)
            updates += 1

        self.adj[u].add(v)
        self.rev[v].add(u)
        affected = tuple(sorted({self.refs[u], *(self.refs[p] for p in predecessors)}))
        return self._finish_receipt(
            "ADD", source_ref, target_ref, basis_source_epoch, basis_graph_epoch,
            result_source_epoch, result_graph_epoch, affected, updates
        )

    def remove_edge(
        self,
        source_ref: str,
        target_ref: str,
        *,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
    ) -> ReachabilityDeltaReceipt:
        self._check_basis(basis_source_epoch, basis_graph_epoch)
        u = self._idx(source_ref)
        v = self._idx(target_ref)
        if v not in self.adj.get(u, ()):
            return self._finish_receipt(
                "REMOVE_NOOP", source_ref, target_ref, basis_source_epoch, basis_graph_epoch,
                result_source_epoch, result_graph_epoch, (), 0
            )

        # Snapshot while the edge still exists; these are exactly the <=2-hop paths that use it.
        predecessors = tuple(self.rev.get(u, ()))
        successors = tuple(self.adj.get(v, ()))
        updates = 0

        self._change_support(u, v, -1)
        updates += 1
        for w in successors:
            self._change_support(u, w, -1)
            updates += 1
        for p in predecessors:
            self._change_support(p, v, -1)
            updates += 1

        self.adj[u].remove(v)
        self.rev[v].remove(u)
        affected = tuple(sorted({self.refs[u], *(self.refs[p] for p in predecessors)}))
        return self._finish_receipt(
            "REMOVE", source_ref, target_ref, basis_source_epoch, basis_graph_epoch,
            result_source_epoch, result_graph_epoch, affected, updates
        )

    def _finish_receipt(
        self,
        operation: str,
        source_ref: str,
        target_ref: str,
        basis_source_epoch: int,
        basis_graph_epoch: int,
        result_source_epoch: int,
        result_graph_epoch: int,
        affected_refs: tuple[str, ...],
        support_updates: int,
    ) -> ReachabilityDeltaReceipt:
        self.source_epoch = int(result_source_epoch)
        self.graph_epoch = int(result_graph_epoch)
        return ReachabilityDeltaReceipt(
            operation=operation,
            source_ref=str(source_ref),
            target_ref=str(target_ref),
            basis_source_epoch=int(basis_source_epoch),
            basis_graph_epoch=int(basis_graph_epoch),
            result_source_epoch=self.source_epoch,
            result_graph_epoch=self.graph_epoch,
            affected_refs=affected_refs,
            support_updates=support_updates,
        )

    def verify_exact(self) -> tuple[bool, tuple[str, ...]]:
        bad = tuple(
            self.refs[source]
            for source in range(len(self.refs))
            if self.masks[source] != self._brute_mask(source)
        )
        return not bad, bad
