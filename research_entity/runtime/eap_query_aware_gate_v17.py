from __future__ import annotations

"""Query-aware bounded propagation candidate for the UnifiedDB possibility preprocessor.

This is a derived model-input optimization only. StateLedger remains semantic/provenance
truth; ClayGraph/EAP remains disposable and rebuildable; activation never mints truth or
effect authority.

V17 deliberately keeps the existing EAP-1.3 implementation as the parent mechanism and
changes only edge traversal weights for one query. The gate is lazy: only adjacency lists
actually expanded by the bounded parent traversal are reweighted. A strength of zero (or an
empty query) is an exact lesion back to the parent path.

The default gate includes one bounded admissible-successor lookahead. This prevents a relevant
multi-hop path from being cut merely because an intermediate bridge has an opaque label while a
query-aligned successor provides the actual semantic evidence. Lookahead never changes the
underlying edge strength; it only decides how much of that authoritative weight to retain.
"""

from dataclasses import dataclass, fields
import math
import re
from typing import Any

from research_entity.harness.reference.state_ledger import h
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)

IMPLEMENTATION_ID = "EAP-1.7-QUERY-AWARE-GATE"
_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
_TARGET_ONLY_MODE = "LEXICAL_COSINE_TARGET_RELATION"
_LOOKAHEAD_MODE = "LEXICAL_COSINE_TARGET_OR_ADMISSIBLE_SUCCESSOR_V1"
_SUPPORTED_MODES = frozenset({_TARGET_ONLY_MODE, _LOOKAHEAD_MODE})


@dataclass(frozen=True)
class QueryAwarePossibilitySpec(PossibilitySpec):
    """Opt-in query-aware propagation controls.

    query_gate_strength=0 is a strict lesion to the parent EAP behavior. The lexical cosine
    gate only damps structural activation; it never boosts an edge above its authoritative
    dependency weight. query_gate_floor protects against a zero-similarity cliff. The default
    mode additionally inspects one admissible structural successor and discounts that evidence
    by the successor edge weight.
    """

    query_gate_strength: float = 0.0
    query_gate_floor: float = 0.10
    query_gate_mode: str = _LOOKAHEAD_MODE


