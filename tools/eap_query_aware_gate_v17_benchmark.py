#!/usr/bin/env python3
from __future__ import annotations

"""Deterministic engineering benchmark for EAP-1.7 query-aware propagation.

The fixture intentionally separates structural strength from query relevance. It measures
whether the opt-in query gate recovers the intended two-hop target under a fixed top-3 budget,
while reporting (not optimizing against) the extra latency. This is mechanism evidence only,
not a claim about general RAG or final Frank answer quality.
"""

import argparse
import json
import math
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (  # noqa: E402
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)
from research_entity.runtime.eap_query_aware_gate_v17 import (  # noqa: E402
    IMPLEMENTATION_ID,
    QueryAwareEmergentAssemblyPreprocessor,
    QueryAwarePossibilitySpec,
)


def percentile(values: list[float], q: float) -> float:
    xs = sorted(values)
    if not xs:
        return 0.0
    pos = (len(xs) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] * (1.0 - frac) + xs[hi] * frac


def build_fixture(cases: int) -> tuple[StateLedger, list[dict[str, str]]]:
    ledger = StateLedger()
    ops: list[dict] = []
    specs: list[dict[str, str]] = []
    for i in range(cases):
        token = f"topic{i}"
        seed = f"memory:seed_{i}"
        rel_bridge = f"memory:rel_bridge_{i}"
        rel_target = f"memory:rel_target_{i}"
        noise_bridge = f"memory:noise_bridge_{i}"
        noise_target = f"memory:noise_target_{i}"
        specs.append(
            {
                "query": f"{token} target",
                "seed": seed,
                "rel_bridge": rel_bridge,
                "rel_target": rel_target,
                "noise_bridge": noise_bridge,
                "noise_target": noise_target,
            }
        )
        ops.extend(
            [
                {"op": "SET", "domain": "memory", "key": f"seed_{i}", "value": {"text": "router root"}},
                {"op": "SET", "domain": "memory", "key": f"rel_bridge_{i}", "value": {"text": f"{token} pathway bridge"}},
                {"op": "SET", "domain": "memory", "key": f"rel_target_{i}", "value": {"text": f"{token} target evidence"}},
                {"op": "SET", "domain": "memory", "key": f"noise_bridge_{i}", "value": {"text": "unrelated noise branch"}},
                {"op": "SET", "domain": "memory", "key": f"noise_target_{i}", "value": {"text": "unrelated noise target"}},
                {"op": "SET", "domain": "dependency", "key": f"sa_{i}", "value": {"source": seed, "target": rel_bridge, "strength": 0.90}},
                {"op": "SET", "domain": "dependency", "key": f"at_{i}", "value": {"source": rel_bridge, "target": rel_target, "strength": 0.90}},
                {"op": "SET", "domain": "dependency", "key": f"sn_{i}", "value": {"source": seed, "target": noise_bridge, "strength": 0.99}},
                {"op": "SET", "domain": "dependency", "key": f"nt_{i}", "value": {"source": noise_bridge, "target": noise_target, "strength": 0.99}},
            ]
        )
    ledger.append_event(
        event_id="benchmark-fixture",
        idem="benchmark-fixture",
        base_epoch=ledger.epoch,
        event_type="BENCHMARK_FIXTURE",
        writer="benchmark",
        ops=ops,
        provenance={"evidence_class": "SYNTHETIC_ENGINEERING_FIXTURE"},
    )
    return ledger, specs


def parent_spec(ledger: StateLedger, case: dict[str, str], assembly_id: str) -> PossibilitySpec:
    return PossibilitySpec(
        assembly_id=assembly_id,
        seed_refs=(case["seed"],),
        query_text=case["query"],
        allowed_domains=("memory",),
        max_items=3,
        max_hops=2,
        frontier_budget=32,
        min_edge_weight=0.30,
        hop_decay=0.88,
        lexical_weight=0.0,
        basis_epoch=ledger.epoch,
    )


def candidate_spec(ledger: StateLedger, case: dict[str, str], assembly_id: str) -> QueryAwarePossibilitySpec:
    return QueryAwarePossibilitySpec(
        **{
            **parent_spec(ledger, case, assembly_id).__dict__,
            "query_gate_strength": 0.85,
            "query_gate_floor": 0.10,
        }
    )


def timed(fn, repeats: int) -> tuple[dict, list[float]]:
    result: dict = {}
    latencies: list[float] = []
    for _ in range(repeats):
        t0 = time.perf_counter_ns()
        result = fn()
        latencies.append((time.perf_counter_ns() - t0) / 1000.0)
    return result, latencies


def summarize_latency(values: list[float]) -> dict[str, float]:
    return {
        "p50_us": round(statistics.median(values), 3),
        "p95_us": round(percentile(values, 0.95), 3),
        "p99_us": round(percentile(values, 0.99), 3),
        "min_us": round(min(values), 3),
        "max_us": round(max(values), 3),
    }


