#!/usr/bin/env python3
"""Validate completion requirements for the global `fusion` RAE meta-trigger."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity" / "global" / "RESEARCH_TRIGGER_REGISTRY.json"
REQUIRED = [
    "INTERCONNECT_MANIFEST.json",
    "GLOBAL_COVERAGE_MANIFEST.json",
    "TOOL_EXECUTION_MANIFEST.json",
    "BRANCH_FEEDBACK_MANIFEST.json",
    "RUN_MANIFEST.json",
    "FINAL_REPORT.md",
]
ALLOWED_EFFECTS = {"SUPPORT", "CHALLENGE", "REVISE", "SUPERSEDE", "NEW_EXPERIMENT", "NO_CHANGE"}

# Persistent scientific/implementation branches are specialized lenses that own an
# ongoing Frank-v0.1 domain. Meta-triggers (go/fusion/hypofusion/atomic/etc.) may create
# experiments or syntheses, but are not themselves feedback branches. Keep legacy kind
# compatibility while covering the current 2026-08-10 FRANK_V0_1 registry taxonomy.
SCIENTIFIC_BRANCH_KINDS = {
    "domain_research",
    "domain_build_research",
    "integrated_research_foundry",
    "integrated_frank_v0_1_research_foundry",
    "whole_target_architecture_build",
    "direct_frank_v0_1_validation_repair",
    "multimodal_perception_research",
}


def scientific_branches() -> list[str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    triggers = data.get("triggers") or {}

    # Future registries may declare branch membership explicitly. If any explicit
    # declarations exist, they become authoritative and remove kind-heuristic drift.
    explicit = [
        name for name, spec in triggers.items()
        if isinstance(spec, dict) and spec.get("scientific_branch") is True
    ]
    if explicit:
        return explicit

    return [
        name for name, spec in triggers.items()
        if isinstance(spec, dict)
        and spec.get("must_reenter_frank_v0_1") is True
        and spec.get("kind") in SCIENTIFIC_BRANCH_KINDS
    ]


def _load(path: Path) -> dict[str, Any]:
    try:
        obj = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing required file: {path.name}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.name}: {exc}") from exc
    if not isinstance(obj, dict):
        raise ValueError(f"{path.name} must contain a JSON object")
    return obj


def validate(run_dir: Path) -> dict[str, Any]:
    branches = scientific_branches()
    violations: list[str] = []
    for name in REQUIRED:
        if not (run_dir / name).exists():
            violations.append(f"missing:{name}")

    if violations:
        return {"ok": False, "run_dir": str(run_dir), "branches": branches, "violations": violations}

    inter = _load(run_dir / "INTERCONNECT_MANIFEST.json")
    coverage = _load(run_dir / "GLOBAL_COVERAGE_MANIFEST.json")
    feedback = _load(run_dir / "BRANCH_FEEDBACK_MANIFEST.json")

    if inter.get("trigger") != "fusion":
        violations.append("interconnect trigger must be fusion")
    if set(inter.get("registry_scientific_branches") or []) != set(branches):
        violations.append("interconnect registry branch set differs from authoritative registry")
    if set(inter.get("branch_priority") or []) != set(branches):
        violations.append("interconnect branch priority must cover every registered scientific branch exactly once")
    special = inter.get("special_rules") or {}
    if special.get("fusion_requires_global_coverage_manifest") is not True:
        violations.append("interconnect must require global coverage manifest")
    if special.get("fusion_requires_feedback_receipt_for_every_branch") is not True:
        violations.append("interconnect must require feedback receipt for every branch")

    covered = coverage.get("branches") or {}
    if isinstance(covered, list):
        covered_names = {x.get("branch") for x in covered if isinstance(x, dict)}
    elif isinstance(covered, dict):
        covered_names = set(covered)
    else:
        covered_names = set()
    for branch in branches:
        if branch not in covered_names:
            violations.append(f"coverage_missing_branch:{branch}")

    receipts = feedback.get("branches") or {}
    if isinstance(receipts, list):
        by_branch = {x.get("branch"): x for x in receipts if isinstance(x, dict)}
    elif isinstance(receipts, dict):
        by_branch = receipts
    else:
        by_branch = {}

    for branch in branches:
        receipt = by_branch.get(branch)
        if not isinstance(receipt, dict):
            violations.append(f"feedback_missing_branch:{branch}")
            continue
        effects = receipt.get("effect")
        if isinstance(effects, str):
            effects = [effects]
        if not isinstance(effects, list) or not effects:
            violations.append(f"feedback_missing_effect:{branch}")
            continue
        bad = [x for x in effects if x not in ALLOWED_EFFECTS]
        if bad:
            violations.append(f"feedback_invalid_effect:{branch}:{','.join(map(str,bad))}")
        if effects != ["NO_CHANGE"] and not receipt.get("durable_writeback_refs"):
            violations.append(f"feedback_missing_writeback_refs:{branch}")

    extra_coverage = covered_names - set(branches)
    extra_feedback = set(by_branch) - set(branches)
    if extra_coverage:
        violations.append("coverage_unknown_branches:" + ",".join(sorted(extra_coverage)))
    if extra_feedback:
        violations.append("feedback_unknown_branches:" + ",".join(sorted(extra_feedback)))

    if coverage.get("shared_ancestry_scanned") is not True:
        violations.append("coverage must record shared ancestry scan")
    if coverage.get("contradictions_scanned") is not True:
        violations.append("coverage must record contradiction scan")

    return {"ok": not violations, "run_dir": str(run_dir), "branches": branches, "violations": violations}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    args = ap.parse_args()
    out = validate(Path(args.run_dir))
    print(json.dumps(out, ensure_ascii=False, indent=2))
    if not out["ok"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
