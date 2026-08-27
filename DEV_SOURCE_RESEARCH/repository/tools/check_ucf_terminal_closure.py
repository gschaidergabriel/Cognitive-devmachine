#!/usr/bin/env python3
"""Fail-closed static guard for UCF post-commit terminal closure.

This guard does not require the canonical source to already use two-phase UCF.
When a candidate source introduces pipeline_cognitive_fabric_finalize after
pipeline_commit, it rejects a fatal `require finalized.ok` after the canonical
commit because that can report failure after durable state is already committed.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def _strip_line_comments(source: str) -> str:
    return "\n".join(line.split("//", 1)[0] for line in source.splitlines())


def evaluate(source: str) -> dict[str, object]:
    code = _strip_line_comments(source)
    commit_marker = 'phase("pipeline_commit"'
    finalize_marker = 'phase("pipeline_cognitive_fabric_finalize"'
    commit_pos = code.find(commit_marker)
    finalize_pos = code.find(finalize_marker)
    has_two_phase_terminal = commit_pos >= 0 and finalize_pos >= 0
    finalize_after_commit = has_two_phase_terminal and commit_pos < finalize_pos

    fatal_post_commit_finalize = False
    if finalize_after_commit:
        tail = code[finalize_pos:]
        fatal_post_commit_finalize = bool(
            re.search(r"\brequire\s+finalized\.ok\b", tail)
        )

    legacy_finalize_before_commit = (
        has_two_phase_terminal and finalize_pos < commit_pos
    )
    pass_ = not legacy_finalize_before_commit and not fatal_post_commit_finalize
    return {
        "schema": "ucf-terminal-closure-static/v1",
        "has_two_phase_terminal": has_two_phase_terminal,
        "finalize_after_commit": finalize_after_commit,
        "fatal_post_commit_finalize": fatal_post_commit_finalize,
        "legacy_finalize_before_commit": legacy_finalize_before_commit,
        "pass": pass_,
        "policy": (
            "Final UCF evidence stays post-terminal. Once canonical commit succeeds, "
            "later finalization failure must not collapse the run back into an "
            "apparently uncommitted failure. Finalization must be idempotent and "
            "commit-aware, or its durable receipt must share the canonical transaction."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    args = parser.parse_args()
    report = evaluate(Path(args.source).read_text(encoding="utf-8"))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
