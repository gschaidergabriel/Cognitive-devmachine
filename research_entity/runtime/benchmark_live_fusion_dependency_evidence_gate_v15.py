from __future__ import annotations

import json
import random

from live_fusion_dependency_evidence_gate_v15 import (
    DependencyEvidenceGateV15,
    DependencyWitness,
    ParentRouteObservation,
    INDEX_ONLY,
    NEXT_CHECKPOINT,
    INTERRUPT_NEXT_SAFE_POINT,
)

SEED = 20260810
N = 100000
random.seed(SEED)
gate = DependencyEvidenceGateV15()

# Synthetic mechanism falsifier only. Dependency-only high-impact conflicts are either
# truly causal or false edges. True edges may have hard evidence or only soft evidence.
# False edges can still look current and semantically plausible.
TRUE_EDGE_RATE = 0.50
HARD_GIVEN_TRUE = 0.80
SOFT_GIVEN_TRUE = 0.15
SOFT_GIVEN_FALSE = 0.05

stats = {
    "v14_parent": {"interrupts": 0, "true_interrupts": 0, "false_interrupts": 0},
    "v15_gate": {"interrupts": 0, "true_interrupts": 0, "false_interrupts": 0, "checkpoints": 0},
}
true_edges = 0
for i in range(N):
    true_edge = random.random() < TRUE_EDGE_RATE
    true_edges += int(true_edge)
    witness = None
    if true_edge:
        r = random.random()
        if r < HARD_GIVEN_TRUE:
            witness = "VERIFIED_CAUSAL"
        elif r < HARD_GIVEN_TRUE + SOFT_GIVEN_TRUE:
            witness = "ASSOCIATIVE_ONLY"
    elif random.random() < SOFT_GIVEN_FALSE:
        witness = "ASSOCIATIVE_ONLY"

    projected = witness is not None
    if projected:
        stats["v14_parent"]["interrupts"] += 1
        if true_edge:
            stats["v14_parent"]["true_interrupts"] += 1
        else:
            stats["v14_parent"]["false_interrupts"] += 1

    if not projected:
        continue

    obs = ParentRouteObservation(
        event_id=f"e{i}", worker_id="w", base_class=INDEX_ONLY,
        proposed_class=INTERRUPT_NEXT_SAFE_POINT, direct_overlap=False, dependency_only=True,
        conflict=True, impact=0.95, urgency=0.90,
        projection_current=True, projection_worker_match=True,
        projection_epoch="g1", projection_state_hash="s1",
    )
    row = gate.adjudicate(obs, [DependencyWitness("w", "dep", witness, True)])
    if row.gated_class == INTERRUPT_NEXT_SAFE_POINT:
        stats["v15_gate"]["interrupts"] += 1
        if true_edge:
            stats["v15_gate"]["true_interrupts"] += 1
        else:
            stats["v15_gate"]["false_interrupts"] += 1
    elif row.gated_class == NEXT_CHECKPOINT:
        stats["v15_gate"]["checkpoints"] += 1

for key in ("v14_parent", "v15_gate"):
    s = stats[key]
    s["interrupt_precision"] = (
        s["true_interrupts"] / s["interrupts"] if s["interrupts"] else 1.0
    )
    s["interrupt_recall_vs_true_edges"] = s["true_interrupts"] / true_edges

print(json.dumps({
    "evidence_class": "SYNTHETIC_MECHANISM_ONLY",
    "seed": SEED,
    "n": N,
    "true_edges": true_edges,
    "parameters": {
        "true_edge_rate": TRUE_EDGE_RATE,
        "hard_given_true": HARD_GIVEN_TRUE,
        "soft_given_true": SOFT_GIVEN_TRUE,
        "soft_given_false": SOFT_GIVEN_FALSE,
    },
    "results": stats,
}, indent=2, sort_keys=True))
