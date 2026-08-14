from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable
import hashlib
import json
import math
import re


def _h(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _stem(token: str) -> str:
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    elif len(token) > 4 and token.endswith("es"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s"):
        token = token[:-1]
    if token.endswith("e") and len(token) > 4:
        token = token[:-1]
    return token


def _tokens(text: str) -> list[str]:
    return [_stem(t) for t in re.findall(r"[a-z0-9_]+", text.lower())]


@dataclass(frozen=True)
class PossibilityQuery:
    query_id: str
    text: str
    basis_epoch: int
    graph_epoch: int
    max_seeds: int = 12
    max_hops: int = 2
    max_candidates: int = 12
    min_completeness: float = 0.66
    min_independent_support: int = 1
    min_marginal_gain: float = 0.01


@dataclass(frozen=True)
class PossibilityCandidate:
    candidate_id: str
    score: float
    completeness: float
    proof_refs: tuple[str, ...]
    missing_refs: tuple[str, ...]
    conflict_refs: tuple[str, ...]
    uncertainty_refs: tuple[str, ...]
    independent_lineages: tuple[str, ...]
    admissible: bool
    authority: str = "NONE"


@dataclass(frozen=True)
class GraphEdge:
    target: str
    weight: float
    relation_type: str
    declared_proof_eligible: bool
    proof_eligible: bool
    source_epoch: int | None
    graph_epoch: int | None
    evidence_class: str
    provenance_verified: bool
    rejection_reason: str | None


class StalePossibilityEpoch(ValueError):
    pass


class PossibilityPreprocessor:
    """Disposable query-time possibility compiler over UnifiedDB/ClayGraph projections.

    ClayGraph activation and proof satisfaction are deliberately separate. Any current
    graph edge may improve accessibility/ranking, but proof support is admitted only when
    *all* proof-policy conditions are satisfied: the edge is explicitly declared proof
    eligible, is bound to the exact current semantic + graph epochs, carries a trusted
    evidence class, and has verified provenance. This turns ``proof_eligible`` from a
    model/graph boolean into a fail-closed derived property.

    Expansion is bounded and records an adaptive STOP decision once the remaining frontier
    cannot deliver material marginal activation/proof gain. This is intentionally a small,
    deterministic approximation of state-aware reconstructive retrieval: NO_EXPAND is a
    first-class valid action rather than forcing every query through all allowed hops.

    Outputs are query-conditioned context only, never a second canonical store. Shared
    lineage roots count once for the independence gate. Neither activation nor candidate
    selection grants execution authority.
    """

    EDGE_MULTIPLIER = {
        "requires": 1.35,
        "enables": 1.20,
        "causal": 1.18,
        "semantic": 1.00,
        "conflicts": 0.70,
        "derived": 0.85,
    }
    REQUIREMENT_WEIGHT = {"rule": 1.45, "cap": 1.20, "constraint": 0.72, "res": 0.85}
    TRUSTED_PROOF_EVIDENCE = {
        "VERIFIED",
        "VALIDATED",
        "MEASURED",
        "AUTHORITATIVE",
        "CANONICAL",
    }

    def __init__(self, *, source_epoch: int, graph_epoch: int, nodes: Iterable[dict[str, Any]], edges: Iterable[dict[str, Any]], affordances: Iterable[dict[str, Any]]):
        self.source_epoch = int(source_epoch)
        self.graph_epoch = int(graph_epoch)
        self.nodes = {str(node["id"]): dict(node) for node in nodes}
        self.edges: dict[str, list[GraphEdge]] = defaultdict(list)
        self.proof_edge_audit = Counter()
        for edge in edges:
            source = str(edge["source"])
            target = str(edge["target"])
            weight = float(edge.get("weight", 1.0))
            relation_type = str(edge.get("relation_type", "semantic"))
            declared = bool(edge.get("proof_eligible", False))
            edge_source_epoch = edge.get("source_epoch")
            edge_graph_epoch = edge.get("graph_epoch")
            source_epoch = int(edge_source_epoch) if edge_source_epoch is not None else None
            graph_epoch = int(edge_graph_epoch) if edge_graph_epoch is not None else None
            evidence_class = str(edge.get("evidence_class", "UNKNOWN")).upper()
            provenance_verified = edge.get("provenance_verified") is True

            rejection_reason: str | None = None
            if not declared:
                rejection_reason = "NOT_DECLARED"
            elif source_epoch != self.source_epoch:
                rejection_reason = "STALE_SOURCE_EPOCH"
            elif graph_epoch != self.graph_epoch:
                rejection_reason = "STALE_GRAPH_EPOCH"
            elif not provenance_verified:
                rejection_reason = "PROVENANCE_UNVERIFIED"
            elif evidence_class not in self.TRUSTED_PROOF_EVIDENCE:
                rejection_reason = "EVIDENCE_CLASS_UNTRUSTED"

            admitted = rejection_reason is None
            self.proof_edge_audit["DECLARED" if declared else "UNDECLARED"] += 1
            self.proof_edge_audit["ADMITTED" if admitted else "REJECTED"] += 1
            if rejection_reason:
                self.proof_edge_audit[rejection_reason] += 1

            fwd = GraphEdge(
                target,
                weight,
                relation_type,
                declared,
                admitted,
                source_epoch,
                graph_epoch,
                evidence_class,
                provenance_verified,
                rejection_reason,
            )
            rev = GraphEdge(
                source,
                weight,
                relation_type,
                declared,
                admitted,
                source_epoch,
                graph_epoch,
                evidence_class,
                provenance_verified,
                rejection_reason,
            )
            self.edges[source].append(fwd)
            self.edges[target].append(rev)
        self.affordances = {str(a["id"]): dict(a) for a in affordances}
        self.docs = {node_id: _tokens(str(node.get("text") or node.get("label") or node_id)) for node_id, node in self.nodes.items()}
        self.df: Counter[str] = Counter()
        for tokens in self.docs.values():
            for token in set(tokens):
                self.df[token] += 1
        self.avgdl = max(1.0, sum(map(len, self.docs.values())) / max(1, len(self.docs)))

    def _bm25(self, query: str, node_id: str) -> float:
        query_tokens = _tokens(query)
        tokens = self.docs[node_id]
        tf = Counter(tokens)
        total = max(1, len(self.docs))
        score = 0.0
        for token in query_tokens:
            if token not in self.df:
                continue
            idf = math.log(1 + (total - self.df[token] + 0.5) / (self.df[token] + 0.5))
            frequency = tf[token]
            if frequency:
                score += idf * (frequency * 2.2) / (frequency + 1.2 * (1 - 0.75 + 0.75 * len(tokens) / self.avgdl))
        return score

    def lexical_baseline(self, text: str, k: int = 12) -> list[str]:
        scored = sorted(((node_id, self._bm25(text, node_id)) for node_id in self.nodes), key=lambda item: (-item[1], item[0]))
        return [node_id for node_id, score in scored if score > 0][:k]

    def compile(self, query: PossibilityQuery) -> dict[str, Any]:
        if not query.query_id.strip() or not query.text.strip():
            raise ValueError("query_id and text required")
        if query.basis_epoch != self.source_epoch or query.graph_epoch != self.graph_epoch:
            raise StalePossibilityEpoch(f"query epochs source={query.basis_epoch}/graph={query.graph_epoch} current={self.source_epoch}/{self.graph_epoch}")
        if query.min_marginal_gain < 0:
            raise ValueError("min_marginal_gain must be non-negative")

        seeds = self.lexical_baseline(query.text, query.max_seeds)
        scores = {node_id: self._bm25(query.text, node_id) for node_id in seeds}
        proof_scores = dict(scores)
        frontier = dict(scores)
        proof_frontier = dict(proof_scores)
        expansion_trace: list[dict[str, Any]] = []

        for hop in range(1, query.max_hops + 1):
            decay = 0.62 if hop == 1 else 0.34 / max(1, hop - 1)
            next_frontier: dict[str, float] = {}
            for source, base in frontier.items():
                for edge in self.edges.get(source, ()):
                    propagated = base * edge.weight * decay * self.EDGE_MULTIPLIER.get(edge.relation_type, 1.0)
                    if propagated > next_frontier.get(edge.target, 0.0):
                        next_frontier[edge.target] = propagated

            next_proof: dict[str, float] = {}
            for source, base in proof_frontier.items():
                for edge in self.edges.get(source, ()):
                    if not edge.proof_eligible:
                        continue
                    propagated = base * edge.weight * decay * self.EDGE_MULTIPLIER.get(edge.relation_type, 1.0)
                    if propagated > next_proof.get(edge.target, 0.0):
                        next_proof[edge.target] = propagated

            activation_gain = max(
                (value - scores.get(node_id, 0.0) for node_id, value in next_frontier.items()),
                default=0.0,
            )
            proof_gain = max(
                (value - proof_scores.get(node_id, 0.0) for node_id, value in next_proof.items()),
                default=0.0,
            )

            for node_id, value in next_frontier.items():
                scores[node_id] = max(scores.get(node_id, 0.0), value)
            for node_id, value in next_proof.items():
                proof_scores[node_id] = max(proof_scores.get(node_id, 0.0), value)

            action = "EXPAND"
            reason = "MARGINAL_GAIN_MATERIAL"
            if not next_frontier:
                action = "STOP"
                reason = "NO_FRONTIER"
            elif max(activation_gain, proof_gain) < query.min_marginal_gain:
                action = "STOP"
                reason = "MARGINAL_GAIN_BELOW_COST_FLOOR"

            expansion_trace.append({
                "hop": hop,
                "action": action,
                "reason": reason,
                "activation_frontier": len(next_frontier),
                "proof_frontier": len(next_proof),
                "activation_gain": round(max(0.0, activation_gain), 8),
                "proof_gain": round(max(0.0, proof_gain), 8),
            })
            frontier = next_frontier
            proof_frontier = next_proof
            if action == "STOP":
                break

        candidates: list[PossibilityCandidate] = []
        for candidate_id, spec in self.affordances.items():
            requirements = tuple(map(str, spec.get("requirements", ())))
            if not requirements:
                continue
            covered = tuple(ref for ref in requirements if proof_scores.get(ref, 0.0) > 0)
            missing = tuple(ref for ref in requirements if ref not in covered)
            completeness = len(covered) / len(requirements)

            def requirement_weight(ref: str) -> float:
                return self.REQUIREMENT_WEIGHT.get(ref.split(":", 1)[0], 1.0)

            denominator = sum(requirement_weight(ref) for ref in requirements) or 1.0
            evidence = sum(proof_scores.get(ref, 0.0) * requirement_weight(ref) for ref in requirements) / denominator
            score = completeness * 3.0 + evidence - 1.25 * (1.0 - completeness)
            conflicts = tuple(ref for ref in covered if str(self.nodes.get(ref, {}).get("epistemic", "KNOWN")).upper() == "CONFLICT")
            uncertainty = tuple(ref for ref in covered if str(self.nodes.get(ref, {}).get("epistemic", "KNOWN")).upper() == "UNKNOWN")
            lineages = tuple(sorted({str(self.nodes.get(ref, {}).get("lineage_root") or ref) for ref in covered}))
            admissible = completeness >= query.min_completeness and len(lineages) >= query.min_independent_support and not conflicts
            candidates.append(PossibilityCandidate(candidate_id, score, completeness, covered, missing, conflicts, uncertainty, lineages, admissible))

        candidates.sort(key=lambda candidate: (not candidate.admissible, -candidate.score, candidate.candidate_id))
        candidates = candidates[: query.max_candidates]
        admissible = [candidate for candidate in candidates if candidate.admissible]
        body = {
            "query": asdict(query),
            "source_epoch": self.source_epoch,
            "graph_epoch": self.graph_epoch,
            "seed_refs": seeds,
            "candidates": [asdict(candidate) for candidate in candidates],
            "selected_ref": admissible[0].candidate_id if admissible else None,
            "abstain": not bool(admissible),
            "derived": True,
            "persistent_second_store": False,
            "authority": "NON_AUTHORITATIVE_PREPROCESSOR_CONTEXT",
            "independence_rule": "shared_lineage_root_counts_once",
            "proof_rule": "proof edges require declared eligibility + exact source/graph epochs + verified provenance + trusted evidence class",
            "proof_edge_audit": dict(sorted(self.proof_edge_audit.items())),
            "expansion_policy": "bounded adaptive expansion with explicit STOP/NO_EXPAND when marginal gain falls below cost floor",
            "expansion_trace": expansion_trace,
        }
        body["receipt_hash"] = _h(body)
        return body
