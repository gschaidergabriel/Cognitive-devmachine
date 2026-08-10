from __future__ import annotations

"""Derived compositional possibility frontier for Clay.

Research candidate only. This module compiles bounded capability routes into Pareto frontiers.
It is not a database, truth source, or effect-authority surface. All outputs are derived from
source/graph epochs and must be discarded when either epoch changes.
"""

from collections import defaultdict
from dataclasses import dataclass
import math
from typing import Iterable, Mapping


@dataclass(frozen=True)
class CapabilityEdge:
    ref: str
    source: str
    target: str
    cost: float = 0.0
    latency: float = 0.0
    reliability: float = 1.0
    authority: int = 0
    fresh: bool = True
    local: bool = False
    lineage: str = ""


@dataclass(frozen=True)
class RouteConstraints:
    min_authority: int = 0
    require_fresh: bool = False
    require_local: bool = False
    max_cost: float = math.inf
    max_latency: float = math.inf
    min_reliability: float = 0.0


@dataclass(frozen=True)
class PossibilityRoute:
    source: str
    target: str
    edge_refs: tuple[str, ...]
    cost: float
    latency: float
    reliability: float
    authority: int
    fresh: bool
    local: bool
    lineages: frozenset[str]

    @property
    def lineage_diversity(self) -> int:
        return len(self.lineages)

    @property
    def utility(self) -> float:
        # Research scoring proxy only; not calibrated probability or authority.
        return (
            2.8 * self.reliability
            + 0.12 * self.lineage_diversity
            - 0.018 * self.cost
            - 0.0018 * self.latency
        )


@dataclass(frozen=True)
class CompiledPossibilityFrontier:
    source_epoch: int
    graph_epoch: int
    routes: Mapping[tuple[str, str], tuple[PossibilityRoute, ...]]
    candidate_routes_seen: int
    retained_routes: int
    approximate: bool
    beam_per_node: int | None
    hub_penalty: float
    authority: str = "NON_AUTHORITATIVE_DERIVED_PREPROCESSOR"


class StalePossibilityEpoch(ValueError):
    pass


def _dominates(a: PossibilityRoute, b: PossibilityRoute) -> bool:
    if (a.authority, a.fresh, a.local) != (b.authority, b.fresh, b.local):
        return False
    weak = (
        a.cost <= b.cost
        and a.latency <= b.latency
        and a.reliability >= b.reliability
        and a.lineage_diversity >= b.lineage_diversity
    )
    strict = (
        a.cost < b.cost
        or a.latency < b.latency
        or a.reliability > b.reliability
        or a.lineage_diversity > b.lineage_diversity
    )
    return weak and strict


def _pareto(routes: Iterable[PossibilityRoute]) -> tuple[PossibilityRoute, ...]:
    buckets: dict[tuple[int, bool, bool], list[PossibilityRoute]] = defaultdict(list)
    for route in routes:
        buckets[(route.authority, route.fresh, route.local)].append(route)
    kept: list[PossibilityRoute] = []
    for candidates in buckets.values():
        front: list[PossibilityRoute] = []
        for route in sorted(candidates, key=lambda x: x.utility, reverse=True):
            if any(_dominates(old, route) for old in front):
                continue
            front = [old for old in front if not _dominates(route, old)]
            front.append(route)
        kept.extend(front)
    return tuple(sorted(kept, key=lambda x: (-x.utility, x.edge_refs)))


