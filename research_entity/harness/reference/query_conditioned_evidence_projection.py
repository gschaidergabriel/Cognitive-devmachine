from __future__ import annotations

"""QCEP-0.3.1: query-conditioned ephemeral evidence projection with exact Top-K stop.

This is a research candidate, not a database/truth/effect surface. It compiles a disposable
per-query navigation projection from one epoch-bound UnifiedDB ledger. Query-conditioned
edge relevance can change accessibility/rank only. It never mints proof or effect authority.

Compared with QCEP-0.2, 0.3 adds the same score-bound idea as EAP-EXACT-TOPK-1.5. The proof
still applies because every transition multiplier is bounded in (0, 1]: edge weight <= 1,
hop decay <= 1, query relevance <= 1 and hub factor <= 1. Therefore a descendant cannot
exceed its frontier ancestor. Once K admissible visited candidates have a Kth score strictly
greater than the best remaining frontier score, no unseen node can enter final Top-K.
Equal-score frontiers are not stopped, preserving deterministic tie ordering.

OOD invariants:
- query conditioning activates at a source only if at least one ADMISSIBLE outgoing edge has
  positive query signal; otherwise local edge factor is exactly 1.0;
- missing labels are UNKNOWN, not counterevidence;
- structural JSON/schema keys such as source/target/strength never count as semantic signal;
- only explicitly evidence-bearing fields may contribute query tokens;
- inadmissible nodes may be observed as negative space but cannot relay or manufacture signal.
"""

from dataclasses import dataclass
import hashlib
import heapq
import json
import math
import re
from typing import Any

_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
_VERSION = "QCEP-0.3.1-EXACT-TOPK"
_EPS = 1e-15
_SEMANTIC_FIELDS = frozenset({
    "text", "label", "description", "query_cue", "cue", "semantic_label",
    "tags", "evidence_tags", "purpose", "constraint", "constraints",
    "predicate", "reason", "meaning", "summary",
})


def _canon(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_canon(value).encode("utf-8")).hexdigest()


def _tokens(value: Any) -> frozenset[str]:
    if not isinstance(value, str):
        value = str(value)
    return frozenset(t.lower() for t in _TOKEN_RE.findall(value) if len(t) > 1)


def _semantic_tokens(value: Any) -> frozenset[str]:
    """Tokenize explicit semantic payload values, never container/schema field names."""
    if isinstance(value, str):
        return _tokens(value)
    if isinstance(value, (list, tuple, set, frozenset)):
        out: set[str] = set()
        for item in value:
            out.update(_semantic_tokens(item))
        return frozenset(out)
    if isinstance(value, dict):
        out: set[str] = set()
        for key in _SEMANTIC_FIELDS:
            if key in value:
                out.update(_semantic_tokens(value[key]))
        return frozenset(out)
    return frozenset()


class StaleEvidenceProjection(ValueError):
    pass


@dataclass(frozen=True)
class QueryEvidenceSpec:
    projection_id: str
    query_text: str
    seed_refs: tuple[str, ...]
    basis_epoch: int
    max_items: int = 12
    max_hops: int = 3
    frontier_budget: int = 512
    hop_decay: float = 0.88
    min_edge_weight: float = 0.0
    relevance_floor: float = 0.28
    hub_penalty: float = 0.24
    allowed_status: tuple[str, ...] = ("CURRENT",)
    allowed_epistemic: tuple[str, ...] = ("KNOWN",)
    exact_top_k_stop: bool = True


