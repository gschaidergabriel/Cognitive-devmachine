from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import time

from research_entity.harness.reference.state_ledger import StateLedger, h
from research_entity.runtime.database_pulse_rank_path_v6 import AdaptiveAuthoritativeRankPathV6
from research_entity.runtime.database_pulse_rank_path_v6_3_attested import AdaptiveAuthoritativeRankPathV63Attested
from research_entity.runtime.semantic_compile_amortization_gate_v16 import CompileEconomics
from research_entity.runtime.semantic_compile_horizon_estimator_v16 import EpochReadLifetime


def economics() -> CompileEconomics:
    return CompileEconomics(
        build_cost_us=1000.0, online_query_us=100.0, compiled_query_us=10.0,
        online_quality=1.0, compiled_quality=1.0,
        expected_reads_before_invalidation=0.0, safety_factor=1.0,
    )


def history() -> list[EpochReadLifetime]:
    return [EpochReadLifetime(i + 1, 200) for i in range(8)]


def provenance() -> dict[str, str]:
    return {
        "actor": "benchmark",
        "policy_provenance_ref": "benchmark://pulse-rank-v63",
        "policy_decision_hash": h({"benchmark": "pulse-rank-v63", "policy": "compile"}),
    }


def seed(rows: int) -> StateLedger:
    ledger = StateLedger()
    ops = []
    for i in range(rows):
        ops.append(
            {
                "op": "SET", "domain": "memory", "key": f"k{i:08d}",
                "value": {
                    "priority": (i % 101) / 100.0,
                    "urgency": (i % 79) / 78.0,
                    "salience": (i % 61) / 60.0,
                    "novelty": (i % 43) / 42.0,
                },
                "epistemic": "KNOWN", "status": "CURRENT",
            }
        )
    ledger.append_event(
        event_id=f"seed-{rows}", idem=f"seed-{rows}", base_epoch=0,
        event_type="SEED", writer="benchmark", ops=ops,
        committed_at="2026-08-10T05:55:00Z",
    )
    return ledger


def select_v6(path: AdaptiveAuthoritativeRankPathV6):
    return path.select(
        source_domains=("memory",), basis_epoch=path.ledger.epoch,
        max_candidates=64, max_focus=8,
        economics_without_horizon=economics(), pulse_history=history(),
    )


def select_v63(path: AdaptiveAuthoritativeRankPathV63Attested):
    return path.select(
        source_domains=("memory",), basis_epoch=path.ledger.epoch,
        max_candidates=64, max_focus=8,
        economics_without_horizon=economics(), pulse_history=history(),
        **provenance(),
    )


def quantiles_us(samples_ns: list[int]) -> dict[str, float | int]:
    values = sorted(samples_ns)
    def q(p: float) -> float:
        return values[min(len(values) - 1, int(round((len(values) - 1) * p)))] / 1000.0
    return {"p50": q(0.50), "p95": q(0.95), "p99": q(0.99), "n": len(values)}


def run_case(rows: int, repetitions: int) -> dict[str, object]:
    ledger_v6 = seed(rows)
    v6 = AdaptiveAuthoritativeRankPathV6(ledger_v6)
    p6 = v6.plan_lifecycle(
        basis_epoch=ledger_v6.epoch,
        economics_without_horizon=economics(),
        pulse_history=history(),
    )
    r6 = v6.apply_maintenance(p6, **provenance())
    assert r6.status == "BUILT", r6

    ledger_v63 = seed(rows)
    v63 = AdaptiveAuthoritativeRankPathV63Attested(ledger_v63)
    p63 = v63.plan_lifecycle(
        basis_epoch=ledger_v63.epoch,
        economics_without_horizon=economics(),
        pulse_history=history(),
        **provenance(),
    )
    r63 = v63.apply_maintenance(p63)
    assert r63.status == "ATTESTED", r63

    baseline = select_v6(v6)
    attested = select_v63(v63)
    semantic_equivalence = (
        baseline.candidate_refs == attested.candidate_refs
        and baseline.focus_refs == attested.focus_refs
        and baseline.candidate_scores == attested.candidate_scores
    )
    if not semantic_equivalence:
        raise AssertionError("V6/V6.3 semantic ranking mismatch")

    v6_ns: list[int] = []
    v63_ns: list[int] = []
    guard_ns: list[int] = []
    for _ in range(repetitions):
        t0 = time.perf_counter_ns(); select_v6(v6); v6_ns.append(time.perf_counter_ns() - t0)
        t0 = time.perf_counter_ns(); select_v63(v63); v63_ns.append(time.perf_counter_ns() - t0)
        t0 = time.perf_counter_ns(); identity = v63.physical_identity(); guard_ns.append(time.perf_counter_ns() - t0)
        if identity.state != "ATTESTED":
            raise AssertionError(identity)

    q6 = quantiles_us(v6_ns)
    q63 = quantiles_us(v63_ns)
    qguard = quantiles_us(guard_ns)
    result = {
        "rows": rows,
        "repetitions": repetitions,
        "semantic_equivalence": semantic_equivalence,
        "v6_compiled_select_us": q6,
        "v6_3_attested_select_us": q63,
        "physical_attestation_guard_us": qguard,
        "attestation_delta_p50_us": float(q63["p50"]) - float(q6["p50"]),
        "attestation_ratio_p50": float(q63["p50"]) / float(q6["p50"]) if q6["p50"] else None,
    }
    ledger_v6.close(); ledger_v63.close()
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rows", default="100,1000")
    parser.add_argument("--repetitions", type=int, default=100)
    parser.add_argument("--output")
    args = parser.parse_args()
    cases = [run_case(int(raw), args.repetitions) for raw in args.rows.split(",") if raw.strip()]
    result = {
        "schema_version": "1.0",
        "candidate": "PULSE_PROVENANCE_PLUS_ABA_SAFE_ATTESTED_RANK_PATH_V6_3",
        "baseline": "PULSE_PROVENANCE_EAP17_RANK_PATH_V6",
        "authority": "PERFORMANCE_CONTINUITY_BENCHMARK_ONLY",
        "metadata": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "sqlite": sqlite3.sqlite_version,
        },
        "results": cases,
        "pass": all(bool(case["semantic_equivalence"]) for case in cases),
    }
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print(text)


if __name__ == "__main__":
    main()
