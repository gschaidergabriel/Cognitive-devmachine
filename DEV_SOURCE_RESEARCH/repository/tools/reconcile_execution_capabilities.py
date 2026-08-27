#!/usr/bin/env python3
"""Reconcile remote execution capability registry state from measured provider health.

This is a state-synchronization tool, not a provider verifier. provider_health_audit.py
owns live smoke execution. This tool consumes its sanitized result and removes stale
status divergence between EXTERNAL_RESEARCH_TOOL_REGISTRY and the measured health state.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "research_entity" / "global" / "EXTERNAL_RESEARCH_TOOL_REGISTRY.json"
HEALTH = ROOT / "research_entity" / "runtime" / "PROVIDER_HEALTH.json"

EXECUTION_TOOLS = {
    "e2b_sandbox",
    "judge0_execute",
    "piston_execute",
    "sandboxapi_sandbox",
}

SANDBOXAPI_DEFAULT = {
    "tool_name": "sandboxapi_sandbox",
    "provider": "SandboxAPI",
    "script": "tools/sandboxapi_sandbox.py",
    "class": "remote_code_sandbox",
    "requires_secret": ["RAPIDAPI_KEY"],
    "credential_required": True,
    "auth_transport": "X-RapidAPI-Key; current direct api.sandboxapi.dev endpoint with RapidAPI gateway fallback",
    "preferred_for": [
        "isolated execution",
        "multi-language execution",
        "reproducibility checks",
        "bounded untrusted code execution",
    ],
    "evidence_class": "isolated_runtime_experiment",
    "verification_receipt": "research_entity/runtime/sandboxapi_verification.json",
    "capability_ref": "research_entity/global/SANDBOXAPI_RESEARCH_CAPABILITY.json",
}


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"expected object: {path}")
    return value


def reconcile(registry: dict[str, Any], health: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    tools = registry.setdefault("tools", [])
    if not isinstance(tools, list):
        raise ValueError("registry.tools must be a list")

    by_name = {
        str(item.get("tool_name")): item
        for item in tools
        if isinstance(item, dict) and item.get("tool_name")
    }
    added = []
    if "sandboxapi_sandbox" not in by_name:
        item = dict(SANDBOXAPI_DEFAULT)
        tools.append(item)
        by_name["sandboxapi_sandbox"] = item
        added.append("sandboxapi_sandbox")

    health_map = {
        str(item.get("tool")): item
        for item in health.get("results", [])
        if isinstance(item, dict) and item.get("tool")
    }
    changed: list[dict[str, Any]] = []
    for name in sorted(EXECUTION_TOOLS):
        entry = by_name.get(name)
        observed = health_map.get(name)
        if entry is None or observed is None:
            continue
        before = {
            "status": entry.get("status"),
            "runtime_health_status": entry.get("runtime_health_status"),
            "runtime_health_checked_at": entry.get("runtime_health_checked_at"),
        }
        runtime_status = str(observed.get("status") or "UNKNOWN")
        checked_at = (
            (observed.get("receipt") or {}).get("checked_at")
            if isinstance(observed.get("receipt"), dict)
            else None
        ) or health.get("checked_at")
        entry["runtime_health_status"] = runtime_status
        entry["runtime_health_checked_at"] = checked_at
        entry["runtime_health_source"] = "research_entity/runtime/PROVIDER_HEALTH.json"
        entry["status"] = runtime_status
        if runtime_status == "RUNTIME_VERIFIED":
            entry.pop("blocker", None)
        after = {
            "status": entry.get("status"),
            "runtime_health_status": entry.get("runtime_health_status"),
            "runtime_health_checked_at": entry.get("runtime_health_checked_at"),
        }
        if before != after:
            changed.append({"tool": name, "before": before, "after": after})

    registry["execution_capability_reconciliation"] = {
        "source": "research_entity/runtime/PROVIDER_HEALTH.json",
        "health_checked_at": health.get("checked_at"),
        "rule": "Measured provider health outranks stale registry status; provider health does not by itself prove worker-surface invocability.",
    }
    return registry, {"added": added, "changed": changed}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    registry = load(REGISTRY)
    health = load(HEALTH)
    updated, delta = reconcile(registry, health)
    if args.write:
        REGISTRY.write_text(json.dumps(updated, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(delta, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
