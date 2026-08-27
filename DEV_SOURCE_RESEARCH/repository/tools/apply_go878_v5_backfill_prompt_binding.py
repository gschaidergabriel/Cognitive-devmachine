#!/usr/bin/env python3
"""Exact-source repair for the active v5 historical-backfill prompt binding.

The active launcher imports ``run_6000_free_swarm_v5`` before installing
``free_swarm_backfill_scheduler`` on ``base.worker_prompt``. v5 currently snapshots the
pre-install prompt function in ``_ORIGINAL_WORKER_PROMPT`` and
``proposal_only_prompt()`` calls that frozen reference. The later scheduler wrapper can
therefore be bypassed even though the launcher says it installed the final prompt
authority.

This patch rebinds proposal construction to the *current* ``base.worker_prompt`` at call
time. With the current import order that reaches the historical-backfill wrapper, whose
``previous`` pointer still terminates at the pre-wrapper prompt without recursion.

The patch is deliberately exact-source and fail-closed. Source repair alone grants no
runtime, provider, model, J-Space, training, or whole-product credit.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess

TARGET_REL = "tools/run_6000_free_swarm_v5.py"
EXPECTED_TARGET_BLOB = "f4d6b0b0239efedb0f2ef16eac8973c729a44523"
FROZEN_ASSIGNMENT = "_ORIGINAL_WORKER_PROMPT = base.worker_prompt\n"
FROZEN_CALL = "    return _ORIGINAL_WORKER_PROMPT(protocol, role, task, state_context, serial) + \"\"\"\n"
DYNAMIC_CALL = "    return base.worker_prompt(protocol, role, task, state_context, serial) + \"\"\"\n"


def git_blob(repo: Path, rel: str) -> str:
    return subprocess.check_output(
        ["git", "-C", str(repo), "hash-object", rel], text=True
    ).strip()


def patch(text: str) -> str:
    if text.count(FROZEN_ASSIGNMENT) != 1:
        raise SystemExit(
            f"V5_FROZEN_ASSIGNMENT_COUNT_{text.count(FROZEN_ASSIGNMENT)}"
        )
    if text.count(FROZEN_CALL) != 1:
        raise SystemExit(f"V5_FROZEN_CALL_COUNT_{text.count(FROZEN_CALL)}")
    if text.count(DYNAMIC_CALL) != 0:
        raise SystemExit("V5_DYNAMIC_PROMPT_BINDING_ALREADY_PRESENT")

    text = text.replace(FROZEN_ASSIGNMENT, "", 1)
    text = text.replace(FROZEN_CALL, DYNAMIC_CALL, 1)
    ast.parse(text, filename=TARGET_REL)
    return text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()
    repo = args.repo.resolve()
    target = repo / TARGET_REL

    observed = git_blob(repo, TARGET_REL)
    if observed != EXPECTED_TARGET_BLOB:
        raise SystemExit(
            "V5_BACKFILL_PROMPT_SOURCE_MOVED_FAIL_CLOSED:"
            f"expected={EXPECTED_TARGET_BLOB}:observed={observed}"
        )

    target.write_text(patch(target.read_text(encoding="utf-8")), encoding="utf-8")
    subprocess.run(
        ["python3", "-m", "py_compile", str(target)],
        check=True,
        cwd=repo,
    )
    print("GO878_V5_BACKFILL_PROMPT_BINDING_PATCHED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
