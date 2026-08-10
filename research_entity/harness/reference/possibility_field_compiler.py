from __future__ import annotations

"""Model-facing possibility-field compiler candidate.

This is an orchestration layer over already-existing Clay research mechanisms:
- coherent V11/V13 semantic access generations,
- EAP active assembly over UnifiedDB state,
- compositional Pareto possibility frontiers.

It is deliberately not a database and not a truth/effect-authority surface.  It returns the
smallest already-grounded field that is sufficient for the requested semantic/route purpose,
and only deepens when the earlier stage is insufficient.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .possibility_frontier import (
    CompiledPossibilityFrontier,
    PossibilityRoute,
    RouteConstraints,
    StalePossibilityEpoch,
    best_route,
)
from .unifieddb_emergent_preprocessor import PossibilitySpec


@dataclass(frozen=True)
class PossibilityFieldQuery:
    query_id: str
    text: str
    basis_epoch: int
    graph_epoch: int
    typed_seed_id: str | None = None
    seed_refs: tuple[str, ...] = ()
    route_source: str | None = None
    route_target: str | None = None
    route_constraints: RouteConstraints = RouteConstraints()
    max_items: int = 12
    max_hops: int = 3
    frontier_budget: int = 512


@dataclass(frozen=True)
class PossibilityFieldReceipt:
    query_id: str
    mode: str
    selected_refs: tuple[str, ...]
    semantic_generation_id: str | None
    semantic_seed_id: str | None
    route: PossibilityRoute | None
    active_assembly_hash: str | None
    suppressed_refs: tuple[str, ...]
    blocked_propagation_refs: tuple[str, ...]
    source_epoch: int
    graph_epoch: int
    sufficient: bool
    deepening_count: int
    authority: str = "CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


class PossibilityFieldCompiler:
    """Bounded sufficiency-first compiler for model-facing context/possibilities.

    `semantic_access` must expose the current SemanticRetrievalFabric-compatible `query_seed`.
    `eap` must expose `ledger` and `compile_active_assembly`.
    `frontier_provider`, when present, receives (source_epoch, graph_epoch) and returns an
    epoch-bound CompiledPossibilityFrontier.
    """

    def __init__(
        self,
        semantic_access: Any,
        eap: Any,
        *,
        frontier_provider: Callable[[int, int], CompiledPossibilityFrontier] | None = None,
    ):
        self.semantic_access = semantic_access
        self.eap = eap
        self.frontier_provider = frontier_provider

    def _require_current_basis(self, query: PossibilityFieldQuery) -> None:
        current = int(self.eap.ledger.epoch)
        if query.basis_epoch != current:
            raise StalePossibilityEpoch(
                f"query source epoch={query.basis_epoch}; current UnifiedDB epoch={current}"
            )

    def compile(self, query: PossibilityFieldQuery) -> PossibilityFieldReceipt:
        if not query.query_id.strip() or not query.text.strip():
            raise ValueError("query_id and text required")
        if query.max_items <= 0:
            raise ValueError("max_items must be positive")
        self._require_current_basis(query)

        # Stage 1: one coherent semantic generation.  Only the V11/V13 `sufficient=True`
        # contract may stop here. A V10 fast-path hit is useful evidence but not sufficient.
        semantic = self.semantic_access.query_seed(
            query.text,
            typed_seed_id=query.typed_seed_id,
            source_epoch=query.basis_epoch,
            graph_epoch=query.graph_epoch,
            limit=query.max_items,
            lexical_ranking=None,
            graph_fallback_ranking=None,
        )
        if bool(getattr(semantic, "sufficient", False)) and tuple(semantic.refs):
            return PossibilityFieldReceipt(
                query_id=query.query_id,
                mode="COMPILED_SUFFICIENT",
                selected_refs=tuple(semantic.refs),
                semantic_generation_id=getattr(semantic, "generation_id", None),
                semantic_seed_id=getattr(semantic, "seed_id", None),
                route=None,
                active_assembly_hash=None,
                suppressed_refs=(),
                blocked_propagation_refs=(),
                source_epoch=query.basis_epoch,
                graph_epoch=query.graph_epoch,
                sufficient=True,
                deepening_count=0,
            )

        # Stage 2: if this is a capability/action possibility question, search only the
        # precompiled feasible Pareto frontier. Guards are already conservative in that
        # compiler; a stale frontier fails closed rather than silently reusing old topology.
        if (
            self.frontier_provider is not None
            and query.route_source is not None
            and query.route_target is not None
        ):
            frontier = self.frontier_provider(query.basis_epoch, query.graph_epoch)
            route = best_route(
                frontier,
                query.route_source,
                query.route_target,
                query.route_constraints,
                source_epoch=query.basis_epoch,
                graph_epoch=query.graph_epoch,
            )
            if route is not None:
                return PossibilityFieldReceipt(
                    query_id=query.query_id,
                    mode="COMPILED_COMPOSITIONAL",
                    selected_refs=route.edge_refs,
                    semantic_generation_id=getattr(semantic, "generation_id", None),
                    semantic_seed_id=getattr(semantic, "seed_id", None),
                    route=route,
                    active_assembly_hash=None,
                    suppressed_refs=(),
                    blocked_propagation_refs=(),
                    source_epoch=query.basis_epoch,
                    graph_epoch=query.graph_epoch,
                    sufficient=True,
                    deepening_count=1,
                )

        # Stage 3: bounded active assembly. EAP itself contains sparse dependency traversal,
        # negative-space blocking and lazy lexical seeding. It is the measured deepening
        # fallback, not a second persistent store.
        assembly = self.eap.compile_active_assembly(
            PossibilitySpec(
                assembly_id=f"possibility-field:{query.query_id}",
                seed_refs=query.seed_refs,
                query_text=query.text,
                max_items=query.max_items,
                max_hops=query.max_hops,
                frontier_budget=query.frontier_budget,
                basis_epoch=query.basis_epoch,
                purpose="POSSIBILITY_FIELD_DEEPENING",
            )
        )
        selected = tuple(str(item["ref"]) for item in assembly.get("selected", ()))
        suppressed = tuple(str(item["ref"]) for item in assembly.get("suppressed", ()))
        blocked = tuple(str(ref) for ref in assembly.get("blocked_propagation_refs", ()))
        return PossibilityFieldReceipt(
            query_id=query.query_id,
            mode="EAP_ACTIVE_ASSEMBLY" if selected else "ABSTAIN",
            selected_refs=selected,
            semantic_generation_id=getattr(semantic, "generation_id", None),
            semantic_seed_id=getattr(semantic, "seed_id", None),
            route=None,
            active_assembly_hash=assembly.get("selection_hash"),
            suppressed_refs=suppressed,
            blocked_propagation_refs=blocked,
            source_epoch=query.basis_epoch,
            graph_epoch=query.graph_epoch,
            sufficient=bool(selected),
            deepening_count=2,
        )
