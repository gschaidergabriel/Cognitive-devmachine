#!/usr/bin/env python3
"""GRID10 RAM breakdown measurement -- real, live (Gabriel-instructed follow-up to the
CPU elastic-poll-rate work). Measures where RAM actually goes, per real process, before
proposing any dynamic reduction mechanism -- 'miss es echt' comes first.

Phases:
1. Parent process RSS/smaps BEFORE loading the model (baseline Python+torch import cost).
2. Parent process RSS/smaps AFTER loading the model, BEFORE fork (static weight footprint
   in a single process, no sharing involved yet).
3. Fork 10 real children (fabric fully set up, one real scope with one real task per
   child so each actually does a real decode). Measure smaps for EVERY child at three
   points: (a) immediately after fork, before any generation; (b) immediately after each
   child's OWN first real generate() call; (c) after all children have run several
   generate() calls (steady state).
4. Also measure the SQLite/WAL file sizes on disk (fabric database + WAL + SHM) as a
   direct, real number for that specific claimed RAM/disk consumer.
"""
from __future__ import annotations

import json
import multiprocessing as mp
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from grid10_fabric import Fabric

MODEL_PATH = "/root/qwen35-08b-hf-cache/models--Goekdeniz-Guelmez--Josiefied-Qwen3.5-0.8B-gabliterated-v1/snapshots/591852bda6e1979f59e4b0f5ee2919697b12e936"
N_NODES = 10


def smaps_rollup(pid: int) -> dict:
    try:
        with open(f"/proc/{pid}/smaps_rollup") as f:
            txt = f.read()
        out = {}
        for line in txt.splitlines():
            for key in ("Rss:", "Pss:", "Shared_Clean:", "Shared_Dirty:", "Private_Clean:", "Private_Dirty:", "Swap:"):
                if line.startswith(key):
                    out[key.rstrip(":")] = int(line.split()[1])
        return out
    except Exception as exc:
        return {"error": repr(exc)}


def rss_simple(pid: int) -> int | None:
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except Exception:
        return None
    return None


def child_worker(node_id: str, fabric_path: str, out_path: str, task_id: str):
    """Runs inside a forked child. Measures its OWN smaps at 3 points and writes a
    small JSON report -- deliberately NOT reusing node_loop, to keep this measurement
    isolated from the fabric-coordination machinery and focused purely on memory."""
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    pid = os.getpid()
    report = {"node_id": node_id, "pid": pid}
    report["smaps_immediately_after_fork"] = smaps_rollup(pid)

    tok = AutoTokenizer.from_pretrained(MODEL_PATH)
    prompt = "2 + 2 ="
    inputs = tok(prompt, return_tensors="pt")

    # NOTE: the model object itself is inherited from the fork -- this worker does
    # NOT reload it; it accesses the SAME MODEL global the parent set up before fork.
    global MODEL
    with torch.no_grad():
        out = MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
    _ = tok.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
    report["smaps_after_first_generate"] = smaps_rollup(pid)

    for _ in range(4):
        with torch.no_grad():
            out = MODEL.generate(**inputs, max_new_tokens=6, do_sample=False)
    report["smaps_after_five_generates_steady_state"] = smaps_rollup(pid)

    Path(out_path).write_text(json.dumps(report, indent=2))


def main(out_dir: str):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    parent_pid = os.getpid()
    report = {"schema": "GRID10_RAM_BREAKDOWN_MEASUREMENT/v1", "parent_pid": parent_pid}

    report["parent_smaps_before_model_load"] = smaps_rollup(parent_pid)
    report["parent_rss_kb_before_model_load"] = rss_simple(parent_pid)

    t0 = time.time()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(1)
    global MODEL
    TOK = AutoTokenizer.from_pretrained(MODEL_PATH)
    MODEL = AutoModelForCausalLM.from_pretrained(MODEL_PATH, dtype=torch.bfloat16, low_cpu_mem_usage=True)
    MODEL.eval()
    model_load_s = time.time() - t0

    report["model_load_time_s"] = round(model_load_s, 2)
    report["parent_smaps_after_model_load_before_fork"] = smaps_rollup(parent_pid)
    report["parent_rss_kb_after_model_load_before_fork"] = rss_simple(parent_pid)

    # real on-disk model size for comparison
    model_dir = Path(MODEL_PATH)
    total_bytes = 0
    for f in model_dir.rglob("*"):
        try:
            if f.is_file():
                total_bytes += f.stat().st_size
        except OSError:
            pass
    report["model_dir_on_disk_bytes"] = total_bytes

    fabric_path = out / "ram_s1.sqlite"
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(fabric_path) + suffix)
        if p.exists():
            p.unlink()
    f = Fabric(fabric_path)
    f.seed_scope("ram:probe")

    ctx = mp.get_context("fork")
    procs = []
    for i in range(N_NODES):
        node_id = f"ram-{i:02d}"
        out_path = out / f"child_{node_id}.json"
        p = ctx.Process(target=child_worker, args=(node_id, str(fabric_path), str(out_path), f"probe-{i}"))
        procs.append((node_id, p, out_path))

    fork_t0 = time.time()
    for _, p, _ in procs:
        p.start()

    time.sleep(0.5)
    report["mid_fork_smaps_sample"] = {n: smaps_rollup(p.pid) for n, p, _ in procs if p.pid}

    for _, p, _ in procs:
        p.join(timeout=60)
    report["all_children_wallclock_s"] = round(time.time() - fork_t0, 2)

    child_reports = {}
    for node_id, p, out_path in procs:
        if out_path.exists():
            child_reports[node_id] = json.loads(out_path.read_text())
    report["child_reports"] = child_reports

    # SQLite/WAL file sizes on disk -- direct, real numbers
    report["fabric_file_sizes_bytes"] = {}
    for suffix, label in (("", "main_db"), ("-wal", "wal"), ("-shm", "shm")):
        p = Path(str(fabric_path) + suffix)
        report["fabric_file_sizes_bytes"][label] = p.stat().st_size if p.exists() else 0

    (out / "GRID10_RAM_BREAKDOWN_REPORT.json").write_text(json.dumps(report, indent=2, default=str))

    # concise console summary
    summary = {
        "model_dir_on_disk_mb": round(total_bytes / 1e6, 1),
        "parent_rss_before_load_mb": round((report["parent_rss_kb_before_model_load"] or 0) / 1024, 1),
        "parent_rss_after_load_mb": round((report["parent_rss_kb_after_model_load_before_fork"] or 0) / 1024, 1),
        "fabric_file_sizes_kb": {k: round(v / 1024, 1) for k, v in report["fabric_file_sizes_bytes"].items()},
    }
    if child_reports:
        sample = next(iter(child_reports.values()))
        summary["sample_child_rss_after_fork_kb"] = sample["smaps_immediately_after_fork"].get("Rss")
        summary["sample_child_shared_clean_after_fork_kb"] = sample["smaps_immediately_after_fork"].get("Shared_Clean")
        summary["sample_child_rss_after_first_generate_kb"] = sample["smaps_after_first_generate"].get("Rss")
        summary["sample_child_shared_clean_after_first_generate_kb"] = sample["smaps_after_first_generate"].get("Shared_Clean")
        summary["sample_child_rss_steady_state_kb"] = sample["smaps_after_five_generates_steady_state"].get("Rss")
        summary["sample_child_shared_clean_steady_state_kb"] = sample["smaps_after_five_generates_steady_state"].get("Shared_Clean")
        summary["sample_child_private_dirty_steady_state_kb"] = sample["smaps_after_five_generates_steady_state"].get("Private_Dirty")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "/root/grid10_ram_measurement")