class _QueryAwareAdjacency:
    """Per-query lazy adjacency view; does not mutate the shared EAP topology."""

    def __init__(
        self,
        *,
        base: Any,
        rows_by_ref: dict[str, dict[str, Any]],
        query_tokens: frozenset[str],
        strength: float,
        floor: float,
        min_edge_weight: float,
        mode: str,
        allowed_epistemic: frozenset[str],
        allowed_status: frozenset[str],
    ) -> None:
        self._base = base
        self._rows_by_ref = rows_by_ref
        self._query_tokens = query_tokens
        self._strength = strength
        self._floor = floor
        self._min_edge_weight = min_edge_weight
        self._mode = mode
        self._allowed_epistemic = allowed_epistemic
        self._allowed_status = allowed_status
        self._source_cache: dict[str, tuple[tuple[str, float, str, str], ...]] = {}
        self._affinity_cache: dict[tuple[str, str], float] = {}
        self.edges_observed = 0
        self.edges_damped = 0
        self.edges_pruned_below_parent_min = 0
        self.sources_expanded = 0
        self.lookahead_edges_scanned = 0
        self.lookahead_affinity_wins = 0

    @staticmethod
    def _tokens(text: str) -> frozenset[str]:
        return frozenset(
            token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1
        )

    def _row_affinity(self, target: str, relation: str) -> float:
        key = (target, relation)
        cached = self._affinity_cache.get(key)
        if cached is not None:
            return cached
        row = self._rows_by_ref.get(target)
        if row is None or not self._query_tokens:
            affinity = 0.0
        else:
            row_tokens = set(EmergentAssemblyPreprocessor._tokens(row))
            row_tokens.update(self._tokens(relation))
            if not row_tokens:
                affinity = 0.0
            else:
                overlap = len(self._query_tokens.intersection(row_tokens))
                affinity = overlap / math.sqrt(
                    float(len(self._query_tokens) * len(row_tokens))
                )
        affinity = max(0.0, min(1.0, float(affinity)))
        self._affinity_cache[key] = affinity
        return affinity

    def _lookahead_admissible(self, ref: str) -> bool:
        row = self._rows_by_ref.get(ref)
        if row is None or row.get("domain") == "dependency":
            return False
        return (
            str(row.get("status", "")).upper() in self._allowed_status
            and str(row.get("epistemic", "")).upper() in self._allowed_epistemic
        )

    def _effective_affinity(self, target: str, relation: str) -> float:
        direct = self._row_affinity(target, relation)
        if self._mode == _TARGET_ONLY_MODE:
            return direct

        best = direct
        for successor, edge_weight, successor_relation, _dependency_ref in self._base.get(
            target, ()
        ):
            self.lookahead_edges_scanned += 1
            if float(edge_weight) < self._min_edge_weight:
                continue
            if not self._lookahead_admissible(successor):
                continue
            successor_affinity = self._row_affinity(successor, successor_relation)
            discounted = max(0.0, min(1.0, float(edge_weight))) * successor_affinity
            if discounted > best + 1e-15:
                best = discounted
                self.lookahead_affinity_wins += 1
        return best

    def get(self, source: str, default=()):
        if source in self._source_cache:
            return self._source_cache[source]
        edges = self._base.get(source, default)
        if not edges:
            self._source_cache[source] = tuple()
            return tuple()

        self.sources_expanded += 1
        out: list[tuple[str, float, str, str]] = []
        for target, weight, relation, dependency_ref in edges:
            self.edges_observed += 1
            affinity = self._effective_affinity(target, relation)
            gate = self._floor + (1.0 - self._floor) * affinity
            multiplier = (1.0 - self._strength) + self._strength * gate
            effective = max(0.0, min(float(weight), float(weight) * multiplier))
            if effective + 1e-15 < float(weight):
                self.edges_damped += 1
            if (
                float(weight) >= self._min_edge_weight
                and effective + 1e-15 < self._min_edge_weight
            ):
                self.edges_pruned_below_parent_min += 1
            out.append((target, effective, relation, dependency_ref))
        result = tuple(out)
        self._source_cache[source] = result
        return result