class QueryConditionedEvidenceProjector:
    """Disposable query-conditioned graph projection over one coherent ledger epoch."""

    def __init__(self, ledger: Any):
        self.ledger = ledger
        self._epoch: int | None = None
        self._state_hash: str | None = None
        self._rows: dict[str, dict[str, Any]] = {}
        self._adj: dict[str, tuple[dict[str, Any], ...]] = {}
        self._out_degree: dict[str, int] = {}

    @staticmethod
    def _ref(row: dict[str, Any]) -> str:
        return f"{row['domain']}:{row['key']}"

    @staticmethod
    def _dep_ref(value: dict[str, Any], side: str) -> str | None:
        direct = value.get(side) or value.get(f"{side}_ref")
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        kind = value.get(f"{side}_kind")
        ident = value.get(f"{side}_id")
        if kind is not None and ident is not None:
            return f"{kind}:{ident}"
        return None

    def _ensure(self) -> None:
        epoch = int(self.ledger.epoch)
        state_hash = str(self.ledger.semantic_state_hash)
        if self._epoch == epoch and self._state_hash == state_hash:
            return
        rows = list(self.ledger.materialized())
        by_ref = {self._ref(row): dict(row) for row in rows}
        adj: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            if row.get("domain") != "dependency":
                continue
            if str(row.get("status", "")).upper() != "CURRENT" or str(row.get("epistemic", "")).upper() != "KNOWN":
                continue
            value = row.get("value")
            if not isinstance(value, dict):
                continue
            source = self._dep_ref(value, "source")
            target = self._dep_ref(value, "target")
            if not source or not target:
                continue
            try:
                weight = float(value.get("strength", value.get("weight", 1.0))) * float(value.get("confidence", 1.0))
            except (TypeError, ValueError):
                continue
            weight = max(0.0, min(1.0, weight))
            edge = {
                "target": target,
                "weight": weight,
                "relation": str(value.get("relation_type", value.get("relation", "SEMANTIC_DEPENDENCY"))),
                "dependency_ref": self._ref(row),
                "dependency_value": value,
            }
            adj.setdefault(source, []).append(edge)
            if bool(value.get("bidirectional", False)):
                back = dict(edge)
                back["target"] = source
                adj.setdefault(target, []).append(back)
        self._rows = by_ref
        self._adj = {source: tuple(sorted(edges, key=lambda e: (e["target"], e["dependency_ref"]))) for source, edges in adj.items()}
        self._out_degree = {source: len(edges) for source, edges in self._adj.items()}
        self._epoch = epoch
        self._state_hash = state_hash

    @staticmethod
    def _admissible(row: dict[str, Any] | None, allowed_status: set[str], allowed_epistemic: set[str]) -> bool:
        return bool(row) and str(row.get("status", "")).upper() in allowed_status and str(row.get("epistemic", "")).upper() in allowed_epistemic

    def _edge_query_overlap(self, edge: dict[str, Any], query_tokens: frozenset[str]) -> float:
        target = self._rows.get(edge["target"], {})
        evidence_tokens = (
            _tokens(edge["relation"])
            | _semantic_tokens(edge["dependency_value"])
            | _semantic_tokens(target.get("value", {}))
        )
        overlap = len(query_tokens & evidence_tokens)
        return min(1.0, overlap / max(1.0, min(4.0, float(len(query_tokens) or 1))))

    def _edge_factor(self, edge: dict[str, Any], query_tokens: frozenset[str], spec: QueryEvidenceSpec, *, conditioning_available: bool) -> tuple[float, float, float]:
        overlap = self._edge_query_overlap(edge, query_tokens)
        if not conditioning_available:
            return 1.0, overlap, 1.0
        relevance = spec.relevance_floor + (1.0 - spec.relevance_floor) * overlap
        hub = self._out_degree.get(edge["target"], 0)
        hub_factor = 1.0 / (1.0 + spec.hub_penalty * math.log1p(hub))
        return relevance * hub_factor, overlap, hub_factor

    def project(self, spec: QueryEvidenceSpec) -> dict[str, Any]:
        if not spec.projection_id.strip() or not spec.query_text.strip():
            raise ValueError("projection_id and query_text required")
        if spec.max_items <= 0 or spec.max_items > 4096 or spec.frontier_budget <= 0 or spec.max_hops < 0:
            raise ValueError("invalid bounds")
        if not 0.0 < spec.hop_decay <= 1.0 or not 0.0 <= spec.min_edge_weight <= 1.0:
            raise ValueError("invalid traversal weights")
        if not 0.0 < spec.relevance_floor <= 1.0 or spec.hub_penalty < 0.0:
            raise ValueError("invalid query-conditioning parameters")
        self._ensure()
        if int(spec.basis_epoch) != int(self._epoch):
            raise StaleEvidenceProjection(f"basis {spec.basis_epoch}!={self._epoch}")

        qtokens = _tokens(spec.query_text)
        allowed_status = {x.upper() for x in spec.allowed_status}
        allowed_epistemic = {x.upper() for x in spec.allowed_epistemic}
        frontier: list[tuple[float, int, str, str | None, str | None, str | None, float, float]] = []
        for ref in sorted(set(spec.seed_refs)):
            if ref in self._rows and self._rows[ref].get("domain") != "dependency":
                heapq.heappush(frontier, (-1.0, 0, ref, None, None, None, 1.0, 1.0))

        best: dict[str, tuple[float, int, str | None, str | None, str | None, float, float]] = {}
        blocked: set[str] = set()
        admissible_visited_scores: list[float] = []
        expansions = 0
        stop_reason = "FRONTIER_EXHAUSTED"

        while frontier and expansions < spec.frontier_budget:
            neg_score, depth, ref, via, relation, dep_ref, query_relevance, hub_factor = heapq.heappop(frontier)
            score = -neg_score
            old = best.get(ref)
            if old is not None and score <= old[0] + _EPS:
                continue
            best[ref] = (score, depth, via, relation, dep_ref, query_relevance, hub_factor)
            expansions += 1
            row = self._rows.get(ref)
            if row is not None and row.get("domain") != "dependency" and self._admissible(row, allowed_status, allowed_epistemic):
                admissible_visited_scores.append(score)

            if row is not None and depth < spec.max_hops:
                if not self._admissible(row, allowed_status, allowed_epistemic):
                    blocked.add(ref)
                else:
                    edges = self._adj.get(ref, ())
                    conditioning_available = any(
                        self._admissible(self._rows.get(edge["target"]), allowed_status, allowed_epistemic)
                        and self._edge_query_overlap(edge, qtokens) > 0.0
                        for edge in edges
                    )
                    for edge in edges:
                        if edge["weight"] < spec.min_edge_weight:
                            continue
                        factor, edge_rel, edge_hub = self._edge_factor(edge, qtokens, spec, conditioning_available=conditioning_available)
                        next_score = score * edge["weight"] * spec.hop_decay * factor
                        previous = best.get(edge["target"])
                        if next_score <= 0.0 or (previous is not None and next_score <= previous[0] + _EPS):
                            continue
                        heapq.heappush(frontier, (-next_score, depth + 1, edge["target"], ref, edge["relation"], edge["dependency_ref"], edge_rel, edge_hub))

            if spec.exact_top_k_stop and len(admissible_visited_scores) >= spec.max_items and frontier:
                kth_score = sorted(admissible_visited_scores, reverse=True)[spec.max_items - 1]
                frontier_upper_bound = -frontier[0][0]
                if kth_score > frontier_upper_bound + _EPS:
                    stop_reason = "EXACT_TOP_K_SCORE_BOUND"
                    break

        if expansions >= spec.frontier_budget and frontier:
            stop_reason = "FRONTIER_BUDGET"
        elif not frontier:
            stop_reason = "FRONTIER_EXHAUSTED"

        selected=[]; suppressed=[]
        for ref,state in best.items():
            row=self._rows.get(ref)
            if row is None or row.get("domain")=="dependency":
                continue
            score,depth,via,relation,dep_ref,query_relevance,hub_factor=state
            item={
                "ref":ref,"domain":row.get("domain"),"key":row.get("key"),"value":row.get("value"),
                "epistemic":row.get("epistemic"),"status":row.get("status"),"source_semantic_hash":row.get("semantic_hash"),
                "activation_score":score,"hop":depth,"via_ref":via,"relation_type":relation,"dependency_ref":dep_ref,
                "edge_query_relevance":query_relevance,"edge_hub_factor":hub_factor,"authority":"CONTEXT_ONLY",
            }
            (selected if self._admissible(row,allowed_status,allowed_epistemic) else suppressed).append(item)
        selected.sort(key=lambda x:(-x["activation_score"],x["hop"],x["ref"]))
        suppressed.sort(key=lambda x:(-x["activation_score"],x["hop"],x["ref"]))
        selected=selected[:spec.max_items]
        receipt={
            "schema_version":"1.2","preprocessor_version":_VERSION,"projection_id":spec.projection_id,
            "basis_epoch":self._epoch,"semantic_state_hash":self._state_hash,"query_hash":_hash(spec.query_text),
            "selected":selected,"suppressed":suppressed[:spec.max_items],"blocked_propagation_refs":sorted(blocked),
            "frontier_expansions":expansions,"frontier_stop_reason":stop_reason,
            "exact_top_k_stop":bool(spec.exact_top_k_stop),"persistent_second_store":False,
            "projection_kind":"QUERY_CONDITIONED_EPHEMERAL_EVIDENCE_GRAPH","truth_authority":"NONE","effect_authority":"NONE",
            "proof_rule":"query-conditioned activation changes accessibility only; it never mints proof eligibility",
            "missing_edge_semantics_rule":"NO_ADMISSIBLE_LOCAL_QUERY_SIGNAL => EXACT_STATIC_EDGE_FACTOR",
            "semantic_signal_rule":"STRUCTURAL_JSON_KEYS_EXCLUDED_ONLY_EXPLICIT_EVIDENCE_FIELDS_COUNT",
            "top_k_proof":"ALL_TRANSITION_MULTIPLIERS_LE_1_DESCENDANT_SCORE_LE_FRONTIER_ANCESTOR",
        }
        receipt["receipt_hash"]=_hash(receipt)
        return receipt
