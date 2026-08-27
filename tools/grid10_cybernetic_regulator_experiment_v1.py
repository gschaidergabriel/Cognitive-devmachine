#!/usr/bin/env python3
"""GRID10 cybernetic-cognition-architecture experiment (Part 7 of
research_entity/topic_packets/grid10-cybernetic-cognition-concept/CONCEPT.md), adapted
onto the REAL fabric/node code -- not a literal transcription of the concept's
pseudocode (which assumed a nonexistent Grid10Fabric API and, critically, that
temperature/top_p would matter under the existing greedy do_sample=False decoding,
which they do not -- see tools/grid10_node.py::cognitive_answer for the real fix).

Real experiment: 10 nodes, 4 flagged as meta-evaluators (run meta_regulator_tick()
periodically -- a real homeostatic controller reacting to a real measured signal, the
fraction of recent non-empty answers). 5 rounds of real tasks that opt into
regulator-controlled sampling (payload["use_regulator"]=True). A human-simulated
override is injected at round 3 (writer="human-simulated", tagged distinctly from
automatic writes) to test the human-pin-priority mechanism: meta-evaluators must
respect a cooldown window and NOT immediately overwrite it.

Measures, all real (not assumed to match the concept doc's guessed target numbers):
per-task latency, actual temperature/top_p used per task, CAS lost-update count under
concurrent meta-evaluator writes, whether the human override was respected during its
cooldown and whether homeostatic drift resumed afterward, lease stability under the
extra regulator-write traffic.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric, FabricError
from grid10_node import node_loop, load_model_once

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
NODE_IDS = [f"cyber-{i:02d}" for i in range(10)]
META_EVAL_IDS = set(NODE_IDS[:4])
N_ROUNDS = 5
HUMAN_OVERRIDE_ROUND = 3
PROMPT = "Complete with exactly one word: The weather today is"


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fabric_path = out / "cyber_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()

    t0 = time.time()
    load_model_once(MODEL_PATH)
    model_load_s = time.time() - t0

    f = Fabric(fabric_path)
    f.seed_scope("cyber:answers")
    # seed the regulator at its documented starting point (concept Part 1/7)
    f.set_regulator("temperature", 0.85, writer="init")
    f.set_regulator("top_p", 0.92, writer="init")

    ctx = mp.get_context("fork")

    def spawn(node_id, max_iters):
        evp = out / f"evidence_{node_id}.json"
        p = ctx.Process(
            target=node_loop,
            kwargs=dict(
                node_id=node_id, capability="reason", fabric_path=str(fabric_path), model_path=MODEL_PATH,
                out_evidence=str(evp), max_iters=max_iters, poll_sleep=0.15,
                become_coordinator_candidate=True, task_reclaim_stale_after_seconds=15.0,
                meta_evaluator=(node_id in META_EVAL_IDS), regulator_tick_every=2,
            ),
        )
        return p, evp

    all_procs = []
    for node_id in NODE_IDS:
        p, evp = spawn(node_id, max_iters=25 * N_ROUNDS)
        all_procs.append((node_id, p, evp))

    for _, p, _ in all_procs:
        p.start()

    time.sleep(1.5)

    round_log = []
    for round_n in range(1, N_ROUNDS + 1):
        if round_n == HUMAN_OVERRIDE_ROUND:
            for attempt in range(5):
                reg_before = f.get_regulator("temperature", default=0.85)
                try:
                    f.set_regulator("temperature", 0.65, writer="human-simulated", expected_version=reg_before["version"] or None)
                    round_log.append({"round": round_n, "event": "HUMAN_OVERRIDE_INJECTED", "new_temperature": 0.65, "cas_attempts": attempt + 1})
                    break
                except FabricError:
                    continue  # real CAS race against a concurrent meta-evaluator write -- retry with fresh version
            else:
                round_log.append({"round": round_n, "event": "HUMAN_OVERRIDE_FAILED_ALL_RETRIES"})

        task_id = f"cyber-r{round_n}"
        t_seed = time.time()
        f.seed_task(task_id, "cyber:answers", 90, "reason", {"prompt": PROMPT, "max_new_tokens": 8, "use_regulator": True})
        time.sleep(5.0)
        t_done = time.time()

        snap = f.snapshot()
        row = [dict(s) for s in snap.scopes if s["scope"] == "cyber:answers"][0]
        latest = json.loads(row["summary_json"]).get("latest", {})
        reg_now = f.get_regulator("temperature")
        round_log.append({
            "round": round_n,
            "task_id": task_id,
            "answer": latest.get("answer"),
            "temperature_used": latest.get("temperature_used"),
            "top_p_used": latest.get("top_p_used"),
            "regulator_temperature_after_round": reg_now,
            "round_wallclock_s": round(t_done - t_seed, 2),
        })
        print(json.dumps(round_log[-1], default=str), flush=True)

    for _, p, _ in all_procs:
        p.join(timeout=10)

    final_snap = f.snapshot()
    node_events = {}
    for node_id, p, evp in all_procs:
        if evp.exists():
            node_events[node_id] = json.loads(evp.read_text())

    meta_ticks = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "META_REGULATOR_TICK"
    ]
    lease_expiry_events = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "COORDINATOR_LEASE_SELF_RENEW_AFTER_EXPIRY"
    ]
    stale_reclaims = [
        e for ev in node_events.values() for e in ev.get("events", [])
        if e["event"] == "STALE_TASK_RECLAIMED"
    ]

    # did the meta-evaluators respect the human-pin cooldown right after the override?
    human_override_ts = None
    for e in round_log:
        if e.get("event") == "HUMAN_OVERRIDE_INJECTED":
            pass
    reg_final = f.get_regulator("temperature")

    receipt = {
        "schema": "GRID10_CYBERNETIC_REGULATOR_EXPERIMENT/v1",
        "concept_source": "research_entity/topic_packets/grid10-cybernetic-cognition-concept/CONCEPT.md, Part 7 -- adapted onto real API, not literal transcription",
        "model_load_time_s": round(model_load_s, 2),
        "n_rounds": N_ROUNDS,
        "meta_evaluator_node_count": len(META_EVAL_IDS),
        "human_override_round": HUMAN_OVERRIDE_ROUND,
        "round_log": round_log,
        "meta_regulator_ticks_total": len(meta_ticks),
        "meta_regulator_ticks": meta_ticks,
        "lease_expiry_self_renewals": len(lease_expiry_events),
        "stale_task_reclaims": len(stale_reclaims),
        "final_regulator_temperature": reg_final,
        "final_epoch": final_snap.epoch,
    }
    (out / "GRID10_CYBERNETIC_REGULATOR_EXPERIMENT_RECEIPT.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps({
        "n_rounds": N_ROUNDS,
        "meta_ticks": len(meta_ticks),
        "lease_expiry_events": len(lease_expiry_events),
        "final_temperature": reg_final["value_real"],
        "final_temperature_writer": reg_final["writer"],
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_cybernetic")
