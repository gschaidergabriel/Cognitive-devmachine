#!/usr/bin/env python3
"""Query the derived ClayGraph using lexical seeds + typed spreading activation.

This is deliberately explainable. It returns activation paths and timing so RAE workers
can compare it against SQLite/FTS and ordinary staged retrieval. Activation affects
retrieval relevance only; it never changes evidence status or canonical truth.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GRAPH = ROOT / "research_entity" / "claygraph" / "runtime" / "current"
STOP = {
    "the", "and", "for", "with", "from", "that", "this", "into", "oder", "und", "der", "die", "das", "ein", "eine", "mit", "von", "für", "wie", "was", "ist", "sind", "auf", "den", "dem", "des", "bei", "zur", "zum",
}
TYPE_PRIOR = {
    "claim": 1.25,
    "hypothesis": 1.2,
    "experiment": 1.18,
    "negative_result": 1.18,
    "architecture": 1.12,
    "topic_packet": 1.05,
    "run": 0.9,
    "source": 0.82,
    "artifact": 0.78,
    "reference": 0.65,
    "branch": 0.35,
}
EDGE_PRIOR = {
    "EVIDENCE_FOR": 1.0,
    "SUPPORTS": 0.98,
    "CHALLENGES": 0.98,
    "CONTRADICTS": 0.98,
    "SUPERSEDES": 0.98,
    "DEPENDS_ON": 0.94,
    "DERIVED_FROM": 0.9,
    "PARENT_OF": 0.88,
    "IN_TOPIC": 0.84,
    "AFFECTS_BRANCH": 0.75,
    "SAME_EVIDENCE_FAMILY": 0.7,
    "HAS_ARTIFACT": 0.64,
    "BELONGS_TO_BRANCH": 0.5,
    "MENTIONS": 0.44,
    "RELATED": 0.4,
}


def tokens(text: str) -> list[str]:
    raw = re.findall(r"[\w.-]{2,}", text.lower(), flags=re.UNICODE)
    return [x for x in raw if x not in STOP and not x.isdigit()]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def ensure_graph(graph_dir: Path, refresh: bool = False) -> None:
    if refresh or not (graph_dir / "manifest.json").exists():
        import sys
        sys.path.insert(0, str(ROOT / "tools"))
        import claygraph_build
        claygraph_build.build(graph_dir)


def searchable(node: dict[str, Any]) -> str:
    return " ".join(str(node.get(k, "")) for k in ("identity", "label", "text", "path", "branch", "status", "evidence_class"))


def seed_scores(query: str, nodes: dict[str, dict[str, Any]]) -> dict[str, float]:
    q = tokens(query)
    qset = set(q)
    qlower = query.lower().strip()
    scores: dict[str, float] = {}
    if not qset and not qlower:
        return scores
    for nid, node in nodes.items():
        text = searchable(node).lower()
        ntoks = set(tokens(text[:12000]))
        overlap = qset & ntoks
        score = 0.0
        if qlower and qlower in text:
            score += 5.0
        if overlap:
            score += 3.5 * len(overlap) / max(1.0, math.sqrt(len(qset)))
            # Reward rare-looking identifiers and exact id/label hits.
            identity = str(node.get("identity", "")).lower()
            label = str(node.get("label", "")).lower()
            for t in overlap:
                if t in identity:
                    score += 1.1
                if t in label:
                    score += 0.5
        if score > 0:
            scores[nid] = score * TYPE_PRIOR.get(str(node.get("type")), 0.8)
    return scores


def activate(query: str, graph_dir: Path = DEFAULT_GRAPH, limit: int = 24, hops: int = 2, seed_limit: int = 14, refresh: bool = False, lexical_only: bool = False) -> dict[str, Any]:
    t0 = time.perf_counter()
    ensure_graph(graph_dir, refresh=refresh)
    t1 = time.perf_counter()
    node_list = load_jsonl(graph_dir / "nodes.jsonl")
    edge_list = load_jsonl(graph_dir / "edges.jsonl")
    nodes = {x["id"]: x for x in node_list}
    t2 = time.perf_counter()

    seeds = seed_scores(query, nodes)
    ranked_seeds = sorted(seeds.items(), key=lambda kv: (-kv[1], kv[0]))[:seed_limit]
    active = dict(ranked_seeds)
    parent: dict[str, dict[str, Any]] = {nid: {"mode": "lexical_seed", "from": None, "edge": None} for nid, _ in ranked_seeds}
    t3 = time.perf_counter()

    if not lexical_only and ranked_seeds and hops > 0:
        adjacency: dict[str, list[tuple[str, str, float, str]]] = defaultdict(list)
        for e in edge_list:
            s, t = e["source"], e["target"]
            et = str(e.get("type", "RELATED"))
            ew = float(e.get("weight", 1.0)) * EDGE_PRIOR.get(et, 0.45)
            adjacency[s].append((t, et, ew, "forward"))
            adjacency[t].append((s, et, ew * 0.78, "reverse"))

        frontier = dict(ranked_seeds)
        decay = 0.58
        for depth in range(1, hops + 1):
            nxt: dict[str, float] = {}
            for source, source_score in frontier.items():
                for target, etype, eweight, direction in adjacency.get(source, []):
                    if target not in nodes:
                        continue
                    propagated = source_score * decay * eweight * TYPE_PRIOR.get(str(nodes[target].get("type")), 0.8)
                    if propagated < 0.08:
                        continue
                    # Max-plus-small-addition keeps hubs from exploding while allowing convergence.
                    prior = active.get(target, 0.0)
                    candidate = max(prior, propagated) + (0.12 * min(prior, propagated) if prior and propagated else 0.0)
                    if candidate > prior + 1e-9:
                        active[target] = candidate
                        if target not in parent or propagated > prior:
                            parent[target] = {"mode": "graph_activation", "from": source, "edge": etype, "direction": direction, "depth": depth}
                    if propagated > nxt.get(target, 0.0):
                        nxt[target] = propagated
            frontier = dict(sorted(nxt.items(), key=lambda kv: (-kv[1], kv[0]))[: max(30, seed_limit * 4)])
            if not frontier:
                break
    t4 = time.perf_counter()

    ranked = sorted(active.items(), key=lambda kv: (-kv[1], kv[0]))[:limit]
    results = []
    total_chars = 0
    for nid, score in ranked:
        n = nodes[nid]
        excerpt = str(n.get("text") or n.get("label") or n.get("identity") or "")[:900]
        total_chars += len(excerpt)
        why = parent.get(nid, {"mode": "unknown"})
        if why.get("from"):
            src = nodes.get(why["from"], {})
            why = dict(why)
            why["from_identity"] = src.get("identity")
            why.pop("from", None)
        results.append({
            "score": round(score, 6),
            "id": nid,
            "type": n.get("type"),
            "identity": n.get("identity"),
            "label": n.get("label"),
            "path": n.get("path"),
            "branch": n.get("branch"),
            "status": n.get("status"),
            "evidence_class": n.get("evidence_class"),
            "excerpt": excerpt,
            "activation_reason": why,
        })

    manifest = json.loads((graph_dir / "manifest.json").read_text(encoding="utf-8"))
    t5 = time.perf_counter()
    return {
        "schema_version": "1.0",
        "query": query,
        "mode": "lexical_only" if lexical_only else "claygraph_activation",
        "graph_manifest": {
            "source_corpus_sha256": manifest.get("source_corpus_sha256"),
            "nodes": manifest.get("nodes"),
            "edges": manifest.get("edges"),
            "architecture_generation": manifest.get("architecture_generation"),
        },
        "results": results,
        "metrics": {
            "graph_prepare_ms": round((t1 - t0) * 1000, 3),
            "load_ms": round((t2 - t1) * 1000, 3),
            "seed_ms": round((t3 - t2) * 1000, 3),
            "propagation_ms": round((t4 - t3) * 1000, 3),
            "render_ms": round((t5 - t4) * 1000, 3),
            "total_ms": round((t5 - t0) * 1000, 3),
            "returned_chars": total_chars,
            "estimated_tokens_chars_div_4": int(math.ceil(total_chars / 4)),
            "seed_count": len(ranked_seeds),
            "active_nodes": len(active),
        },
        "scientific_boundary": "Retrieval/activation utility only. Scores are not evidence strength and latency is environment-specific.",
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--graph-dir", default=str(DEFAULT_GRAPH))
    ap.add_argument("--limit", type=int, default=24)
    ap.add_argument("--hops", type=int, default=2)
    ap.add_argument("--seed-limit", type=int, default=14)
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--lexical-only", action="store_true")
    args = ap.parse_args()
    out = activate(args.query, Path(args.graph_dir), max(1, min(args.limit, 100)), max(0, min(args.hops, 4)), max(1, min(args.seed_limit, 50)), args.refresh, args.lexical_only)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
