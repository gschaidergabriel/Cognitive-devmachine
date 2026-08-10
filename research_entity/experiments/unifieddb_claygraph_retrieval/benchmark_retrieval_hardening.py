from __future__ import annotations

import json
import os
import platform
import statistics
import tempfile
import time
from pathlib import Path

from unifieddb_claygraph_retrieval_candidate import (
    MAX_LIVE_FANOUT,
    ProjectionBasis,
    UnifiedDBClayGraphRetrievalCandidate,
)


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, max(0, int((len(xs) - 1) * p)))]


def row(key: str, lid: str, text: str):
    return {
        "domain": "semantic",
        "key": key,
        "value": {"logical_id": lid, "record_kind": "stress_fact", "evidence_class": "VERIFIED", "search_text": text},
        "epistemic": "KNOWN",
        "status": "CURRENT",
        "domain_epoch": 7,
        "semantic_hash": "h-" + key,
    }


def build(branching: int):
    rows = [row("root", "root", "root component relation chain")]
    edges = []
    for i in range(branching):
        a = f"a_{i}"
        rows.append(row(a, a, f"{a} service capability"))
        edges.append({"source_logical_id": "root", "target_logical_id": a, "relation_type": "REQUIRES", "weight": 1.0 - i * 1e-7, "confidence": 0.99})
        for j in range(branching):
            b = f"b_{i}_{j}"
            rows.append(row(b, b, f"{b} resource downstream"))
            edges.append({"source_logical_id": a, "target_logical_id": b, "relation_type": "DEPENDS_ON", "weight": 1.0 - j * 1e-7, "confidence": 0.99})
    rows.append(row("counter", "counter", "counter contradiction negative evidence"))
    edges.append({"source_logical_id": "root", "target_logical_id": "counter", "relation_type": "CONTRADICTS", "weight": 0.001, "confidence": 0.2})
    basis = ProjectionBasis(7, "stress-state-hash", 4, True, True)
    x = UnifiedDBClayGraphRetrievalCandidate()
    stats = x.rebuild(state_rows=rows, graph_edges=edges, basis=basis)
    return x, basis, stats


LEGACY_OUTPUT_LIMIT_SQL = """
WITH RECURSIVE walk(node,depth,path_score,path) AS (
  SELECT ?1,0,1.0,'|'||?1||'|'
  UNION ALL
  SELECT e.target_logical_id,w.depth+1,
         w.path_score*e.weight*COALESCE(e.confidence,0.5)*0.82,
         w.path||e.target_logical_id||'|'
  FROM walk w JOIN claygraph_neighbor_cache e ON e.source_logical_id=w.node
  WHERE w.depth < ?2 AND e.graph_epoch=?3
    AND instr(w.path,'|'||e.target_logical_id||'|')=0
)
SELECT d.record_id,d.logical_id,d.record_kind,d.epistemic_class,
       MIN(w.depth) AS depth,MAX(w.path_score) AS path_score
FROM walk w JOIN udb_retrieval_documents d ON d.logical_id=w.node
WHERE w.depth>0 AND d.status='CURRENT'
GROUP BY d.record_id,d.logical_id,d.record_kind,d.epistemic_class
ORDER BY depth ASC,path_score DESC LIMIT ?4
"""

CAPPED_BUT_FULLSCAN_SQL = """
WITH RECURSIVE walk(node,depth,path_score,path) AS (
  SELECT ?1,0,1.0,'|'||?1||'|'
  UNION ALL
  SELECT e.target_logical_id,w.depth+1,
         w.path_score*e.weight*COALESCE(e.confidence,0.5)*0.82,
         w.path||e.target_logical_id||'|'
  FROM walk w JOIN claygraph_neighbor_cache e ON e.source_logical_id=w.node
  WHERE w.depth < ?2 AND e.graph_epoch=?3 AND e.source_rank<=?5
    AND instr(w.path,'|'||e.target_logical_id||'|')=0
)
SELECT d.record_id,d.logical_id,d.record_kind,d.epistemic_class,
       MIN(w.depth) AS depth,MAX(w.path_score) AS path_score
FROM walk w JOIN udb_retrieval_documents d ON d.logical_id=w.node
WHERE w.depth>0 AND d.status='CURRENT'
GROUP BY d.record_id,d.logical_id,d.record_kind,d.epistemic_class
ORDER BY depth ASC,path_score DESC LIMIT ?4
"""


def timed(fn, reps=9):
    samples = []
    fn()
    for _ in range(reps):
        t0 = time.perf_counter_ns()
        fn()
        samples.append((time.perf_counter_ns() - t0) / 1_000_000.0)
    return {"n": len(samples), "p50_ms": statistics.median(samples), "p95_ms": q(samples, 0.95), "min_ms": min(samples), "max_ms": max(samples)}


