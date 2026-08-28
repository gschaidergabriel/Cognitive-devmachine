#!/usr/bin/env python3
"""GRID10 use-case 1 (autonomous task/processing pipelines) -- real, live experiment.

Tests the coordinator's literal claim for this use case: "bei Fehler/Absturz eines
Agenten sichert die Lease-/CAS-Logik den Datenzustand, verbleibende Knoten fuehren
ohne Datenverlust fort" (on agent failure/crash, the lease/CAS logic preserves data
state, remaining nodes continue without data loss).

This was FALSE for ordinary task claims before 2026-08-27 (verified empirically: a
claimed-but-uncompleted task from a dead node was stuck forever, no reclaim path
existed). Fixed today: Fabric.runtime_reclaim_stale_claims() + wired into
grid10_node.py's poll loop. This script is the real, live, multi-process proof that
the fix actually closes the gap end to end -- not a unit test against the fabric in
isolation, a REAL SIGKILL against a REAL forked process running REAL model inference,
with a second real process completing the orphaned work afterward.

Pipeline modeled: a 3-stage "code review" pipeline.
  Stage "review" (parallel, 3 independent tasks) -> Stage "aggregate" (1 task, only
  seeded once all 3 review results are committed) -> final verdict.
One of the 3 review tasks is deliberately orphaned by a real SIGKILL against its
claiming process's real PID, mid-flight, before it can emit a result.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import signal
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric, FabricError, result_packet, summary_packet
from grid10_node import node_loop, load_model_once

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"

REVIEW_ITEMS = [
    ("review-1", "Code diff adds a null check before dereferencing a pointer. Is this a reasonable safety fix? Answer YES or NO."),
    ("review-2", "Code diff removes an existing null check before dereferencing a pointer. Is this a reasonable safety fix? Answer YES or NO."),
    ("review-3", "Code diff renames a local variable with no behavior change. Is this a reasonable safety fix? Answer YES or NO."),
]


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fabric_path = out / "pipeline_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()

    t0 = time.time()
    load_model_once(MODEL_PATH)
    model_load_s = time.time() - t0

    f = Fabric(fabric_path)
    f.seed_scope("pipeline:review")
    f.seed_scope("pipeline:aggregate")
    for task_id, prompt in REVIEW_ITEMS:
        f.seed_task(task_id, "pipeline:review", 90, "reason", {"prompt": prompt})

    ctx = mp.get_context("fork")

    def spawn(node_id, max_iters=40):
        evp = out / f"evidence_{node_id}.json"
        p = ctx.Process(
            target=node_loop,
            kwargs=dict(
                node_id=node_id, capability="reason", fabric_path=str(fabric_path), model_path=MODEL_PATH,
                out_evidence=str(evp), max_iters=max_iters, poll_sleep=0.15,
                become_coordinator_candidate=True, task_reclaim_stale_after_seconds=3.0,
            ),
        )
        return p, evp

    # Phase 1: launch ONE node only, deliberately alone, so it is forced to claim
    # review-1 (the highest-priority OPEN task) -- this makes the victim predictable.
    victim_proc, victim_evp = spawn("victim-node")
    victim_proc.start()

    # poll until the fabric shows review-1 actually CLAIMED by the victim (real,
    # observed state -- not just assumed timing)
    claimed_by_victim = False
    for _ in range(50):
        snap = f.snapshot()
        row = [dict(t) for t in snap.tasks if t["task_id"] == "review-1"]
        if row and row[0]["status"] == "CLAIMED" and row[0]["claimed_by"] == "victim-node":
            claimed_by_victim = True
            break
        time.sleep(0.1)

    if not claimed_by_victim:
        print(json.dumps({"FATAL": "victim never claimed review-1 in time"}))
        victim_proc.terminate()
        return

    killed_pid = victim_proc.pid
    kill_ts = time.time()
    os.kill(killed_pid, signal.SIGKILL)
    victim_proc.join(timeout=3)

    pre_rescue_snapshot = f.snapshot()
    review1_row_after_kill = [dict(t) for t in pre_rescue_snapshot.tasks if t["task_id"] == "review-1"][0]

    # Phase 2: launch survivor nodes for the remaining two review tasks AND a rescuer
    # that will (per the fix) reclaim review-1 once stale_after_seconds elapses.
    survivors = []
    for node_id in ("survivor-A", "survivor-B", "rescuer-C"):
        p, evp = spawn(node_id, max_iters=60)
        p.start()
        survivors.append((node_id, p, evp))

    # give real wall-clock time for: heartbeats, staleness threshold (3.0s) to pass,
    # reclaim scan, re-claim by a live node, real model decode, commit
    time.sleep(8.0)

    for node_id, p, evp in survivors:
        p.join(timeout=15)

    final_snap = f.snapshot()
    review1_final = [dict(t) for t in final_snap.tasks if t["task_id"] == "review-1"][0]

    node_events = {}
    for node_id, evp in [("victim-node", victim_evp)] + [(n, e) for n, _, e in survivors]:
        if evp.exists():
            node_events[node_id] = json.loads(evp.read_text())

    reclaim_events = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "STALE_TASK_RECLAIMED"
    ]
    review1_reclaimed_result = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "NODE_RESULT_EMITTED" and e.get("task_id") == "review-1"
    ]

    # Did the OUTBOX/coordinator-commit path actually finish for review-1 (i.e. is
    # there a real, committed answer for it now, not just "reclaimed but stuck again")?
    scope_row = [dict(s) for s in final_snap.scopes if s["scope"] == "pipeline:review"][0]
    scope_summary = json.loads(scope_row["summary_json"])
    committed_task_ids_seen = []
    latest = scope_summary.get("latest", {})
    if latest.get("task_id"):
        committed_task_ids_seen.append(latest["task_id"])
    prev = scope_summary.get("previous", {})
    while isinstance(prev, dict) and prev.get("latest", {}).get("task_id"):
        committed_task_ids_seen.append(prev["latest"]["task_id"])
        prev = prev.get("previous", {})

    receipt = {
        "schema": "GRID10_PIPELINE_RESILIENCE_EXPERIMENT/v1",
        "use_case": "autonomous_task_processing_pipelines",
        "claim_under_test": "on agent crash mid-task, the lease/CAS logic preserves data state and remaining nodes continue without data loss",
        "prior_finding_this_fixes": "before 2026-08-27, this was FALSE for ordinary (non-coordinator) task claims -- verified empirically that a claimed-but-uncompleted task from a dead node was stuck forever with no reclaim path",
        "model_load_time_s": round(model_load_s, 2),
        "victim_pid_killed": killed_pid,
        "victim_kill_ts": kill_ts,
        "review1_status_immediately_after_kill": review1_row_after_kill,
        "review1_status_after_recovery_window": review1_final,
        "stale_task_reclaimed_events": reclaim_events,
        "review1_completed_by_a_different_node_after_reclaim": review1_reclaimed_result,
        "committed_task_ids_seen_in_final_scope_summary_chain": committed_task_ids_seen,
        "pass": (
            review1_row_after_kill["status"] == "CLAIMED"
            and review1_row_after_kill["claimed_by"] == "victim-node"
            and len(reclaim_events) >= 1
            and any(e["task_id"] == "review-1" for e in reclaim_events)
            and review1_final["status"] in ("CLAIMED", "OPEN")  # OPEN would mean still unclaimed (real gap); CLAIMED by someone else means recovery worked
            and len(review1_reclaimed_result) >= 1
            and "review-1" in committed_task_ids_seen
        ),
    }
    (out / "GRID10_PIPELINE_RESILIENCE_EXPERIMENT_RECEIPT.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps({
        "pass": receipt["pass"],
        "review1_status_after_kill": review1_row_after_kill["status"],
        "reclaim_events": len(reclaim_events),
        "review1_completed_after_recovery": len(review1_reclaimed_result) >= 1,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_pipeline_resilience")
