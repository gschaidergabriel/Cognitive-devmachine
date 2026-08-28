#!/usr/bin/env python3
"""Repeated non-provider acceptance for GRID10 idle-memory release.

Purpose
-------
The existing v1 A/B experiment demonstrated a large one-cycle reduction in
Private_Dirty after ``grid10_node.release_idle_memory()``.  This v2 acceptance
asks the next falsifiable question: does that benefit remain useful after repeated
idle -> trim -> resume cycles, without creating cumulative latency or memory
regressions?

This tool makes NO provider/network calls.  It uses the locally cached 0.8B model
and real forked OS processes.  Three processes use the retained
``release_idle_memory()`` implementation and three are matched controls.

Credit boundary
---------------
A PASS is RAM-efficiency component evidence only.  It is not Physical-GRID10,
HCU, J-Space, semantic or training credit.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

DEFAULT_MODEL_PATH = (
    "/root/qwen35-08b-hf-cache/"
    "models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/"
    "snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
)


def smaps_rollup(pid: int) -> dict[str, int | str]:
    try:
        with open(f"/proc/{pid}/smaps_rollup", encoding="utf-8") as fh:
            text = fh.read()
        out: dict[str, int | str] = {}
        for line in text.splitlines():
            for key in ("Rss:", "Private_Dirty:", "Shared_Clean:"):
                if line.startswith(key):
                    out[key[:-1]] = int(line.split()[1])
        return out
    except Exception as exc:  # fail is retained in child receipt
        return {"error": repr(exc)}


def pct(a: float, b: float) -> float:
    return 0.0 if b == 0 else (a - b) / b * 100.0


def child_worker(
    node_id: str,
    group: str,
    model_path: str,
    cycles: int,
    idle_s: float,
    out_path: str,
) -> None:
    import torch
    from transformers import AutoTokenizer

    from grid10_node import release_idle_memory

    global MODEL
    pid = os.getpid()
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
    prompt = "2 + 2 ="
    inputs = tok(prompt, return_tensors="pt")
    report: dict = {
        "node_id": node_id,
        "group": group,
        "pid": pid,
        "cycles": [],
    }

    # Establish the same post-generate allocator state for both arms.
    with torch.no_grad():
        MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
    report["baseline"] = smaps_rollup(pid)

    for cycle in range(cycles):
        time.sleep(idle_s)
        release_result = None
        if group == "trimmed":
            t_trim = time.perf_counter()
            release_result = release_idle_memory()
            trim_latency_s = time.perf_counter() - t_trim
        else:
            trim_latency_s = 0.0

        after_idle = smaps_rollup(pid)
        t0 = time.perf_counter()
        with torch.no_grad():
            MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
        generate_latency_s = time.perf_counter() - t0
        after_resume = smaps_rollup(pid)
        report["cycles"].append(
            {
                "cycle": cycle,
                "release_result": release_result,
                "trim_latency_s": trim_latency_s,
                "after_idle": after_idle,
                "generate_latency_s": generate_latency_s,
                "after_resume": after_resume,
            }
        )

    Path(out_path).write_text(json.dumps(report, indent=2), encoding="utf-8")


def median(values: list[float]) -> float | None:
    return statistics.median(values) if values else None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="/root/grid10_ram_release_v2")
    ap.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    ap.add_argument("--cycles", type=int, default=5)
    ap.add_argument("--idle-seconds", type=float, default=1.0)
    ap.add_argument("--per-group", type=int, default=3)
    args = ap.parse_args()

    if args.cycles < 3 or args.per_group < 2 or args.idle_seconds < 0:
        raise SystemExit("cycles>=3, per-group>=2 and idle-seconds>=0 required")

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    torch.set_num_threads(1)
    global MODEL
    # Fail closed: cached local checkpoint only; this acceptance must not download.
    AutoTokenizer.from_pretrained(args.model_path, local_files_only=True)
    MODEL = AutoModelForCausalLM.from_pretrained(
        args.model_path,
        dtype=torch.bfloat16,
        low_cpu_mem_usage=True,
        local_files_only=True,
    )
    MODEL.eval()

    ctx = mp.get_context("fork")
    procs = []
    for group, prefix in (("trimmed", "trim"), ("control", "ctrl")):
        for i in range(args.per_group):
            node_id = f"{prefix}-{i}"
            path = out / f"child_{node_id}.json"
            p = ctx.Process(
                target=child_worker,
                args=(node_id, group, args.model_path, args.cycles, args.idle_seconds, str(path)),
            )
            procs.append((node_id, group, p, path))

    for _, _, p, _ in procs:
        p.start()
    for _, _, p, _ in procs:
        p.join(timeout=max(120, int(args.cycles * (args.idle_seconds + 8) + 30)))

    children: dict[str, dict] = {}
    process_failures = []
    for node_id, group, p, path in procs:
        if p.is_alive():
            p.terminate()
            p.join(timeout=5)
            process_failures.append({"node_id": node_id, "reason": "timeout"})
        elif p.exitcode != 0:
            process_failures.append({"node_id": node_id, "reason": f"exitcode={p.exitcode}"})
        if path.exists():
            children[node_id] = json.loads(path.read_text(encoding="utf-8"))

    def group_cycles(group: str):
        return [c for r in children.values() if r["group"] == group for c in r["cycles"]]

    tc = group_cycles("trimmed")
    cc = group_cycles("control")
    trim_idle_pd = [float(c["after_idle"]["Private_Dirty"]) for c in tc if "Private_Dirty" in c["after_idle"]]
    ctrl_idle_pd = [float(c["after_idle"]["Private_Dirty"]) for c in cc if "Private_Dirty" in c["after_idle"]]
    trim_resume_pd = [float(c["after_resume"]["Private_Dirty"]) for c in tc if "Private_Dirty" in c["after_resume"]]
    ctrl_resume_pd = [float(c["after_resume"]["Private_Dirty"]) for c in cc if "Private_Dirty" in c["after_resume"]]
    trim_gen = [float(c["generate_latency_s"]) for c in tc]
    ctrl_gen = [float(c["generate_latency_s"]) for c in cc]
    trim_call = [float(c["trim_latency_s"]) for c in tc]

    m_trim_idle = median(trim_idle_pd)
    m_ctrl_idle = median(ctrl_idle_pd)
    m_trim_resume = median(trim_resume_pd)
    m_ctrl_resume = median(ctrl_resume_pd)
    m_trim_gen = median(trim_gen)
    m_ctrl_gen = median(ctrl_gen)

    # Acceptance thresholds are intentionally conservative relative to the v1 result
    # (~97 MB idle saving and ~72 MB post-resume saving).  They are preregistered here.
    idle_saving_kb = None if m_trim_idle is None or m_ctrl_idle is None else m_ctrl_idle - m_trim_idle
    resume_saving_kb = None if m_trim_resume is None or m_ctrl_resume is None else m_ctrl_resume - m_trim_resume
    latency_overhead_pct = None if m_trim_gen is None or m_ctrl_gen in (None, 0) else pct(m_trim_gen, m_ctrl_gen)

    per_trim_node_end = []
    per_trim_node_start = []
    for r in children.values():
        if r["group"] != "trimmed" or not r["cycles"]:
            continue
        first = r["cycles"][0]["after_resume"].get("Private_Dirty")
        last = r["cycles"][-1]["after_resume"].get("Private_Dirty")
        if first is not None and last is not None:
            per_trim_node_start.append(float(first))
            per_trim_node_end.append(float(last))
    cumulative_growth_kb = None
    if per_trim_node_start and per_trim_node_end:
        cumulative_growth_kb = median(per_trim_node_end) - median(per_trim_node_start)

    release_calls_ok = all(
        (c.get("release_result") or {}).get("malloc_trim_called") is True for c in tc
    ) if tc else False

    criteria = {
        "all_children_completed": not process_failures and len(children) == args.per_group * 2,
        "all_expected_cycles_present": all(len(r["cycles"]) == args.cycles for r in children.values()),
        "release_called_every_trim_cycle": release_calls_ok,
        "median_idle_private_dirty_saving_at_least_64mb": idle_saving_kb is not None and idle_saving_kb >= 64 * 1024,
        "median_post_resume_private_dirty_saving_at_least_32mb": resume_saving_kb is not None and resume_saving_kb >= 32 * 1024,
        "median_resume_latency_overhead_at_most_20pct": latency_overhead_pct is not None and latency_overhead_pct <= 20.0,
        "no_cumulative_trimmed_private_dirty_growth_over_64mb": cumulative_growth_kb is not None and cumulative_growth_kb <= 64 * 1024,
    }
    passed = all(criteria.values())

    receipt = {
        "schema": "GRID10_RAM_RELEASE_REPEATED_ACCEPTANCE/v2",
        "provider_calls": 0,
        "network_model_download_allowed": False,
        "model_path": args.model_path,
        "cycles": args.cycles,
        "per_group": args.per_group,
        "idle_seconds": args.idle_seconds,
        "metrics": {
            "median_trimmed_idle_private_dirty_kb": m_trim_idle,
            "median_control_idle_private_dirty_kb": m_ctrl_idle,
            "median_idle_saving_kb": idle_saving_kb,
            "median_trimmed_post_resume_private_dirty_kb": m_trim_resume,
            "median_control_post_resume_private_dirty_kb": m_ctrl_resume,
            "median_post_resume_saving_kb": resume_saving_kb,
            "median_trimmed_generate_latency_s": m_trim_gen,
            "median_control_generate_latency_s": m_ctrl_gen,
            "median_generate_latency_overhead_pct": latency_overhead_pct,
            "median_trim_call_latency_s": median(trim_call),
            "trimmed_private_dirty_growth_first_to_last_resume_kb": cumulative_growth_kb,
        },
        "criteria": criteria,
        "pass": passed,
        "process_failures": process_failures,
        "children": children,
        "credit_boundary": "RAM_EFFICIENCY_COMPONENT_ONLY_NO_PHYSICAL_GRID10_HCU_TRAINING_OR_SEMANTIC_CREDIT",
    }
    receipt_path = out / "GRID10_RAM_RELEASE_REPEATED_ACCEPTANCE_V2.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({"pass": passed, "criteria": criteria, "metrics": receipt["metrics"], "receipt": str(receipt_path)}, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