def run(cases: int, repeats: int) -> dict:
    ledger, fixture = build_fixture(cases)
    parent = EmergentAssemblyPreprocessor(ledger)
    candidate = QueryAwareEmergentAssemblyPreprocessor(ledger)

    # Warm both topology compilers before measuring hot assembly calls.
    parent.compile_active_assembly(parent_spec(ledger, fixture[0], "warm-parent"))
    candidate.compile_active_assembly(candidate_spec(ledger, fixture[0], "warm-candidate"))

    parent_lat: list[float] = []
    candidate_lat: list[float] = []
    parent_hits = 0
    candidate_hits = 0
    exact_branch_recoveries = 0
    gate_edges_observed = 0
    gate_edges_pruned = 0
    candidate_expansions: list[int] = []
    parent_expansions: list[int] = []

    for i, case in enumerate(fixture):
        p, p_lat = timed(
            lambda c=case, n=i: parent.compile_active_assembly(
                parent_spec(ledger, c, f"p-{n}")
            ),
            repeats,
        )
        q, q_lat = timed(
            lambda c=case, n=i: candidate.compile_active_assembly(
                candidate_spec(ledger, c, f"q-{n}")
            ),
            repeats,
        )
        parent_lat.extend(p_lat)
        candidate_lat.extend(q_lat)
        p_refs = [x["ref"] for x in p["selected"]]
        q_refs = [x["ref"] for x in q["selected"]]
        parent_hits += int(case["rel_target"] in p_refs)
        candidate_hits += int(case["rel_target"] in q_refs)
        exact_branch_recoveries += int(
            q_refs == [case["seed"], case["rel_bridge"], case["rel_target"]]
        )
        gate_edges_observed += int(q["query_gate"]["edges_observed"])
        gate_edges_pruned += int(q["query_gate"]["edges_pruned_below_parent_min"])
        candidate_expansions.append(int(q["frontier_expansions"]))
        parent_expansions.append(int(p["frontier_expansions"]))

    parent_hit_rate = parent_hits / cases
    candidate_hit_rate = candidate_hits / cases
    out = {
        "schema_version": "1.0",
        "benchmark_class": "SYNTHETIC_DISCRIMINATING_MECHANISM_TEST",
        "implementation": IMPLEMENTATION_ID,
        "cases": cases,
        "repeats_per_case": repeats,
        "fixture_nodes": cases * 5,
        "fixture_dependencies": cases * 4,
        "quality": {
            "parent_relevant_target_hit_at_3": parent_hit_rate,
            "query_aware_relevant_target_hit_at_3": candidate_hit_rate,
            "delta_hit_at_3": candidate_hit_rate - parent_hit_rate,
            "query_aware_exact_relevant_branch_rate": exact_branch_recoveries / cases,
        },
        "latency": {
            "parent": summarize_latency(parent_lat),
            "query_aware": summarize_latency(candidate_lat),
            "p50_ratio_query_aware_over_parent": round(
                statistics.median(candidate_lat) / max(1e-12, statistics.median(parent_lat)), 4
            ),
        },
        "work": {
            "parent_frontier_expansions_p50": statistics.median(parent_expansions),
            "query_aware_frontier_expansions_p50": statistics.median(candidate_expansions),
            "query_gate_edges_observed_total": gate_edges_observed,
            "query_gate_edges_pruned_below_parent_min_total": gate_edges_pruned,
        },
        "semantic_contract": {
            "persistent_second_store": False,
            "truth_authority": False,
            "effect_authority": False,
            "lesion": "query_gate_strength=0",
        },
        "limitations": [
            "Synthetic graph intentionally favors a query-conditioned discriminator; it is not independent real-corpus evidence.",
            "Lexical cosine is a dependency-free proxy for a semantic gate, not an embedding model.",
            "Hot assembly latency excludes initial StateLedger construction and first topology compilation.",
            "Target-hit@3 is retrieval mechanism quality only; downstream Frank answer/tool-routing quality remains unmeasured.",
        ],
    }
    out["discriminating_result"] = (
        "SUPPORTED_ON_FIXTURE"
        if candidate_hit_rate > parent_hit_rate and candidate_hit_rate == 1.0
        else "NOT_SUPPORTED_ON_FIXTURE"
    )
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=64)
    ap.add_argument("--repeats", type=int, default=5)
    ap.add_argument("--output")
    args = ap.parse_args()
    cases = max(4, min(args.cases, 512))
    repeats = max(1, min(args.repeats, 50))
    out = run(cases, repeats)
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    print(text, end="")
    if out["discriminating_result"] != "SUPPORTED_ON_FIXTURE":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
