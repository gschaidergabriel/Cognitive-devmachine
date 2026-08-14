#!/usr/bin/env python3
"""Actual-repository ClayGraph retrieval benchmark.

Builds the derived ClayGraph from the checked-out repository, then derives a deterministic
relation-grounded evaluation set from explicit graph edges.  This closes a limitation of
EXP-CG2-ACTIVE-ENVELOPE-ROUTER-001: the benchmark exercises the real claygraph_build
materialization instead of a hand-built proxy.

The arms are intentionally hard to game:
  * sqlite_fts5: ordinary lexical retrieval over the same node text.
  * fixed_graph: current-style lexical seeds + unqualified 2-hop spreading activation.
  * planned_graph: relation-planned bounded traversal from the same lexical seeds.
  * sqlite_structured_upper_bound: exact source identity + indexed relation query.  This is
    an explicit counterhypothesis/upper bound: ClayGraph must not claim that SQL cannot
    traverse explicit structure.

The gold set is not independent human answer-quality ground truth.  It is a reproducible
structural-retrieval benchmark: for a source and declared relation type, the direct targets
already encoded by claygraph_build are the expected results.  Results therefore support
retrieval-engineering claims only, never scientific truth or effect authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sqlite3
import statistics
import tempfile
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Callable

import claygraph_build
import claygraph_query

ROOT = Path(__file__).resolve().parents[1]
BAD_CURRENT_STATUSES = {"STALE", "REFUTED", "SUPERSEDED", "REVOKED", "RETRACTED", "QUARANTINED"}
RELATIONS = (
    "DEPENDS_ON",
    "SUPPORTS",
    "CHALLENGES",
    "CONTRADICTS",
    "SUPERSEDES",
    "DERIVED_FROM",
    "EVIDENCE_FOR",
    "PARENT_OF",
)
RELATION_PROMPT = {
    "DEPENDS_ON": "What does {source} depend on?",
    "SUPPORTS": "What does {source} support?",
    "CHALLENGES": "What does {source} challenge?",
    "CONTRADICTS": "What does {source} contradict?",
    "SUPERSEDES": "What does {source} supersede?",
    "DERIVED_FROM": "What is {source} derived from?",
    "EVIDENCE_FOR": "What does {source} provide evidence for?",
    "PARENT_OF": "What is a child or successor of {source}?",
}
MEANINGFUL_TYPES = {
    "claim", "hypothesis", "experiment", "negative_result", "architecture",
    "topic_packet", "run", "event", "reference", "artifact", "source",
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def percentile(values: list[float], q: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, min(len(ordered) - 1, math.ceil(q * len(ordered)) - 1))]


def identity_for_query(node: dict[str, Any]) -> str:
    identity = str(node.get("identity") or "").strip()
    if identity and len(identity) <= 180:
        return identity
    label = str(node.get("label") or "").strip()
    if label:
        return label[:180]
    return str(node.get("id"))


def is_current_admissible(node: dict[str, Any]) -> bool:
    status = str(node.get("status") or "").upper()
    return status not in BAD_CURRENT_STATUSES


def make_cases(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]], max_per_relation: int) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str], set[str]] = defaultdict(set)
    for edge in edges:
        relation = str(edge.get("type") or "")
        source = str(edge.get("source") or "")
        target = str(edge.get("target") or "")
        if relation not in RELATIONS or source not in nodes or target not in nodes:
            continue
        if nodes[source].get("type") not in MEANINGFUL_TYPES or nodes[target].get("type") not in MEANINGFUL_TYPES:
            continue
        if not is_current_admissible(nodes[target]):
            continue
        grouped[(source, relation)].add(target)

    by_relation: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for (source, relation), gold in grouped.items():
        if not gold:
            continue
        source_text = identity_for_query(nodes[source])
        # Avoid degenerate queries with no meaningful lexical source anchor.
        if len(claygraph_query.tokens(source_text)) < 1:
            continue
        query = RELATION_PROMPT[relation].format(source=source_text)
        case = {
            "source": source,
            "source_identity": nodes[source].get("identity"),
            "relation": relation,
            "query": query,
            "gold": sorted(gold),
        }
        digest = hashlib.sha256(f"{source}|{relation}".encode()).hexdigest()
        case["order"] = digest
        by_relation[relation].append(case)

    cases: list[dict[str, Any]] = []
    for relation in RELATIONS:
        candidates = sorted(by_relation.get(relation, []), key=lambda x: x["order"])
        cases.extend(candidates[:max_per_relation])
    for case in cases:
        case.pop("order", None)
    return cases


def searchable(node: dict[str, Any]) -> str:
    return " ".join(str(node.get(k, "")) for k in ("identity", "label", "text", "path", "branch", "status", "evidence_class"))


def build_fts(nodes: dict[str, dict[str, Any]]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("CREATE VIRTUAL TABLE node_fts USING fts5(id UNINDEXED, body, tokenize='unicode61')")
    con.executemany("INSERT INTO node_fts(id,body) VALUES(?,?)", ((nid, searchable(n)) for nid, n in nodes.items()))
    con.commit()
    return con


def fts_query(con: sqlite3.Connection, query: str, k: int) -> list[str]:
    toks = claygraph_query.tokens(query)
    if not toks:
        return []
    # OR preserves recall and makes the baseline robust to relation prompt words.
    expr = " OR ".join('"' + t.replace('"', '""') + '"' for t in dict.fromkeys(toks))
    try:
        return [r[0] for r in con.execute(
            "SELECT id FROM node_fts WHERE node_fts MATCH ? ORDER BY bm25(node_fts) LIMIT ?", (expr, k)
        )]
    except sqlite3.OperationalError:
        return []


def build_adjacency(edges: list[dict[str, Any]]) -> dict[str, list[tuple[str, str, float, str]]]:
    adjacency: dict[str, list[tuple[str, str, float, str]]] = defaultdict(list)
    for edge in edges:
        source, target = str(edge["source"]), str(edge["target"])
        relation = str(edge.get("type", "RELATED"))
        weight = float(edge.get("weight", 1.0)) * claygraph_query.EDGE_PRIOR.get(relation, 0.45)
        adjacency[source].append((target, relation, weight, "forward"))
        adjacency[target].append((source, relation, weight * 0.78, "reverse"))
    return adjacency


def fixed_graph_query(query: str, nodes: dict[str, dict[str, Any]], adjacency, k: int, seed_limit: int = 14, hops: int = 2) -> list[str]:
    seeds = claygraph_query.seed_scores(query, nodes)
    ranked = sorted(seeds.items(), key=lambda kv: (-kv[1], kv[0]))[:seed_limit]
    active = dict(ranked)
    frontier = dict(ranked)
    decay = 0.58
    for _depth in range(1, hops + 1):
        nxt: dict[str, float] = {}
        for source, source_score in frontier.items():
            for target, _etype, eweight, _direction in adjacency.get(source, []):
                node = nodes.get(target)
                if not node:
                    continue
                propagated = source_score * decay * eweight * claygraph_query.TYPE_PRIOR.get(str(node.get("type")), 0.8)
                if propagated < 0.08:
                    continue
                prior = active.get(target, 0.0)
                candidate = max(prior, propagated) + (0.12 * min(prior, propagated) if prior and propagated else 0.0)
                if candidate > prior:
                    active[target] = candidate
                if propagated > nxt.get(target, 0.0):
                    nxt[target] = propagated
        frontier = dict(sorted(nxt.items(), key=lambda kv: (-kv[1], kv[0]))[: max(30, seed_limit * 4)])
        if not frontier:
            break
    return [nid for nid, _ in sorted(active.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


def planned_graph_query(query: str, relation: str, nodes: dict[str, dict[str, Any]], out_edges, k: int, seed_limit: int = 14) -> list[str]:
    """Relation-planned one-hop traversal with current-status gating.

    This isolates G1b's core claim: when a relation is explicitly requested, traversal is
    earned by the query and should follow only the requested qualified relation.  It does
    not pretend to solve natural-language query classification here.
    """
    seeds = claygraph_query.seed_scores(query, nodes)
    ranked = sorted(seeds.items(), key=lambda kv: (-kv[1], kv[0]))[:seed_limit]
    candidates: dict[str, float] = {}
    relation_prior = claygraph_query.EDGE_PRIOR.get(relation, 0.45)
    for source, source_score in ranked:
        for target, edge_weight in out_edges.get((source, relation), []):
            node = nodes.get(target)
            if not node or not is_current_admissible(node):
                continue
            score = source_score * relation_prior * edge_weight * claygraph_query.TYPE_PRIOR.get(str(node.get("type")), 0.8)
            if score > candidates.get(target, float("-inf")):
                candidates[target] = score
    return [nid for nid, _ in sorted(candidates.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]


def build_structured_sqlite(nodes: dict[str, dict[str, Any]], edges: list[dict[str, Any]]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.executescript("""
      CREATE TABLE nodes(id TEXT PRIMARY KEY, identity TEXT, status TEXT, node_type TEXT);
      CREATE INDEX idx_nodes_identity ON nodes(identity);
      CREATE TABLE edges(source TEXT NOT NULL, target TEXT NOT NULL, relation TEXT NOT NULL, weight REAL NOT NULL);
      CREATE INDEX idx_edges_source_relation ON edges(source,relation,target);
    """)
    con.executemany("INSERT INTO nodes VALUES(?,?,?,?)", (
        (nid, str(n.get("identity") or ""), str(n.get("status") or ""), str(n.get("type") or "")) for nid, n in nodes.items()
    ))
    con.executemany("INSERT INTO edges VALUES(?,?,?,?)", (
        (str(e["source"]), str(e["target"]), str(e.get("type") or ""), float(e.get("weight", 1.0))) for e in edges
    ))
    con.commit()
    return con


def structured_query(con: sqlite3.Connection, source: str, relation: str, k: int) -> list[str]:
    return [r[0] for r in con.execute(
        "SELECT target FROM edges WHERE source=? AND relation=? ORDER BY target LIMIT ?", (source, relation, k)
    )]


def evaluate(cases: list[dict[str, Any]], nodes: dict[str, dict[str, Any]], fn: Callable[[dict[str, Any]], list[str]]) -> dict[str, Any]:
    latencies: list[float] = []
    recalls: list[float] = []
    precisions: list[float] = []
    hit = 0
    stale = 0
    returned = 0
    by_relation: dict[str, list[float]] = defaultdict(list)
    for case in cases:
        t0 = time.perf_counter_ns()
        result = fn(case)
        latencies.append((time.perf_counter_ns() - t0) / 1e6)
        gold = set(case["gold"])
        selected = set(result)
        tp = len(gold & selected)
        recall = tp / len(gold) if gold else 1.0
        precision = tp / len(selected) if selected else 0.0
        recalls.append(recall)
        precisions.append(precision)
        by_relation[case["relation"]].append(recall)
        hit += int(tp > 0)
        for nid in result:
            returned += 1
            if nid in nodes and not is_current_admissible(nodes[nid]):
                stale += 1
    if not cases:
        return {"cases": 0, "error": "no eligible cases"}
    return {
        "cases": len(cases),
        "hit_rate": hit / len(cases),
        "mean_recall_at_k": statistics.mean(recalls),
        "mean_precision_at_k": statistics.mean(precisions),
        "stale_rate": stale / returned if returned else 0.0,
        "latency_ms": {
            "p50": statistics.median(latencies),
            "p95": percentile(latencies, 0.95),
            "p99": percentile(latencies, 0.99),
            "mean": statistics.mean(latencies),
        },
        "recall_by_relation": {k: statistics.mean(v) for k, v in sorted(by_relation.items())},
    }


def run(max_per_relation: int = 24, k: int = 8) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="claygraph-actual-") as td:
        graph_dir = Path(td)
        manifest = claygraph_build.build(graph_dir)
        node_list = load_jsonl(graph_dir / "nodes.jsonl")
        edges = load_jsonl(graph_dir / "edges.jsonl")
        nodes = {n["id"]: n for n in node_list}
        cases = make_cases(nodes, edges, max_per_relation=max_per_relation)

        adjacency = build_adjacency(edges)
        out_edges: dict[tuple[str, str], list[tuple[str, float]]] = defaultdict(list)
        for e in edges:
            out_edges[(str(e["source"]), str(e.get("type") or ""))].append((str(e["target"]), float(e.get("weight", 1.0))))
        fts = build_fts(nodes)
        structured = build_structured_sqlite(nodes, edges)

        arms = {
            "sqlite_fts5": evaluate(cases, nodes, lambda c: fts_query(fts, c["query"], k)),
            "fixed_graph": evaluate(cases, nodes, lambda c: fixed_graph_query(c["query"], nodes, adjacency, k)),
            "planned_graph": evaluate(cases, nodes, lambda c: planned_graph_query(c["query"], c["relation"], nodes, out_edges, k)),
            "sqlite_structured_upper_bound": evaluate(cases, nodes, lambda c: structured_query(structured, c["source"], c["relation"], k)),
        }
        fts.close()
        structured.close()

        return {
            "schema_version": "1.0",
            "benchmark": "ACTUAL_REPOSITORY_RELATION_RETRIEVAL",
            "evidence_class": "DERIVED_ACTUAL_CORPUS_ENGINEERING_BENCHMARK",
            "graph_manifest": manifest,
            "case_generation": {
                "cases": len(cases),
                "max_per_relation": max_per_relation,
                "k": k,
                "relations": list(RELATIONS),
                "gold": "direct current-admissible targets of explicit claygraph_build edges",
                "query": "relation prompt over source identity/label; target identity is never inserted into the prompt",
            },
            "arms": arms,
            "boundaries": [
                "This measures structural retrieval against relations already encoded by claygraph_build, not downstream answer correctness.",
                "sqlite_structured_upper_bound is intentionally strong and may tie/beat ClayGraph; SQL graph traversal is not a Clay-exclusive capability.",
                "planned_graph receives the relation class to isolate retrieval routing from natural-language query-classification accuracy.",
                "ClayGraph activation is relevance/navigation only and never truth/effect authority.",
            ],
        }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-per-relation", type=int, default=24)
    ap.add_argument("--k", type=int, default=8)
    ap.add_argument("--output")
    args = ap.parse_args()
    result = run(max(1, min(args.max_per_relation, 100)), max(1, min(args.k, 64)))
    text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        Path(args.output).write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
