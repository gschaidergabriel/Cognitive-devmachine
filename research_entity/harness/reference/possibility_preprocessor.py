from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from typing import Any, Iterable
import hashlib
import json
import math
import re


def _h(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    ).hexdigest()


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


class StalePossibilityEpoch(ValueError):
    pass


class PossibilityPreprocessor:
    """Disposable query-time possibility compiler over UnifiedDB/ClayGraph projections.

    This intentionally is not another database or truth store. It compiles a bounded,
    query-conditioned candidate surface from current semantic/graph projections. Outputs
    remain context only: reachability or score never grants effect authority. Evidence
    sharing one lineage_root counts once for the independence gate.
    """

    EDGE_MULTIPLIER = {
        "requires": 1.35,
        "enables": 1.20,
        "causal": 1.18,
        "semantic": 1.00,
        "conflicts": 0.70,
        "derived": 0.85,
    }
    REQUIREMENT_WEIGHT = {
        "rule": 1.45,
        "cap": 1.20,
        "constraint": 0.72,
        "res": 0.85,
    }

    def __init__(
        self,
        *,
        source_epoch: int,
        graph_epoch: int,
        nodes: Iterable[dict[str, Any]],
        edges: Iterable[dict[str, Any]],
        affordances: Iterable[dict[str, Any]],
    ):
        self.source_epoch = int(source_epoch)
        self.graph_epoch = int(graph_epoch)
        self.nodes = {str(node["id"]): dict(node) for node in nodes}
        self.edges: dict[str, list[tuple[str, float, str]]] = defaultdict(list)
        for edge in edges:
            source = str(edge["source"])
            target = str(edge["target"])
            weight = float(edge.get("weight", 1.0))
            relation_type = str(edge.get("relation_type", "semantic"))
            self.edges[source].append((target, weight, relation_type))
            self.edges[target].append((source, weight, relation_type))
        self.affordances = {str(a["id"]): dict(a) for a in affordances}
        self.docs = {
            node_id: _tokens(str(node.get("text") or node.get("label") or node_id))
            for node_id, node in self.nodes.items()
        }
        self.df: Counter[str] = Counter()
        for tokens in self.docs.values():
            for token in set(tokens):
                self.df[token] += 1
        self.avgdl = max(
            1.0,
            sum(map(len, self.docs.values())) / max(1, len(self.docs)),
        )

    def _bm25(self, query: str, node_id: str) -> float:
        query_tokens = _tokens(query)
        tokens = self.docs[node_id]
        tf = Counter(tokens)
        total = max(1, len(self.docs))
        score = 0.0
        for token in query_tokens:
            if token not in self.df:
                continue
            idf = math.log(
                1 + (total - self.df[token] + 0.5) / (self.df[token] + 0.5)
            )
            frequency = tf[token]
            if frequency:
                score += idf * (frequency * 2.2) / (
                    frequency
                    + 1.2 * (1 - 0.75 + 0.75 * len(tokens) / self.avgdl)
                )
        return score

    def lexical_baseline(self, text: str, k: int = 12) -> list[str]:
        scored = sorted(
            ((node_id, self._bm25(text, node_id)) for node_id in self.nodes),
            key=lambda item: (-item[1], item[0]),
        )
        return [node_id for node_id, score in scored if score > 0][:k]

    def compile(self, query: PossibilityQuery) -> dict[str, Any]:
        if not query.query_id.strip() or not query.text.strip():
            raise ValueError("query_id and text required")
        if (
            query.basis_epoch != self.source_epoch
            or query.graph_epoch != self.graph_epoch
        ):
            raise StalePossibilityEpoch(
                "query epochs "
                f"source={query.basis_epoch}/graph={query.graph_epoch} "
                f"current={self.source_epoch}/{self.graph_epoch}"
            )

        seeds = self.lexical_baseline(query.text, query.max_seeds)
        scores = {node_id: self._bm25(query.text, node_id) for node_id in seeds}
        frontier = dict(scores)
        for hop in range(1, query.max_hops + 1):
            decay = 0.62 if hop == 1 else 0.34 / max(1, hop - 1)
            next_frontier: dict[str, float] = {}
            for source, base in frontier.items():
                for target, weight, relation_type in self.edges.get(source, ()):
                    propagated = (
                        base
                        * weight
                        * decay
                        * self.EDGE_MULTIPLIER.get(relation_type, 1.0)
                    )
                    if propagated > next_frontier.get(target, 0.0):
                        next_frontier[target] = propagated
            for node_id, value in next_frontier.items():
                scores[node_id] = max(scores.get(node_id, 0.0), value)
            frontier = next_frontier

        candidates: list[PossibilityCandidate] = []
        for candidate_id, spec in self.affordances.items():
            requirements = tuple(map(str, spec.get("requirements", ())))
            if not requirements:
                continue
            covered = tuple(
                ref for ref in requirements if scores.get(ref, 0.0) > 0
            )
            missing = tuple(ref for ref in requirements if ref not in covered)
            completeness = len(covered) / len(requirements)

            def requirement_weight(ref: str) -> float:
                return self.REQUIREMENT_WEIGHT.get(ref.split(":", 1)[0], 1.0)

            denominator = sum(requirement_weight(ref) for ref in requirements) or 1.0
            evidence = sum(
                scores.get(ref, 0.0) * requirement_weight(ref)
                for ref in requirements
            ) / denominator
            score = (
                completeness * 3.0
                + evidence
                - 1.25 * (1.0 - completeness)
            )
            conflicts = tuple(
                ref
                for ref in covered
                if str(self.nodes.get(ref, {}).get("epistemic", "KNOWN")).upper()
                == "CONFLICT"
            )
            uncertainty = tuple(
                ref
                for ref in covered
                if str(self.nodes.get(ref, {}).get("epistemic", "KNOWN")).upper()
                == "UNKNOWN"
            )
            lineages = tuple(
                sorted(
                    {
                        str(self.nodes.get(ref, {}).get("lineage_root") or ref)
                        for ref in covered
                    }
                )
            )
            admissible = (
                completeness >= query.min_completeness
                and len(lineages) >= query.min_independent_support
                and not conflicts
            )
            candidates.append(
                PossibilityCandidate(
                    candidate_id=candidate_id,
                    score=score,
                    completeness=completeness,
                    proof_refs=covered,
                    missing_refs=missing,
                    conflict_refs=conflicts,
                    uncertainty_refs=uncertainty,
                    independent_lineages=lineages,
                    admissible=admissible,
                )
            )

        candidates.sort(
            key=lambda candidate: (
                not candidate.admissible,
                -candidate.score,
                candidate.candidate_id,
            )
        )
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
        }
        body["receipt_hash"] = _h(body)
        return body
