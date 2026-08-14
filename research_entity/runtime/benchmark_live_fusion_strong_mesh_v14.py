from __future__ import annotations

import json

from live_fusion_reentry_v13 import DELIVERY_INDEX, DELIVERY_INTERRUPT, LiveDelta, WorkerView
from live_fusion_strong_mesh_v14 import DependencyProjection, StrongMeshShadowRouter


def delta(event_id, *, branches=(), keys=(), work=(), claims=(), impact=.7, urgency=.5, conflict=False):
    return LiveDelta(
        event_id=event_id, source="bench", source_seq=int(event_id[1:]), source_epoch="bench-1",
        semantic_keys=tuple(keys), affected_branches=tuple(branches), novelty="CONTRADICTS" if conflict else "REFINES",
        impact=impact, urgency=urgency, conflict=conflict, payload={"id": event_id}, applicability="CURRENT_MATERIAL",
        affected_work=tuple(work), affected_claims=tuple(claims),
    )


def worker(worker_id, branch, *, keys=(), work=(), claims=()):
    return WorkerView(worker_id=worker_id, branches=(branch,), active_keys=tuple(keys), active_work=tuple(work),
                      active_claims=tuple(claims), subscription_revision="bench-r1", plan_revision="p1")


def projection(worker_id, *, keys=(), work=(), claims=()):
    return DependencyProjection(worker_id=worker_id, graph_epoch="bench-g1", state_hash="bench-s1",
                                semantic_keys=tuple(keys), work_ids=tuple(work), claim_ids=tuple(claims),
                                provenance_refs=("fixture:adjudicated",), current=True)


def metrics(predicted, required):
    tp = len(predicted & required)
    return {
        "predicted": len(predicted), "required": len(required), "tp": tp,
        "recall": tp / len(required) if required else 1.0,
        "precision": tp / len(predicted) if predicted else (1.0 if not required else 0.0),
    }


router = StrongMeshShadowRouter()
workers = {
    "udb": worker("udb", "unifieddb", keys=("pulse",), work=("WP-UDB",)),
    "graph": worker("graph", "claygraph", keys=("edge",)),
    "harness": worker("harness", "harness", work=("WP-H1",)),
    "frank": worker("frank", "frank", claims=("CLAIM-LOOP",)),
    "gwt": worker("gwt", "gwt", keys=("ignition",)),
    "claycode": worker("claycode", "claycode", keys=("parser",)),
}
projections = {
    "udb": projection("udb"),
    "graph": projection("graph", work=("WP-UDB",)),
    "harness": projection("harness", keys=("pulse",), claims=("CLAIM-LOOP",)),
    "frank": projection("frank", work=("WP-H1",)),
    "gwt": projection("gwt", claims=("CLAIM-LOOP",)),
    "claycode": projection("claycode"),
}
deltas = [
    delta("d1", keys=("pulse",), work=("WP-UDB",), impact=.95, urgency=.9, conflict=True),
    delta("d2", claims=("CLAIM-LOOP",), impact=.9, urgency=.8, conflict=True),
    delta("d3", branches=("harness",), impact=.1, urgency=.1),
    delta("d4", branches=("claycode",), keys=("parser",), impact=.8, urgency=.6),
    delta("d5", work=("WP-H1",), impact=.8, urgency=.6),
    delta("d6", branches=("gwt",), keys=("ignition",), impact=.7, urgency=.6),
    delta("d7", branches=("unifieddb",), impact=.15, urgency=.15),
    delta("d8", keys=("edge",), branches=("claygraph",), impact=.75, urgency=.55),
]

# Frozen adjudicated routing need for this synthetic mechanism fixture.
required_active = {
    ("d1", "udb"), ("d1", "graph"), ("d1", "harness"),
    ("d2", "frank"), ("d2", "harness"), ("d2", "gwt"),
    ("d4", "claycode"), ("d5", "harness"), ("d5", "frank"),
    ("d6", "gwt"), ("d8", "graph"),
}
required_interrupt = {
    ("d1", "udb"), ("d1", "graph"), ("d1", "harness"),
    ("d2", "frank"), ("d2", "harness"), ("d2", "gwt"),
}

rows = []
for d in deltas:
    for wid, w in workers.items():
        rows.append(router.plan(d, w, projections[wid]))

base_active = {(r.event_id, r.worker_id) for r in rows if r.base_class != DELIVERY_INDEX}
candidate_active = {(r.event_id, r.worker_id) for r in rows if r.candidate_class != DELIVERY_INDEX}
base_interrupt = {(r.event_id, r.worker_id) for r in rows if r.base_class == DELIVERY_INTERRUPT}
candidate_interrupt = {(r.event_id, r.worker_id) for r in rows if r.candidate_class == DELIVERY_INTERRUPT}

out = {
    "evidence_class": "SYNTHETIC_MECHANISM_ONLY",
    "rows": len(rows),
    "base_active": metrics(base_active, required_active),
    "candidate_active": metrics(candidate_active, required_active),
    "base_interrupt": metrics(base_interrupt, required_interrupt),
    "candidate_interrupt": metrics(candidate_interrupt, required_interrupt),
    "base_missed_active": sorted(required_active - base_active),
    "candidate_missed_active": sorted(required_active - candidate_active),
    "base_extra_active": sorted(base_active - required_active),
    "candidate_extra_active": sorted(candidate_active - required_active),
    "shadow_changes": router.summarize(rows),
}
print(json.dumps(out, indent=2, sort_keys=True))
