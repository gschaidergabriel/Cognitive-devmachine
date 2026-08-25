#!/usr/bin/env python3
"""Wire the existing backlog-first Forge into the one active 6000 supervisor path.

Supervisor 8.78 requires conversion of historical Free-Swarm output before more raw
scale. This patcher does not create another Forge authority: it replaces the active
safe-only launcher with the existing backlog-first wrapper, which itself delegates to
the same safe Forge implementation/evaluator.

The patch is bound to the exact inspected supervisor Git blob and fails closed if a
parallel worker has moved that source. It performs no provider call and reads no
credential.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import subprocess

EXPECTED_SUPERVISOR_BLOB = "35550943dd829a3f9e7072a91cd018a76d17f185"
SUPERVISOR_REL = "tools/run_6000_free_swarm_supervisor.sh"

OLD_START_FORGE = '''start_forge(){
  local x="$ROOT/tools/run_free_evidence_forge_safe.py"; [[ -f "$x" ]] || return 0
  # The active 6000 lane must never keep the shell-capable legacy Forge alive.
  # Retire any pre-fix process before starting the argv-only, secret-free,
  # bubblewrap-gated successor. A zero-match is the normal steady state.
  while IFS= read -r pid; do
    [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
  done < <(pgrep -f '[r]un_free_evidence_forge.py' || true)
  pgrep -f '[r]un_free_evidence_forge_safe.py' >/dev/null 2>&1 && return 0
  nohup python3 "$x" --hours 24 --sleep-seconds 20 --discovery-parallel 8 --local-parallel 4 --e2b-parallel 20 >"$STATE_DIR/forge.log" 2>&1 </dev/null &
  echo $! >"$STATE_DIR/forge.pid"
}
'''

NEW_START_FORGE = '''start_forge(){
  # One Forge authority, backlog-first entrypoint. The wrapper reuses the existing
  # safe/bubblewrap evaluator while ingesting historical worker output and applying
  # conversion backpressure before new discovery work.
  local x="$ROOT/tools/run_free_evidence_forge_backfill.py"; [[ -f "$x" ]] || return 0

  # Retire both historical Forge executors before activating the successor. This
  # prevents safe-only + backlog-first processes from evaluating the same SQLite
  # authority concurrently as competing supervisor paths.
  local pattern pid
  for pattern in '[r]un_free_evidence_forge.py' '[r]un_free_evidence_forge_safe.py'; do
    while IFS= read -r pid; do
      [[ -n "$pid" ]] && kill "$pid" 2>/dev/null || true
    done < <(pgrep -f "$pattern" || true)
  done

  pgrep -f '[r]un_free_evidence_forge_backfill.py' >/dev/null 2>&1 && return 0
  nohup python3 "$x" --hours 24 >"$STATE_DIR/forge.log" 2>&1 </dev/null &
  echo $! >"$STATE_DIR/forge.pid"
}
'''


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "hash-object", rel], text=True
    ).strip()


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"PATCH_MARKER_{label}_COUNT_{count}")
    return text.replace(old, new, 1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    supervisor = repo / SUPERVISOR_REL

    observed = git_blob(repo, SUPERVISOR_REL)
    if observed != EXPECTED_SUPERVISOR_BLOB:
        raise SystemExit(
            f"SUPERVISOR_SOURCE_BLOB_MOVED_FAIL_CLOSED:expected={EXPECTED_SUPERVISOR_BLOB}:observed={observed}"
        )

    text = supervisor.read_text(encoding="utf-8")
    text = replace_once(text, OLD_START_FORGE, NEW_START_FORGE, "START_FORGE")
    text = replace_once(
        text,
        " 'forge_running':running('run_free_evidence_forge_safe.py'),\n 'legacy_forge_running':running('run_free_evidence_forge.py'),",
        " 'forge_running':running('run_free_evidence_forge_backfill.py'),\n 'superseded_safe_forge_running':running('run_free_evidence_forge_safe.py'),\n 'legacy_forge_running':running('run_free_evidence_forge.py'),",
        "STATUS_FORGE",
    )
    text = replace_once(
        text,
        "LEGACY_FORGE_TERMINATED; SAFE_FORGE_ONLY",
        "LEGACY_AND_SUPERSEDED_SAFE_FORGE_TERMINATED; BACKLOG_FIRST_SAFE_FORGE_ONLY",
        "REVOCATION_POLICY",
    )

    if "local x=\"$ROOT/tools/run_free_evidence_forge_safe.py\"" in text:
        raise SystemExit("ACTIVE_SAFE_ONLY_FORGE_STILL_PRESENT_FAIL_CLOSED")
    if "local x=\"$ROOT/tools/run_free_evidence_forge_backfill.py\"" not in text:
        raise SystemExit("BACKLOG_FIRST_ACTIVE_FORGE_MISSING_FAIL_CLOSED")
    if text.count("'forge_running':running('run_free_evidence_forge_backfill.py')") != 1:
        raise SystemExit("BACKLOG_FIRST_STATUS_BINDING_INVALID")

    supervisor.write_text(text, encoding="utf-8")
    subprocess.run(["bash", "-n", str(supervisor)], check=True)
    subprocess.run(
        ["python3", "-m", "py_compile", str(repo / "tools/run_free_evidence_forge_backfill.py")],
        check=True,
    )
    print("GO878_ACTIVE_BACKLOG_FORGE_WIRING_PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
