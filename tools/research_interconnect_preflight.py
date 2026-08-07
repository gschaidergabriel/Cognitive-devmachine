#!/usr/bin/env python3
"""Build a machine-readable cross-trigger research foundation manifest.

Every RAE scientific trigger uses this before Fusion 1. The authoritative scientific
branch set comes from RESEARCH_TRIGGER_REGISTRY.json. The manifest keeps a deliberately
rich but bounded active Topic/Micro-Packet envelope while preserving full indexed
reachability through the RAE stores/ClayGraph.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TRIGGER_RUNS = ROOT / "research_entity" / "trigger_runs"
TOPIC_PACKETS = ROOT / "research_entity" / "topic_packets"
MICRO_PACKETS = ROOT / "research_entity" / "knowledge_micro_packets"
REGISTRY = ROOT / "research_entity" / "global" / "RESEARCH_TRIGGER_REGISTRY.json"
ACTIVE_POLICY = "research_entity/global/DOMAIN_ACTIVE_KNOWLEDGE_POLICY.md"


def _registered_scientific_branches() -> list[str]:
    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    out = []
    for name, spec in (data.get("triggers") or {}).items():
        if (spec or {}).get("kind") in {"domain_research", "integrated_research_foundry"}:
            out.append(name)
    return out


BRANCHES = _registered_scientific_branches()

PRIORITY = {
    "fusion": ["clay", "frank", "gwt", "emergenz", "claycode", "hyperposition", "claygraph"],
    "clay": ["clay", "frank", "claycode", "claygraph", "gwt", "emergenz", "hyperposition"],
    "frank": ["clay", "claycode", "claygraph", "gwt", "hyperposition", "emergenz", "frank"],
    "gwt": ["clay", "claygraph", "frank", "emergenz", "hyperposition", "claycode", "gwt"],
    "emergenz": ["clay", "gwt", "claygraph", "hyperposition", "frank", "claycode", "emergenz"],
    "claycode": ["frank", "clay", "claygraph", "gwt", "hyperposition", "emergenz", "claycode"],
    "hyperposition": ["clay", "claygraph", "frank", "claycode", "gwt", "emergenz", "hyperposition"],
    "claygraph": ["clay", "frank", "claycode", "hyperposition", "gwt", "emergenz", "claygraph"],
}

for trigger, order in PRIORITY.items():
    if set(order) != set(BRANCHES) or len(order) != len(BRANCHES):
        raise RuntimeError(
            f"research mesh governance drift: {trigger} priority={order!r} registry_branches={BRANCHES!r}"
        )

# Topic/Micro packet active-envelope ceilings. These are intentionally much richer than
# the old single 8-item packet cap. Raw evidence remains on-demand.
BASE_PACKET_BUDGETS: dict[str, tuple[int, int]] = {
    "clay": (48, 96),
    "frank": (40, 80),
    "claycode": (40, 80),
    "claygraph": (48, 96),
    "gwt": (32, 64),
    "hyperposition": (32, 64),
    "emergenz": (32, 64),
}

DEEP_PACKET_OVERRIDES: dict[tuple[str, str], tuple[int, int]] = {
    ("frank", "clay"): (64, 128),
    ("frank", "claycode"): (64, 128),
    ("frank", "claygraph"): (64, 128),
    ("claycode", "frank"): (64, 128),
    ("claycode", "claygraph"): (64, 128),
    ("gwt", "claygraph"): (56, 112),
    ("hyperposition", "claygraph"): (56, 112),
}

ALIASES = {
    "clay": ["clay", "synthetic-clay", "synthetic_clay"],
    "frank": ["frank", "frankenstein"],
    "gwt": ["gwt", "workspace", "global-workspace", "global_workspace"],
    "emergenz": ["emergenz", "emergence", "causal-emergence", "causal_emergence"],
    "claycode": ["claycode", "xeno", "xeno-claycode", "xeno_claycode", "cc6", "cc7", "cc8"],
    "hyperposition": ["hyperposition", "hypergraph", "codependency", "h1", "h2"],
    "claygraph": ["claygraph", "clay graph", "knowledge graph", "associative memory", "database migration", "database transcendence"],
}

ARTIFACT_NAMES = [
    "FINAL_REPORT.md", "HYPOTHESES.md", "HYPOTHESES.json",
    "GLOBAL_HYPOTHESIS_MATRIX.md", "GLOBAL_HYPOTHESIS_MATRIX.json",
    "EXPERIMENTS.json", "EXPERIMENTS.jsonl", "EXPERIMENT_RESULTS.json",
    "NEGATIVE_RESULTS.md", "NEGATIVE_RESULTS.jsonl",
    "CONTRADICTION_MAP.md", "CONTRADICTION_MAP.json",
    "BRANCH_FEEDBACK_MANIFEST.json", "GLOBAL_COVERAGE_MANIFEST.json",
    "RUN_MANIFEST.json", "TOOL_EXECUTION_MANIFEST.json", "INTERCONNECT_MANIFEST.json",
    "ARCHITECTURE.md", "ARCHITECTURE.json",
    "FRANK_ARCHITECTURE.claycode.json", "CLAYCODE_ARCHITECTURE_MAPPING.md",
    "FRANK_CLAYCODE_GOODMAN_REVIEW.json",
    "DATABASE_INVENTORY.json", "CLAYGRAPH_SCHEMA.claycode.json", "CLAYGRAPH_CANDIDATE.claycode.json",
    "SELF_USE_BENCHMARK.json", "MIGRATION_PLAN.json", "FRANK_CLAYGRAPH_FEEDBACK.json",
    "GRAPH_EVOLUTION_DECISION.json",
]

META_RE = re.compile(r"<!--\s*RAE_META\s*\n(\{.*?\})\s*\nRAE_META\s*-->", re.S)
ACTIVE_STATUSES = {"CURRENT", "OPEN", "ACTIVE", "IN_PROGRESS", "PROPOSED"}
HISTORIC_STATUSES = {"SUPERSEDED", "REFUTED", "ARCHIVED", "STALE", "CLOSED"}


def _rel(path: Path) -> str:
    return str(path.relative_to(ROOT))


def _read_text(path: Path, limit: int = 40000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except OSError:
        return ""


def _meta(path: Path) -> dict[str, Any]:
    text = _read_text(path)
    if path.suffix.lower() == ".json":
        try:
            obj = json.loads(text)
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            return {}
    m = META_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(1))
            return obj if isinstance(obj, dict) else {}
        except json.JSONDecodeError:
            pass
    return {}


def _status(meta: dict[str, Any]) -> str:
    for key in ("status", "state", "lifecycle", "current_status"):
        value = meta.get(key)
        if value is not None:
            return str(value).upper()
    return ""


def _material_category(path: Path) -> str:
    hay = (_rel(path) + "\n" + _read_text(path, 5000)).lower()
    if "negative_result" in hay or "negative result" in hay or "refuted" in hay:
        return "negative"
    if "contradiction" in hay or "supersed" in hay:
        return "contradiction"
    if "experiment" in hay or "falsifier" in hay:
        return "experiment"
    if "architecture" in hay or "migration" in hay or "schema" in hay:
        return "architecture"
    if "hypothesis" in hay or "hypothese" in hay:
        return "hypothesis"
    if "feedback" in hay or "cross-branch" in hay:
        return "feedback"
    return "general"


def _material_score(path: Path) -> tuple[int, int, str, str]:
    meta = _meta(path)
    status = _status(meta)
    status_score = 4 if status in ACTIVE_STATUSES else (1 if status in HISTORIC_STATUSES else 2)
    category = _material_category(path)
    category_score = {
        "contradiction": 7,
        "negative": 7,
        "experiment": 6,
        "architecture": 5,
        "feedback": 5,
        "hypothesis": 4,
        "general": 2,
    }[category]
    stamp = str(meta.get("updated_at") or meta.get("created_at") or meta.get("run_id") or "")
    return status_score, category_score, stamp, _rel(path)


def _matches_branch(path: Path, branch: str) -> bool:
    aliases = ALIASES.get(branch, [branch])
    hay = (_rel(path) + "\n" + _read_text(path, 12000)).lower()
    return any(alias.lower() in hay for alias in aliases)


def _runs(branch: str, include_incomplete: bool = True) -> list[Path]:
    base = TRIGGER_RUNS / branch
    if not base.exists():
        return []
    runs = [p for p in base.iterdir() if p.is_dir()]
    if not include_incomplete:
        runs = [p for p in runs if (p / "FINAL_REPORT.md").exists()]
    return sorted(runs, key=lambda p: p.name, reverse=True)


def _artifacts(run: Path) -> list[str]:
    found: list[str] = []
    for name in ARTIFACT_NAMES:
        p = run / name
        if p.exists():
            found.append(_rel(p))
    for p in sorted(run.iterdir()):
        if p.is_file() and p.suffix.lower() in {".md", ".json", ".jsonl"}:
            rel = _rel(p)
            if rel not in found:
                found.append(rel)
    return found


def _material_candidates(base: Path, branch: str) -> list[Path]:
    if not base.exists():
        return []
    out = []
    for p in base.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".md", ".json", ".jsonl"}:
            continue
        if _matches_branch(p, branch):
            out.append(p)
    out.sort(key=_material_score, reverse=True)
    return out


def _select_material(base: Path, branch: str, limit: int) -> tuple[list[str], int, dict[str, int]]:
    candidates = _material_candidates(base, branch)
    if not candidates or limit <= 0:
        return [], len(candidates), {}

    # First reserve a small diversity slice across failure/contradiction/experiment/
    # architecture/hypothesis/feedback categories, then fill by global priority.
    selected: list[Path] = []
    seen: set[Path] = set()
    category_counts: dict[str, int] = {}
    for category in ("negative", "contradiction", "experiment", "architecture", "hypothesis", "feedback", "general"):
        for p in candidates:
            if len(selected) >= limit:
                break
            if p in seen or _material_category(p) != category:
                continue
            if category_counts.get(category, 0) >= 3:
                continue
            selected.append(p)
            seen.add(p)
            category_counts[category] = category_counts.get(category, 0) + 1
    for p in candidates:
        if len(selected) >= limit:
            break
        if p in seen:
            continue
        selected.append(p)
        seen.add(p)
        cat = _material_category(p)
        category_counts[cat] = category_counts.get(cat, 0) + 1
    return [_rel(p) for p in selected], len(candidates), category_counts


def _run_depth(trigger: str, branch: str, base_depth: int) -> int:
    run_depth = max(1, base_depth)
    deep = {
        ("frank", "clay"): 3, ("frank", "claycode"): 4, ("frank", "claygraph"): 4,
        ("claycode", "frank"): 4, ("claycode", "clay"): 3, ("claycode", "claygraph"): 4,
        ("hyperposition", "claygraph"): 4, ("gwt", "claygraph"): 4,
    }
    return max(run_depth, deep.get((trigger, branch), run_depth))


def _packet_budget(trigger: str, branch: str) -> tuple[int, int]:
    return DEEP_PACKET_OVERRIDES.get((trigger, branch), BASE_PACKET_BUDGETS.get(branch, (32, 64)))


def _latest_artifact(branches: list[dict[str, Any]], branch: str, suffix: str) -> str | None:
    for b in branches:
        if b.get("branch") != branch:
            continue
        for run in b.get("runs", []):
            for artifact in run.get("artifacts", []):
                if artifact.endswith(suffix):
                    return artifact
    return None


def build(trigger: str, run_id: str, history_per_branch: int = 2) -> dict:
    if trigger not in PRIORITY:
        raise ValueError(f"unknown connected trigger: {trigger}")
    branches = []
    coverage_all = trigger in {"fusion", "claygraph"}
    for rank, branch in enumerate(PRIORITY[trigger], 1):
        if coverage_all:
            all_runs = _runs(branch, include_incomplete=True)
            run_depth: int | str = "ALL_DISCOVERED"
        else:
            numeric_depth = _run_depth(trigger, branch, history_per_branch)
            all_runs = _runs(branch, include_incomplete=True)[:numeric_depth]
            run_depth = numeric_depth

        topic_limit, micro_limit = _packet_budget(trigger, branch)
        topics, topic_total, topic_categories = _select_material(TOPIC_PACKETS, branch, topic_limit)
        micros, micro_total, micro_categories = _select_material(MICRO_PACKETS, branch, micro_limit)
        completed = [r for r in all_runs if (r / "FINAL_REPORT.md").exists()]
        branches.append({
            "branch": branch,
            "priority_rank": rank,
            "run_history_depth": run_depth,
            "latest_run": all_runs[0].name if all_runs else None,
            "latest_run_complete": bool(all_runs and (all_runs[0] / "FINAL_REPORT.md").exists()),
            "latest_completed_run": completed[0].name if completed else None,
            "runs": [{"run_id": r.name, "complete": (r / "FINAL_REPORT.md").exists(), "artifacts": _artifacts(r)} for r in all_runs],
            "active_knowledge": {
                "topic_packet_limit": topic_limit,
                "knowledge_micro_packet_limit": micro_limit,
                "topic_packet_indexed_candidates": topic_total,
                "knowledge_micro_packet_indexed_candidates": micro_total,
                "topic_packet_categories": topic_categories,
                "knowledge_micro_packet_categories": micro_categories,
                "selection_policy": ACTIVE_POLICY,
            },
            "topic_packets": topics,
            "knowledge_micro_packets": micros,
        })

    latest_frank_arch = _latest_artifact(branches, "frank", "/FRANK_ARCHITECTURE.claycode.json")
    latest_claygraph = _latest_artifact(branches, "claygraph", "/CLAYGRAPH_CANDIDATE.claycode.json") or _latest_artifact(branches, "claygraph", "/CLAYGRAPH_SCHEMA.claycode.json")
    return {
        "schema_version": "1.5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "trigger": trigger,
        "run_id": run_id,
        "registry_scientific_branches": BRANCHES,
        "protocol": "research_entity/global/INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md",
        "active_knowledge_policy": ACTIVE_POLICY,
        "goodman_protocol": "research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md" if trigger in {"claycode", "fusion"} else None,
        "branch_priority": PRIORITY[trigger],
        "coverage_mode": "ALL_DISCOVERED_INDEXED_WITH_RICH_ACTIVE_PACKET_ENVELOPE" if coverage_all else "PRIORITY_BOUNDED_WITH_RICH_ACTIVE_PACKET_ENVELOPE",
        "branches": branches,
        "requirements": {
            "must_ingest_all_connected_branches": True,
            "must_include_fresh_incomplete_material": True,
            "must_preserve_evidence_status": True,
            "must_scan_cross_branch_contradictions": True,
            "must_write_back_cross_links": True,
            "must_use_rich_active_packet_envelopes": True,
            "raw_evidence_expands_on_demand": True,
            "strong_promotion_blocked_if_missing": True,
        },
        "special_rules": {
            "fusion_requires_global_coverage_manifest": trigger == "fusion",
            "fusion_requires_feedback_receipt_for_every_branch": trigger == "fusion",
            "frank_requires_latest_clay_architecture_as_primary_foundation": trigger == "frank",
            "frank_requires_deep_claycode_architecture_input": trigger == "frank",
            "frank_requires_deep_claygraph_substrate_input": trigger == "frank",
            "frank_architecture_source_language": "ClayCode semantic IR" if trigger == "frank" else None,
            "claycode_requires_latest_frank_research_as_primary_feedback": trigger == "claycode",
            "claycode_requires_deep_claygraph_input": trigger == "claycode",
            "claycode_requires_goodman_anti_echo_review": trigger == "claycode",
            "claycode_latest_frank_architecture_artifact": latest_frank_arch if trigger == "claycode" else None,
            "claycode_frank_architecture_artifact_missing_must_be_explicit": trigger == "claycode" and latest_frank_arch is None,
            "hyperposition_requires_deep_claygraph_input": trigger == "hyperposition",
            "gwt_requires_deep_claygraph_input": trigger == "gwt",
            "latest_claygraph_artifact": latest_claygraph if trigger in {"frank", "claycode", "hyperposition", "gwt", "fusion", "clay"} else None,
            "claygraph_requires_full_mesh_coverage": trigger == "claygraph",
            "claygraph_requires_iterative_parent_candidate_selection": trigger == "claygraph",
            "clay_is_integrated_master_foundry": trigger == "clay",
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trigger", required=True, choices=list(PRIORITY))
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