class QueryAwareEmergentAssemblyPreprocessor(EmergentAssemblyPreprocessor):
    """EAP parent plus an opt-in bounded query-conditioned propagation view."""

    @staticmethod
    def _base_spec(spec: QueryAwarePossibilitySpec) -> PossibilitySpec:
        return PossibilitySpec(
            **{field.name: getattr(spec, field.name) for field in fields(PossibilitySpec)}
        )

    @staticmethod
    def _normalized_query_tokens(query_text: str) -> frozenset[str]:
        return frozenset(
            token.lower() for token in _TOKEN_RE.findall(query_text) if len(token) > 1
        )

    @staticmethod
    def _validate_gate(spec: QueryAwarePossibilitySpec) -> None:
        if not 0.0 <= float(spec.query_gate_strength) <= 1.0:
            raise ValueError("query_gate_strength must be in [0,1]")
        if not 0.0 <= float(spec.query_gate_floor) <= 1.0:
            raise ValueError("query_gate_floor must be in [0,1]")
        if spec.query_gate_mode not in _SUPPORTED_MODES:
            raise ValueError(f"unsupported query_gate_mode: {spec.query_gate_mode}")

    def compile_active_assembly(self, spec: PossibilitySpec) -> dict[str, Any]:
        if not isinstance(spec, QueryAwarePossibilitySpec):
            return super().compile_active_assembly(spec)

        self._validate_gate(spec)
        base_spec = self._base_spec(spec)
        query_tokens = self._normalized_query_tokens(spec.query_text)
        lesion_reason = None
        if float(spec.query_gate_strength) == 0.0:
            lesion_reason = "ZERO_STRENGTH_PARENT_LESION"
        elif not query_tokens:
            lesion_reason = "NO_QUERY_TOKENS_PARENT_LESION"

        if lesion_reason is not None:
            result = super().compile_active_assembly(base_spec)
            parent_version = result.get("preprocessor_version")
            result["parent_preprocessor_version"] = parent_version
            result["preprocessor_version"] = IMPLEMENTATION_ID
            result["query_gate"] = {
                "enabled": False,
                "reason": lesion_reason,
                "mode": spec.query_gate_mode,
                "strength": float(spec.query_gate_strength),
                "floor": float(spec.query_gate_floor),
                "query_token_count": len(query_tokens),
                "edges_observed": 0,
                "edges_damped": 0,
                "edges_pruned_below_parent_min": 0,
                "sources_expanded": 0,
                "lookahead_edges_scanned": 0,
                "lookahead_affinity_wins": 0,
                "authority": "PERFORMANCE_RETRIEVAL_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY",
            }
            return result

        # Compile/validate the shared parent topology once. The query-aware adjacency is a
        # disposable local view over exactly this epoch/hash; the shared parent is never mutated.
        self._ensure_preprocessor()
        parent_index_hash = self._compiled_index_hash
        gate_manifest_hash = h(
            {
                "implementation": IMPLEMENTATION_ID,
                "basis_epoch": self._compiled_epoch,
                "semantic_state_hash": self._compiled_state_hash,
                "parent_index_hash": parent_index_hash,
                "query_tokens": tuple(sorted(query_tokens)),
                "mode": spec.query_gate_mode,
                "strength": float(spec.query_gate_strength),
                "floor": float(spec.query_gate_floor),
                "min_edge_weight": float(spec.min_edge_weight),
                "allowed_epistemic": tuple(sorted(str(x).upper() for x in spec.allow_epistemic)),
                "allowed_status": tuple(sorted(str(x).upper() for x in spec.allow_status)),
            }
        )
        gated_adj = _QueryAwareAdjacency(
            base=self._adj,
            rows_by_ref=self._rows_by_ref,
            query_tokens=query_tokens,
            strength=float(spec.query_gate_strength),
            floor=float(spec.query_gate_floor),
            min_edge_weight=float(spec.min_edge_weight),
            mode=spec.query_gate_mode,
            allowed_epistemic=frozenset(str(x).upper() for x in spec.allow_epistemic),
            allowed_status=frozenset(str(x).upper() for x in spec.allow_status),
        )

        # Reuse the tested parent compiler without copying or mutating the canonical transient
        # topology. Matching epoch/hash prevents shadow._ensure_preprocessor() from rebuilding.
        shadow = EmergentAssemblyPreprocessor(self.ledger)
        shadow._compiled_epoch = self._compiled_epoch
        shadow._compiled_state_hash = self._compiled_state_hash
        shadow._rows_by_ref = self._rows_by_ref
        shadow._token_index = self._token_index
        shadow._token_index_epoch = self._token_index_epoch
        shadow._adj = gated_adj
        shadow._edge_count = self._edge_count
        shadow._compiled_index_hash = h(
            {
                "parent_index_hash": parent_index_hash,
                "query_gate_manifest_hash": gate_manifest_hash,
                "derived_query_view": True,
            }
        )

        result = shadow.compile_active_assembly(base_spec)
        parent_version = result.get("preprocessor_version")
        result["parent_preprocessor_version"] = parent_version
        result["preprocessor_version"] = IMPLEMENTATION_ID
        result["query_gate_manifest_hash"] = gate_manifest_hash
        result["query_gate"] = {
            "enabled": True,
            "reason": "QUERY_CONDITIONED_PROPAGATION",
            "mode": spec.query_gate_mode,
            "strength": float(spec.query_gate_strength),
            "floor": float(spec.query_gate_floor),
            "query_token_count": len(query_tokens),
            "edges_observed": gated_adj.edges_observed,
            "edges_damped": gated_adj.edges_damped,
            "edges_pruned_below_parent_min": gated_adj.edges_pruned_below_parent_min,
            "sources_expanded": gated_adj.sources_expanded,
            "lookahead_edges_scanned": gated_adj.lookahead_edges_scanned,
            "lookahead_affinity_wins": gated_adj.lookahead_affinity_wins,
            "authority": "PERFORMANCE_RETRIEVAL_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY",
        }
        result["persistent_second_store"] = False
        result["authority"] = "ASSEMBLY_CONTEXT_ONLY"
        return result
