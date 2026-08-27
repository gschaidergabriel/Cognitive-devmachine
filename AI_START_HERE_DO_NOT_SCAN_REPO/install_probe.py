#!/usr/bin/env python3
"""Project Frankenstein AI installer capability probe.

Non-destructive by default. It does not scan the repository and performs no network,
provider, credential, package-install, hook-install, or external effect action.

NATIVE is deliberately hard to obtain: callers must provide concrete proof paths for
lifecycle firing, durable state, and effect/result receipt in addition to the native
instruction surface and CLI executable. Otherwise the probe reports ADAPTED/DEGRADED.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path

HOSTS = (
    "claude-code",
    "codex-cli",
    "hermes-agent",
    "chatgpt-web",
    "claude-web",
    "grok-web",
    "generic",
)

CLI_ROUTES = {
    "claude-code": {"instruction": "CLAUDE.md", "executables": ("claude",)},
    "codex-cli": {"instruction": "AGENTS.md", "executables": ("codex",)},
    "hermes-agent": {"instruction": None, "executables": ("hermes",)},
}

MINIMAL_READ_SET = (
    "AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json",
    "HUMAN_READ_THIS/START_HERE.md",
    "DEV_SOURCE_RESEARCH/README.md",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)


def repo_root() -> Path:
    # This script lives exactly one directory below the repository root.
    return Path(__file__).resolve().parent.parent


def inside_repo(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    p = Path(raw)
    p = p if p.is_absolute() else root / p
    try:
        resolved = p.resolve(strict=False)
        resolved.relative_to(root.resolve())
    except (ValueError, OSError):
        raise ValueError(f"proof path must stay inside repository: {raw}")
    return resolved


def existing_proof(root: Path, raw: str | None) -> dict:
    if not raw:
        return {"provided": False, "exists": False, "path": None}
    p = inside_repo(root, raw)
    assert p is not None
    return {
        "provided": True,
        "exists": p.is_file(),
        "path": str(p.relative_to(root)) if p.exists() else str(p),
    }


def read_supervisor_summary(root: Path) -> dict:
    inbox = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    if not inbox.is_file():
        return {"read": False, "reason": "missing SUPERVISOR_INBOX.json"}
    try:
        data = json.loads(inbox.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"read": False, "reason": f"cannot parse inbox: {type(exc).__name__}"}

    free_only = data.get("free_only") if isinstance(data.get("free_only"), dict) else {}
    frontier = data.get("current_frontier") if isinstance(data.get("current_frontier"), dict) else {}
    return {
        "read": True,
        "schema_version": data.get("schema_version"),
        "supervisor_delta": data.get("supervisor_delta"),
        "provider_routes_admitted": free_only.get("provider_routes_admitted"),
        "together_forbidden": free_only.get("together_forbidden"),
        "remaining_together_paid_runs_authorized": free_only.get("remaining_together_paid_runs_authorized"),
        "runtime_provider_authority": frontier.get("runtime_provider_authority"),
    }


def missing_minimal_paths(root: Path) -> list[str]:
    return [rel for rel in MINIMAL_READ_SET if not (root / rel).is_file()]


def find_executable(candidates: tuple[str, ...]) -> str | None:
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return None


def classify(args: argparse.Namespace) -> dict:
    root = repo_root()
    out: dict = {
        "schema": "FRANKENSTEIN_AI_INSTALL_PROBE/v1",
        "host": args.host,
        "repo_root": str(root),
        "repo_resolved_dynamically": True,
        "network_called": False,
        "credentials_read": False,
        "provider_called": False,
        "repo_scanned": False,
        "mutated": False,
    }

    missing = missing_minimal_paths(root)
    out["minimal_read_set_missing"] = missing
    out["supervisor"] = read_supervisor_summary(root)

    if missing or not out["supervisor"].get("read"):
        out["result"] = "BLOCKED"
        out["reason"] = "minimal bootstrap surface missing or current supervisor inbox unreadable"
        return out

    proofs = {
        "lifecycle": existing_proof(root, args.lifecycle_proof),
        "state": existing_proof(root, args.state_proof),
        "receipt": existing_proof(root, args.receipt_proof),
    }
    out["proofs"] = proofs

    if args.host in CLI_ROUTES:
        route = CLI_ROUTES[args.host]
        instruction_rel = route["instruction"]
        instruction_ok = bool(instruction_rel and (root / instruction_rel).is_file())
        executable = find_executable(route["executables"])
        out["instruction_surface"] = instruction_rel
        out["instruction_surface_exists"] = instruction_ok
        out["executable"] = executable

        if args.host == "hermes-agent" and executable is None:
            out["result"] = "DEGRADED"
            out["reason"] = "no Hermes executable detected; no Hermes lifecycle contract is assumed"
            return out

        if args.host != "hermes-agent" and (not instruction_ok or executable is None):
            out["result"] = "BLOCKED"
            out["reason"] = "native CLI route lacks its instruction surface or executable"
            return out

        all_proofs = all(v["provided"] and v["exists"] for v in proofs.values())
        if executable and all_proofs and (instruction_ok or args.host == "hermes-agent"):
            out["result"] = "NATIVE"
            out["reason"] = "native route plus caller-supplied lifecycle/state/receipt proof files are present"
        elif executable:
            out["result"] = "ADAPTED"
            out["reason"] = "host route exists, but full lifecycle/state/receipt proof is not present"
        else:
            out["result"] = "DEGRADED"
            out["reason"] = "project context is readable but host executable is not detected"
        return out

    # Browser/web and generic routes cannot be inferred from local filesystem presence.
    out["result"] = "DEGRADED"
    out["reason"] = (
        "web/generic connected capabilities are session-specific and cannot be proven by this local probe; "
        "inventory them in the actual host before promotion"
    )
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Non-destructive Project Frankenstein AI host probe")
    p.add_argument("--host", required=True, choices=HOSTS)
    p.add_argument("--lifecycle-proof", help="repo-local file proving a real lifecycle/hook firing")
    p.add_argument("--state-proof", help="repo-local file proving durable state write/read-back")
    p.add_argument("--receipt-proof", help="repo-local file proving effect/result receipt when applicable")
    return p


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = classify(args)
    except ValueError as exc:
        print(json.dumps({"schema": "FRANKENSTEIN_AI_INSTALL_PROBE/v1", "result": "BLOCKED", "reason": str(exc)}, indent=2))
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("result") != "BLOCKED" else 1


if __name__ == "__main__":
    sys.exit(main())
