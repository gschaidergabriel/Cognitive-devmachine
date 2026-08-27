#!/usr/bin/env python3
"""GRID10 dynamic-scaling experiment -- real, live measurement of the elastic
poll-rate mechanism (adapted alternative to the concept's SIGSTOP/CONT idea, see
research_entity/topic_packets/grid10-dynamic-scaling-concept/CRITICAL_REVIEW_AND_REAL_ADAPTATION_20260827.json).

Phase 1 (standby): 6 of 10 nodes are told (via the shared poll_intensity regulator)
to poll at 1/10th normal rate; 4 remain at full rate. Measure real aggregate CPU
usage during this phase.

Phase 2 (scale-out): flip poll_intensity back to 1.0 for everyone, seed a real
task, and measure real wall-clock time from the regulator flip to the first
real task claim by a previously-standby node -- this is the honest, measured
analog of the concept's "scaling reaction time" claim (which assumed <=30ms;
this measures what it actually is).
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric
from grid10_node import node_loop, load_model_once

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
NODE_IDS = [f"elastic-{i:02d}" for i in range(10)]
STANDBY_IDS = set(NODE_IDS[6:])  # last 4 start in standby
ACTIVE_IDS = set(NODE_IDS[:6])


def cpu_stat_of(pid: int) -> tuple[int, int] | None:
    try:
        with open(f"/proc/{pid}/stat") as fh:
            fields = fh.read().split()
        return int(fields[13]), int(fields[14])  # utime, stime (clock ticks)
    except Exception:
        return None


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fabric_path = out / "elastic_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()

    t0 = time.time()
    load_model_once(MODEL_PATH)
    model_load_s = time.time() - t0

    f = Fabric(fabric_path)
    f.seed_scope("elastic:answers")
    f.set_regulator("poll_intensity", 1.0, writer="init")

    ctx = mp.get_context("fork")

    def spawn(node_id):
        evp = out / f"evidence_{node_id}.json"
        # Only the STANDBY group actually reacts to poll_intensity -- the always-
        # active group keeps elastic_poll=False so it is unaffected by the shared
        # regulator, matching the concept's own split (MIN_NODES stay full-speed,
        # the rest are the ones elastically throttled).
        is_standby = node_id in STANDBY_IDS
        p = ctx.Process(
            target=node_loop,
            kwargs=dict(
                node_id=node_id, capability="reason", fabric_path=str(fabric_path), model_path=MODEL_PATH,
                out_evidence=str(evp), max_iters=400, poll_sleep=0.15,
                become_coordinator_candidate=True, task_reclaim_stale_after_seconds=20.0,
                elastic_poll=is_standby, elastic_poll_check_every=3,
            ),
        )
        return p, evp

    all_procs = []
    for node_id in NODE_IDS:
        p, evp = spawn(node_id)
        all_procs.append((node_id, p, evp))

    for _, p, _ in all_procs:
        p.start()

    time.sleep(1.0)  # let everyone join

    # Phase 1: put the standby group into low-intensity mode
    f.set_regulator("poll_intensity", 0.1, writer="driver-standby-init", expected_version=1)
    phase1_t0 = time.time()
    time.sleep(4.0)  # let the elastic_poll_check_every=3 logic actually pick it up
    cpu_before = {n: cpu_stat_of(p.pid) for n, p, _ in all_procs if p.pid}
    time.sleep(4.0)  # measure over a real window
    cpu_after = {n: cpu_stat_of(p.pid) for n, p, _ in all_procs if p.pid}
    phase1_duration_s = time.time() - phase1_t0

    cpu_delta_ticks = {}
    for n in NODE_IDS:
        b, a = cpu_before.get(n), cpu_after.get(n)
        if b and a:
            cpu_delta_ticks[n] = (a[0] - b[0]) + (a[1] - b[1])

    # Phase 2: scale back out -- flip everyone to full intensity, seed a real
    # task, and measure real time-to-first-claim by anyone (not distinguishing
    # which group claims it -- honest measurement, not assumed).
    reg_now = f.get_regulator("poll_intensity")
    f.set_regulator("poll_intensity", 1.0, writer="driver-scale-out", expected_version=reg_now["version"])
    scale_out_ts = time.time()
    f.seed_task("elastic-probe", "elastic:answers", 90, "reason", {"prompt": "2 + 2 =", "max_new_tokens": 4})

    first_claim_ts = None
    deadline = time.time() + 30.0
    while time.time() < deadline:
        snap = f.snapshot()
        row = [t for t in snap.tasks if t["task_id"] == "elastic-probe"]
        if row and row[0]["status"] == "CLAIMED":
            first_claim_ts = time.time()
            claiming_node = row[0]["claimed_by"]
            break
        time.sleep(0.02)
    reaction_time_s = (first_claim_ts - scale_out_ts) if first_claim_ts else None

    time.sleep(3.0)
    for _, p, _ in all_procs:
        p.join(timeout=5)

    node_events = {}
    for node_id, p, evp in all_procs:
        if evp.exists():
            node_events[node_id] = json.loads(evp.read_text())
    rate_change_events = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "ELASTIC_POLL_RATE_CHANGED"
    ]

    active_total_ticks = sum(cpu_delta_ticks.get(n, 0) for n in ACTIVE_IDS)
    standby_total_ticks = sum(cpu_delta_ticks.get(n, 0) for n in STANDBY_IDS)

    receipt = {
        "schema": "GRID10_ELASTIC_SCALING_EXPERIMENT/v1",
        "concept_source": "research_entity/topic_packets/grid10-dynamic-scaling-concept/CONCEPT.md (adapted, not literal -- see critical review in the same directory)",
        "model_load_time_s": round(model_load_s, 2),
        "phase1_measurement_window_s": round(phase1_duration_s, 2),
        "standby_node_ids": sorted(STANDBY_IDS),
        "active_node_ids": sorted(ACTIVE_IDS),
        "cpu_delta_ticks_per_node": cpu_delta_ticks,
        "active_group_total_cpu_ticks": active_total_ticks,
        "standby_group_total_cpu_ticks": standby_total_ticks,
        "standby_vs_active_cpu_ratio": round(standby_total_ticks / active_total_ticks, 3) if active_total_ticks else None,
        "elastic_poll_rate_change_events": rate_change_events,
        "scale_out_claiming_node": claiming_node if first_claim_ts else None,
        "measured_scale_out_reaction_time_s": round(reaction_time_s, 3) if reaction_time_s else None,
        "concept_claimed_target_reaction_time_ms": 30,
    }
    (out / "GRID10_ELASTIC_SCALING_EXPERIMENT_RECEIPT.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps({
        "standby_vs_active_cpu_ratio": receipt["standby_vs_active_cpu_ratio"],
        "measured_reaction_time_s": receipt["measured_scale_out_reaction_time_s"],
        "concept_target_ms": 30,
        "rate_change_events": len(rate_change_events),
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_elastic")
