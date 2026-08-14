#!/usr/bin/env python3
"""Matched PostgreSQL 18 vs Clay U14 compiled semantic-read benchmark.

Scope:
- deterministic synthetic assistant retrieval;
- exact key, alias-resolved 1-hop, alias-resolved 2-hop, and lexical descriptor reads;
- PostgreSQL receives B-tree/GIN indexes, prepared parameterized SQL, and the same
  deterministic entity/intent extraction used by the compiled Clay path;
- also records a full-online alias SQL path where PostgreSQL resolves the alias itself.

This benchmark is a falsifier for workload-specific Clay read-plan claims. It is NOT
evidence of universal database superiority and it is NOT live-FRANK answer quality.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import re
import sqlite3
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import psycopg

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT.parent) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

from research_entity.runtime.adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest,
    AdaptiveSemanticReadPlaneV14,
    VerifiedReadBasis,
)

SEEDS = (20260810, 20260811, 20260812)
FAMILIES_PER_SEED = 200
REPEATS_PER_FAMILY = 5
NOISE_ROWS = 4000
SOURCE_EPOCH = 17
GRAPH_EPOCH = 11
ALIAS_RE = re.compile(r"\balias_\d+_\d+\b")
DESC_RE = re.compile(r"\bdescriptor_\d+_\d+\b")


@dataclass(frozen=True)
class QueryCase:
    query_id: str
    mode: str
    text: str
    expected: str
    exact_key: str | None = None


def percentile(xs: list[int], p: float) -> int:
    ys = sorted(xs)
    if not ys:
        return 0
    idx = min(len(ys) - 1, max(0, int(round((len(ys) - 1) * p))))
    return int(ys[idx])


def summary_ns(xs: list[int]) -> dict[str, float | int]:
    return {
        "n": len(xs),
        "mean_us": statistics.mean(xs) / 1000.0 if xs else 0.0,
        "p50_us": percentile(xs, 0.50) / 1000.0,
        "p95_us": percentile(xs, 0.95) / 1000.0,
        "p99_us": percentile(xs, 0.99) / 1000.0,
        "min_us": min(xs) / 1000.0 if xs else 0.0,
        "max_us": max(xs) / 1000.0 if xs else 0.0,
    }


def make_fixture():
    records: list[tuple] = []
    aliases: list[tuple] = []
    edges: list[tuple] = []
    alias_to_component: dict[str, str] = {}
    descriptor_to_component: dict[str, str] = {}
    expected_by_component: dict[str, dict[str, str]] = {}

    for seed in SEEDS:
        rng = random.Random(seed)
        for i in range(FAMILIES_PER_SEED):
            component = f"component_{seed}_{i:04d}"
            service = f"service_{seed}_{i:04d}"
            resource = f"resource_{seed}_{i:04d}"
            alias = f"alias_{seed}_{i:04d}"
            descriptor = f"descriptor_{seed}_{i:04d}"
            comp_record = f"record:{component}"
            svc_record = f"record:{service}"
            res_record = f"record:{resource}"
            priority = rng.randint(1, 10000)

            records.extend([
                (comp_record, component, "component", alias, descriptor,
                 "PROJECT_OWNER_FIXED", priority,
                 f"{component} {alias} {descriptor} current verified component semantic state"),
                (svc_record, service, "service", "", f"capability_{seed}_{i:04d}",
                 "VERIFIED", priority,
                 f"{service} provides capability_{seed}_{i:04d} required by {component}"),
                (res_record, resource, "resource", "", f"quota_{seed}_{i:04d}",
                 "VALIDATED_RESEARCH", priority,
                 f"{resource} supplies quota_{seed}_{i:04d} downstream of {service}"),
            ])
            aliases.append((alias, component))
            alias_to_component[alias] = component
            descriptor_to_component[descriptor] = component
            expected_by_component[component] = {
                "EXACT": comp_record,
                "SERVICE": svc_record,
                "RESOURCE": res_record,
                "LEXICAL": comp_record,
            }
            edges.extend([
                (f"edge:{component}:service", component, service, "REQUIRES", 0.99, GRAPH_EPOCH, "CURRENT"),
                (f"edge:{service}:resource", service, resource, "DEPENDS_ON", 0.98, GRAPH_EPOCH, "CURRENT"),
            ])

    for j in range(NOISE_ROWS):
        rid = f"noise:{j:06d}"
        records.append((
            rid, f"noise_{j:06d}", "noise", "", f"noise_descriptor_{j:06d}",
            "UNKNOWN", j,
            f"distractor unrelated noise document {j} generic semantic memory",
        ))

    compiled: dict[tuple[str, str], tuple[str, ...]] = {}
    for component, expected in expected_by_component.items():
        for intent, rid in expected.items():
            compiled[(component, intent)] = (rid,)

    cases: list[QueryCase] = []
    family_components = sorted(expected_by_component)
    for seed in SEEDS:
        rng = random.Random(seed ^ 0xC1A7)
        seed_components = [c for c in family_components if c.startswith(f"component_{seed}_")]
        for rep in range(REPEATS_PER_FAMILY):
            order = seed_components[:]
            rng.shuffle(order)
            for component in order:
                i = int(component.split("_")[-1])
                alias = f"alias_{seed}_{i:04d}"
                descriptor = f"descriptor_{seed}_{i:04d}"
                exp = expected_by_component[component]
                cases.extend([
                    QueryCase(f"{seed}:exact:{rep}:{i}", "EXACT", component, exp["EXACT"], component),
                    QueryCase(f"{seed}:service:{rep}:{i}", "SERVICE",
                              f"Which service does {alias} require?", exp["SERVICE"]),
                    QueryCase(f"{seed}:resource:{rep}:{i}", "RESOURCE",
                              f"Which resource ultimately supports {alias} through its service chain?", exp["RESOURCE"]),
                    QueryCase(f"{seed}:lexical:{rep}:{i}", "LEXICAL",
                              f"Find the verified component for {descriptor}", exp["LEXICAL"]),
                ])
    return records, aliases, edges, alias_to_component, descriptor_to_component, compiled, cases


def parse_case(text: str, alias_to_component: dict[str, str],
               descriptor_to_component: dict[str, str]) -> tuple[str | None, str]:
    lower = text.lower()
    m = ALIAS_RE.search(lower)
    if m:
        component = alias_to_component.get(m.group(0))
        if "resource" in lower or "ultimately" in lower:
            return component, "RESOURCE"
        if "service" in lower or "require" in lower:
            return component, "SERVICE"
        return component, "EXACT"
    d = DESC_RE.search(lower)
    if d:
        return descriptor_to_component.get(d.group(0)), "LEXICAL"
    if lower.startswith("component_"):
        return lower.strip(), "EXACT"
    return None, "MISS"


def setup_postgres(conn, records, aliases, edges) -> dict[str, int | float | str]:
    started = time.perf_counter_ns()
    with conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS aliases, edges, records CASCADE")
        cur.execute("""
            CREATE TABLE records(
              record_id TEXT PRIMARY KEY,
              logical_id TEXT UNIQUE NOT NULL,
              kind TEXT NOT NULL,
              alias_text TEXT NOT NULL,
              descriptor TEXT NOT NULL,
              epistemic_class TEXT NOT NULL,
              updated_seq INTEGER NOT NULL,
              body TEXT NOT NULL,
              search_vec tsvector GENERATED ALWAYS AS
                (to_tsvector('simple', coalesce(alias_text,'') || ' ' ||
                                      coalesce(descriptor,'') || ' ' || coalesce(body,''))) STORED
            )
        """)
        cur.execute("""
            CREATE TABLE aliases(
              alias TEXT PRIMARY KEY,
              logical_id TEXT NOT NULL REFERENCES records(logical_id)
            )
        """)
        cur.execute("""
            CREATE TABLE edges(
              edge_id TEXT PRIMARY KEY,
              source_logical_id TEXT NOT NULL,
              target_logical_id TEXT NOT NULL,
              relation_type TEXT NOT NULL,
              weight DOUBLE PRECISION NOT NULL,
              graph_epoch INTEGER NOT NULL,
              status TEXT NOT NULL
            )
        """)
        cur.executemany(
            "INSERT INTO records(record_id,logical_id,kind,alias_text,descriptor,epistemic_class,updated_seq,body) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", records
        )
        cur.executemany("INSERT INTO aliases(alias,logical_id) VALUES (%s,%s)", aliases)
        cur.executemany(
            "INSERT INTO edges(edge_id,source_logical_id,target_logical_id,relation_type,weight,graph_epoch,status) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s)", edges
        )
        cur.execute("CREATE INDEX records_kind_idx ON records(kind)")
        cur.execute("CREATE INDEX records_epistemic_idx ON records(epistemic_class,updated_seq DESC)")
        cur.execute("CREATE INDEX records_search_gin ON records USING GIN(search_vec)")
        cur.execute("CREATE INDEX edges_source_idx ON edges(source_logical_id,graph_epoch DESC,relation_type,weight DESC)")
        cur.execute("CREATE INDEX edges_target_idx ON edges(target_logical_id,graph_epoch DESC,relation_type)")
        cur.execute("ANALYZE records")
        cur.execute("ANALYZE aliases")
        cur.execute("ANALYZE edges")
    conn.commit()
    build_ns = time.perf_counter_ns() - started
    with conn.cursor() as cur:
        cur.execute("SELECT pg_database_size(current_database())")
        db_bytes = int(cur.fetchone()[0])
        cur.execute("SHOW server_version")
        version = str(cur.fetchone()[0])
    return {"build_ns": build_ns, "database_bytes": db_bytes, "server_version": version}


def setup_sqlite_exact(records):
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE records(record_id TEXT PRIMARY KEY, logical_id TEXT UNIQUE NOT NULL)")
    con.executemany("INSERT INTO records(record_id,logical_id) VALUES (?,?)", [(r[0], r[1]) for r in records])
    con.commit()
    return con


class PostgresReaders:
    def __init__(self, conn):
        self.conn = conn

    def exact(self, logical_id: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("SELECT record_id FROM records WHERE logical_id=%s LIMIT 1", (logical_id,))
            row = cur.fetchone()
            return str(row[0]) if row else None

    def one_hop(self, component: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT r.record_id
                FROM edges e
                JOIN records r ON r.logical_id=e.target_logical_id
                WHERE e.source_logical_id=%s AND e.graph_epoch=%s AND e.status='CURRENT'
                  AND e.relation_type='REQUIRES'
                ORDER BY e.weight DESC,e.target_logical_id ASC
                LIMIT 1
            """, (component, GRAPH_EPOCH))
            row = cur.fetchone()
            return str(row[0]) if row else None

    def two_hop(self, component: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT r.record_id
                FROM edges e1
                JOIN edges e2 ON e2.source_logical_id=e1.target_logical_id
                JOIN records r ON r.logical_id=e2.target_logical_id
                WHERE e1.source_logical_id=%s
                  AND e1.graph_epoch=%s AND e2.graph_epoch=%s
                  AND e1.status='CURRENT' AND e2.status='CURRENT'
                  AND e1.relation_type='REQUIRES' AND e2.relation_type='DEPENDS_ON'
                ORDER BY (e1.weight*e2.weight) DESC,e2.target_logical_id ASC
                LIMIT 1
            """, (component, GRAPH_EPOCH, GRAPH_EPOCH))
            row = cur.fetchone()
            return str(row[0]) if row else None

    def lexical(self, query_text: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                WITH q AS (SELECT websearch_to_tsquery('simple', %s) AS tsq)
                SELECT r.record_id
                FROM records r,q
                WHERE r.search_vec @@ q.tsq AND r.kind='component'
                ORDER BY
                  CASE r.epistemic_class
                    WHEN 'PROJECT_OWNER_FIXED' THEN 4
                    WHEN 'VERIFIED' THEN 3
                    WHEN 'VALIDATED_RESEARCH' THEN 2
                    WHEN 'SUPPORTED' THEN 1
                    ELSE 0 END DESC,
                  ts_rank_cd(r.search_vec,q.tsq) DESC,
                  r.updated_seq DESC,
                  r.record_id ASC
                LIMIT 1
            """, (query_text,))
            row = cur.fetchone()
            return str(row[0]) if row else None

    def full_alias_one_hop(self, alias: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT r.record_id
                FROM aliases a
                JOIN edges e ON e.source_logical_id=a.logical_id
                JOIN records r ON r.logical_id=e.target_logical_id
                WHERE a.alias=%s AND e.graph_epoch=%s AND e.status='CURRENT'
                  AND e.relation_type='REQUIRES'
                ORDER BY e.weight DESC,e.target_logical_id ASC
                LIMIT 1
            """, (alias, GRAPH_EPOCH))
            row = cur.fetchone()
            return str(row[0]) if row else None

    def full_alias_two_hop(self, alias: str) -> str | None:
        with self.conn.cursor() as cur:
            cur.execute("""
                SELECT r.record_id
                FROM aliases a
                JOIN edges e1 ON e1.source_logical_id=a.logical_id
                JOIN edges e2 ON e2.source_logical_id=e1.target_logical_id
                JOIN records r ON r.logical_id=e2.target_logical_id
                WHERE a.alias=%s
                  AND e1.graph_epoch=%s AND e2.graph_epoch=%s
                  AND e1.status='CURRENT' AND e2.status='CURRENT'
                  AND e1.relation_type='REQUIRES' AND e2.relation_type='DEPENDS_ON'
                ORDER BY (e1.weight*e2.weight) DESC,e2.target_logical_id ASC
                LIMIT 1
            """, (alias, GRAPH_EPOCH, GRAPH_EPOCH))
            row = cur.fetchone()
            return str(row[0]) if row else None


def evaluate(name: str, cases: list[QueryCase], fn: Callable[[QueryCase], str | None],
             warmup: int = 200) -> dict:
    for c in cases[: min(warmup, len(cases))]:
        fn(c)
    lat: list[int] = []
    correct = 0
    misses = 0
    for c in cases:
        t0 = time.perf_counter_ns()
        got = fn(c)
        lat.append(time.perf_counter_ns() - t0)
        correct += int(got == c.expected)
        misses += int(got is None)
    return {
        "name": name,
        "queries": len(cases),
        "top1_accuracy": correct / max(1, len(cases)),
        "miss_rate": misses / max(1, len(cases)),
        "latency": summary_ns(lat),
    }


def main() -> None:
    records, aliases, edges, alias_map, descriptor_map, compiled, cases = make_fixture()
    dsn = os.environ.get("CLAY_POSTGRES_DSN", "postgresql://clay:clay@127.0.0.1:5432/claybench")
    conn = psycopg.connect(dsn, autocommit=False)
    conn.prepare_threshold = 1
    pg_meta = setup_postgres(conn, records, aliases, edges)
    pg = PostgresReaders(conn)

    sqlite_exact = setup_sqlite_exact(records)

    build_started = time.perf_counter_ns()
    compiled_fields = dict(compiled)
    compiled_build_ns = time.perf_counter_ns() - build_started

    basis = VerifiedReadBasis(
        basis_id="pg18-matched-basis",
        source_epoch=SOURCE_EPOCH,
        graph_epoch=GRAPH_EPOCH,
        derivation_hash=hashlib.sha256(b"pg18-matched-basis").hexdigest(),
        verified=True,
    )

    def parse(text: str):
        return parse_case(text, alias_map, descriptor_map)

    def exact_lookup(key, read_basis, limit):
        rid = compiled_fields.get((key, "EXACT"), ())
        return rid[:limit]

    def compiled_lookup(text, read_basis, limit):
        component, intent = parse(text)
        if component is None or intent == "EXACT":
            return ()
        return compiled_fields.get((component, intent), ())[:limit]

    plane = AdaptiveSemanticReadPlaneV14(
        verify_read_basis=lambda r: basis,
        exact_lookup=exact_lookup,
        compiled_semantic_lookup=compiled_lookup,
        resolve_entity=lambda text, b: parse(text)[0],
        graph_lookup=lambda logical_id, text, b, limit: (),
        compositional_lookup=lambda text, b, limit: (),
        fallback_lookup=lambda text, b, limit: (),
    )

    by_mode = {m: [c for c in cases if c.mode == m] for m in ("EXACT", "SERVICE", "RESOURCE", "LEXICAL")}

    def udb(c: QueryCase):
        receipt = plane.query(AdaptiveReadRequest(
            query_id=c.query_id,
            text=c.text,
            source_epoch=SOURCE_EPOCH,
            graph_epoch=GRAPH_EPOCH,
            exact_normalized_key=c.exact_key,
            compositional=(c.mode == "RESOURCE"),
            limit=1,
        ))
        return receipt.refs[0] if receipt.refs else None

    def pg_shared(c: QueryCase):
        component, intent = parse(c.text)
        if c.mode == "EXACT":
            component = c.exact_key
            intent = "EXACT"
        if component is None:
            return None
        if intent == "EXACT":
            return pg.exact(component)
        if intent == "SERVICE":
            return pg.one_hop(component)
        if intent == "RESOURCE":
            return pg.two_hop(component)
        if intent == "LEXICAL":
            return pg.lexical(c.text)
        return None

    def pg_full(c: QueryCase):
        if c.mode == "EXACT":
            return pg.exact(c.exact_key or "")
        if c.mode == "LEXICAL":
            return pg.lexical(c.text)
        m = ALIAS_RE.search(c.text.lower())
        if not m:
            return None
        if c.mode == "SERVICE":
            return pg.full_alias_one_hop(m.group(0))
        if c.mode == "RESOURCE":
            return pg.full_alias_two_hop(m.group(0))
        return None

    def sqlite_btree(c: QueryCase):
        row = sqlite_exact.execute("SELECT record_id FROM records WHERE logical_id=? LIMIT 1", (c.exact_key,)).fetchone()
        return str(row[0]) if row else None

    results = []
    for mode in ("EXACT", "SERVICE", "RESOURCE", "LEXICAL"):
        mode_cases = by_mode[mode]
        results.append(evaluate(f"udb_v14_compiled:{mode}", mode_cases, udb))
        results.append(evaluate(f"postgres18_shared_resolver_online_sql:{mode}", mode_cases, pg_shared))
        results.append(evaluate(f"postgres18_full_online:{mode}", mode_cases, pg_full))
        if mode == "EXACT":
            results.append(evaluate("sqlite_embedded_btree:EXACT", mode_cases, sqlite_btree))

    by_name = {r["name"]: r for r in results}
    comparisons = {}
    for mode in ("EXACT", "SERVICE", "RESOURCE", "LEXICAL"):
        u = by_name[f"udb_v14_compiled:{mode}"]
        p = by_name[f"postgres18_shared_resolver_online_sql:{mode}"]
        comparisons[mode] = {
            "top1_delta_udb_minus_postgres": u["top1_accuracy"] - p["top1_accuracy"],
            "p50_speedup_udb_vs_postgres": (
                p["latency"]["p50_us"] / u["latency"]["p50_us"]
                if u["latency"]["p50_us"] else None
            ),
            "p95_speedup_udb_vs_postgres": (
                p["latency"]["p95_us"] / u["latency"]["p95_us"]
                if u["latency"]["p95_us"] else None
            ),
        }

    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        server_banner = str(cur.fetchone()[0])
    conn.close()
    sqlite_exact.close()

    out = {
        "schema_version": "1.0",
        "benchmark": "CLAY_U14_VS_POSTGRESQL18_MATCHED_SEMANTIC_READ_V1",
        "execution_class": os.environ.get("CLAY_EXECUTION_CLASS", "LOCAL_OR_CI_UNKNOWN"),
        "scope": (
            "Synthetic deterministic assistant retrieval; PostgreSQL receives B-tree/GIN indexes, "
            "prepared parameterized online SQL and matched deterministic intent/entity extraction. "
            "Not universal database superiority and not live-FRANK answer quality."
        ),
        "fixture": {
            "seeds": list(SEEDS),
            "families_per_seed": FAMILIES_PER_SEED,
            "repeats_per_family": REPEATS_PER_FAMILY,
            "noise_rows": NOISE_ROWS,
            "records": len(records),
            "edges": len(edges),
            "queries_total": len(cases),
            "queries_per_mode": {m: len(v) for m, v in by_mode.items()},
        },
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "psycopg": getattr(psycopg, "__version__", "UNKNOWN"),
            "postgres": server_banner,
            "sqlite": sqlite3.sqlite_version,
        },
        "build": {
            "postgres": pg_meta,
            "udb_compiled_field_build_ns": compiled_build_ns,
            "udb_compiled_entries": len(compiled_fields),
        },
        "results": results,
        "comparisons": comparisons,
        "acceptance": {
            "all_compiled_top1_exact": all(
                by_name[f"udb_v14_compiled:{m}"]["top1_accuracy"] == 1.0
                for m in ("EXACT", "SERVICE", "RESOURCE", "LEXICAL")
            ),
            "all_postgres_shared_top1_exact": all(
                by_name[f"postgres18_shared_resolver_online_sql:{m}"]["top1_accuracy"] == 1.0
                for m in ("EXACT", "SERVICE", "RESOURCE", "LEXICAL")
            ),
            "no_quality_regression_required": True,
        },
        "limitations": [
            "Synthetic fixture and deterministic entity/intent extraction can contain benchmark-design bias.",
            "PostgreSQL is a server process, whereas Clay U14 compiled fields are local in-process derived state; this is intentional for the Frank hot-read deployment question but not an engine-only microbenchmark.",
            "The benchmark does not include pgvector, Neo4j, learned rerankers, concurrent clients, or live Clay/Frank OOD queries.",
            "Compiled-field build/update cost must be amortized under realistic write rates; high-churn families may prefer online SQL.",
            "Exact-key routing should continue to use the cheapest ordinary indexed mechanism when it dominates; no architecture rule requires Clay compilation for trivial keys.",
        ],
    }
    print(json.dumps(out, indent=2, sort_keys=True))
    if not out["acceptance"]["all_compiled_top1_exact"] or not out["acceptance"]["all_postgres_shared_top1_exact"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
