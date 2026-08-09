#!/usr/bin/env python3
"""CLI wrapper for FULL_FRANK target finalizer with explicit registration path.

The canonical clean target collector runs first. This wrapper therefore permits only the
known generated evidence namespaces (including corpus/base_v1) to be dirty; source,
toolchain, grammar, runtime and harness code must remain clean.
"""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

import claycode_full_frank_target_finalizer as finalizer
from claycode_target_host_identity import DEFAULT_REGISTRATION

ROOT = Path(__file__).resolve().parents[1]


def evidence_only_clean_source_tree():
    cp = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, text=True, capture_output=True, check=False)
    allowed = (
        "research_entity/claycode/autonomous/",
        "research_entity/claycode/target/",
        "research_entity/claycode/target_receipts/",
        "research_entity/claycode/corpus/base_v1/",
        "CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json",
    )
    bad = []
    for line in cp.stdout.splitlines():
        path = line[3:] if len(line) >= 4 else line
        parts = [x.strip() for x in path.split(" -> ")]
        if not all(any(x.startswith(prefix) for prefix in allowed) for x in parts):
            bad.append(line)
    return cp.returncode == 0 and not bad, bad


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--registration", type=Path, default=DEFAULT_REGISTRATION)
    args = ap.parse_args()
    finalizer.DEFAULT_REGISTRATION = args.registration
    finalizer.clean_source_tree = evidence_only_clean_source_tree
    return finalizer.main()


if __name__ == "__main__":
    raise SystemExit(main())
