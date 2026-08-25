#!/usr/bin/env python3
"""Exact-source Supervisor-8.78 raw-generation backpressure repair.

Supervisor 8.78 requires zero-cost capacity to move away from new raw generation while
historical conversion is incomplete or conversion pressure remains high. The current
6000 supervisor applies BACKLOG_FIRST only inside Forge discovery, yet still
unconditionally calls start_6000().

This patcher closes that control-plane gap without increasing provider concurrency,
reading credentials, or creating another Forge/effect authority. The decision itself
is delegated to the single deterministic helper
``free_swarm_raw_generation_gate_878.py`` so scan completeness, extraction saturation,
and backlog pressure can be tested independently of the shell supervisor.

The patch is deliberately pinned to the exact inspected supervisor blob and fail-closes
on source movement. Applying this file is source work only; runtime credit requires a
later admitted exact-source execution receipt.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

TARGET_REL = "tools/run_6000_free_swarm_supervisor.sh"
HELPER_REL = "tools/free_swarm_raw_generation_gate_878.py"
EXPECTED_TARGET_BLOB = "cdbe6a4da423b2fb35fe988adc04397407360c3f"


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), "hash-object", rel], text=True).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


RAW_GENERATION_GATE = r'''raw_generation_allowed(){
  # Supervisor 8.78 historical-conversion gate. The helper is credential blind,
  # reads only local artifact/Forge state, and fails closed on incomplete scans,
  # unsaturated historical chunks, unstable workers.jsonl identity, or backlog.
  python3 "$ROOT/tools/free_swarm_raw_generation_gate_878.py" \
    --artifact-root "$STATE_DIR" \
    --threshold "${CLAY_SWARM_RAW_GENERATION_BACKPRESSURE_THRESHOLD:-64}"
}

'''


def patch(text: str) -> str:
    if "free_swarm_raw_generation_gate_878.py" in text or "CLAY_SWARM_RAW_GENERATION_BACKPRESSURE/v2" in text:
        raise SystemExit("RAW_GENERATION_BACKPRESSURE_ALREADY_PRESENT")
    text = replace_once(text, "start_6000(){\n", RAW_GENERATION_GATE + "start_6000(){\n", "INSERT_GATE")
    text = replace_once(
        text,
        "  reconcile_6000_admission\n  start_6000\n  refresh_root_results",
        "  reconcile_6000_admission\n  if raw_generation_allowed; then\n    start_6000\n  else\n    stop_6000\n  fi\n  refresh_root_results",
        "CONTROL_LOOP_GATE",
    )
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    target = repo / TARGET_REL
    helper = repo / HELPER_REL
    if not helper.is_file():
        raise SystemExit(f"RAW_GENERATION_GATE_HELPER_MISSING:{HELPER_REL}")
    observed = git_blob(repo, TARGET_REL)
    if observed != EXPECTED_TARGET_BLOB:
        raise SystemExit(
            f"SWARM_SUPERVISOR_MOVED_FAIL_CLOSED:expected={EXPECTED_TARGET_BLOB}:observed={observed}"
        )
    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    subprocess.run(["bash", "-n", str(target)], check=True)
    print("GO878_RAW_GENERATION_BACKPRESSURE_PATCHED_V2")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