def compile_frontier(
    edges: Iterable[CapabilityEdge],
    *,
    source_epoch: int,
    graph_epoch: int,
    max_hops: int = 3,
    beam_per_node: int | None = None,
    hub_penalty: float = 0.0,
) -> CompiledPossibilityFrontier:
    """Compile bounded compositional possibilities.

    No guard is upgraded while composing a route:
    authority=min(edge authority), fresh=AND, local=AND, reliability=product.
    With beam_per_node=None the bounded path universe is exhaustive before Pareto pruning.
    With a beam the result is explicitly approximate and must be benchmarked against exhaustive.
    """
    if source_epoch < 0 or graph_epoch < 0:
        raise ValueError("epochs must be non-negative")
    if max_hops < 1:
        raise ValueError("max_hops must be >= 1")
    if beam_per_node is not None and beam_per_node < 1:
        raise ValueError("beam_per_node must be >= 1")

    adjacency: dict[str, list[CapabilityEdge]] = defaultdict(list)
    nodes: set[str] = set()
    for edge in edges:
        if edge.reliability < 0.0 or edge.reliability > 1.0:
            raise ValueError(f"invalid reliability for {edge.ref}")
        adjacency[edge.source].append(edge)
        nodes.add(edge.source)
        nodes.add(edge.target)
    degree = {node: len(items) for node, items in adjacency.items()}

    candidates: dict[tuple[str, str], list[PossibilityRoute]] = defaultdict(list)
    candidate_count = 0
    for root in sorted(nodes):
        frontier = [
            (root, tuple(), 0.0, 0.0, 1.0, 2**31 - 1, True, True, frozenset(), frozenset({root}))
        ]
        for _hop in range(max_hops):
            nxt = []
            for node, refs, cost, latency, reliability, authority, fresh, local, lineages, visited in frontier:
                for edge in adjacency.get(node, ()):
                    if edge.target in visited:
                        continue
                    route = PossibilityRoute(
                        source=root,
                        target=edge.target,
                        edge_refs=refs + (edge.ref,),
                        cost=cost + edge.cost,
                        latency=latency + edge.latency,
                        reliability=reliability * edge.reliability,
                        authority=min(authority, edge.authority),
                        fresh=fresh and edge.fresh,
                        local=local and edge.local,
                        lineages=lineages | frozenset({edge.lineage or edge.ref}),
                    )
                    candidates[(root, edge.target)].append(route)
                    candidate_count += 1
                    nxt.append(
                        (
                            edge.target,
                            route.edge_refs,
                            route.cost,
                            route.latency,
                            route.reliability,
                            route.authority,
                            route.fresh,
                            route.local,
                            route.lineages,
                            visited | frozenset({edge.target}),
                        )
                    )
            if beam_per_node is not None and nxt:
                grouped: dict[str, list[tuple[float, tuple]]] = defaultdict(list)
                for state in nxt:
                    node = state[0]
                    score = (
                        2.8 * state[4]
                        + 0.12 * len(state[8])
                        - 0.018 * state[2]
                        - 0.0018 * state[3]
                        - hub_penalty * math.log1p(degree.get(node, 0))
                    )
                    grouped[node].append((score, state))
                nxt = [
                    state
                    for group in grouped.values()
                    for _score, state in sorted(group, key=lambda item: item[0], reverse=True)[:beam_per_node]
                ]
            frontier = nxt

    compiled = {key: _pareto(value) for key, value in candidates.items()}
    retained = sum(len(value) for value in compiled.values())
    return CompiledPossibilityFrontier(
        source_epoch=source_epoch,
        graph_epoch=graph_epoch,
        routes=compiled,
        candidate_routes_seen=candidate_count,
        retained_routes=retained,
        approximate=beam_per_node is not None,
        beam_per_node=beam_per_node,
        hub_penalty=hub_penalty,
    )


def _feasible(route: PossibilityRoute, constraints: RouteConstraints) -> bool:
    return (
        route.authority >= constraints.min_authority
        and (not constraints.require_fresh or route.fresh)
        and (not constraints.require_local or route.local)
        and route.cost <= constraints.max_cost
        and route.latency <= constraints.max_latency
        and route.reliability >= constraints.min_reliability
    )


def best_route(
    compiled: CompiledPossibilityFrontier,
    source: str,
    target: str,
    constraints: RouteConstraints = RouteConstraints(),
    *,
    source_epoch: int,
    graph_epoch: int,
) -> PossibilityRoute | None:
    if source_epoch != compiled.source_epoch or graph_epoch != compiled.graph_epoch:
        raise StalePossibilityEpoch(
            f"query source/graph={source_epoch}/{graph_epoch}; compiled={compiled.source_epoch}/{compiled.graph_epoch}"
        )
    for route in compiled.routes.get((source, target), ()):
        if _feasible(route, constraints):
            return route
    return None
