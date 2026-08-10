#!/usr/bin/env python3
from __future__ import annotations

"""Deterministic engineering benchmark for EAP-1.7 query-aware propagation.

Two matched cohorts are built:
- labeled bridge: the relevant intermediate node itself contains the query token;
- opaque bridge: only its one-hop successor contains the query token.

The benchmark compares the EAP-1.3 parent, the V17 target-only gate ablation, and the default
bounded one-successor lookahead. It is mechanism evidence only, not a claim about general RAG
or final Frank answer/tool quality.
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

TARGET_ONLY_MODE = "LEXICAL_COSINE_TARGET_RELATION"
LOOKAHEAD_MODE = "LEXICAL_COSINE_TARGET_OR_ADMISSIBLE_SUCCESSOR_V1"


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


def build_fixture(cases_per_cohort: int) -> tuple[StateLedger, list[dict[str, str]]]:
    ledger = StateLedger()
    ops: list[dict] = []
    specs: list[dict[str, str]] = []
    for cohort, opaque in (("labeled", False), ("opaque", True)):
        for i in range(cases_per_cohort):
            token = f"{cohort}topic{i}"
            stem = f"{cohort}_{i}"
            seed = f"memory:seed_{stem}"
            rel_bridge = f"memory:rel_bridge_{stem}"
            rel_target = f"memory:rel_target_{stem}"
            noise_bridge = f"memory:noise_bridge_{stem}"
            noise_target = f"memory:noise_target_{stem}"
            specs.append(
                {
                    "cohort": cohort,
                    "query": f"{token} target",
                    "seed": seed,
                    "rel_bridge": rel_bridge,
                    "rel_target": rel_target,
                    "noise_bridge": noise_bridge,
                    "noise_target": noise_target,
                }
            )
            bridge_text = "connector intermediate" if opaque else f"{token} pathway bridge"
            ops.extend(
                [
                    {"op": "SET", "domain": "memory", "key": f"seed_{stem}", "value": {"text": "router root"}},
                    {"op": "SET", "domain": "memory", "key": f"rel_bridge_{stem}", "value": {"text": bridge_text}},
                    {"op": "SET", "domain": "memory", "key": f"rel_target_{stem}", "value": {"text": f"{token} target evidence"}},
                    {"op": "SET", "domain": "memory", "key": f"noise_bridge_{stem}", "value": {"text": "unrelated noise branch"}},
                    {"op": "SET", "domain": "memory", "key": f"noise_target_{stem}", "value": {"text": "unrelated noise target"}},
                    {"op": "SET", "domain": "dependency", "key": f"sa_{stem}", "value": {"source": seed, "target": rel_bridge, "strength": 0.90}},
                    {"op": "SET", "domain": "dependency", "key": f"at_{stem}", "value": {"source": rel_bridge, "target": rel_target, "strength": 0.90}},
                    {"op": "SET", "domain": "dependency", "key": f"sn_{stem}", "value": {"source": seed, "target": noise_bridge, "strength": 0.99}},
                    {"op": "SET", "domain": "dependency", "key": f"nt_{stem}", "value": {"source": noise_bridge, "target": noise_target, "strength": 0.99}},
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


def candidate_spec(
    ledger: StateLedger,
    case: dict[str, str],
    assembly_id: str,
    mode: str,
) -> QueryAwarePossibilitySpec:
    return QueryAwarePossibilitySpec(
        **{
            **parent_spec(ledger, case, assembly_id).__dict__,
            "query_gate_strength": 0.85,
            "query_gate_floor": 0.10,
            "query_gate_mode": mode,
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


def run(cases_per_cohort: int, repeats: int) -> dict:
    ledger, fixture = build_fixture(cases_per_cohort)
    parent = EmergentAssemblyPreprocessor(ledger)
    query_pre = QueryAwareEmergentAssemblyPreprocessor(ledger)
    parent.compile_active_assembly(parent_spec(ledger, fixture[0], "warm-parent"))
    for mode in (TARGET_ONLY_MODE, LOOKAHEAD_MODE):
        query_pre.compile_active_assembly(candidate_spec(ledger, fixture[0], f"warm-{mode}", mode))

    modes = ("parent", "target_only", "lookahead")
    latency: dict[str, list[float]] = {mode: [] for mode in modes}
    hit: dict[str, dict[str, int]] = {
        mode: {"labeled": 0, "opaque": 0} for mode in modes
    }
    exact: dict[str, dict[str, int]] = {
        mode: {"labeled": 0, "opaque": 0} for mode in modes
    }
    work = {
        "target_only_edges_observed": 0,
        "lookahead_edges_observed": 0,
        "lookahead_edges_scanned": 0,
        "lookahead_affinity_wins": 0,
        "lookahead_edges_pruned_below_parent_min": 0,
    }

    for i, case in enumerate(fixture):
        cohort = case["cohort"]
        p, p_lat = timed(
            lambda c=case, n=i: parent.compile_active_assembly(parent_spec(ledger, c, f"p-{n}")),
            repeats,
        )
        t, t_lat = timed(
            lambda c=case, n=i: query_pre.compile_active_assembly(
                candidate_spec(ledger, c, f"t-{n}", TARGET_ONLY_MODE)
            ),
            repeats,
        )
        q, q_lat = timed(
            lambda c=case, n=i: query_pre.compile_active_assembly(
                candidate_spec(ledger, c, f"q-{n}", LOOKAHEAD_MODE)
            ),
            repeats,
        )
        latency["parent"].extend(p_lat)
        latency["target_only"].extend(t_lat)
        latency["lookahead"].extend(q_lat)
        results = {"parent": p, "target_only": t, "lookahead": q}
        expected_exact = [case["seed"], case["rel_bridge"], case["rel_target"]]
        for mode, result in results.items():
            refs = [x["ref"] for x in result["selected"]]
            hit[mode][cohort] += int(case["rel_target"] in refs)
            exact[mode][cohort] += int(refs == expected_exact)
        work["target_only_edges_observed"] += int(t["query_gate"]["edges_observed"])
        work["lookahead_edges_observed"] += int(q["query_gate"]["edges_observed"])
        work["lookahead_edges_scanned"] += int(q["query_gate"]["lookahead_edges_scanned"])
        work["lookahead_affinity_wins"] += int(q["query_gate"]["lookahead_affinity_wins"])
        work["lookahead_edges_pruned_below_parent_min"] += int(q["query_gate"]["edges_pruned_below_parent_min"])

    quality: dict[str, dict[str, float]] = {}
    for mode in modes:
        quality[mode] = {}
        for cohort in ("labeled", "opaque"):
            quality[mode][f"{cohort}_target_hit_at_3"] = hit[mode][cohort] / cases_per_cohort
            quality[mode][f"{cohort}_exact_branch_rate"] = exact[mode][cohort] / cases_per_cohort

    lat_summary = {mode: summarize_latency(latency[mode]) for mode in modes}
    lat_summary["target_only_p50_over_parent"] = round(
        statistics.median(latency["target_only"]) / max(1e-12, statistics.median(latency["parent"])), 4
    )
    lat_summary["lookahead_p50_over_parent"] = round(
        statistics.median(latency["lookahead"]) / max(1e-12, statistics.median(latency["parent"])), 4
    )
    lat_summary["lookahead_p50_over_target_only"] = round(
        statistics.median(latency["lookahead"]) / max(1e-12, statistics.median(latency["target_only"])), 4
    )

    target_only_opaque = quality["target_only"]["opaque_target_hit_at_3"]
    lookahead_opaque = quality["lookahead"]["opaque_target_hit_at_3"]
    lookahead_labeled = quality["lookahead"]["labeled_target_hit_at_3"]
    supported = (
        lookahead_opaque > target_only_opaque
        and lookahead_opaque == 1.0
        and lookahead_labeled == 1.0
    )
    return {
        "schema_version": "2.0",
        "benchmark_class": "SYNTHETIC_DISCRIMINATING_MECHANISM_TEST",
        "implementation": IMPLEMENTATION_ID,
        "cases_per_cohort": cases_per_cohort,
        "total_cases": len(fixture),
        "repeats_per_case": repeats,
        "fixture_nodes": len(fixture) * 5,
        "fixture_dependencies": len(fixture) * 4,
        "quality": quality,
        "latency": lat_summary,
        "work": work,
        "semantic_contract": {
            "persistent_second_store": False,
            "truth_authority": False,
            "effect_authority": False,
            "lesion": "query_gate_strength=0",
            "lookahead_depth": 1,
        },
        "discriminating_result": "SUPPORTED_ON_FIXTURE" if supported else "NOT_SUPPORTED_ON_FIXTURE",
        "limitations": [
            "Both cohorts are synthetic and deliberately discriminating; this is not independent real-corpus evidence.",
            "Lexical cosine is a dependency-free proxy for a semantic gate, not an embedding model.",
            "The one-successor lookahead can increase edge inspections; held-out benefit/resource tradeoff is still unmeasured.",
            "Hot assembly latency excludes initial StateLedger construction and first topology compilation.",
            "Target-hit@3 is retrieval mechanism quality only; downstream Frank answer/tool-routing quality remains unmeasured.",
        ],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=int, default=64, help="cases per cohort")
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
