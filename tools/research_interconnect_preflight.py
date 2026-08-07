#!/usr/bin/env python3
"""Build a machine-readable cross-trigger research foundation manifest.

Every RAE research trigger can use this before Fusion 1 to discover current material
from all connected branches. The script scans repository-local trigger runs and records
latest material without changing evidence status.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIGGER_RUNS = ROOT / "research_entity" / "trigger_runs"
BRANCHES = ["clay", "frank", "gwt", "emergenz", "claycode", "hyperposition"]

PRIORITY = {
    "clay": ["clay", "frank", "gwt", "emergenz", "claycode", "hyperposition"],
    "frank": ["clay", "gwt", "claycode", "hyperposition", "emergenz", "frank"],
    "gwt": ["clay", "frank", "emergenz", "hyperposition", "claycode", "gwt"],
    "emergenz": ["clay", "gwt", "hyperposition", "frank", "claycode", "emergenz"],
    "claycode": ["clay", "frank", "gwt", "hyperposition", "emergenz", "claycode"],
    "hyperposition": ["clay", "frank", "claycode", "gwt", "emergenz", "hyperposition"],
}

ARTIFACT_NAMES = [
    "FINAL_REPORT.md",
    "HYPOTHESES.md",
    "EXPERIMENTS.json",
    "EXPERIMENTS.jsonl",
    "NEGATIVE_RESULTS.md",
    "NEGATIVE_RESULTS.jsonl",
    "RUN_MANIFEST.json",
    "TOOL_EXECUTION_MANIFEST.json",
    "INTERCONNECT_MANIFEST.json",
]


def _run_score(path: Path) -> tuple[float, str]:
    try:
        mt = max((p.stat().st_mtime for p in path.rglob("*") if p.is_file()), default=path.stat().st_mtime)
    except FileNotFoundError:
        mt = 0.0
    return mt, path.name


def _completed_runs(branch: str) -> list[Path]:
    base = TRIGGER_RUNS / branch
    if not base.exists():
        return []
    runs = [p for p in base.iterdir() if p.is_dir() and (p / "FINAL_REPORT.md").exists()]
    return sorted(runs, key=_run_score, reverse=True)


def _artifacts(run: Path) -> list[str]:
    found = []
    for name in ARTIFACT_NAMES:
        p = run / name
        if p.exists():
            found.append(str(p.relative_to(ROOT)))
    # Include branch-run architecture/evidence files not covered by the canonical names.
    for p in sorted(run.iterdir()):
        if p.is_file() and p.suffix.lower() in {".md", ".json", ".jsonl"}:
            rel = str(p.relative_to(ROOT))
            if rel not in found:
                found.append(rel)
    return found


def build(trigger: str, run_id: str, history_per_branch: int = 2) -> dict:
    if trigger not in BRANCHES:
        raise ValueError(f"unknown connected trigger: {trigger}")
    branches = []
    for rank, branch in enumerate(PRIORITY[trigger], 1):
        runs = _completed_runs(branch)[:max(1, history_per_branch)]
        branches.append({
            "branch": branch,
            "priority_rank": rank,
            "latest_completed_run": runs[0].name if runs else None,
            "runs": [
                {
                    "run_id": r.name,
                    "artifacts": _artifacts(r),
                }
                for r in runs
            ],
        })
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "run_id": run_id,
        "protocol": "research_entity/global/INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md",
        "branch_priority": PRIORITY[trigger],
        "branches": branches,
        "requirements": {
            "must_ingest_all_connected_branches": True,
            "must_preserve_evidence_status": True,
            "must_scan_cross_branch_contradictions": True,
            "must_write_back_cross_links": True,
            "strong_promotion_blocked_if_missing": True,
        },
        "special_rules": {
            "frank_requires_latest_clay_architecture_as_primary_foundation": trigger == "frank",
            "clay_is_integrated_master_foundry": trigger == "clay",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", required=True, choices=BRANCHES)
    ap.add_argument("--run-id", required=True)
    ap.add_argument("--history-per-branch", type=int, default=2)
    ap.add_argument("--output")
    args = ap.parse_args()
    out = build(args.trigger, args.run_id, args.history_per_branch)
    text = json.dumps(out, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
