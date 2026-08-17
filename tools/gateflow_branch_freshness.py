#!/usr/bin/env python3
"""GateFlow semantic branch freshness classifier.

This tool is coordination-only. It never rebases, merges, closes or deletes refs.
It classifies a branch/PR snapshot using semantic/path evidence instead of treating
`behind_by` as a correctness metric.
"""
from __future__ import annotations

import argparse
import fnmatch
import json
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0"

EVIDENCE_ONLY_PREFIXES = (
    "research_entity/trigger_runs/",
    "research_entity/mesh_feedback/",
    "research_entity/research_reports/",
    "research_entity/benchmarks/",
    "research_entity/rooms/throughput/",
)

SENSITIVE_PREFIXES = (
    ".github/workflows/",
    "tools/",
    "tests/",
    "research_entity/runtime/",
    "research_entity/claycode/",
    "research_entity/frank_v0_1/",
    "research_entity/gateflow/",
    "research_entity/continuity/",
    "research_entity/global/",
)

SENSITIVE_NAME_TOKENS = (
    "schema",
    "contract",
    "authority",
    "runtime",
    "compiler",
    "parser",
    "typed_ir",
    "evaluator",
    "migration",
    "workspace",
    "program_state",
    "canonical",
)

RECOMMENDATION_ORDER = {
    "SAFE_TO_CLOSE_AFTER_SUPERSESSION_CONFIRMATION": 0,
    "FOLLOW_STACKED_PARENT": 1,
    "REBASE_AND_RERUN": 2,
    "RERUN_CHEAP_GATES": 3,
    "KEEP_ACTIVE_NO_REBASE_REQUIRED": 4,
}


def norm(path: str) -> str:
    return str(path or "").replace("\\", "/").lstrip("./")


def _matches(path: str, pattern: str) -> bool:
    p = norm(path)
    pat = norm(pattern)
    if pat.endswith("/**"):
        return p.startswith(pat[:-3])
    if pat.endswith("/"):
        return p.startswith(pat)
    if any(ch in pat for ch in "*?["):
        return fnmatch.fnmatchcase(p, pat)
    return p == pat or p.startswith(pat.rstrip("/") + "/")


def _any_match(paths: list[str], patterns: list[str]) -> list[str]:
    return sorted({norm(p) for p in paths for pat in patterns if _matches(p, pat)})


def is_evidence_only(path: str) -> bool:
    p = norm(path)
    return any(p.startswith(prefix) for prefix in EVIDENCE_ONLY_PREFIXES)


def is_sensitive(path: str) -> bool:
    p = norm(path)
    if any(p.startswith(prefix) for prefix in SENSITIVE_PREFIXES):
        return True
    low = p.lower()
    return any(token in low for token in SENSITIVE_NAME_TOKENS)


def top_semantic_zone(path: str) -> str:
    p = norm(path)
    parts = p.split("/")
    if not parts:
        return ""
    if parts[0] == "research_entity" and len(parts) >= 2:
        return "/".join(parts[:2])
    return parts[0]


