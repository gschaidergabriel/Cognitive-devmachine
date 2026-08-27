#!/usr/bin/env python3
"""Frank-v0.1 research interconnect preflight.

Schema-v3 registry compatible successor to the legacy peer-kind filter.  The public
interface intentionally mirrors research_interconnect_preflight.py: BRANCHES, PRIORITY,
build() and main().  Peer membership is derived from current trigger roles, while explicit
priority lists remain fail-closed governance.
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
MANDATORY_ACTIVE_KNOWLEDGE = ROOT / "research_entity" / "global" / "MANDATORY_ACTIVE_KNOWLEDGE.json"
ACTIVE_POLICY = "research_entity/global/DOMAIN_ACTIVE_KNOWLEDGE_POLICY.md"
MANDATORY_POLICY = "research_entity/global/MANDATORY_ACTIVE_KNOWLEDGE.json"

# Current Frank-v0.1 operational research/build roles.  Legacy names remain accepted so
# an in-flight checkout cannot silently lose peers during a registry migration.
PEER_KINDS = {
    "domain_research",
    "domain_build_research",
    "integrated_frank_v0_1_research_foundry",
    "whole_target_architecture_build",
    "multimodal_perception_research",
    "direct_frank_v0_1_validation_repair",
    "integrated_research_foundry",
}


def _registered_scientific_branches_from_data(data: dict[str, Any]) -> list[str]:
    out: list[str] = []
    for name, spec in (data.get("triggers") or {}).items():
        spec = spec or {}
        if spec.get("kind") in PEER_KINDS:
            out.append(str(name))
    return out


def _registered_scientific_branches() -> list[str]:
    return _registered_scientific_branches_from_data(json.loads(REGISTRY.read_text(encoding="utf-8")))


BRANCHES = _registered_scientific_branches()

PRIORITY: dict[str, list[str]] = {
    "fusion": ["clayresearch", "frank", "q23", "gwt", "emergenz", "claycode", "hyperposition", "claygraph", "unifieddb", "harness"],
    "clayresearch": ["clayresearch", "frank", "claycode", "harness", "q23", "claygraph", "unifieddb", "gwt", "emergenz", "hyperposition"],
    "frank": ["clayresearch", "claycode", "harness", "q23", "claygraph", "unifieddb", "gwt", "hyperposition", "emergenz", "frank"],
    "q23": ["frank", "harness", "claygraph", "unifieddb", "gwt", "claycode", "emergenz", "hyperposition", "clayresearch", "q23"],
    "gwt": ["clayresearch", "harness", "q23", "claygraph", "unifieddb", "frank", "emergenz", "hyperposition", "claycode", "gwt"],
    "emergenz": ["clayresearch", "gwt", "harness", "q23", "claygraph", "unifieddb", "hyperposition", "frank", "claycode", "emergenz"],
    "claycode": ["frank", "clayresearch", "harness", "q23", "claygraph", "unifieddb", "gwt", "hyperposition", "emergenz", "claycode"],
    "hyperposition": ["clayresearch", "harness", "q23", "claygraph", "unifieddb", "frank", "claycode", "gwt", "emergenz", "hyperposition"],
    "claygraph": ["clayresearch", "frank", "claycode", "harness", "q23", "unifieddb", "hyperposition", "gwt", "emergenz", "claygraph"],
    "unifieddb": ["clayresearch", "frank", "claycode", "harness", "q23", "claygraph", "hyperposition", "gwt", "emergenz", "unifieddb"],
    "harness": ["frank", "claycode", "clayresearch", "q23", "gwt", "claygraph", "unifieddb", "hyperposition", "emergenz", "harness"],
}

for trigger, order in PRIORITY.items():
    if set(order) != set(BRANCHES) or len(order) != len(BRANCHES):
        raise RuntimeError(
            f"research mesh governance drift: {trigger} priority={order!r} registry_branches={BRANCHES!r}"
        )

BASE_PACKET_BUDGETS: dict[str, tuple[int, int]] = {
    "clayresearch": (48, 96), "frank": (40, 80), "q23": (48, 96),
    "claycode": (40, 80), "claygraph": (48, 96), "unifieddb": (48, 96),
    "gwt": (32, 64), "hyperposition": (32, 64), "emergenz": (32, 64),
    "harness": (64, 128),
}

DEEP_PACKET_OVERRIDES: dict[tuple[str, str], tuple[int, int]] = {
    ("frank", "clayresearch"): (64, 128), ("frank", "claycode"): (64, 128),
    ("frank", "q23"): (64, 128), ("frank", "claygraph"): (64, 128),
    ("frank", "unifieddb"): (64, 128), ("frank", "harness"): (64, 128),
    ("claycode", "frank"): (64, 128), ("claycode", "q23"): (48, 96),
    ("claycode", "claygraph"): (64, 128), ("claycode", "unifieddb"): (56, 112),
    ("claycode", "harness"): (64, 128), ("gwt", "q23"): (56, 112),
    ("gwt", "claygraph"): (56, 112), ("gwt", "unifieddb"): (48, 96),
    ("gwt", "harness"): (64, 128), ("q23", "frank"): (80, 160),
    ("q23", "harness"): (80, 160), ("q23", "claygraph"): (72, 144),
    ("q23", "unifieddb"): (72, 144), ("q23", "gwt"): (72, 144),
    ("hyperposition", "claygraph"): (56, 112), ("hyperposition", "unifieddb"): (48, 96),
    ("hyperposition", "harness"): (56, 112), ("claygraph", "q23"): (56, 112),
    ("claygraph", "unifieddb"): (64, 128), ("claygraph", "harness"): (64, 128),
    ("unifieddb", "q23"): (56, 112), ("unifieddb", "claygraph"): (64, 128),
    ("unifieddb", "frank"): (64, 128), ("unifieddb", "claycode"): (64, 128),
    ("unifieddb", "harness"): (64, 128), ("harness", "clayresearch"): (72, 144),
    ("harness", "frank"): (96, 192), ("harness", "claycode"): (96, 192),
    ("harness", "q23"): (80, 160), ("harness", "gwt"): (80, 160),
    ("harness", "claygraph"): (80, 160), ("harness", "unifieddb"): (80, 160),
    ("harness", "hyperposition"): (64, 128), ("harness", "emergenz"): (64, 128),
    ("harness", "harness"): (96, 192),
}

ALIASES: dict[str, list[str]] = {
    "clayresearch": ["clay", "clayresearch", "synthetic-clay", "synthetic_clay"],
    "frank": ["frank", "frankenstein", "self.root"],
    "q23": ["q23", "multimodal perception", "digital retina", "visual learner", "retina"],
    "gwt": ["gwt", "workspace", "global-workspace", "global_workspace", "rcwc"],
    "emergenz": ["emergenz", "emergence", "causal-emergence", "causal_emergence"],
    "claycode": ["claycode", "xeno", "uecc", "iarc"],
    "hyperposition": ["hyperposition", "hypergraph", "codependency", "carts"],
    "claygraph": ["claygraph", "clay graph", "knowledge graph", "associative memory", "ibca", "casar"],
    "unifieddb": ["unifieddb", "unified database", "unified_database", "cppf"],
    "harness": ["harness", "simulation harness", "frank simulator", "golden trace", "replay validation"],
}

ARTIFACT_NAMES = [
    "FINAL_REPORT.md", "HYPOTHESES.md", "HYPOTHESES.json", "EXPERIMENTS.json",
    "EXPERIMENT_RESULTS.json", "NEGATIVE_RESULTS.md", "NEGATIVE_RESULTS.jsonl",
    "CONTRADICTION_MAP.md", "CONTRADICTION_MAP.json", "BRANCH_FEEDBACK_MANIFEST.json",
    "GLOBAL_COVERAGE_MANIFEST.json", "RUN_MANIFEST.json", "TOOL_EXECUTION_MANIFEST.json",
    "INTERCONNECT_MANIFEST.json", "FRANK_ARCHITECTURE.claycode.json",
    "FRANK_CLAYCODE_GOODMAN_REVIEW.json", "CLAYGRAPH_SCHEMA.claycode.json",
    "CLAYGRAPH_CANDIDATE.claycode.json", "UNIFIED_DATABASE_ARCHITECTURE.claycode.json",
    "FRANK_UNIFIEDDB_FEEDBACK.json", "HARNESS_RELEASE_MANIFEST.json",
    "TEST_EXECUTION_MANIFEST.json", "EXECUTABLE_RESEARCH_RECEIPT.json",
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
    match = META_RE.search(text)
    if not match:
        return {}
    try:
        obj = json.loads(match.group(1))
        return obj if isinstance(obj, dict) else {}
    except json.JSONDecodeError:
        return {}


def _material_category(path: Path) -> str:
    hay = (_rel(path) + "\n" + _read_text(path, 5000)).lower()
    if "negative_result" in hay or "negative result" in hay or "refuted" in hay:
        return "negative"
    if "contradiction" in hay or "supersed" in hay:
        return "contradiction"
    if "experiment" in hay or "falsifier" in hay or "test_execution" in hay:
        return "experiment"
    if "architecture" in hay or "migration" in hay or "schema" in hay:
        return "architecture"
    if "hypothesis" in hay or "hypothese" in hay:
        return "hypothesis"
    if "feedback" in hay or "cross-branch" in hay or "cross_branch" in hay:
        return "feedback"
    return "general"


def _material_score(path: Path) -> tuple[int, int, str, str]:
    meta = _meta(path)
    status = str(meta.get("status") or meta.get("state") or "").upper()
    status_score = 4 if status in ACTIVE_STATUSES else (1 if status in HISTORIC_STATUSES else 2)
    category = _material_category(path)
    category_score = {"contradiction": 7, "negative": 7, "experiment": 6, "architecture": 5,
                      "feedback": 5, "hypothesis": 4, "general": 2}[category]
    stamp = str(meta.get("updated_at") or meta.get("created_at") or meta.get("run_id") or "")
    return status_score, category_score, stamp, _rel(path)


def _matches_branch(path: Path, branch: str) -> bool:
    hay = (_rel(path) + "\n" + _read_text(path, 12000)).lower()
    return any(alias.lower() in hay for alias in ALIASES.get(branch, [branch]))


def _runs(branch: str, include_incomplete: bool = True) -> list[Path]:
    base = TRIGGER_RUNS / ("clay" if branch == "clayresearch" else branch)
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


def _mandatory_material(base: Path, branch: str) -> list[Path]:
    if not MANDATORY_ACTIVE_KNOWLEDGE.exists():
        return []
    try:
        data = json.loads(MANDATORY_ACTIVE_KNOWLEDGE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    out: list[Path] = []
    base_resolved = base.resolve()
    for rel in ((data.get("branches") or {}).get(branch) or []):
        p = (ROOT / str(rel)).resolve()
        try:
            p.relative_to(base_resolved)
        except ValueError:
            continue
        if p.is_file() and p.suffix.lower() in {".md", ".json", ".jsonl"} and _matches_branch(p, branch):
            out.append(p)
    return out


def _select_material(base: Path, branch: str, limit: int) -> tuple[list[str], int, dict[str, int]]:
    if not base.exists() or limit <= 0:
        return [], 0, {}
    candidates = [p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in {".md", ".json", ".jsonl"} and _matches_branch(p, branch)]
    candidates.sort(key=_material_score, reverse=True)
    selected: list[Path] = []
    seen: set[Path] = set()
    counts: dict[str, int] = {}
    for p in _mandatory_material(base, branch) + candidates:
        if len(selected) >= limit:
            break
        if p in seen:
            continue
        selected.append(p); seen.add(p)
        cat = _material_category(p); counts[cat] = counts.get(cat, 0) + 1
    return [_rel(p) for p in selected], len(candidates), counts


def _run_depth(trigger: str, branch: str, base_depth: int) -> int:
    if trigger == "harness":
        return max(6, base_depth)
    if trigger == "q23" and branch in {"frank", "harness", "claygraph", "unifieddb", "gwt"}:
        return max(5, base_depth)
    if trigger in {"frank", "claycode", "gwt", "claygraph", "unifieddb"} and branch in {"frank", "claycode", "harness", "claygraph", "unifieddb", "q23"}:
        return max(4, base_depth)
    return max(1, base_depth)


def _packet_budget(trigger: str, branch: str) -> tuple[int, int]:
    return DEEP_PACKET_OVERRIDES.get((trigger, branch), BASE_PACKET_BUDGETS.get(branch, (32, 64)))


def _latest_artifact(branches: list[dict[str, Any]], branch: str, suffix: str) -> str | None:
    for payload in branches:
        if payload.get("branch") != branch:
            continue
        for run in payload.get("runs", []):
            for artifact in run.get("artifacts", []):
                if artifact.endswith(suffix):
                    return artifact
    return None


def build(trigger: str, run_id: str, history_per_branch: int = 2) -> dict[str, Any]:
    if trigger not in PRIORITY:
        raise ValueError(f"unknown connected trigger: {trigger}")
    branches: list[dict[str, Any]] = []
    coverage_all = trigger in {"fusion", "claygraph", "unifieddb", "harness"}
    for rank, branch in enumerate(PRIORITY[trigger], 1):
        all_runs = _runs(branch, include_incomplete=True)
        if coverage_all:
            selected_runs = all_runs
            depth: int | str = "ALL_DISCOVERED"
        else:
            depth = _run_depth(trigger, branch, history_per_branch)
            selected_runs = all_runs[:depth]
        topic_limit, micro_limit = _packet_budget(trigger, branch)
        topics, topic_total, topic_categories = _select_material(TOPIC_PACKETS, branch, topic_limit)
        micros, micro_total, micro_categories = _select_material(MICRO_PACKETS, branch, micro_limit)
        completed = [r for r in selected_runs if (r / "FINAL_REPORT.md").exists()]
        branches.append({
            "branch": branch, "priority_rank": rank, "run_history_depth": depth,
            "latest_run": selected_runs[0].name if selected_runs else None,
            "latest_run_complete": bool(selected_runs and (selected_runs[0] / "FINAL_REPORT.md").exists()),
            "latest_completed_run": completed[0].name if completed else None,
            "runs": [{"run_id": r.name, "complete": (r / "FINAL_REPORT.md").exists(), "artifacts": _artifacts(r)} for r in selected_runs],
            "active_knowledge": {
                "topic_packet_limit": topic_limit, "knowledge_micro_packet_limit": micro_limit,
                "topic_packet_indexed_candidates": topic_total, "knowledge_micro_packet_indexed_candidates": micro_total,
                "topic_packet_categories": topic_categories, "knowledge_micro_packet_categories": micro_categories,
                "selection_policy": ACTIVE_POLICY, "mandatory_active_knowledge_policy": MANDATORY_POLICY,
            },
            "topic_packets": topics, "knowledge_micro_packets": micros,
        })
    latest_frank_arch = _latest_artifact(branches, "frank", "/FRANK_ARCHITECTURE.claycode.json")
    latest_claygraph = _latest_artifact(branches, "claygraph", "/CLAYGRAPH_CANDIDATE.claycode.json") or _latest_artifact(branches, "claygraph", "/CLAYGRAPH_SCHEMA.claycode.json")
    latest_unifieddb = _latest_artifact(branches, "unifieddb", "/UNIFIED_DATABASE_ARCHITECTURE.claycode.json")
    latest_harness_release = _latest_artifact(branches, "harness", "/HARNESS_RELEASE_MANIFEST.json")
    return {
        "schema_version": "2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "program_target": "FRANK_V0_1",
        "trigger": trigger, "run_id": run_id,
        "registry_scientific_branches": BRANCHES, "peer_branch_count": len(BRANCHES),
        "registry_peer_kinds": sorted(PEER_KINDS),
        "protocol": "research_entity/global/INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md",
        "active_knowledge_policy": ACTIVE_POLICY, "mandatory_active_knowledge_policy": MANDATORY_POLICY,
        "goodman_protocol": "research_entity/global/GOODMAN_ANTI_ECHO_PROTOCOL.md" if trigger in {"claycode", "fusion", "harness"} else None,
        "branch_priority": PRIORITY[trigger],
        "coverage_mode": "ALL_DISCOVERED_INDEXED_WITH_RICH_ACTIVE_PACKET_ENVELOPE" if coverage_all else "PRIORITY_BOUNDED_WITH_RICH_ACTIVE_PACKET_ENVELOPE",
        "branches": branches,
        "requirements": {
            "must_ingest_all_connected_branches": True, "must_include_fresh_incomplete_material": True,
            "must_preserve_evidence_status": True, "must_scan_cross_branch_contradictions": True,
            "must_write_back_cross_links": True, "strong_promotion_blocked_if_missing": True,
            "harness_is_peer_research_center_branch": "harness" in BRANCHES,
            "q23_is_peer_research_center_branch": "q23" in BRANCHES,
            "all_peers_target_frank_v0_1": True,
        },
        "special_rules": {
            "claycode_requires_latest_frank_research_as_primary_feedback": trigger == "claycode",
            "claycode_requires_deep_claygraph_input": trigger == "claycode",
            "claycode_requires_unifieddb_contract_input": trigger == "claycode",
            "claycode_requires_harness_execution_feedback": trigger == "claycode",
            "claycode_requires_goodman_anti_echo_review": trigger == "claycode",
            "claycode_latest_frank_architecture_artifact": latest_frank_arch if trigger in {"claycode", "harness"} else None,
            "latest_claygraph_artifact": latest_claygraph,
            "latest_unifieddb_artifact": latest_unifieddb,
            "latest_harness_release_artifact": latest_harness_release,
            "harness_requires_full_mesh_coverage": trigger == "harness",
            "harness_must_build_and_execute": trigger == "harness",
            "q23_requires_harness_frank_claygraph_unifieddb_gwt_input": trigger == "q23",
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
        p = Path(args.output); p.parent.mkdir(parents=True, exist_ok=True); p.write_text(text, encoding="utf-8")
    print(text, end="")


if __name__ == "__main__":
    main()
