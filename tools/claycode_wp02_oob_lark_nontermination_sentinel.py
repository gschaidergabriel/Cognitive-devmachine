#!/usr/bin/env python3
"""Bounded GO OOB experiment: detect a current Lark LALR nontermination hazard.

This is a research-only sentinel. It does not edit or promote ClayCode grammar.
It runs three bounded arms in isolated child processes:
  A) upstream issue #1585 minimal LALR reproducer (expected watchdog timeout on Lark 1.3.1),
  B) same recursive grammar under Earley as rescue/control (expected bounded completion),
  C) simple LALR grammar as watchdog negative control (expected bounded completion).

PASS means the environment reproduces the dependency hazard while the bounded watchdog
and rescue/control arms behave as expected. Production ClayCode parser closure is tested
separately by the workflow and is not inferred from this sentinel.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

BUG_CODE = r'''from lark import Lark
Lark('start.1: "a" | start start*', parser='lalr').parse('aa')
'''
EARLEY_RESCUE_CODE = r'''from lark import Lark
Lark('start.1: "a" | start start*', parser='earley').parse('aa')
'''
LALR_CONTROL_CODE = r'''from lark import Lark
Lark('start: "a"+', parser='lalr').parse('aa')
'''


def run_arm(name: str, code: str, timeout_s: float) -> dict:
    t0 = time.monotonic_ns()
    try:
        cp = subprocess.run(
            [sys.executable, "-c", code],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout_s,
            check=False,
            env=os.environ.copy(),
        )
        elapsed_ns = time.monotonic_ns() - t0
        return {
            "arm": name,
            "outcome": "EXITED",
            "returncode": cp.returncode,
            "timed_out": False,
            "elapsed_ns": elapsed_ns,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
    except subprocess.TimeoutExpired as exc:
        elapsed_ns = time.monotonic_ns() - t0
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        return {
            "arm": name,
            "outcome": "WATCHDOG_TIMEOUT",
            "returncode": None,
            "timed_out": True,
            "elapsed_ns": elapsed_ns,
            "stdout": stdout[-4000:],
            "stderr": stderr[-4000:],
        }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", default="/tmp/CLAYCODE_GO_OOB_LARK_NONTERMINATION.json")
    ap.add_argument("--timeout-seconds", type=float, default=2.0)
    args = ap.parse_args()

    timeout_s = max(0.25, min(args.timeout_seconds, 10.0))
    lark_version = importlib.metadata.version("lark")
    interegular_version = None
    try:
        interegular_version = importlib.metadata.version("interegular")
    except importlib.metadata.PackageNotFoundError:
        pass

    arms = {
        "lalr_issue_1585": run_arm("lalr_issue_1585", BUG_CODE, timeout_s),
        "earley_rescue": run_arm("earley_rescue", EARLEY_RESCUE_CODE, timeout_s),
        "lalr_simple_control": run_arm("lalr_simple_control", LALR_CONTROL_CODE, timeout_s),
    }

    hazard_reproduced = arms["lalr_issue_1585"]["timed_out"] is True
    earley_rescue_pass = (
        arms["earley_rescue"]["timed_out"] is False
        and arms["earley_rescue"]["returncode"] == 0
    )
    lalr_control_pass = (
        arms["lalr_simple_control"]["timed_out"] is False
        and arms["lalr_simple_control"]["returncode"] == 0
    )
    passed = hazard_reproduced and earley_rescue_pass and lalr_control_pass

    payload = {
        "schema_version": "1.0",
        "experiment_id": "GO-OOB-LARK-1585-NONTERMINATION-SENTINEL",
        "experiment_class": "BOUNDED_ADVERSARIAL_DEPENDENCY_SENTINEL_WITH_RESCUE_CONTROL",
        "evidence_scope": "DEPENDENCY_HAZARD_AND_WATCHDOG_ONLY_NOT_CLAYCODE_SEMANTIC_PROMOTION",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "lark_version": lark_version,
        "interegular_version": interegular_version,
        "timeout_seconds": timeout_s,
        "source_issue": "lark-parser/lark#1585",
        "hypothesis": "Pinned Lark LALR can nonterminate on a recursive-priority grammar; a hard watchdog contains it while rescue/control parsers remain bounded.",
        "counterhypothesis": "The reported bug does not reproduce in this pinned environment, or the watchdog/control design falsely times out benign parsing.",
        "arms": arms,
        "hazard_reproduced": hazard_reproduced,
        "earley_rescue_pass": earley_rescue_pass,
        "lalr_simple_control_pass": lalr_control_pass,
        "pass": passed,
        "architecture_delta": "NO_CHANGE",
        "rollback": "Remove this sentinel/workflow; no ClayCode grammar or runtime semantics are mutated.",
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "pass": passed,
        "lark_version": lark_version,
        "hazard_reproduced": hazard_reproduced,
        "earley_rescue_pass": earley_rescue_pass,
        "lalr_simple_control_pass": lalr_control_pass,
        "output": str(out),
    }, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
