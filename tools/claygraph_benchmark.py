#!/usr/bin/env python3
"""Benchmark ClayGraph retrieval/activation against simpler RAE retrieval baselines.

The benchmark is an engineering/self-use proxy. It measures the environment in which it
runs and must not be interpreted as live-FRANK cognitive performance.
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import claygraph_query  # noqa: E402

DEFAULT_CASES = [
    {"id": "frank-freshness", "query": "FRANK workspace causal freshness hybrid heartbeat", "expect": ["freshness", "workspace"]},
    {"id": "cc-transition-closure", "query": "ClayCode transition closure trusted derived effect dependency footprint", "expect": ["transition", "closure"]},
    {"id": "goodman", "query": "Goodman anti echo FRANK ClayCode shared ancestry independent evidence", "expect": ["goodman", "ancestry"]},
    {"id": "hyperposition", "query": "hyperposition semantic coordination physical topology", "expect": ["topology", "hyperposition"]},
    {"id": "gwt-gate", "query": "GWT gate ignition reconstruction causal closure", "expect": ["ignition", "gwt"]},
    {"id": "provider-quota", "query": "Hugging Face Qwen3 4B monthly inference credits quota exhausted", "expect": ["quota", "hugging"]},
    {"id": "claygraph-memory", "query": "Synthetic Clay associative memory graph database migration persistent agent state", "expect": ["memory", "graph"]},
]


def p95(values: list[float]) -> float | None:
    if not values:
        return None
    s = sorted(values)
    return s[min(len(s) - 1, max(0, math.ceil(0.95 * len(s)) - 1))]


def hit(text: str, expected: list[str]) -> bool:
    low = text.lower()
    return all(x.lower() in low for x in expected)


def graph_mode(case: dict[str, Any], graph_dir: Path, lexical_only: bool, repeat: int, limit: int) -> dict[str, Any]:
    latencies = []
    last: dict[str, Any] | None = None
    for i in range(repeat):
        last = claygraph_query.activate(case["query"], graph_dir, limit=limit, hops=2, seed_limit=14, refresh=(i == 0 and not (graph_dir / "manifest.json").exists()), lexical_only=lexical_only)
        latencies.append(float(last["metrics"]["total_ms"]))
    assert last is not None
    combined = "\n".join((str(x.get("label") or "") + " " + str(x.get("excerpt") or "")) for x in last["results"])
    return {
        "mode": "graph_lexical" if lexical_only else "claygraph_activation",
        "hit": hit(combined, case["expect"]),
        "latency_ms": {"median": round(statistics.median(latencies), 3), "p95": round(float(p95(latencies) or 0), 3), "runs": latencies},
        "returned_chars": last["metrics"]["returned_chars"],
        "estimated_tokens_chars_div_4": last["metrics"]["estimated_tokens_chars_div_4"],
        "top_identities": [x.get("identity") for x in last["results"][:8]],
        "graph_active_nodes": last["metrics"]["active_nodes"],
    }


def ensure_sqlite() -> Path:
    default = ROOT / "research_sources" / "sources.db"
    if default.exists():
        return default
    tmp = Path(tempfile.gettempdir()) / "rae-claygraph-benchmark-sources.db"
    subprocess.run([sys.executable, str(ROOT / "tools" / "build_source_db.py"), "--db", str(tmp)], check=True, stdout=subprocess.DEVNULL)
    return tmp


def sqlite_query(db: Path, query: str, limit: int) -> tuple[str, int]:
    import sqlite3
    con = sqlite3.connect(db)
    con.row_factory = sqlite3.Row
    toks = [t for t in claygraph_query.tokens(query) if len(t) >= 3][:12]
    fts = " OR ".join('"' + t.replace('"', '""') + '"' for t in toks) or '"' + query.replace('"', '""') + '"'
    parts: list[str] = []
    try:
        rows = con.execute("SELECT c.claim_id,c.proposition FROM claim_fts f JOIN claims c USING(claim_id) WHERE claim_fts MATCH ? LIMIT ?", (fts, limit)).fetchall()
        parts.extend(f"{r['claim_id']} {r['proposition']}" for r in rows)
    except sqlite3.OperationalError:
        pass
    try:
        rows = con.execute("SELECT s.path,substr(f.text,1,900) excerpt FROM chunk_fts f JOIN sources s USING(source_id) WHERE chunk_fts MATCH ? LIMIT ?", (fts, limit)).fetchall()
        parts.extend(f"{r['path']} {r['excerpt']}" for r in rows)
    except sqlite3.OperationalError:
        pass
    con.close()
    text = "\n".join(parts)
    return text, len(text)


def sqlite_mode(case: dict[str, Any], db: Path, repeat: int, limit: int) -> dict[str, Any]:
    latencies = []
    text = ""
    chars = 0
    for _ in range(repeat):
        t0 = time.perf_counter()
        text, chars = sqlite_query(db, case["query"], limit)
        latencies.append((time.perf_counter() - t0) * 1000)
    return {
        "mode": "sqlite_fts",
        "hit": hit(text, case["expect"]),
        "latency_ms": {"median": round(statistics.median(latencies), 3), "p95": round(float(p95(latencies) or 0), 3), "runs": [round(x, 3) for x in latencies]},
        "returned_chars": chars,
        "estimated_tokens_chars_div_4": int(math.ceil(chars / 4)),
    }


def benchmark(graph_dir: Path, repeat: int = 3, limit: int = 16, cases: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    cases = cases or DEFAULT_CASES
    claygraph_query.ensure_graph(graph_dir, refresh=True)
    db = ensure_sqlite()
    rows = []
    for case in cases:
        modes = [
            graph_mode(case, graph_dir, False, repeat, limit),
            graph_mode(case, graph_dir, True, repeat, limit),
            sqlite_mode(case, db, repeat, limit),
        ]
        rows.append({"id": case["id"], "query": case["query"], "expect": case["expect"], "modes": modes})

    summary: dict[str, Any] = {}
    for mode in ["claygraph_activation", "graph_lexical", "sqlite_fts"]:
        selected = [m for row in rows for m in row["modes"] if m["mode"] == mode]
        summary[mode] = {
            "hit_rate": round(sum(1 for x in selected if x["hit"]) / max(1, len(selected)), 4),
            "median_case_latency_ms": round(statistics.median(x["latency_ms"]["median"] for x in selected), 3),
            "median_returned_chars": int(statistics.median(x["returned_chars"] for x in selected)),
            "median_estimated_tokens": int(statistics.median(x["estimated_tokens_chars_div_4"] for x in selected)),
        }
    manifest = json.loads((graph_dir / "manifest.json").read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0",
        "benchmark_class": "RAE_SELF_USE_ENGINEERING_PROXY",
        "graph": {"source_corpus_sha256": manifest.get("source_corpus_sha256"), "nodes": manifest.get("nodes"), "edges": manifest.get("edges"), "architecture_generation": manifest.get("architecture_generation")},
        "cases": rows,
        "summary": summary,
        "limitations": [
            "Default gold checks are keyword-based and intentionally modest; they are not a cognitive-quality ground truth.",
            "Graph structural tests can favor graph retrieval, so future generations must add independently grounded and adversarial gold sets.",
            "Runner/sandbox latency does not establish live FRANK latency.",
            "Character/4 token estimates are rough context-size proxies, not provider tokenizer measurements."
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph-dir", default=str(claygraph_query.DEFAULT_GRAPH))
    ap.add_argument("--repeat", type=int, default=3)
    ap.add_argument("--limit", type=int, default=16)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = benchmark(Path(args.graph_dir), max(1, min(args.repeat, 20)), max(4, min(args.limit, 50)))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
