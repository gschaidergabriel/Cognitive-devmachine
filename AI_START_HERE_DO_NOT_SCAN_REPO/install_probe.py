#!/usr/bin/env python3
"""Non-destructive Project Frankenstein host capability probe.

The probe performs no network/provider/credential/package-install/hook-install action.
It does not scan the repository. It reads only the curated bootstrap surfaces plus
optional explicit proof receipts supplied by the caller.
"""
from __future__ import annotations

import argparse
import json
import shutil
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
    "CLAY_EXECUTION_AUTHORITY.md",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
    "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
    "AI_START_HERE_DO_NOT_SCAN_REPO/README.md",
    "DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_SOURCE_INDEX.json",
)

PROOF_SCHEMA = "FRANKENSTEIN_HOST_PROOF/v1"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def parse_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def supervisor_summary(root: Path) -> dict:
    path = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
    try:
        data = parse_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return {"read": False, "reason": type(exc).__name__}
    free = data.get("free_only") if isinstance(data.get("free_only"), dict) else {}
    frontier = data.get("current_frontier") if isinstance(data.get("current_frontier"), dict) else {}
    return {
        "read": True,
        "schema_version": data.get("schema_version"),
        "supervisor_delta": data.get("supervisor_delta"),
        "runtime_provider_authority": frontier.get("runtime_provider_authority"),
        "provider_routes_admitted": free.get("provider_routes_admitted"),
        "together_forbidden": free.get("together_forbidden"),
        "remaining_together_paid_runs_authorized": free.get("remaining_together_paid_runs_authorized"),
    }


def find_executable(names: tuple[str, ...]) -> str | None:
    for name in names:
        found = shutil.which(name)
        if found:
            return found
    return None


def resolve_repo_local(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"proof path must remain inside repository: {raw}") from exc
    return resolved


def proof_receipt(root: Path, raw: str | None, *, host: str, kind: str) -> dict:
    if not raw:
        return {"provided": False, "valid": False}
    path = resolve_repo_local(root, raw)
    assert path is not None
    result = {"provided": True, "valid": False, "path": str(path)}
    if not path.is_file():
        result["reason"] = "missing_file"
        return result
    try:
        data = parse_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        result["reason"] = type(exc).__name__
        return result
    required = {
        "schema": PROOF_SCHEMA,
        "host": host,
        "kind": kind,
        "observed": True,
    }
    mismatches = {k: {"expected": v, "actual": data.get(k)} for k, v in required.items() if data.get(k) != v}
    if not data.get("receipt_id"):
        mismatches["receipt_id"] = {"expected": "non-empty", "actual": data.get("receipt_id")}
    if not data.get("observed_at"):
        mismatches["observed_at"] = {"expected": "non-empty", "actual": data.get("observed_at")}
    if mismatches:
        result["reason"] = "schema_mismatch"
        result["mismatches"] = mismatches
        return result
    result["valid"] = True
    result["receipt_id"] = data.get("receipt_id")
    result["observed_at"] = data.get("observed_at")
    result["scope"] = data.get("scope")
    return result


def classify(args: argparse.Namespace) -> dict:
    root = repo_root()
    missing = [rel for rel in MINIMAL_READ_SET if not (root / rel).is_file()]
    out: dict = {
        "schema": "FRANKENSTEIN_AI_INSTALL_PROBE/v1",
        "host": args.host,
        "repo_root": str(root),
        "repo_resolved_from_installer_location": True,
        "repo_scanned": False,
        "network_called": False,
        "credentials_read": False,
        "provider_called": False,
        "mutated": False,
        "minimal_read_set_missing": missing,
        "supervisor": supervisor_summary(root),
    }

    if missing or not out["supervisor"].get("read"):
        out["result"] = "BLOCKED"
        out["reason"] = "minimal curated bootstrap missing or current supervisor unreadable"
        return out

    proofs = {
        "lifecycle": proof_receipt(root, args.lifecycle_proof, host=args.host, kind="lifecycle"),
        "state": proof_receipt(root, args.state_proof, host=args.host, kind="state"),
        "effect": proof_receipt(root, args.effect_proof, host=args.host, kind="effect"),
    }
    out["proofs"] = proofs

    if args.host in CLI_ROUTES:
        route = CLI_ROUTES[args.host]
        instruction = route["instruction"]
        executable = find_executable(route["executables"])
        instruction_ok = True if instruction is None else (root / instruction).is_file()
        out["instruction_surface"] = instruction
        out["instruction_surface_exists"] = instruction_ok
        out["executable"] = executable

        if executable is None:
            out["result"] = "DEGRADED" if args.host == "hermes-agent" else "BLOCKED"
            out["reason"] = "host executable not detected in this environment"
            return out
        if not instruction_ok:
            out["result"] = "BLOCKED"
            out["reason"] = "native instruction surface missing"
            return out

        required_proofs = [proofs["lifecycle"], proofs["state"]]
        if args.effects_claimed:
            required_proofs.append(proofs["effect"])
        if all(p.get("valid") for p in required_proofs):
            out["result"] = "NATIVE"
            out["reason"] = "native CLI surface detected and required explicit host proof receipts validate"
        else:
            out["result"] = "ADAPTED"
            out["reason"] = "CLI/instruction surface exists, but full lifecycle/state/effect proof is not established"
        return out

    # Web/generic capability is session-specific and cannot be inferred from local files.
    out["result"] = "DEGRADED"
    out["reason"] = "web/generic session capabilities require observation in the actual host; local probe cannot invent them"
    return out


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Non-destructive Project Frankenstein host capability probe")
    p.add_argument("--host", required=True, choices=HOSTS)
    p.add_argument("--lifecycle-proof", help=f"repo-local JSON receipt with schema {PROOF_SCHEMA} and kind=lifecycle")
    p.add_argument("--state-proof", help=f"repo-local JSON receipt with schema {PROOF_SCHEMA} and kind=state")
    p.add_argument("--effect-proof", help=f"repo-local JSON receipt with schema {PROOF_SCHEMA} and kind=effect")
    p.add_argument("--effects-claimed", action="store_true", help="require a validated effect receipt for NATIVE status")
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        result = classify(args)
    except ValueError as exc:
        result = {"schema": "FRANKENSTEIN_AI_INSTALL_PROBE/v1", "result": "BLOCKED", "reason": str(exc)}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 1 if result.get("result") == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
