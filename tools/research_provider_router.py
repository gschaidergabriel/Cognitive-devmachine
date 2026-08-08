#!/usr/bin/env python3
"""Quota/health-aware provider planner and execution-manifest validator for RAE."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity" / "global" / "EXTERNAL_RESEARCH_TOOL_REGISTRY.json"
CAPABILITY_FILES = [
    ROOT / "research_entity" / "global" / "NVIDIA_RESEARCH_CAPABILITY.json",
    ROOT / "research_entity" / "global" / "OPENROUTER_RESEARCH_CAPABILITY.json",
    ROOT / "research_entity" / "global" / "SANDBOXAPI_RESEARCH_CAPABILITY.json",
]
QUOTA = ROOT / "research_entity" / "runtime" / "TOOL_QUOTA_STATE.json"
HEALTH = ROOT / "research_entity" / "runtime" / "PROVIDER_HEALTH.json"
GROQ_VERIFY = ROOT / "research_entity" / "runtime" / "groq_verification.json"

ALLOWED_FALLBACKS = {
    "NOT_APPLICABLE", "QUOTA_EXHAUSTED", "QUOTA_EXHAUSTED_CACHED", "QUOTA_OR_PLAN_EXHAUSTED",
    "RATE_LIMITED", "PROVIDER_UNAVAILABLE", "NETWORK_OR_PROVIDER_UNAVAILABLE", "CREDENTIAL_UNAVAILABLE",
    "CREDENTIAL_BLOCKED", "AUTH_FAILED", "HTTP_ERROR", "DEPENDENCY_MISSING", "CONNECTOR_BLOCKED",
    "RUNTIME_UNAVAILABLE", "DUPLICATE_EVIDENCE_NO_INFORMATION_GAIN", "MODEL_IDENTITY_UNAVAILABLE",
    "SUBSCRIPTION_UNAVAILABLE",
}

FAILURE_STATUSES_REQUIRING_FALLBACK = {
    "QUOTA_EXHAUSTED", "QUOTA_OR_PLAN_EXHAUSTED", "RATE_LIMITED", "AUTH_FAILED", "HTTP_ERROR",
    "PROVIDER_ERROR", "PROVIDER_UNAVAILABLE", "NETWORK_OR_PROVIDER_UNAVAILABLE", "CREDENTIAL_UNAVAILABLE",
    "CREDENTIAL_BLOCKED", "DEPENDENCY_MISSING", "RUNTIME_ERROR", "RUNTIME_UNAVAILABLE", "CONNECTOR_BLOCKED",
    "MODEL_IDENTITY_UNAVAILABLE", "SUBSCRIPTION_UNAVAILABLE",
}

BUNDLES = {
    "scholarly": [
        {"tool": "openalex_search", "mode": "MUST_ATTEMPT"},
        {"tool": "arxiv_search", "mode": "MUST_ATTEMPT"},
        {"tool": "semantic_scholar_search", "mode": "MUST_ATTEMPT"},
    ],
    "bibliographic": [{"tool": "crossref_lookup", "mode": "MUST_ATTEMPT"}],
    "current_web": [
        {"tool": "tavily_search", "mode": "MUST_ATTEMPT"},
        {"tool": "exa_search", "mode": "MUST_ATTEMPT"},
        {"tool": "duckduckgo_search", "mode": "FALLBACK"},
    ],
    "implementation": [{"tool": "github_connector", "mode": "MUST_ATTEMPT"}],
    "executable": [
        {"tool": "local_sandbox", "mode": "MUST_ATTEMPT"},
        {"tool": "e2b_sandbox", "mode": "MUST_ATTEMPT"},
        {"tool": "judge0_execute", "mode": "FALLBACK"},
        {"tool": "piston_execute", "mode": "FALLBACK"},
    ],
    "claycode_executable": [
        {"tool": "sandboxapi_sandbox", "mode": "MUST_ATTEMPT"},
        {"tool": "local_sandbox", "mode": "FALLBACK"},
        {"tool": "judge0_execute", "mode": "FALLBACK"},
    ],
    "model_experiment": [
        {"tool": "nvidia_nim", "mode": "MUST_ATTEMPT"},
        {"tool": "openrouter_inference", "mode": "FALLBACK"},
        {"tool": "groq_inference", "mode": "FALLBACK"},
        {"tool": "huggingface_inference", "mode": "FALLBACK"},
    ],
    "small_model_experiment": [
        {"tool": "nvidia_nim", "mode": "MUST_ATTEMPT"},
        {"tool": "openrouter_inference", "mode": "FALLBACK"},
        {"tool": "groq_inference", "mode": "FALLBACK"},
        {"tool": "huggingface_inference", "mode": "FALLBACK"},
    ],
    "embedding_experiment": [
        {"tool": "nvidia_nim", "mode": "MUST_ATTEMPT"},
    ],
}

LEGACY_FALLBACK = [
    "native_web", "direct_primary_sources", "github_connector", "duckduckgo_search",
    "local_sandbox", "judge0_execute", "archived_rae_sources",
]


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def registry_state() -> dict:
    data = load_json(REGISTRY, {"tools": []})
    tools = list(data.get("tools", []))
    known = {x.get("tool_name") for x in tools}
    for path in CAPABILITY_FILES:
        item = load_json(path, {})
        if item.get("tool_name") and item.get("tool_name") not in known:
            tools.append(item)
            known.add(item.get("tool_name"))
    data["tools"] = tools
    data["capability_extensions"] = [str(p.relative_to(ROOT)) for p in CAPABILITY_FILES if p.exists()]
    return data


def tool_statuses() -> dict[str, dict]:
    return {x["tool_name"]: x for x in registry_state().get("tools", [])}


def quota_state() -> dict:
    return load_json(QUOTA, {"schema_version": "1.0", "providers": {}})


def health_state() -> tuple[datetime | None, dict[str, dict]]:
    data = load_json(HEALTH, {"results": []})
    checked = None
    try:
        if data.get("checked_at"):
            checked = datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00"))
    except ValueError:
        checked = None
    return checked, {x.get("tool"): x for x in data.get("results", []) if x.get("tool")}


def _health_blocker(tool: str) -> str | None:
    if tool == "groq_inference":
        receipt = load_json(GROQ_VERIFY, {})
        if receipt.get("status") == "RUNTIME_VERIFIED" and receipt.get("model") == "llama-3.1-8b-instant":
            return None
        return "RUNTIME_UNAVAILABLE"
    if tool in {"nvidia_nim", "openrouter_inference", "sandboxapi_sandbox"}:
        return None
    checked, items = health_state()
    if checked is None or (datetime.now(timezone.utc) - checked).total_seconds() > 21600:
        return None
    item = items.get(tool)
    if not item:
        return None
    st = item.get("status")
    if st == "RUNTIME_VERIFIED":
        return None
    if st in ALLOWED_FALLBACKS:
        return st
    if st == "SMOKE_FAILED":
        return "PROVIDER_UNAVAILABLE"
    return None


def unavailable_reason(tool: str, status: dict[str, dict], quota: dict) -> str | None:
    q = quota.get("providers", {}).get(tool, {})
    state = q.get("state")
    if state in {"QUOTA_EXHAUSTED", "QUOTA_EXHAUSTED_CACHED", "RATE_LIMITED"}:
        reset_at = q.get("reset_at")
        if reset_at:
            try:
                reset = datetime.fromisoformat(reset_at.replace("Z", "+00:00"))
                if reset <= datetime.now(timezone.utc):
                    state = None
            except ValueError:
                pass
        if state:
            return state
    if tool in {"github_connector", "local_sandbox"}:
        return None
    health_blocker = _health_blocker(tool)
    if health_blocker:
        return health_blocker
    if tool == "groq_inference":
        return None
    item = status.get(tool)
    if not item:
        return "PROVIDER_UNAVAILABLE"
    st = str(item.get("status", ""))
    if st.startswith("RUNTIME_VERIFIED"):
        return None
    if "NOT_SUBSCRIBED" in st:
        return "SUBSCRIPTION_UNAVAILABLE"
    if "CREDENTIAL" in st:
        return "CREDENTIAL_UNAVAILABLE"
    if "RATE_LIMIT" in st:
        return "RATE_LIMITED"
    if "PENDING_RUNTIME_VERIFICATION" in st or "NOT_RUNTIME_VERIFIED" in st:
        return "RUNTIME_UNAVAILABLE"
    return "PROVIDER_UNAVAILABLE"


def invocation_surface(tool: str, registry: dict) -> str:
    if tool in {"github_connector", "local_sandbox"}:
        return "DIRECT_RUNTIME"
    if tool in {"nvidia_nim", "openrouter_inference"}:
        return "DEDICATED_GITHUB_RUNNER"
    if tool == "groq_inference":
        return "DIRECT_ADAPTER_OR_REPO_RUNNER_BRIDGE"
    bridge = registry.get("worker_invocation_bridge", {})
    if bridge.get("status") == "OPERATIONAL":
        return "DIRECT_ADAPTER_OR_REPO_RUNNER_BRIDGE"
    return "DIRECT_ADAPTER_IF_AVAILABLE"


def plan(classes: list[str]) -> dict:
    registry = registry_state()
    status = {x["tool_name"]: x for x in registry.get("tools", [])}
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
            row["invocation_surface"] = invocation_surface(spec["tool"], registry)
            if spec["tool"] == "nvidia_nim":
                row["verified_small_model"] = "nvidia/nemotron-mini-4b-instruct"
                row["executed_model_class"] = "4B"
                row["evidence_role"] = "direct_generic_4b_hosted_runtime"
                row["embedding_model"] = "nvidia/nv-embedqa-e5-v5"
                row["qwen3_4b_status"] = "NOT_EXPOSED_IN_OBSERVED_CATALOG"
            elif spec["tool"] == "openrouter_inference":
                row["verified_small_model"] = "google/gemma-3-4b-it"
                row["executed_model_class"] = "4B"
                row["evidence_role"] = "direct_generic_4b_hosted_runtime"
                row["qwen3_4b_status"] = "ACCOUNT_CATALOG_UNAVAILABLE"
            elif spec["tool"] == "groq_inference":
                row["default_model"] = "llama-3.1-8b-instant"
                row["evidence_role"] = "8b_proxy_for_4b"
                row["proxy_policy"] = "research_entity/global/SMALL_MODEL_PROXY_POLICY.md"
            elif spec["tool"] == "sandboxapi_sandbox":
                row["capability"] = "research_entity/global/SANDBOXAPI_RESEARCH_CAPABILITY.json"
                row["evidence_role"] = "isolated_runtime_experiment"
                row["preferred_for"] = "real ClayCode compiler/parser/typechecker/interpreter/fuzz execution"
            selected.append(row)
    return {
        "schema_version": "1.5",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "classes": classes,
        "planned_tools": selected,
        "legacy_fallback": LEGACY_FALLBACK,
        "allowed_fallback_reasons": sorted(ALLOWED_FALLBACKS),
        "bridge": registry.get("worker_invocation_bridge"),
        "rule": "MUST_ATTEMPT tools require an attempt while healthy. ClayCode executable research prefers SandboxAPI once runtime-verified and records SUBSCRIPTION_UNAVAILABLE separately from runtime failure; local/Judge0 cover the blocked path. Verified NVIDIA Nemotron-Mini-4B is direct generic-4B hosted evidence but never Qwen-specific evidence. OpenRouter Gemma-3-4B is an independent generic-4B fallback. Groq remains an explicitly labeled 8B proxy. Target/local hardware/training/live-system questions remain open unless the executed capability actually matches them. Every blocked/failed MUST_ATTEMPT tool requires a successful covering fallback.",
    }


def _fallback_covers(tool: str, attempts: list[dict]) -> bool:
    for attempt in attempts:
        if attempt.get("status") != "SUCCESS":
            continue
        covers = attempt.get("covers") or []
        if isinstance(covers, str):
            covers = [covers]
        if tool in covers or attempt.get("fallback_for") == tool:
            return True
    return False


def validate_manifest(path: Path) -> dict:
    manifest = load_json(path, {})
    planned = manifest.get("planned_tools", [])
    attempts = {x.get("tool"): x for x in manifest.get("attempts", [])}
    fallback_attempts = manifest.get("fallback_attempts", [])
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
            if blocker != "NOT_APPLICABLE" and not _fallback_covers(tool, fallback_attempts):
                violations.append({"tool": tool, "reason": f"{blocker}_WITHOUT_COVERING_FALLBACK"})
            continue
        if not attempt or not attempt.get("status"):
            violations.append({"tool": tool, "reason": "MISSING_ATTEMPT"})
            continue
        attempt_status = attempt.get("status")
        if attempt_status in FAILURE_STATUSES_REQUIRING_FALLBACK:
            reason = attempt.get("fallback_reason") or attempt_status
            if reason not in ALLOWED_FALLBACKS:
                violations.append({"tool": tool, "reason": "INVALID_FALLBACK_REASON"})
                continue
            if not _fallback_covers(tool, fallback_attempts):
                violations.append({"tool": tool, "reason": f"{attempt_status}_WITHOUT_COVERING_FALLBACK"})
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
