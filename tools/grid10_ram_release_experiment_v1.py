#!/usr/bin/env python3
"""GRID10 RAM-efficiency experiment -- real before/after measurement of
release_idle_memory() (gc.collect() + malloc_trim()), built earlier today.

6 real processes. All 6 do one real generate() call first (establishing the measured
~379MB Private_Dirty baseline from the earlier grounding measurement). Then split:
3 call release_idle_memory() (the "trimmed" group), 3 do nothing (the "control"
group) during an equal idle window. Measure real Private_Dirty for both groups
immediately after. Then ALL 6 do one more real generate() call -- measuring (a) real
wall-clock latency of that call for trimmed vs control (does the page-fault re-touch
cost show up as measurable?), and (b) Private_Dirty afterward for both groups (does
memory return to the same steady state either way -- i.e. no permanent capability
loss from trimming).
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
N_PER_GROUP = 3


def smaps_rollup(pid: int) -> dict:
    try:
        with open(f"/proc/{pid}/smaps_rollup") as f:
            txt = f.read()
        out = {}
        for line in txt.splitlines():
            for key in ("Rss:", "Private_Dirty:", "Shared_Clean:"):
                if line.startswith(key):
                    out[key.rstrip(":")] = int(line.split()[1])
        return out
    except Exception as exc:
        return {"error": repr(exc)}


def child_worker(node_id: str, group: str, out_path: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    global MODEL, TOK
    pid = os.getpid()
    report = {"node_id": node_id, "group": group, "pid": pid}

    tok = AutoTokenizer.from_pretrained(MODEL_PATH)
    prompt = "2 + 2 ="
    inputs = tok(prompt, return_tensors="pt")

    with torch.no_grad():
        MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
    report["smaps_after_first_generate"] = smaps_rollup(pid)

    time.sleep(1.0)  # real idle window, matching what a throttled elastic-poll node would see

    if group == "trimmed":
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from grid10_node import release_idle_memory
        release_result = release_idle_memory()
        report["release_result"] = release_result

    report["smaps_after_idle_window"] = smaps_rollup(pid)

    t0 = time.time()
    with torch.no_grad():
        MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
    report["second_generate_latency_s"] = round(time.time() - t0, 4)
    report["smaps_after_second_generate"] = smaps_rollup(pid)

    Path(out_path).write_text(json.dumps(report, indent=2))


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(1)
    global MODEL, TOK
    TOK = AutoTokenizer.from_pretrained(MODEL_PATH)
    MODEL = AutoModelForCausalLM.from_pretrained(MODEL_PATH, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    MODEL.eval()
    model_load_s = time.time() - t0

    ctx = mp.get_context("fork")
    procs = []
    for i in range(N_PER_GROUP):
        node_id = f"trim-{i}"
        out_path = out / f"child_{node_id}.json"
        p = ctx.Process(target=child_worker, args=(node_id, "trimmed", str(out_path)))
        procs.append((node_id, p, out_path))
    for i in range(N_PER_GROUP):
        node_id = f"ctrl-{i}"
        out_path = out / f"child_{node_id}.json"
        p = ctx.Process(target=child_worker, args=(node_id, "control", str(out_path)))
        procs.append((node_id, p, out_path))

    for _, p, _ in procs:
        p.start()
    for _, p, _ in procs:
        p.join(timeout=60)

    child_reports = {}
    for node_id, p, out_path in procs:
        if out_path.exists():
            child_reports[node_id] = json.loads(out_path.read_text())

    trimmed_pd_before = [r["smaps_after_first_generate"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "trimmed"]
    trimmed_pd_after_idle = [r["smaps_after_idle_window"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "trimmed"]
    control_pd_before = [r["smaps_after_first_generate"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "control"]
    control_pd_after_idle = [r["smaps_after_idle_window"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "control"]

    trimmed_latency = [r["second_generate_latency_s"] for r in child_reports.values() if r["group"] == "trimmed"]
    control_latency = [r["second_generate_latency_s"] for r in child_reports.values() if r["group"] == "control"]

    trimmed_pd_after_second = [r["smaps_after_second_generate"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "trimmed"]
    control_pd_after_second = [r["smaps_after_second_generate"]["Private_Dirty"] for r in child_reports.values() if r["group"] == "control"]

    summary = {
        "schema": "GRID10_RAM_RELEASE_EXPERIMENT/v1",
        "model_load_time_s": round(model_load_s, 2),
        "trimmed_group_private_dirty_kb": {"before_trim": trimmed_pd_before, "after_trim_idle_window": trimmed_pd_after_idle},
        "control_group_private_dirty_kb": {"before": control_pd_before, "after_idle_window_no_trim": control_pd_after_idle},
        "trimmed_group_avg_reduction_kb": round(sum(trimmed_pd_before) / len(trimmed_pd_before) - sum(trimmed_pd_after_idle) / len(trimmed_pd_after_idle), 1) if trimmed_pd_before else None,
        "control_group_avg_change_kb": round(sum(control_pd_before) / len(control_pd_before) - sum(control_pd_after_idle) / len(control_pd_after_idle), 1) if control_pd_before else None,
        "second_generate_latency_s": {"trimmed": trimmed_latency, "control": control_latency},
        "trimmed_group_avg_latency_s": round(sum(trimmed_latency) / len(trimmed_latency), 4) if trimmed_latency else None,
        "control_group_avg_latency_s": round(sum(control_latency) / len(control_latency), 4) if control_latency else None,
        "private_dirty_after_second_generate_kb": {"trimmed": trimmed_pd_after_second, "control": control_pd_after_second},
        "child_reports": child_reports,
    }
    (out / "GRID10_RAM_RELEASE_EXPERIMENT_RECEIPT.json").write_text(json.dumps(summary, indent=2, default=str))
    print(json.dumps({
        "trimmed_avg_reduction_kb": summary["trimmed_group_avg_reduction_kb"],
        "control_avg_change_kb": summary["control_group_avg_change_kb"],
        "trimmed_avg_latency_s": summary["trimmed_group_avg_latency_s"],
        "control_avg_latency_s": summary["control_group_avg_latency_s"],
        "trimmed_pd_after_second_generate": trimmed_pd_after_second,
        "control_pd_after_second_generate": control_pd_after_second,
    }, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_ram_release")
