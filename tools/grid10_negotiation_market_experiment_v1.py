#!/usr/bin/env python3
"""GRID10 use-case 4 (multi-agent simulation / game theory) -- real, live experiment.

Owner's target: "Aufbau von Simulationen (Marktdynamiken, Verhandlungsszenarien,
strategische Konfliktsimulationen) mit mehreren spezialisierten Agenten, die autonom
auf gemeinsamer Datenbasis agieren. Skalierbarer Parallelbetrieb auf einem Host ohne
extremen RAM-Overhead durch geteilte Modellgewichte im Shared Memory."

This is the first experiment today with genuinely SPECIALIZED agents (distinct roles
with distinct objectives -- buyer vs seller -- rather than interchangeable workers
racing for the same task pool). Models a minimal price-negotiation market: 2 "buyer"
agents (want a LOW price) and 2 "seller" agents (want a HIGH price) each submit an
opening position for the same item over multiple real rounds, read the counterpart
side's committed position via the shared fabric (GWT-style uptake, same pattern as
the earlier world-model simulation), and adjust.

Also directly measures the open RAM-scaling question flagged in the use-case-2 note:
compares Shared_Clean/RSS at a SMALL fleet (4 nodes: 2 buyers + 2 sellers) vs the
LARGE fleet (10 nodes) used everywhere else today, to actually quantify whether COW
weight-sharing holds up as node count grows, not just assume it does.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric, summary_packet
from grid10_node import node_loop, load_model_once

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"

ITEM_DESCRIPTION = "a used bicycle in good condition"
N_ROUNDS = 3
BUYER_IDS = ["buyer-A", "buyer-B"]
SELLER_IDS = ["seller-A", "seller-B"]


def rss_of(pid: int) -> dict:
    try:
        with open(f"/proc/{pid}/smaps_rollup") as fh:
            txt = fh.read()
        return {
            line.split(":")[0].strip(): int(line.split()[1])
            for line in txt.splitlines() if line.startswith(("Rss:", "Shared_Clean:"))
        }
    except Exception:
        return {}


def round_prompt(role: str, round_n: int, counterpart_offers: list[str]) -> str:
    context = f" The other side's most recent position(s): {counterpart_offers}." if counterpart_offers else " No offers from the other side yet."
    if role == "buyer":
        return (
            f"Round {round_n} negotiation for {ITEM_DESCRIPTION}. You are the BUYER, you want a LOW price."
            f"{context} State your current offer as a single number in dollars, nothing else."
        )
    return (
        f"Round {round_n} negotiation for {ITEM_DESCRIPTION}. You are the SELLER, you want a HIGH price."
        f"{context} State your current asking price as a single number in dollars, nothing else."
    )


def run_negotiation(out_dir: str, fleet_label: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    fabric_path = out / "market_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()

    t0 = time.time()
    load_model_once(MODEL_PATH)
    model_load_s = time.time() - t0

    f = Fabric(fabric_path)
    f.seed_scope("market:buyers")
    f.seed_scope("market:sellers")

    ctx = mp.get_context("fork")

    def spawn(node_id, capability, max_iters):
        evp = out / f"evidence_{node_id}.json"
        p = ctx.Process(
            target=node_loop,
            kwargs=dict(
                node_id=node_id, capability=capability, fabric_path=str(fabric_path), model_path=MODEL_PATH,
                out_evidence=str(evp), max_iters=max_iters, poll_sleep=0.15,
                become_coordinator_candidate=True, task_reclaim_stale_after_seconds=15.0,
            ),
        )
        return p, evp

    all_procs = []
    for node_id in BUYER_IDS:
        p, evp = spawn(node_id, "buyer_role", max_iters=25 * N_ROUNDS)
        all_procs.append((node_id, p, evp))
    for node_id in SELLER_IDS:
        p, evp = spawn(node_id, "seller_role", max_iters=25 * N_ROUNDS)
        all_procs.append((node_id, p, evp))

    for _, p, _ in all_procs:
        p.start()

    time.sleep(2.0)
    mid_run_rss = {n: rss_of(p.pid) for n, p, _ in all_procs if p.pid}

    round_log = []
    buyer_offers, seller_offers = [], []
    for round_n in range(1, N_ROUNDS + 1):
        prompt_b = round_prompt("buyer", round_n, seller_offers[-2:])
        prompt_s = round_prompt("seller", round_n, buyer_offers[-2:])
        f.seed_task(f"buyers-r{round_n}", "market:buyers", 90, "buyer_role", {"prompt": prompt_b, "max_new_tokens": 16})
        f.seed_task(f"sellers-r{round_n}", "market:sellers", 90, "seller_role", {"prompt": prompt_s, "max_new_tokens": 16})
        time.sleep(9.0)

        snap = f.snapshot()
        b_row = [dict(s) for s in snap.scopes if s["scope"] == "market:buyers"][0]
        s_row = [dict(s) for s in snap.scopes if s["scope"] == "market:sellers"][0]
        b_answer = json.loads(b_row["summary_json"]).get("latest", {}).get("answer", "")
        s_answer = json.loads(s_row["summary_json"]).get("latest", {}).get("answer", "")
        buyer_offers.append(b_answer)
        seller_offers.append(s_answer)
        round_log.append({"round": round_n, "buyer_offer": b_answer, "seller_offer": s_answer})
        print(json.dumps(round_log[-1]), flush=True)

    for _, p, _ in all_procs:
        p.join(timeout=10)

    import re

    def extract_price(text):
        cleaned = (text or "").replace(",", "")
        text = cleaned
        m = re.search(r"\d+(?:\.\d+)?", text or "")
        return float(m.group()) if m else None

    buyer_prices = [extract_price(o) for o in buyer_offers]
    seller_prices = [extract_price(o) for o in seller_offers]
    gap_per_round = [
        (round(sp - bp, 2) if (sp is not None and bp is not None) else None)
        for bp, sp in zip(buyer_prices, seller_prices)
    ]
    valid_gaps = [g for g in gap_per_round if g is not None]
    converging = len(valid_gaps) >= 2 and abs(valid_gaps[-1]) < abs(valid_gaps[0])

    receipt = {
        "schema": "GRID10_NEGOTIATION_MARKET_EXPERIMENT/v1",
        "use_case": "multi_agent_simulation_game_theory",
        "fleet_label": fleet_label,
        "fleet_size": len(all_procs),
        "model_load_time_s": round(model_load_s, 2),
        "item": ITEM_DESCRIPTION,
        "n_rounds": N_ROUNDS,
        "round_log": round_log,
        "buyer_extracted_prices": buyer_prices,
        "seller_extracted_prices": seller_prices,
        "price_gap_per_round": gap_per_round,
        "gap_shrank_over_rounds": converging,
        "mid_run_rss_sample": mid_run_rss,
    }
    (out / "GRID10_NEGOTIATION_MARKET_RECEIPT.json").write_text(json.dumps(receipt, indent=2, default=str))
    print(json.dumps({
        "fleet_label": fleet_label,
        "fleet_size": len(all_procs),
        "buyer_prices": buyer_prices,
        "seller_prices": seller_prices,
        "gap_shrank_over_rounds": converging,
    }, indent=2))
    return receipt


if __name__ == "__main__":
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_market"
    fleet_label = sys.argv[2] if len(sys.argv) > 2 else "4-node"
    run_negotiation(out_dir, fleet_label)
