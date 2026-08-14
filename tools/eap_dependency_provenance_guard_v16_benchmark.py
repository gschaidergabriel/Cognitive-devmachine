#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import statistics
import time
from pathlib import Path

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
)
from research_entity.runtime.eap_dependency_provenance_guard_v16 import (
    ProvenanceGuardedEmergentAssemblyPreprocessor,
)


def percentile(xs: list[float], p: float) -> float:
    ys = sorted(xs)
    return ys[min(len(ys) - 1, max(0, math.ceil(p * len(ys)) - 1))]


def latency(xs: list[float]) -> dict[str, float]:
    return {
        "n": len(xs),
        "mean_us": statistics.mean(xs),
        "p50_us": statistics.median(xs),
        "p95_us": percentile(xs, 0.95),
        "p99_us": percentile(xs, 0.99),
        "max_us": max(xs),
    }


def seed(families: int, poison_every: int) -> tuple[StateLedger, list[tuple[str, str, bool]]]:
    ledger = StateLedger()
    truth = []
    node_ops = []
    for i in range(families):
        node_ops.extend([
            {"op":"SET","domain":"semantic","key":f"a{i}","value":{"label":f"anchor {i}"},"epistemic":"KNOWN","status":"CURRENT"},
            {"op":"SET","domain":"semantic","key":f"t{i}","value":{"label":f"target {i}"},"epistemic":"KNOWN","status":"CURRENT"},
            {"op":"SET","domain":"semantic","key":f"d{i}","value":{"label":f"decoy {i}"},"epistemic":"KNOWN","status":"CURRENT"},
        ])
        truth.append((f"semantic:a{i}", f"semantic:t{i}", i % poison_every == 0))
    ledger.append_event(
        event_id="nodes", idem="nodes", base_epoch=0, event_type="NODES", writer="bench",
        provenance={"evidence_class":"VERIFIED"}, source={"fixture":"u16-benchmark"},
        ops=node_ops,
    )
    for i in range(families):
        ledger.append_event(
            event_id=f"good-{i}", idem=f"good-{i}", base_epoch=ledger.epoch,
            event_type="VERIFIED_DEPENDENCY", writer="bench",
            provenance={"evidence_class":"VERIFIED"}, source={"fixture":"u16-good"},
            ops=[{
                "op":"SET","domain":"dependency","key":f"good{i}",
                "value":{"source":f"semantic:a{i}","target":f"semantic:t{i}","strength":0.55,"relation_type":"requires"},
                "epistemic":"KNOWN","status":"CURRENT",
            }],
        )
        if i % poison_every == 0:
            ledger.append_event(
                event_id=f"poison-{i}", idem=f"poison-{i}", base_epoch=ledger.epoch,
                event_type="MODEL_PROPOSAL", writer="adversary",
                provenance={"evidence_class":"MODEL_INFERRED"}, source={"fixture":"u16-poison"},
                ops=[{
                    "op":"SET","domain":"dependency","key":f"poison{i}",
                    "value":{"source":f"semantic:a{i}","target":f"semantic:d{i}","strength":1.0,"relation_type":"requires"},
                    "epistemic":"KNOWN","status":"CURRENT",
                }],
            )
    return ledger, truth


def run(families: int, poison_every: int, repeats: int) -> dict:
    ledger, truth = seed(families, poison_every)
    baseline = EmergentAssemblyPreprocessor(ledger)
    guarded = ProvenanceGuardedEmergentAssemblyPreprocessor(ledger)

    def query(pp, qid: str, anchor: str):
        return pp.compile_active_assembly(PossibilitySpec(
            qid, seed_refs=(anchor,), max_items=2, max_hops=1,
            frontier_budget=16, basis_epoch=ledger.epoch,
        ))

    t0 = time.perf_counter_ns()
    baseline_first = query(baseline, "baseline-cold", truth[0][0])
    baseline_cold_us = (time.perf_counter_ns() - t0) / 1000.0
    t0 = time.perf_counter_ns()
    guarded_first = query(guarded, "guard-cold", truth[0][0])
    guarded_cold_us = (time.perf_counter_ns() - t0) / 1000.0

    baseline_lat: list[float] = []
    guard_lat: list[float] = []
    baseline_correct = 0
    guard_correct = 0
    baseline_poison_errors = 0
    guard_poison_errors = 0
    for i in range(repeats):
        anchor, target, poisoned = truth[i % len(truth)]
        t0 = time.perf_counter_ns()
        b = query(baseline, f"b{i}", anchor)
        baseline_lat.append((time.perf_counter_ns() - t0) / 1000.0)
        t0 = time.perf_counter_ns()
        g = query(guarded, f"g{i}", anchor)
        guard_lat.append((time.perf_counter_ns() - t0) / 1000.0)
        brefs = [x["ref"] for x in b["selected"]]
        grefs = [x["ref"] for x in g["selected"]]
        baseline_correct += target in brefs
        guard_correct += target in grefs
        if poisoned:
            baseline_poison_errors += target not in brefs
            guard_poison_errors += target not in grefs

    audit = guarded_first["edge_proof_audit"]
    out = {
        "schema_version":"1.0",
        "benchmark":"EAP_DEPENDENCY_PROVENANCE_GUARD_V16",
        "evidence_class":"EXECUTED_WHEN_RUN",
        "fixture":{
            "families":families,
            "poison_every":poison_every,
            "repeats":repeats,
            "state_epoch":ledger.epoch,
            "trusted_edge_count":families,
            "untrusted_edge_count":sum(1 for _,_,p in truth if p),
        },
        "quality":{
            "baseline_target_recall":baseline_correct/repeats,
            "guard_target_recall":guard_correct/repeats,
            "baseline_poison_query_errors":baseline_poison_errors,
            "guard_poison_query_errors":guard_poison_errors,
        },
        "latency":{
            "baseline_cold_first_query_us":baseline_cold_us,
            "guard_cold_first_query_us":guarded_cold_us,
            "baseline_hot":latency(baseline_lat),
            "guard_hot":latency(guard_lat),
        },
        "guard_audit_first_query":audit,
        "cold_examples":{
            "baseline_selected":[x["ref"] for x in baseline_first["selected"]],
            "guard_selected":[x["ref"] for x in guarded_first["selected"]],
        },
        "authority_boundary":"provenance guard filters derived dependency propagation only; StateLedger remains canonical and EAP remains context-only",
        "limitations":[
            "Synthetic event provenance classes; real Clay/Frank provenance conventions require migration study.",
            "Exact-seed workload; no NL resolver uncertainty measured here.",
            "Python mechanism benchmark; not universal database superiority.",
            "Hostinger is preliminary target-OS evidence, not Andreas final target acceptance."
        ],
    }
    ledger.close()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--families", type=int, default=300)
    ap.add_argument("--poison-every", type=int, default=5)
    ap.add_argument("--repeats", type=int, default=1500)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = run(max(20,args.families), max(2,args.poison_every), max(50,args.repeats))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p=Path(args.output); p.parent.mkdir(parents=True,exist_ok=True); p.write_text(text,encoding="utf-8")
    print(text,end="")


if __name__ == "__main__":
    main()
