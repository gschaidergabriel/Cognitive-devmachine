#!/usr/bin/env python3
"""Adversarial benchmark for coherent Clay U11 semantic possibility access.

Purpose:
- challenge U11 with a stronger conventional SQLite competitor than flat FTS/BM25;
- keep the comparison inside one deterministic synthetic assistant-retrieval workload;
- require coherent-generation semantics and an explicit stale-epoch fail-closed lesion.

This is an engineering proxy only. It must never be reported as universal database
superiority or as live-FRANK cognitive performance.
"""
from __future__ import annotations

import json
import os
import sqlite3
import tempfile
from pathlib import Path

from benchmark_semantic_retrieval_v10 import (
    TOPICS,
    assess,
    authority,
    build_db,
    fts_meta,
    hybrid_v1,
    norm,
)
from semantic_retrieval_runtime_v11 import SemanticRetrievalFabricV11

HERE = Path(__file__).resolve().parent
U11_SCHEMA = (HERE / "RAE_UNIFIEDDB_V11_COHERENT_ACCESS_GENERATIONS.sql").read_text(
    encoding="utf-8"
)


def _dedup(xs: list[str], k: int) -> list[str]:
    out: list[str] = []
    for x in xs:
        if x not in out:
            out.append(x)
        if len(out) >= k:
            break
    return out


def sqlite_online_semantic(con: sqlite3.Connection, query: str, k: int = 5) -> list[str]:
    """Strong online SQL baseline without semantic-access materialization.

    It resolves an exact alias/topic when possible. Otherwise it derives a topic online
    from ordinary FTS5 results, CURRENT metadata and epistemic authority, then follows
    ordinary relational edges. No per-seed semantic access projection is consumed.
    """
    key = norm(query)
    topic_row = con.execute("SELECT topic FROM aliases WHERE alias=?", (key,)).fetchone()
    topic = str(topic_row[0]) if topic_row else (key if key in TOPICS else None)

    if topic is None:
        toks = key.split()
        if toks:
            match = " OR ".join(toks)
            rows = con.execute(
                """SELECT r.topic,bm25(fts) AS bm,r.epistemic_class,r.updated_seq
                   FROM fts JOIN records r ON r.record_id=fts.record_id
                   WHERE fts MATCH ? AND r.status='CURRENT' AND r.topic!='noise'
                   ORDER BY bm ASC LIMIT 64""",
                (match,),
            ).fetchall()
            votes: dict[str, float] = {}
            for t, bm, ep, updated in rows:
                score = (
                    authority(ep) * 1000.0
                    + max(0.0, -float(bm))
                    + float(updated) * 0.001
                )
                votes[str(t)] = max(votes.get(str(t), float("-inf")), score)
            if votes:
                topic = min(votes, key=lambda t: (-votes[t], t))

    if topic is None:
        return fts_meta(con, query, k)

    canonical = con.execute(
        """SELECT record_id FROM records
           WHERE topic=? AND status='CURRENT'
           ORDER BY CASE epistemic_class
                      WHEN 'PROJECT_OWNER_FIXED' THEN 3
                      WHEN 'VALIDATED_RESEARCH' THEN 1
                      ELSE 0 END DESC,
                    updated_seq DESC,record_id ASC
           LIMIT 1""",
        (topic,),
    ).fetchone()
    related = [
        str(r[0])
        for r in con.execute(
            """SELECT target_record_id FROM edges
               WHERE source_topic=?
               ORDER BY CASE relation WHEN 'CANONICAL_OF' THEN 0 ELSE 1 END,
                        weight DESC,target_record_id ASC""",
            (topic,),
        ).fetchall()
    ]
    lexical = fts_meta(con, query, max(k * 2, 10))
    prefix = [str(canonical[0])] if canonical else []
    return _dedup(prefix + related + lexical, k)


