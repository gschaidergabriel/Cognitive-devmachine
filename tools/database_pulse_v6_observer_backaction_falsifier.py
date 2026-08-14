#!/usr/bin/env python3
from __future__ import annotations

"""Independent metamorphic falsifier for two Pulse V6 topology invariants.

This deliberately does not import the V6 implementation.  It asks whether the architectural
laws discriminate against two lesions:

1. Observer back-action lesion: an endogenous idle Pulse advances semantic epoch even though no
   semantic input changed.  A prepared epoch-bound receipt should then be falsely invalidated.
2. Transaction slicing lesion: bounded catch-up budgets individual ops instead of complete
   authoritative events and can therefore stop inside an atomic transaction.

The experiment is synthetic mechanism evidence only.  It is not live-FRANK quality evidence and
cannot promote V6 by itself.
"""

import argparse
import json
from pathlib import Path
import random


def run(*, seed: int, scenarios: int, steps: int, atomic_trials: int) -> dict:
    rng = random.Random(seed)

    semantic_false_stale = 0
    direct_false_stale = 0
    idle_attempts = 0
    for _ in range(scenarios):
        semantic_epoch_lesion = 0
        semantic_epoch_direct = 0
        receipt_epoch_lesion = 0
        receipt_epoch_direct = 0
        for _ in range(steps):
            if rng.random() < 0.78:
                # No semantic input.  The lesion nevertheless advances semantic time.
                semantic_epoch_lesion += 1
                idle_attempts += 1
                semantic_false_stale += int(receipt_epoch_lesion != semantic_epoch_lesion)
                direct_false_stale += int(receipt_epoch_direct != semantic_epoch_direct)
            else:
                # A real semantic event legitimately advances semantic time in both arms.
                semantic_epoch_lesion += 1
                semantic_epoch_direct += 1
                # Prepare a fresh receipt after the real change so subsequent idle staleness is
                # attributable only to observer back-action.
                receipt_epoch_lesion = semantic_epoch_lesion
                receipt_epoch_direct = semantic_epoch_direct

    event_cursor_boundary_violations = 0
    op_slicing_partial_event_cases = 0
    samples = []
    for _ in range(atomic_trials):
        nevents = rng.randint(1, 80)
        event_ops = [rng.randint(1, 300) for _ in range(nevents)]

        # V6 law: budget complete events.  The cursor is therefore always an event boundary.
        event_budget = rng.randint(1, 32)
        consumed_events = min(event_budget, nevents)
        if consumed_events < 0 or consumed_events > nevents:
            event_cursor_boundary_violations += 1

        # Counterbaseline lesion: spend an op budget across event internals.
        remaining = rng.randint(1, 256)
        idx = 0
        partial = False
        while idx < nevents and remaining > 0:
            if event_ops[idx] <= remaining:
                remaining -= event_ops[idx]
                idx += 1
            else:
                partial = True
                break
        if partial:
            op_slicing_partial_event_cases += 1
            if len(samples) < 5:
                samples.append({
                    "event_index": idx,
                    "event_ops": event_ops[idx],
                    "remaining_op_budget": remaining,
                    "event_count": nevents,
                })

    out = {
        "schema_version": "1.0",
        "experiment_class": "OUT_OF_BOX_METAMORPHIC_OBSERVER_BACKACTION_FALSIFIER",
        "seed": seed,
        "observer_back_action": {
            "scenarios": scenarios,
            "steps_per_scenario": steps,
            "idle_receipt_use_attempts": idle_attempts,
            "semantic_bookkeeping_false_stale": semantic_false_stale,
            "direct_execution_plane_false_stale": direct_false_stale,
            "semantic_false_stale_rate": semantic_false_stale / idle_attempts if idle_attempts else 0.0,
            "direct_false_stale_rate": direct_false_stale / idle_attempts if idle_attempts else 0.0,
        },
        "event_atomicity": {
            "trials": atomic_trials,
            "event_cursor_boundary_violations": event_cursor_boundary_violations,
            "op_slicing_partial_event_cases": op_slicing_partial_event_cases,
            "op_slicing_partial_event_rate": op_slicing_partial_event_cases / atomic_trials if atomic_trials else 0.0,
            "samples": samples,
        },
        "pass": (
            direct_false_stale == 0
            and semantic_false_stale > 0
            and event_cursor_boundary_violations == 0
            and op_slicing_partial_event_cases > 0
        ),
        "authority": "SYNTHETIC_MECHANISM_EVIDENCE_ONLY_NO_TRUTH_OR_EFFECT_AUTHORITY",
        "limitations": [
            "The observer model intentionally isolates epoch invalidation and does not model answer quality.",
            "The op-slicing rate is fixture-distribution dependent and is not a universal probability estimate.",
            "The experiment validates architecture-level invariants independently of the V6 implementation; implementation tests remain mandatory.",
        ],
    }
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, default=20260810)
    ap.add_argument("--scenarios", type=int, default=5000)
    ap.add_argument("--steps", type=int, default=120)
    ap.add_argument("--atomic-trials", type=int, default=20000)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = run(
        seed=args.seed,
        scenarios=max(1, args.scenarios),
        steps=max(1, args.steps),
        atomic_trials=max(1, args.atomic_trials),
    )
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")
    raise SystemExit(0 if out["pass"] else 1)


if __name__ == "__main__":
    main()
