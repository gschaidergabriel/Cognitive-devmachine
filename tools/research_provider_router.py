#!/usr/bin/env python3
"""Quota-aware provider planner and manifest validator for RAE research runs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity" / "global" / "EXTERNAL_RESEARCH_TOOL_REGISTRY.json"
QUOTA = ROOT / "research_entity" / "runtime" / "TOOL_QUOTA_STATE.json"

ALLOWED_FALLBACKS = {
    "NOT_APPLICABLE",
    "QUOTA_EXHAUSTED",
    "QUOTA_EXHAUSTED_CACHED",
    "RATE_LIMITED",
    "PROVIDER_UNAVAILABLE",
    "CREDENTIAL_UNAVAILABLE",
    "CONNECTOR_BLOCKED",
    "RUNTIME_UNAVAILABLE",
    "DUPLICATE_EVIDENCE_NO_INFORMATION_GAIN",
}

FAILURE_STATUSES_REQUIRING_FALLBACK = {
    "QUOTA_EXHAUSTED",
    "RATE_LIMITED",
    "AUTH_FAILED",
    "PROVIDER_ERROR",
    "RUNTIME_ERROR",
}

BUNDLES = {
    "scholarly": [
        {"tool": "openalex_search", "mode": "MUST_ATTEMPT"},
        {"tool": "arxiv_search", "mode": "MUST_ATTEMPT"},
        {"tool": "semantic_scholar_search", "mode": "MUST_ATTEMPT"},
    ],
    "bibliographic": [
        {"tool": "crossref_lookup", "mode": "MUST_ATTEMPT"},
    ],
    "current_web": [
        {"tool": "tavily_search", "mode": "MUST_ATTEMPT"},
        {"tool": "exa_search", "mode": "MUST_ATTEMPT"},
        {"tool": "duckduckgo_search", "mode": "FALLBACK"},
    ],
    "implementation": [
        {"tool": "github_connector", "mode": "MUST_ATTEMPT"},
    ],
    "executable": [
        {"tool": "local_sandbox", "mode": "MUST_ATTEMPT"},
        {"tool": "e2b_sandbox", "mode": "MUST_ATTEMPT"},
        {"tool": "piston_execute", "mode": "FALLBACK"},
        {"tool": "judge0_execute", "mode": "FALLBACK"},
    ],
    "model_experiment": [
        {"tool": "huggingface_inference", "mode": "MUST_ATTEMPT"},
    ],
}

LEGACY_FALLBACK = [
    "native_web",
    "direct_primary_sources",
    "github_connector",
    "duckduckgo_search",
    "local_sandbox",
    "archived_rae_sources",
]


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return default


def tool_statuses() -> dict[str, dict]:
    registry = load_json(REGISTRY, {"tools": []})
    return {x["tool_name"]: x for x in registry.get("tools", [])}


def quota_state() -> dict:
    return load_json(QUOTA, {"schema_version": "1.0", "providers": {}})


def unavailable_reason(tool: str, status: dict[str, dict], quota: dict) -> str | None:
    q = quota.get("providers", {}).get(tool, {})
    state = q.get("state")
    if state in {"QUOTA_EXHAUSTED", "QUOTA_EXHAUSTED_CACHED", "RATE_LIMITED"}:
        reset_at = q.get("reset_at")
        if reset_at:
            try:
                reset = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
                if reset <= datetime.now(timezone.utc):
                    return None
            except ValueError:
                pass
        return state

    if tool in {"github_connector", "local_sandbox"}:
        return None
    item = status.get(tool)
    if not item:
        return "PROVIDER_UNAVAILABLE"
    st = item.get("status", "")
    if st == "RUNTIME_VERIFIED":
        return None
    if "CREDENTIAL_NOT_PERSISTED" in st:
        return "CREDENTIAL_UNAVAILABLE"
    if "PENDING_RUNTIME_VERIFICATION" in st or "NOT_RUNTIME_VERIFIED" in st:
        return "RUNTIME_UNAVAILABLE"
    return "PROVIDER_UNAVAILABLE"


def plan(classes: list[str]) -> dict:
    status = tool_statuses()
    quota = quota_state()
    selected = []
    seen = set()
    for cls in classes:
        for spec in BUNDLES.get(cls, []):
            key = (spec["tool"], spec["mode"])
            if key in seen:
                continue
            seen.add(key)
            row = dict(spec)
            row["class"] = cls
            row["availability_blocker"] = unavailable_reason(spec["tool"], status, quota)
            selected.append(row)
    return {
        "schema_version": "1.1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classes": classes,
        "planned_tools": selected,
        "legacy_fallback": LEGACY_FALLBACK,
        "allowed_fallback_reasons": sorted(ALLOWED_FALLBACKS),
        "rule": "MUST_ATTEMPT tools require an attempt while available; blocked or failed attempts require an explicit legacy fallback where applicable.",
    }


def validate_manifest(path: Path) -> dict:
    manifest = load_json(path, {})
    planned = manifest.get("planned_tools", [])
    attempts = {x.get("tool"): x for x in manifest.get("attempts", [])}
    fallback_attempts = {x.get("tool"): x for x in manifest.get("fallback_attempts", [])}
    violations = []

    for spec in planned:
        if spec.get("mode") != "MUST_ATTEMPT":
            continue
        tool = spec.get("tool")
        blocker = spec.get("availability_blocker")
        attempt = attempts.get(tool)

        if blocker:
            if blocker not in ALLOWED_FALLBACKS:
                violations.append({"tool": tool, "reason": blocker})
                continue
            if blocker != "NOT_APPLICABLE" and not fallback_attempts:
                violations.append({"tool": tool, "reason": f"{blocker}_WITHOUT_FALLBACK"})
            continue

        if not attempt or not attempt.get("status"):
            violations.append({"tool": tool, "reason": "MISSING_ATTEMPT"})
            continue

        status = attempt.get("status")
        if status in FAILURE_STATUSES_REQUIRING_FALLBACK:
            reason = attempt.get("fallback_reason")
            if reason not in ALLOWED_FALLBACKS and status not in ALLOWED_FALLBACKS:
                violations.append({"tool": tool, "reason": "INVALID_FALLBACK_REASON"})
                continue
            if not fallback_attempts:
                violations.append({"tool": tool, "reason": f"{status}_WITHOUT_FALLBACK"})

    return {"ok": not violations, "violations": violations}


def record_quota(tool: str, state: str, reset_at: str | None, note: str | None):
    data = quota_state()
    data.setdefault("providers", {})[tool] = {
        "state": state,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "reset_at": reset_at,
        "note": note,
    }
    QUOTA.parent.mkdir(parents=True, exist_ok=True)
    QUOTA.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return {"ok": True, "tool": tool, "state": state}


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("plan")
    p.add_argument("--class", dest="classes", action="append", required=True, choices=sorted(BUNDLES))

    v = sub.add_parser("validate-manifest")
    v.add_argument("path")

    r = sub.add_parser("record-quota")
    r.add_argument("tool")
    r.add_argument("state", choices=["AVAILABLE", "QUOTA_EXHAUSTED", "QUOTA_EXHAUSTED_CACHED", "RATE_LIMITED"])
    r.add_argument("--reset-at")
    r.add_argument("--note")

    args = ap.parse_args()
    if args.cmd == "plan":
        out = plan(args.classes)
    elif args.cmd == "validate-manifest":
        out = validate_manifest(Path(args.path))
        if not out["ok"]:
            print(json.dumps(out, indent=2))
            raise SystemExit(2)
    else:
        out = record_quota(args.tool, args.state, args.reset_at, args.note)
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
