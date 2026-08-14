#!/usr/bin/env python3
from __future__ import annotations

"""Adversarial falsifier for bounded Database Pulse candidate selection.

Hypothesis: applying max_candidates in lexicographic UnifiedDB query order before Pulse
salience scoring can hide a later high-salience state. The wide-census arm is a matched
control. This script records the result and intentionally exits 0 whether the hypothesis is
supported or refuted; architecture promotion must inspect the receipt rather than encode the
expected answer into CI success.
"""

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402
from research_entity.runtime.database_pulse_candidate_v1 import (  # noqa: E402
    DatabasePulseRuntime,
    PulseSpec,
)


def seed_events(low_rows: int):
    ledger = StateLedger()
    ops = []
    for i in range(low_rows):
        ops.append(
            {
                "op": "SET",
                "domain": "memory",
                "key": f"k{i:04d}",
                "value": {"fact": i, "priority": 0.0, "urgency": 0.0, "salience": 0.0, "novelty": 0.0},
                "epistemic": "KNOWN",
                "status": "CURRENT",
            }
        )
    ops.append(
        {
            "op": "SET",
            "domain": "memory",
            "key": "zzzz-critical",
            "value": {"fact": "critical", "priority": 1.0, "urgency": 1.0, "salience": 1.0, "novelty": 1.0},
            "epistemic": "KNOWN",
            "status": "CURRENT",
        }
    )
    ledger.append_event(
        event_id="seed-many-memory",
        idem="seed-many-memory",
        base_epoch=ledger.epoch,
        event_type="PULSE_TRUNCATION_FALSIFIER_SEED",
        writer="chatgpt-secondary",
        ops=ops,
        committed_at="2026-08-10T00:20:00Z",
    )
    runtime = DatabasePulseRuntime(ledger)
    runtime.set_scheduler(
        enabled=True,
        event_id="scheduler-on",
        base_epoch=ledger.epoch,
        actor="chatgpt-secondary",
        reason="adversarial candidate-selection falsifier",
        committed_at="2026-08-10T00:20:01Z",
    )
    events = ledger.export_events()
    ledger.close()
    return events


def arm(events, *, pulse_id: str, max_candidates: int):
    ledger = StateLedger.replay(events)
    runtime = DatabasePulseRuntime(ledger)
    t0 = time.perf_counter_ns()
    receipt = runtime.run_pulse(
        PulseSpec(
            pulse_id,
            basis_epoch=ledger.epoch,
            source_domains=("memory",),
            max_candidates=max_candidates,
            max_focus=1,
            reentry_mode="NO_REENTRY",
        ),
        committed_at="2026-08-10T00:20:02Z",
    )
    latency_ms = (time.perf_counter_ns() - t0) / 1_000_000.0
    out = {
        "max_candidates": max_candidates,
        "focus_refs": list(receipt.focus_refs),
        "assembly_hash": receipt.assembly_hash,
        "latency_ms": round(latency_ms, 6),
        "semantic_state_hash": receipt.input_semantic_state_hash,
    }
    ledger.close()
    return out


def run(low_rows: int, bounded: int):
    events = seed_events(low_rows)
    narrow = arm(events, pulse_id="bounded-arm", max_candidates=bounded)
    wide = arm(events, pulse_id="wide-arm", max_candidates=min(512, low_rows + 1))
    target = "memory:zzzz-critical"
    bug_reproduced = target not in narrow["focus_refs"] and target in wide["focus_refs"]
    return {
        "schema_version": "1.0",
        "experiment_class": "DISCRIMINATING_COUNTERHYPOTHESIS_TEST",
        "hypothesis": "pre-ranking lexicographic max_candidates truncation can hide a later high-salience state",
        "strongest_counterhypothesis": "bounded candidate selection remains semantically adequate despite query ordering",
        "low_salience_rows": low_rows,
        "critical_ref": target,
        "bounded_arm": narrow,
        "wide_control_arm": wide,
        "pre_ranking_truncation_bug_reproduced": bug_reproduced,
        "interpretation": (
            "SUPPORTED: candidate generation needs salience-aware/incremental preselection before max_candidates"
            if bug_reproduced
            else "REFUTED_OR_NOT_REPRODUCED: retain v1 selection pending other falsifiers"
        ),
        "authority_boundary": "focus selection is context-only and never effect authority",
        "limitations": [
            "Synthetic StateLedger fixture; live-FRANK downstream answer quality is not measured.",
            "Wide arm spends more read budget and is a correctness control, not a production recommendation.",
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--low-rows", type=int, default=180)
    ap.add_argument("--bounded", type=int, default=64)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = run(max(70, args.low_rows), max(8, min(128, args.bounded)))
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
