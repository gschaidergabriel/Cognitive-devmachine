#!/usr/bin/env python3
from __future__ import annotations

"""Randomized differential falsifier for Pulse authoritative rank index V3.

For multiple deterministic seeds this script mutates authoritative StateLedger state through
SET/RETRACT/SUPERSEDE operations with mixed scalar/dict/bool/string/missing signal values.
After every admitted transaction it compares V3's bounded top-k directly with a full Python
reference using the v1/v2 signal semantics. It also replays the complete event log and repeats
the comparison. Any divergence is a hard falsifier.

This is an engineering semantics test, not live-FRANK cognition evidence.
"""

import argparse
import json
import random
from pathlib import Path
import sys
import time
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from research_entity.harness.reference.state_ledger import StateLedger  # noqa: E402
from research_entity.runtime.database_pulse_active_field_v2 import signal_score  # noqa: E402
from research_entity.runtime.database_pulse_rank_index_v3 import AuthoritativeRankIndexV3  # noqa: E402

DOMAINS = ("memory", "goal", "world")


def random_signal_value(rng: random.Random, serial: int) -> Any:
    mode = rng.randrange(8)
    if mode == 0:
        return serial
    if mode == 1:
        return f"scalar-{serial}"
    if mode == 2:
        return {"priority": bool(rng.randrange(2)), "urgency": bool(rng.randrange(2))}
    if mode == 3:
        return {"priority": str(round(rng.uniform(-1, 2), 3)), "note": serial}
    if mode == 4:
        return {"priority": rng.uniform(-2, 3), "urgency": rng.uniform(-2, 3)}
    if mode == 5:
        return {"salience": rng.random(), "novelty": rng.random(), "fact": serial}
    if mode == 6:
        return {
            "priority": rng.random(), "urgency": rng.random(),
            "salience": rng.random(), "novelty": rng.random(), "fact": serial,
        }
    return {"fact": serial}


def full_reference(ledger: StateLedger, domains: tuple[str, ...], budget: int) -> tuple[str, ...]:
    placeholders = ",".join("?" for _ in domains)
    rows = list(
        ledger.conn.execute(
            f"""SELECT domain,k,value_json,semantic_hash FROM state
                WHERE status='CURRENT' AND epistemic='KNOWN' AND domain IN ({placeholders})""",
            domains,
        )
    )
    ranked = []
    for row in rows:
        value = json.loads(row["value_json"]) if row["value_json"] is not None else None
        score, _ = signal_score(value)
        ranked.append((float(score), f"{row['domain']}:{row['k']}", str(row["semantic_hash"])))
    ranked.sort(key=lambda x: (-x[0], x[1], x[2]))
    return tuple(x[1] for x in ranked[:budget])


def compare(ledger: StateLedger, rank: AuthoritativeRankIndexV3, budget: int) -> dict[str, Any] | None:
    expected = full_reference(ledger, DOMAINS, budget)
    got = rank.select(
        source_domains=DOMAINS,
        basis_epoch=ledger.epoch,
        max_candidates=budget,
        max_focus=min(4, budget),
        reentry_mode="NO_REENTRY",
    )
    if got.candidate_refs != expected:
        return {
            "epoch": ledger.epoch,
            "expected": list(expected),
            "actual": list(got.candidate_refs),
            "query_plan": list(got.query_plan),
            "selection_hash": got.selection_hash,
        }
    return None


