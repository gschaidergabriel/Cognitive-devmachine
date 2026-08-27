#!/usr/bin/env python3
"""GRID10 world-model simulation v2 -- corrects two real bugs found in v1 during review:

BUG 1 (v1): classify_evidence_strength() used naive substring matching, so "confirmed"
matched inside "unconfirmed" and inside "neither confirmed" (the literal opposite of
confirming evidence), producing false STRONG classifications.

BUG 2 (v1): the code comment claimed collapse requires "every STRONG tick agreed on the
same alternative", but the actual code never checked agreement -- ANY strong-classified
tick triggered COLLAPSE regardless of which alternative it supported. Also, evidence
direction (which of the two named alternatives a piece of evidence supports) was never
explicitly encoded at all, only inferred implicitly (incorrectly) from marker words.

v2 fix: every evidence item is now an explicit (text, strength, supports_index) triple,
authored by hand per-scope (supports_index indexes into WORLD[scope]['alternatives']).
COLLAPSE_VALID now requires >=1 STRONG item AND all STRONG items (seen so far) agreeing
on the same supports_index; if STRONG items disagree (genuine conflicting strong
evidence), that now correctly stays PRESERVE_BRANCHES (a real, distinct case that v1
could not represent at all).

Everything else (fabric, node, multi-tick GWT broadcast/uptake, 10 real processes) is
UNCHANGED from v1 and reuses the same proven grid10_fabric.py / grid10_node.py.

Usage: python3 run_grid10_world_model_simulation_v2.py <out_dir> [n_ticks]
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric, FabricError, result_packet, summary_packet
from grid10_node import node_loop, load_model_once

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
NODE_IDS = [f"xeno-{i:02d}" for i in range(10)]

WORLD = {
    "region:north": {"question": "stockpile status", "alternatives": ["SUFFICIENT", "CRITICAL"]},
    "region:south": {"question": "stockpile status", "alternatives": ["SUFFICIENT", "CRITICAL"]},
    "region:east": {"question": "stockpile status", "alternatives": ["SUFFICIENT", "CRITICAL"]},
    "weather:forecast": {"question": "storm arrival", "alternatives": ["CLEAR", "STORM_ARRIVING"]},
    "threat:assessment": {"question": "hostile activity", "alternatives": ["FALSE_POSITIVE", "CONFIRMED"]},
}
REGIONAL_SCOPES = list(WORLD.keys())

# Each item: (evidence_text, strength, supports_index). strength in {STRONG, WEAK, NEUTRAL}.
# supports_index indexes WORLD[scope]['alternatives'] -- which alternative this evidence
# points toward (only meaningful when strength != NEUTRAL; NEUTRAL items still carry an
# indicative supports_index for readability but it is not used for the collapse decision).
EVIDENCE_SCRIPT = {
    "region:north": [
        ("A supply report notes stock levels are within normal range this week.", "WEAK", 0),
        ("A separate, unverified report suggests stock may be somewhat lower, cause unclear.", "WEAK", 1),
        ("No new supply data available this cycle.", "NEUTRAL", 0),
        ("Two depots report conflicting counts; neither has been independently verified.", "NEUTRAL", 1),
        ("A partial recount shows numbers close to normal again, but the recount itself is informal.", "WEAK", 0),
        ("Still no confirmed audit either way.", "NEUTRAL", 0),
    ],
    "region:south": [
        ("An initial spot-check suggests stock may be running low.", "WEAK", 1),
        ("A formal audit confirms stock has dropped below the safety threshold.", "STRONG", 1),
        ("A second, independent audit team reaches the same conclusion: below threshold.", "STRONG", 1),
        ("Warehouse logs, cross-checked against the audits, corroborate the shortfall.", "STRONG", 1),
        ("No new information contradicts the two confirmed audits.", "NEUTRAL", 1),
        ("A third confirmation arrives, consistent with the prior two audits.", "STRONG", 1),
    ],
    "region:east": [
        ("Routine check shows stock at expected levels.", "WEAK", 0),
        ("Nothing unusual reported this cycle.", "NEUTRAL", 0),
        ("A minor discrepancy noted but attributed to counting error.", "WEAK", 0),
        ("Two independent formal counts both confirm stock is at normal levels.", "STRONG", 0),
        ("No concerns raised in this cycle's report.", "NEUTRAL", 0),
        ("Levels remain steady per the latest formally confirmed count.", "STRONG", 0),
    ],
    "weather:forecast": [
        ("Satellite imagery shows clear skies over the region.", "WEAK", 0),
        ("Regional forecast models agree conditions will stay clear this week.", "WEAK", 0),
        ("No storm systems detected in the surrounding area.", "NEUTRAL", 0),
        ("Atmospheric pressure remains stable, consistent with clear conditions.", "WEAK", 0),
        ("A new pressure system is now forming rapidly offshore, still unconfirmed as a storm.", "WEAK", 1),
        ("Meteorologists issue a formal storm warning: the system will make landfall within 24 hours.", "STRONG", 1),
    ],
    "threat:assessment": [
        ("An unverified report mentions unusual movement near the border.", "WEAK", 1),
        ("A follow-up patrol finds no evidence supporting the initial report.", "WEAK", 0),
        ("A second, unrelated report raises similar but still unverified concerns.", "WEAK", 1),
        ("Aerial reconnaissance finds nothing conclusive either way.", "NEUTRAL", 0),
        ("Local sources offer conflicting accounts, none independently verified.", "NEUTRAL", 0),
        ("Command formally closes the inquiry, citing the pattern as consistent with prior false alarms and no verified evidence.", "STRONG", 0),
    ],
}
N_TICKS_DEFAULT = 6


def ctx_prompt(scope: str, tick: int, evidence_text: str, global_broadcast: dict | None) -> str:
    q = WORLD[scope]["question"]
    alts = WORLD[scope]["alternatives"]
    uptake = ""
    if global_broadcast:
        prior_tags = list(global_broadcast.get("region_status", {}).keys())
        if prior_tags:
            uptake = f" Prior global summary covered: {', '.join(prior_tags)}."
    return (
        f"Tick {tick} report for {scope} ({q}, options {alts[0]}/{alts[1]}):"
        f" {evidence_text}{uptake} In one word ({alts[0]} or {alts[1]} or UNCLEAR), assess:"
    )


def rss_shared_of(pid: int) -> dict:
    try:
        with open(f"/proc/{pid}/smaps_rollup") as f:
            txt = f.read()
        d = {}
        for line in txt.splitlines():
            for key in ("Rss:", "Shared_Clean:"):
                if line.startswith(key):
                    d[key.rstrip(":")] = int(line.split()[1])
        return d
    except Exception:
        return {}


def hyperposition_state(scope: str, tick: int) -> dict:
    """Correct version: requires >=1 STRONG item AND all STRONG items seen so far
    (ticks 0..tick inclusive) to agree on the same supports_index. Disagreeing STRONG
    evidence is a genuine, distinct case (contested-but-strong) and correctly stays
    PRESERVE_BRANCHES rather than being silently treated as agreement (v1's bug)."""
    seen = EVIDENCE_SCRIPT[scope][: tick + 1]
    strong_supports = [supports for (_, strength, supports) in seen if strength == "STRONG"]
    if not strong_supports:
        return {"state": "PRESERVE_BRANCHES", "reason": "no STRONG evidence yet"}
    distinct = set(strong_supports)
    if len(distinct) > 1:
        return {"state": "PRESERVE_BRANCHES", "reason": f"STRONG evidence exists but DISAGREES across alternatives {sorted(distinct)} -- contested, not resolved"}
    winner_idx = next(iter(distinct))
    first_strong_tick = next(i for i, (_, strength, supports) in enumerate(seen) if strength == "STRONG" and supports == winner_idx)
    return {
        "state": "COLLAPSE_VALID",
        "reason": f"all STRONG evidence agrees on alternative[{winner_idx}]={WORLD[scope]['alternatives'][winner_idx]}",
        "collapsed_to": WORLD[scope]["alternatives"][winner_idx],
        "collapsed_at_tick": first_strong_tick,
    }


def main(out_dir: str, n_ticks: int = N_TICKS_DEFAULT):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fabric_path = out / "grid10_world_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()

    t_load0 = time.time()
    load_model_once(MODEL_PATH)
    t_load = time.time() - t_load0

    f = Fabric(fabric_path)
    for scope in REGIONAL_SCOPES + ["GLOBAL"]:
        f.seed_scope(scope)

    for scope, cfg in WORLD.items():
        tid = f"hp-init-{scope.replace(':', '-')}"
        f.seed_task(tid, scope, 99, "reason", {
            "prompt": f"State (do not decide) the two live alternatives for {scope} ({cfg['question']}).",
            "unresolved_alternatives": list(cfg["alternatives"]),
        })

    ctx = mp.get_context("fork")

    def spawn(node_id, capability, max_iters):
        ev_path = out / f"evidence_{node_id}.json"
        p = ctx.Process(
            target=node_loop,
            kwargs=dict(
                node_id=node_id, capability=capability, fabric_path=str(fabric_path), model_path=MODEL_PATH,
                out_evidence=str(ev_path), max_iters=max_iters, poll_sleep=0.15,
                become_coordinator_candidate=True, self_pause_after_join=0.0, scenario="default",
            ),
        )
        return p, ev_path

    total_max_iters = 60 * n_ticks
    procs = []
    for node_id in NODE_IDS:
        p, evp = spawn(node_id, "reason", max_iters=total_max_iters)
        procs.append((node_id, p, evp))

    launch_t0 = time.time()
    for _, p, _ in procs:
        p.start()

    time.sleep(2.0)
    mid_run_rss = {node_id: rss_shared_of(p.pid) for node_id, p, _ in procs if p.pid}

    tick_log = []
    global_broadcast = None
    global_coordinator_rotation = ["xeno-09", "xeno-08", "xeno-07", "xeno-06", "xeno-05", "xeno-04"]

    for tick in range(n_ticks):
        tick_t0 = time.time()
        injected = []
        for scope in REGIONAL_SCOPES:
            evidence_text, strength, supports = EVIDENCE_SCRIPT[scope][tick % len(EVIDENCE_SCRIPT[scope])]
            prompt = ctx_prompt(scope, tick, evidence_text, global_broadcast)
            tid = f"t{tick}-{scope.replace(':', '-')}"
            f.seed_task(tid, scope, 90 - tick, "reason", {"prompt": prompt, "evidence_text": evidence_text, "evidence_strength": strength, "evidence_supports": WORLD[scope]["alternatives"][supports]})
            injected.append({"task_id": tid, "scope": scope, "evidence_text": evidence_text, "evidence_strength": strength, "evidence_supports": WORLD[scope]["alternatives"][supports]})

        time.sleep(4.0)

        candidate = global_coordinator_rotation[tick % len(global_coordinator_rotation)]
        region_status = {}
        for scope in REGIONAL_SCOPES:
            row = [r for r in f.snapshot().scopes if r["scope"] == scope][0]
            summary = json.loads(row["summary_json"])
            latest = summary.get("latest", {})
            region_status[scope] = {"latest_answer": latest.get("answer"), "evidence_count": row["evidence_count"]}

        hp_status = {scope: hyperposition_state(scope, tick) for scope in REGIONAL_SCOPES}

        elect = f.elect_coordinator("GLOBAL", candidate_node_ids=[candidate])
        if elect is None:
            old = [r for r in f.snapshot().leases if r["scope"] == "GLOBAL" and r["valid"]]
            if old:
                f.revoke_lease(old[0]["lease_id"])
            elect = f.elect_coordinator("GLOBAL", candidate_node_ids=[candidate])
        broadcast_committed = False
        new_epoch = None
        if elect is not None:
            lease, token = elect
            gsnap = f.snapshot()
            payload = {"tick": tick, "region_status": region_status, "hyperposition_status": hp_status}
            summary = summary_packet(candidate, gsnap, "GLOBAL", payload)
            try:
                delta = f.coordinator_commit(lease=lease, token=token, packet=summary, expected_epoch=gsnap.epoch, expected_digest=gsnap.state_digest)
                broadcast_committed = True
                new_epoch = delta["new_epoch"]
                global_broadcast = payload
            except FabricError as exc:
                tick_log.append({"tick": tick, "global_commit_error": str(exc)})

        tick_log.append({
            "tick": tick, "coordinator_candidate": candidate, "injected_tasks": injected,
            "region_status_snapshot": region_status, "hyperposition_status": hp_status,
            "global_broadcast_committed": broadcast_committed, "global_new_epoch": new_epoch,
            "tick_wallclock_s": round(time.time() - tick_t0, 2),
        })
        print(json.dumps({"tick": tick, "broadcast_committed": broadcast_committed, "hp_status": hp_status}), flush=True)

    time.sleep(3.0)
    final_snap = f.snapshot()

    node_events = {node_id: {"pid": p.pid, "alive": p.is_alive()} for node_id, p, _ in procs}

    receipt = {
        "schema": "GRID10_WORLD_MODEL_SIMULATION/v2",
        "corrects_v1_bugs": [
            "classify_evidence_strength() substring false-positive ('confirmed' matched inside 'unconfirmed' and inside 'neither confirmed') -- v2 uses explicit hand-authored (strength, supports_index) triples per evidence item instead of inferring from substrings",
            "hp_status collapse logic never actually checked agreement across STRONG evidence despite the v1 code comment claiming it did -- v2 requires all STRONG items seen so far to agree on the same alternative, and correctly stays PRESERVE_BRANCHES when STRONG evidence disagrees (a real case v1 could not represent)",
        ],
        "honest_scope_statement": (
            "Real 10-node multi-process coordination over a genuinely multi-tick, multi-scope "
            "task graph (5 regional/domain scopes + GLOBAL, 6 ticks, GWT broadcast/uptake each "
            "tick). The Hyperposition collapse/preserve state is computed by THIS DRIVER from "
            "hand-authored evidence strength/direction labels, not by the small model -- the "
            "model's role is answering short completion prompts per task as its 'sensing' "
            "contribution, separately recorded but NOT the source of the collapse decision."
        ),
        "model_load_time_s": round(t_load, 2),
        "n_ticks": n_ticks,
        "n_regional_scopes": len(REGIONAL_SCOPES),
        "physical_node_count": len(NODE_IDS),
        "tick_log": tick_log,
        "final_fabric_snapshot": {"epoch": final_snap.epoch, "generation": final_snap.generation, "scopes": [dict(s) for s in final_snap.scopes]},
        "mid_run_rss_sample": mid_run_rss,
        "nodes_left_running": node_events,
        "fabric_path": str(fabric_path),
    }
    (out / "GRID10_WORLD_MODEL_SIMULATION_RECEIPT_V2.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps({"done": True, "n_ticks": n_ticks, "final_epoch": final_snap.epoch, "nodes_still_alive": sum(1 for v in node_events.values() if v["alive"])}, indent=2))


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_world_model"
    n_ticks = int(sys.argv[2]) if len(sys.argv) > 2 else N_TICKS_DEFAULT
    main(out_dir, n_ticks)
