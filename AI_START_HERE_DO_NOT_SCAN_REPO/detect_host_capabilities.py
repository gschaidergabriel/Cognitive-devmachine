#!/usr/bin/env python3
"""Detect local host capabilities for the Frankenstein AI entry layer.

No network calls. No installs. No provider key reads. The result is a capability
snapshot and suggested integration candidate, not an installation-success receipt.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path

MARKERS = (
    "CLAY_EXECUTION_AUTHORITY.md",
    "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
)
TOOLS = {
    "git": "git",
    "python": "python3",
    "claude_code": "claude",
    "codex_cli": "codex",
    "hermes_agent": "hermes",
}


def find_repo_root(start: Path) -> Path | None:
    start = start.resolve()
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
        if all((candidate / marker).exists() for marker in MARKERS):
            return candidate
    return None


def command_paths() -> dict[str, str | None]:
    return {name: shutil.which(binary) for name, binary in TOOLS.items()}


def classify(snapshot: dict) -> dict:
    commands = snapshot["commands"]
    repo = snapshot["repo"]
    writable = bool(repo.get("writable"))
    git_ok = bool(commands.get("git")) and bool(repo.get("root"))

    routes = {
        "claude_code": "NATIVE_CANDIDATE" if git_ok and writable and commands.get("claude_code") else "BLOCKED",
        "codex_cli": "NATIVE_CANDIDATE" if git_ok and writable and commands.get("codex_cli") else "BLOCKED",
        "hermes_agent": "ADAPTED_CANDIDATE" if git_ok and writable and commands.get("hermes_agent") else "BLOCKED",
        "chatgpt_web": "DEGRADED",
        "claude_web": "DEGRADED",
        "grok_web": "DEGRADED",
        "generic_fallback": "ADAPTED_CANDIDATE" if git_ok and writable else ("DEGRADED_CANDIDATE" if git_ok else "BLOCKED"),
    }
    return routes


def snapshot(start: Path) -> dict:
    root = find_repo_root(start)
    repo = {
        "root": str(root) if root else None,
        "writable": bool(root and os.access(root, os.W_OK)),
        "authority_pointer_present": bool(root and (root / "CLAY_EXECUTION_AUTHORITY.md").is_file()),
        "bootstrap_present": bool(root and (root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json").is_file()),
        "supervisor_inbox_present": bool(root and (root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json").is_file()),
    }
    result = {
        "schema": "FRANKENSTEIN_HOST_CAPABILITY_SNAPSHOT/v1",
        "start": str(start.resolve()),
        "commands": command_paths(),
        "repo": repo,
        "network_checked": False,
        "provider_credentials_checked": False,
        "hooks_verified": False,
        "durable_write_verified": False,
        "effect_receipt_verified": False,
    }
    result["routes"] = classify(result)
    result["installation_result"] = "UNVERIFIED_CAPABILITY_SNAPSHOT_ONLY"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default=".")
    parser.add_argument("--compact", action="store_true")
    args = parser.parse_args()
    result = snapshot(Path(args.start))
    print(json.dumps(result, indent=None if args.compact else 2, sort_keys=True))


if __name__ == "__main__":
    main()