def validate_candidate(c: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    ident = c.get("id") or c.get("branch") or "<candidate>"
    if not c.get("branch"):
        errors.append(f"{ident}: missing branch")
    for key in ("ahead_by", "behind_by"):
        try:
            value = int(c.get(key, 0))
            if value < 0:
                errors.append(f"{ident}: {key} must be >= 0")
        except (TypeError, ValueError):
            errors.append(f"{ident}: invalid {key}")
    for key in ("head_files", "main_since_base_files", "dependency_cone"):
        value = c.get(key, [])
        if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
            errors.append(f"{ident}: {key} must be list[str]")
    return errors


def classify(c: dict[str, Any]) -> dict[str, Any]:
    ident = c.get("id") or c.get("branch")
    branch = str(c.get("branch"))
    base_branch = str(c.get("base_branch") or "main")
    ahead = int(c.get("ahead_by", 0))
    behind = int(c.get("behind_by", 0))
    head_files = [norm(x) for x in c.get("head_files", [])]
    main_files = [norm(x) for x in c.get("main_since_base_files", [])]
    cone = [norm(x) for x in c.get("dependency_cone", [])]
    superseded_by = c.get("superseded_by")

    direct_overlap = sorted(set(head_files) & set(main_files))
    cone_hits = _any_match(main_files, cone) if cone else []
    head_sensitive = sorted(p for p in head_files if is_sensitive(p))
    main_sensitive = sorted(p for p in main_files if is_sensitive(p))
    evidence_only = bool(head_files) and all(is_evidence_only(p) for p in head_files)

    head_zones = {top_semantic_zone(p) for p in head_sensitive}
    main_zones = {top_semantic_zone(p) for p in main_sensitive}
    zone_overlap = sorted(z for z in head_zones & main_zones if z)

    if superseded_by:
        freshness = "GREEN"
        disposition = "SUPERSEDED"
        recommendation = "SAFE_TO_CLOSE_AFTER_SUPERSESSION_CONFIRMATION"
        reason = f"explicitly superseded by {superseded_by}; retain history before closing"
    elif base_branch != "main":
        freshness = "AMBER"
        disposition = "STACKED"
        recommendation = "FOLLOW_STACKED_PARENT"
        reason = f"stacked on {base_branch}; evaluate against parent before main"
    elif direct_overlap:
        freshness = "RED"
        disposition = "SEMANTIC_STALE"
        recommendation = "REBASE_AND_RERUN"
        reason = "main changed files also changed by candidate"
    elif cone_hits:
        freshness = "RED"
        disposition = "DEPENDENCY_CONE_STALE"
        recommendation = "REBASE_AND_RERUN"
        reason = "main changed inside declared dependency cone"
    elif evidence_only:
        freshness = "GREEN"
        disposition = "EVIDENCE_ONLY_APPEND"
        recommendation = "KEEP_ACTIVE_NO_REBASE_REQUIRED"
        reason = "candidate is append-only evidence; behind_by is historical distance only"
    elif head_sensitive and (main_sensitive or zone_overlap):
        freshness = "AMBER"
        disposition = "EXECUTABLE_REVALIDATION_REQUIRED"
        recommendation = "RERUN_CHEAP_GATES"
        reason = "candidate changes sensitive surfaces while main also changed sensitive surfaces"
    elif head_sensitive and behind > 0:
        freshness = "AMBER"
        disposition = "EXECUTABLE_REVALIDATION_REQUIRED"
        recommendation = "RERUN_CHEAP_GATES"
        reason = "candidate changes sensitive surfaces; main advanced, but no dependency hit is proven"
    else:
        freshness = "GREEN"
        disposition = "NONOVERLAPPING_DELTA"
        recommendation = "KEEP_ACTIVE_NO_REBASE_REQUIRED"
        reason = "no direct or declared semantic dependency overlap found"

    return {
        "id": ident,
        "branch": branch,
        "base_branch": base_branch,
        "ahead_by": ahead,
        "behind_by": behind,
        "freshness": freshness,
        "disposition": disposition,
        "recommendation": recommendation,
        "reason": reason,
        "evidence": {
            "head_file_count": len(head_files),
            "main_since_base_file_count": len(main_files),
            "direct_overlap": direct_overlap,
            "dependency_cone_hits": cone_hits,
            "sensitive_head_files": head_sensitive,
            "sensitive_main_files": main_sensitive,
            "sensitive_zone_overlap": zone_overlap,
            "evidence_only_head": evidence_only,
        },
        "invariants": {
            "behind_by_alone_can_never_make_red": True,
            "destructive_action_performed": False,
        },
    }


def compile_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if str(snapshot.get("schema_version")) != SCHEMA_VERSION:
        errors.append(
            f"schema_version must be {SCHEMA_VERSION}, got {snapshot.get('schema_version')!r}"
        )
    candidates = snapshot.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        candidates = []
    for c in candidates:
        if not isinstance(c, dict):
            errors.append("candidate must be object")
        else:
            errors.extend(validate_candidate(c))
    if errors:
        return {"ok": False, "errors": errors}

    rows = [classify(c) for c in candidates]
    counts: dict[str, int] = {}
    recommendations: dict[str, int] = {}
    for row in rows:
        counts[row["freshness"]] = counts.get(row["freshness"], 0) + 1
        r = row["recommendation"]
        recommendations[r] = recommendations.get(r, 0) + 1

    rows.sort(
        key=lambda r: (
            RECOMMENDATION_ORDER.get(r["recommendation"], 99),
            -int(r["behind_by"]),
            str(r["id"]),
        )
    )
    return {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "main_head": snapshot.get("main_head"),
        "policy": "semantic_freshness_not_branch_age",
        "summary": {
            "candidate_count": len(rows),
            "freshness_counts": counts,
            "recommendation_counts": recommendations,
            "destructive_action_performed": False,
        },
        "candidates": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    snapshot = json.loads(args.snapshot.read_text(encoding="utf-8"))
    result = compile_snapshot(snapshot)
    text = json.dumps(result, indent=2, sort_keys=True)
    if args.output:
        args.output.write_text(text + "\n", encoding="utf-8")
    else:
        print(text)
    return 0 if result.get("ok") else 2


if __name__ == "__main__":
    raise SystemExit(main())