def install_coherent_generation(con: sqlite3.Connection) -> None:
    con.executescript(U11_SCHEMA)
    seed_count = con.execute(
        "SELECT count(*) FROM semantic_query_seeds WHERE status='CURRENT'"
    ).fetchone()[0]
    path_count = con.execute(
        "SELECT count(*) FROM semantic_access_projection WHERE status='CURRENT'"
    ).fetchone()[0]
    con.execute(
        "INSERT INTO semantic_access_generations VALUES"
        "('adv-g1',1,1,'adv-v11','adv-hash',?,?, '{}','CURRENT','t','t','t')",
        (seed_count, path_count),
    )
    con.execute(
        """INSERT INTO semantic_access_projection_v11
           SELECT 'adv-g1',seed_id,target_record_id,target_logical_id,path_rank,hop_count,
                  path_weight,authority_rank,path_clay
           FROM semantic_access_projection WHERE status='CURRENT'"""
    )
    con.execute(
        "INSERT INTO semantic_access_head VALUES"
        "('CURRENT','adv-g1',1,1,'adv-hash','t')"
    )
    con.commit()


def main() -> None:
    with tempfile.TemporaryDirectory() as td:
        db = os.path.join(td, "bench.sqlite")
        con, target, queries, rows, storage = build_db(db)
        install_coherent_generation(con)
        fabric = SemanticRetrievalFabricV11(con)

        def u11(query: str, k: int) -> list[str]:
            fast = fabric.query(query, source_epoch=1, graph_epoch=1, limit=k)
            return list(fast.refs) if fast.refs else fts_meta(con, query, k)

        results = [
            assess(
                "sqlite_fts5_current_authority",
                lambda q, k: fts_meta(con, q, k),
                queries,
                target,
                repeats=100,
            ),
            assess(
                "udb_claygraph_v1_query_time",
                lambda q, k: hybrid_v1(con, q, k),
                queries,
                target,
                repeats=100,
            ),
            assess(
                "sqlite_online_semantic_adversary",
                lambda q, k: sqlite_online_semantic(con, q, k),
                queries,
                target,
                repeats=100,
            ),
            assess(
                "udb_claygraph_v11_coherent_generation",
                u11,
                queries,
                target,
                repeats=100,
            ),
        ]

        stale_fastpath_accepts = 0
        for q, _ in queries:
            stale = fabric.query(q, source_epoch=2, graph_epoch=2, limit=5)
            stale_fastpath_accepts += int(stale.mode == "COHERENT_SEMANTIC_FASTPATH")

        by_name = {r["name"]: r for r in results}
        adv = by_name["sqlite_online_semantic_adversary"]
        cand = by_name["udb_claygraph_v11_coherent_generation"]
        speedup_p50 = (
            adv["latency_ns"]["p50"] / cand["latency_ns"]["p50"]
            if cand["latency_ns"]["p50"]
            else None
        )
        quality_delta = {
            "hit_at_1": cand["hit_at_1"] - adv["hit_at_1"],
            "recall_at_5": cand["recall_at_5"] - adv["recall_at_5"],
            "mrr": cand["mrr"] - adv["mrr"],
        }

        out = {
            "schema": "clay.semantic_retrieval_adversarial_benchmark.v2",
            "scope": (
                "synthetic deterministic assistant semantic retrieval; engineering proxy; "
                "not universal database superiority"
            ),
            "dataset": {
                "rows": rows,
                "queries": len(queries),
                "topics": len(TOPICS),
                "noise_rows": 4000,
            },
            "projection": storage,
            "results": results,
            "candidate_vs_online_sql": {
                "quality_delta": quality_delta,
                "p50_speedup_ratio": speedup_p50,
            },
            "stale_epoch_lesion": {
                "attempts": len(queries),
                "semantic_fastpath_accepts": stale_fastpath_accepts,
                "accept_rate": stale_fastpath_accepts / max(1, len(queries)),
                "required": 0.0,
            },
            "limitations": [
                "Synthetic source data and query families are model-authored and can contain benchmark-design bias.",
                "The online SQL adversary is strong for this schema but does not represent every database, vector engine, graph database, or learned retriever.",
                "The benchmark measures retrieval of a canonical target, not downstream answer quality.",
                "Materialization build/update cost must be amortized and separately measured under realistic write rates.",
                "Typed/normalized seed coverage can advantage U11; held-out paraphrases and repo-native counterevidence remain mandatory.",
            ],
        }
        con.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        con.close()
        print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
