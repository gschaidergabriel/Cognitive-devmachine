from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import time

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.runtime.database_pulse_rank_path_v5 import AdaptiveAuthoritativeRankPathV5
from research_entity.runtime.database_pulse_rank_path_v5_1_attested import AttestedAdaptiveAuthoritativeRankPathV5_1
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics():
    return CompileEconomics(
        build_cost_us=1000.0, online_query_us=100.0, compiled_query_us=10.0,
        online_quality=1.0, compiled_quality=1.0,
        expected_reads_before_invalidation=0.0, safety_factor=1.0,
    )


def history():
    return [EpochReadLifetime(i + 1, 200) for i in range(8)]


def seed(rows: int):
    ledger = StateLedger()
    ops = []
    for i in range(rows):
        ops.append({
            "op": "SET", "domain": "memory", "key": f"k{i:08d}",
            "value": {
                "priority": (i % 101) / 100.0, "urgency": (i % 79) / 78.0,
                "salience": (i % 61) / 60.0, "novelty": (i % 43) / 42.0,
            },
            "epistemic": "KNOWN", "status": "CURRENT",
        })
    ledger.append_event(
        event_id=f"seed-{rows}", idem=f"seed-{rows}", base_epoch=0,
        event_type="SEED", writer="benchmark", ops=ops,
        committed_at="2026-08-10T05:20:00Z",
    )
    return ledger


def q_v5(v):
    return v.select(
        source_domains=("memory",), basis_epoch=v.ledger.epoch,
        max_candidates=64, max_focus=8,
        economics_without_horizon=economics(), pulse_history=history(),
    )


def q_v51(v):
    return v.select(
        source_domains=("memory",), basis_epoch=v.ledger.epoch,
        max_candidates=64, max_focus=8,
        economics_without_horizon=economics(), pulse_history=history(),
        actor="benchmark", policy_provenance_ref="benchmark://fixed-economics-v1",
    )


def quantiles_us(samples):
    xs = sorted(samples)
    def at(p):
        if not xs:
            return None
        return xs[min(len(xs) - 1, int(round((len(xs) - 1) * p)))] / 1000.0
    return {"p50": at(0.50), "p95": at(0.95), "p99": at(0.99), "n": len(xs)}


def bench(rows: int, repeat: int):
    l5 = seed(rows)
    v5 = AdaptiveAuthoritativeRankPathV5(l5)
    p5 = v5.plan_lifecycle(
        basis_epoch=l5.epoch, economics_without_horizon=economics(), pulse_history=history()
    )
    v5.apply_maintenance(p5)

    l51 = seed(rows)
    v51 = AttestedAdaptiveAuthoritativeRankPathV5_1(l51)
    p51 = v51.plan_lifecycle(
        basis_epoch=l51.epoch, economics_without_horizon=economics(), pulse_history=history(),
        actor="benchmark", policy_provenance_ref="benchmark://fixed-economics-v1",
    )
    v51.apply_maintenance(p51)

    base = q_v5(v5)
    att = q_v51(v51)
    equivalent = (
        base.candidate_refs == att.candidate_refs
        and base.focus_refs == att.focus_refs
        and base.candidate_scores == att.candidate_scores
    )
    s5 = []
    s51 = []
    for _ in range(repeat):
        t = time.perf_counter_ns(); q_v5(v5); s5.append(time.perf_counter_ns() - t)
        t = time.perf_counter_ns(); q_v51(v51); s51.append(time.perf_counter_ns() - t)
    q5 = quantiles_us(s5)
    q51 = quantiles_us(s51)

    # Deliberately unusual falsifier: a correct same-name index produced outside the attested
    # lifecycle must be treated as an untrusted accelerator, while answer semantics stay intact.
    llegacy = seed(rows)
    legacy = AttestedAdaptiveAuthoritativeRankPathV5_1(llegacy)
    legacy.v3.ensure_index()
    legacy_read = q_v51(legacy)
    legacy_state = legacy.physical_identity().state
    legacy_safe = (
        legacy_state == "UNATTESTED"
        and legacy_read.physical_read_mode == "ONLINE_PENDING_REBUILD"
        and legacy_read.candidate_refs == base.candidate_refs
    )

    out = {
        "rows": rows,
        "repeat": repeat,
        "semantic_equivalence": equivalent,
        "v5_compiled_us": q5,
        "v5_1_attested_compiled_us": q51,
        "attestation_overhead_p50_us": q51["p50"] - q5["p50"],
        "attestation_overhead_p50_ratio": q51["p50"] / q5["p50"] if q5["p50"] else None,
        "legacy_unattested_fails_online": legacy_safe,
        "legacy_physical_state": legacy_state,
        "legacy_read_mode": legacy_read.physical_read_mode,
    }
    l5.close(); l51.close(); llegacy.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rows", default="100,1000")
    ap.add_argument("--repeat", type=int, default=100)
    ap.add_argument("--output")
    args = ap.parse_args()
    result = {
        "schema_version": "1.0",
        "candidate": "PULSE_ATTESTED_AUTHORITATIVE_RANK_PATH_V5_1",
        "authority": "PERFORMANCE_CONTINUITY_BENCHMARK_ONLY",
        "metadata": {
            "platform": platform.platform(), "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "results": [bench(int(x), args.repeat) for x in args.rows.split(",") if x.strip()],
    }
    result["pass"] = all(
        r["semantic_equivalence"] and r["legacy_unattested_fails_online"] for r in result["results"]
    )
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        open(args.output, "w", encoding="utf-8").write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