def fanout_case(branching: int):
    x, basis, stats = build(branching)
    args_legacy = ("root", 2, basis.graph_epoch, 48)
    args_capped = ("root", 2, basis.graph_epoch, 48, MAX_LIVE_FANOUT)
    legacy = timed(lambda: x.conn.execute(LEGACY_OUTPUT_LIMIT_SQL, args_legacy).fetchall())
    capped_fullscan = timed(lambda: x.conn.execute(CAPPED_BUT_FULLSCAN_SQL, args_capped).fetchall())
    hardened = timed(lambda: x._walk("root", 2, 48))
    legacy_plan = [r[-1] for r in x.conn.execute("EXPLAIN QUERY PLAN " + LEGACY_OUTPUT_LIMIT_SQL, args_legacy)]
    capped_plan = [r[-1] for r in x.conn.execute("EXPLAIN QUERY PLAN " + CAPPED_BUT_FULLSCAN_SQL, args_capped)]
    counter_rank = x.conn.execute("SELECT source_rank FROM claygraph_neighbor_cache WHERE source_logical_id='root' AND target_logical_id='counter'").fetchone()[0]
    x.close()
    return {
        "branching": branching,
        "documents": 1 + branching + branching * branching + 1,
        "history_edges_in_projection": branching + branching * branching + 1,
        "projection_stats": stats,
        "counter_rank": counter_rank,
        "legacy_output_limit": legacy,
        "capped_but_fullscan": capped_fullscan,
        "hardened": hardened,
        "speedup_hardened_vs_legacy_p50": legacy["p50_ms"] / hardened["p50_ms"],
        "speedup_hardened_vs_capped_fullscan_p50": capped_fullscan["p50_ms"] / hardened["p50_ms"],
        "legacy_plan_has_document_scan": any("SCAN d" in p for p in legacy_plan),
        "capped_plan_has_document_scan": any("SCAN d" in p for p in capped_plan),
    }


def reopen_and_unicode():
    fd, path = tempfile.mkstemp(prefix="clay-retrieval-hardening-", suffix=".db")
    os.close(fd)
    try:
        basis = ProjectionBasis(7, "unicode-state-hash", 4, True, True)
        x = UnifiedDBClayGraphRetrievalCandidate(path)
        x.rebuild(state_rows=[row("de", "prüfung_a", "Größenprüfung Überprüfung zuverlässig österreichische Straße")], graph_edges=[], basis=basis)
        before = x.query(query_id="de-before", text="Welche Größenprüfung wurde verifiziert?", basis=basis)
        fts = x._fts_query("Größenprüfung Überprüfung Straße")
        x.close()
        y = UnifiedDBClayGraphRetrievalCandidate(path)
        after = y.query(query_id="de-after", text="Welche Größenprüfung wurde verifiziert?", basis=basis)
        restored = y.basis == basis
        y.close()
        return {"fts_query": fts, "before_top1": before.results[0].record_id if before.results else None, "after_top1": after.results[0].record_id if after.results else None, "basis_restored": restored}
    finally:
        Path(path).unlink(missing_ok=True)


def main():
    started = time.perf_counter()
    cases = [fanout_case(n) for n in [25, 50, 100, 200]]
    unicode_restart = reopen_and_unicode()
    result = {
        "schema_version": "1.0",
        "benchmark": "UNIFIEDDB_CLAYGRAPH_RETRIEVAL_HARDENING_V1",
        "environment": {"platform": platform.platform(), "python": platform.python_version(), "sqlite": __import__("sqlite3").sqlite_version},
        "fanout_cap": MAX_LIVE_FANOUT,
        "fanout_cases": cases,
        "unicode_restart": unicode_restart,
        "wall_seconds": time.perf_counter() - started,
    }
    result["pass"] = bool(
        unicode_restart["basis_restored"]
        and unicode_restart["before_top1"] == "h-de"
        and unicode_restart["after_top1"] == "h-de"
        and all(c["counter_rank"] <= MAX_LIVE_FANOUT for c in cases)
        and cases[-1]["speedup_hardened_vs_legacy_p50"] > 5.0
        and cases[-1]["hardened"]["p50_ms"] < cases[-1]["legacy_output_limit"]["p50_ms"]
    )
    print(json.dumps(result, indent=2, sort_keys=True, ensure_ascii=False))
    raise SystemExit(0 if result["pass"] else 2)


if __name__ == "__main__":
    main()