def run_seed(seed: int, *, initial_keys: int, steps: int, budget: int) -> dict[str, Any]:
    rng = random.Random(seed)
    ledger = StateLedger()
    rank = AuthoritativeRankIndexV3(ledger)
    mismatches = []
    query_plan_uses_index = True
    try:
        initial = []
        for i in range(initial_keys):
            domain = DOMAINS[i % len(DOMAINS)]
            initial.append({
                "op": "SET", "domain": domain, "key": f"k{i:04d}",
                "value": random_signal_value(rng, i),
                "epistemic": "KNOWN" if rng.random() > 0.18 else rng.choice(["UNKNOWN", "CONFLICT"]),
                "status": "CURRENT",
            })
        ledger.append_event(
            event_id=f"seed-{seed}-initial", idem=f"seed-{seed}-initial",
            base_epoch=ledger.epoch, event_type="RANK_V3_RANDOM_INITIAL", writer="falsifier",
            ops=initial, committed_at=f"2026-08-10T01:{seed % 50:02d}:00Z",
        )
        first = rank.select(
            source_domains=DOMAINS, basis_epoch=ledger.epoch,
            max_candidates=budget, max_focus=min(4, budget),
        )
        query_plan_uses_index = all("idx_state_pulse_salience_known_current_v3" in p for p in first.query_plan if "SEARCH" in p or "SCAN" in p)
        mismatch = compare(ledger, rank, budget)
        if mismatch:
            mismatches.append({"step": -1, **mismatch})

        for step in range(steps):
            domain = rng.choice(DOMAINS)
            key = f"k{rng.randrange(initial_keys):04d}"
            r = rng.random()
            if r < 0.12:
                op = {"op": "RETRACT", "domain": domain, "key": key, "value": None,
                      "epistemic": "KNOWN", "status": "CURRENT"}
            elif r < 0.18:
                op = {"op": "SUPERSEDE", "domain": domain, "key": key, "value": random_signal_value(rng, step),
                      "epistemic": "KNOWN", "status": "CURRENT"}
            else:
                epistemic = "KNOWN" if rng.random() > 0.16 else rng.choice(["UNKNOWN", "CONFLICT"])
                op = {"op": "SET", "domain": domain, "key": key,
                      "value": random_signal_value(rng, 100000 + step),
                      "epistemic": epistemic, "status": "CURRENT"}
            ledger.append_event(
                event_id=f"seed-{seed}-step-{step}", idem=f"seed-{seed}-step-{step}",
                base_epoch=ledger.epoch, event_type="RANK_V3_RANDOM_MUTATION", writer="falsifier",
                ops=[op], committed_at=f"2026-08-10T02:{(step // 60) % 60:02d}:{step % 60:02d}Z",
            )
            mismatch = compare(ledger, rank, budget)
            if mismatch:
                mismatches.append({"step": step, **mismatch})
                break

        events = ledger.export_events()
        semantic_hash = ledger.semantic_state_hash
        trace_hash = ledger.trace_root_hash
        epoch = ledger.epoch
    finally:
        ledger.close()

    replay = StateLedger.replay(events)
    try:
        replay_rank = AuthoritativeRankIndexV3(replay)
        replay_mismatch = compare(replay, replay_rank, budget)
        replay_roots_pass = (
            replay.epoch == epoch and replay.semantic_state_hash == semantic_hash and replay.trace_root_hash == trace_hash
        )
        replay_index_verify = replay_rank.verify_index_semantics(domains=DOMAINS, max_candidates=budget)
    finally:
        replay.close()

    return {
        "seed": seed,
        "steps_completed": steps if not mismatches else mismatches[0]["step"] + 1,
        "mismatch_count": len(mismatches),
        "first_mismatch": mismatches[0] if mismatches else None,
        "replay_mismatch": replay_mismatch,
        "replay_roots_pass": replay_roots_pass,
        "replay_index_verify_pass": replay_index_verify["pass"],
        "query_plan_uses_index": query_plan_uses_index,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=12)
    ap.add_argument("--initial-keys", type=int, default=180)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--budget", type=int, default=64)
    ap.add_argument("--output")
    args = ap.parse_args()
    t0 = time.perf_counter()
    results = [
        run_seed(seed, initial_keys=max(32, args.initial_keys), steps=max(1, args.steps), budget=max(4, min(128, args.budget)))
        for seed in range(max(1, args.seeds))
    ]
    passed = all(
        r["mismatch_count"] == 0 and r["replay_mismatch"] is None and r["replay_roots_pass"]
        and r["replay_index_verify_pass"] and r["query_plan_uses_index"]
        for r in results
    )
    out = {
        "schema_version": "1.0",
        "experiment_class": "RANDOMIZED_DIFFERENTIAL_FALSIFIER",
        "implementation": "PULSE_AUTHORITATIVE_RANK_INDEX_V3",
        "configuration": {
            "seeds": len(results), "initial_keys": max(32, args.initial_keys),
            "mutation_steps_per_seed": max(1, args.steps), "candidate_budget": max(4, min(128, args.budget)),
        },
        "pass": passed,
        "total_transactions_checked": sum(r["steps_completed"] + 1 for r in results),
        "results": results,
        "elapsed_seconds": round(time.perf_counter() - t0, 6),
        "authority_boundary": "differential engineering evidence only; no semantic truth or effect authority",
        "limitations": [
            "Randomized synthetic StateLedger values, not live-FRANK task quality.",
            "The Python reference shares signal_score semantics with the candidate ancestry; independent semantic review remains required.",
            "SQLite/version portability and write amplification still require target-hardware measurements.",
        ],
    }
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if passed else 1)


if __name__ == "__main__":
    main()
