#!/usr/bin/env python3
"""GRID10 latency experiment -- real A/B measurement of torch thread count.

For each thread-count setting (1, 2, 4), spawns 4 real concurrent processes (a
realistic "active this tick" count, per the concept's own grounding: typically
3-5 of 10 nodes are active-in-decode at once, not all 10), each doing 3 real
generate() calls, and measures real wall-clock decode latency per call. GRID10_TORCH_THREADS
is set via environment variable before each process group runs.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
N_CONCURRENT = 4
N_CALLS_PER_PROC = 3
THREAD_SETTINGS = [1, 2, 4]


def child_worker(node_id: str, thread_count: int, out_path: str):
    os.environ["GRID10_TORCH_THREADS"] = str(thread_count)
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(thread_count)  # mirrors what load_model_once now does
    tok = AutoTokenizer.from_pretrained(MODEL_PATH)
    model = AutoModelForCausalLM.from_pretrained(MODEL_PATH, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    model.eval()

    prompt = "Complete with exactly one word: The weather today is"
    inputs = tok(prompt, return_tensors="pt")

    latencies = []
    for _ in range(N_CALLS_PER_PROC):
        t0 = time.time()
        with torch.no_grad():
            model.generate(**inputs, max_new_tokens=16, do_sample=False)
        latencies.append(round(time.time() - t0, 4))

    Path(out_path).write_text(json.dumps({"node_id": node_id, "thread_count": thread_count, "latencies_s": latencies}))


def run_group(thread_count: int, out_dir: Path) -> dict:
    ctx = mp.get_context("fork")
    procs = []
    for i in range(N_CONCURRENT):
        node_id = f"t{thread_count}-{i}"
        out_path = out_dir / f"child_{node_id}.json"
        p = ctx.Process(target=child_worker, args=(node_id, thread_count, str(out_path)))
        procs.append((node_id, p, out_path))

    group_t0 = time.time()
    for _, p, _ in procs:
        p.start()
    for _, p, _ in procs:
        p.join(timeout=90)
    group_wallclock_s = time.time() - group_t0

    all_latencies = []
    for node_id, p, out_path in procs:
        if out_path.exists():
            data = json.loads(out_path.read_text())
            all_latencies.extend(data["latencies_s"])

    return {
        "thread_count": thread_count,
        "n_concurrent_processes": N_CONCURRENT,
        "group_wallclock_s": round(group_wallclock_s, 2),
        "all_per_call_latencies_s": all_latencies,
        "avg_per_call_latency_s": round(sum(all_latencies) / len(all_latencies), 4) if all_latencies else None,
        "n_samples": len(all_latencies),
    }


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    results = []
    for tc in THREAD_SETTINGS:
        group_out = out / f"threads_{tc}"
        group_out.mkdir(exist_ok=True)
        print(f"running thread_count={tc}...", flush=True)
        r = run_group(tc, group_out)
        results.append(r)
        print(json.dumps(r, indent=2), flush=True)

    (out / "GRID10_THREAD_LATENCY_EXPERIMENT_RECEIPT.json").write_text(json.dumps({
        "schema": "GRID10_THREAD_LATENCY_EXPERIMENT/v1",
        "n_concurrent_processes_per_group": N_CONCURRENT,
        "n_calls_per_process": N_CALLS_PER_PROC,
        "results_by_thread_count": results,
    }, indent=2, default=str))

    print(json.dumps({
        "summary_avg_latency_by_thread_count": {r["thread_count"]: r["avg_per_call_latency_s"] for r in results},
        "summary_group_wallclock_by_thread_count": {r["thread_count"]: r["group_wallclock_s"] for r in results},
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_thread_latency")
