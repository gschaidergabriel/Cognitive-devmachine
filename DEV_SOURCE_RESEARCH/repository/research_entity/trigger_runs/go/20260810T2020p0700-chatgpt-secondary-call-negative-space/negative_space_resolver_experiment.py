#!/usr/bin/env python3
"""GO out-of-box experiment: adversarial negative-space call resolver falsifier.

Uses the 27 exact target+arity identities reconstructed from the current G9 V3 main cycle.
The current ClayCode inventory reports 26 ordinary unresolved signatures plus one separate
Needle.execute effect-boundary signature. This experiment does NOT invent production
CallContracts. It perturbs the 26 ordinary unresolved identities with deliberately misleading
namespace/suffix and wrong-arity shadows and compares resolver policies.

Research-only. No package/canonical promotion and no effect authority.
"""
from __future__ import annotations

import hashlib
import json
import random
import statistics

SEED = 20260810
TRIALS = 1000

PAIRS = [
    ("resolve_latest", 3),
    ("task", 1),
    ("load_dialects", 1),
    ("verify", 5),
    ("normalize", 1),
    ("observe_changes", 2),
    ("apply_incremental", 1),
    ("task_relevant", 1),
    ("state.query", 1),
    ("graph.project", 1),
    ("preserve_conflict_unknown", 1),
    ("state.open_pressures", 1),
    ("emerge", 1),
    ("gwt.select", 1),
    ("state.answer_capsule", 1),
    ("cognitive_choice", 1),
    ("EffectIntent", 1),
    ("Needle.execute", 1),
    ("verify", 1),
    ("causal_credit", 2),
    ("frank_reward.derive_typed_reward_outcome_evidence", 3),
    ("frank_reward.update", 1),
    ("frank_reward.control", 2),
    ("admit_slow_plasticity", 3),
    ("Delta", 1),
    ("reenter", 1),
    ("meta.analyze_explicit_turn", 0),
]


def strict_exact(query, candidates):
    hits = [c for c in candidates if c["target"] == query[0] and c["arity"] == query[1]]
    return hits[0] if len(hits) == 1 else None


def suffix_first(query, candidates):
    hits = [
        c
        for c in candidates
        if (c["target"] == query[0] or c["target"].endswith("." + query[0]))
        and c["arity"] == query[1]
    ]
    return hits[0] if hits else None


def target_only_first(query, candidates):
    hits = [c for c in candidates if c["target"] == query[0]]
    return hits[0] if hits else None


def main() -> int:
    assert len(PAIRS) == 27 and len(set(PAIRS)) == 27
    unresolved = [pair for pair in PAIRS if pair[0] != "Needle.execute"]
    assert len(unresolved) == 26

    rng = random.Random(SEED)
    strict_false = []
    suffix_false = []
    arity_false = []

    for _ in range(TRIALS):
        candidates = []
        for target, arity in unresolved:
            # Current inventory has no exact declared contract for these calls. Add only
            # adversarial non-exact alternatives; they must never become authority.
            candidates.append(
                {"target": "Shadow." + target, "arity": arity, "kind": "suffix_shadow"}
            )
            candidates.append(
                {"target": target, "arity": arity + 1, "kind": "wrong_arity_shadow"}
            )
        rng.shuffle(candidates)

        strict_count = 0
        suffix_count = 0
        arity_count = 0
        for query in unresolved:
            strict_count += int(strict_exact(query, candidates) is not None)
            suffix_count += int(suffix_first(query, candidates) is not None)
            arity_count += int(target_only_first(query, candidates) is not None)
        strict_false.append(strict_count)
        suffix_false.append(suffix_count)
        arity_false.append(arity_count)

    report = {
        "schema_version": "1.0",
        "experiment": "GO_OOB_CALL_BINDING_NEGATIVE_SPACE",
        "status": "PASS_RESEARCH_PROXY_NO_PROMOTION",
        "seed": SEED,
        "trials": TRIALS,
        "basis": {
            "real_cycle_unique_target_arity_pairs": 27,
            "unresolved_non_effect_pairs": 26,
            "needle_effect_pair": 1,
        },
        "candidate_perturbation_per_unresolved": [
            "same-arity namespace/suffix shadow",
            "exact-target wrong-arity shadow",
        ],
        "false_admissions_per_trial": {
            "strict_exact_target_plus_arity": {
                "min": min(strict_false),
                "median": statistics.median(strict_false),
                "max": max(strict_false),
            },
            "suffix_first_same_arity": {
                "min": min(suffix_false),
                "median": statistics.median(suffix_false),
                "max": max(suffix_false),
            },
            "target_only_ignores_arity": {
                "min": min(arity_false),
                "median": statistics.median(arity_false),
                "max": max(arity_false),
            },
        },
        "interpretation": (
            "Synthetic adversarial resolver test over real G9 call identities. It tests "
            "resolver policy only; it is not evidence that these shadow declarations exist "
            "in current ClayCode."
        ),
        "effect_authority": "NONE",
        "promotion": "NONE",
        "wp03_status": "OPEN",
        "base_status": "NOT_PASS",
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"))
    report["result_sha256"] = hashlib.sha256(canonical.encode()).hexdigest()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
