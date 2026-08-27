#!/usr/bin/env python3
"""Non-networking AI installation/capability probe for Triggerword 3.

This probe does not install packages, call an LLM/provider, read secrets, scan the
repository, or trigger a host merely to manufacture installation evidence. It:

* resolves the repository from this file's location;
* reads only the declared bootstrap surfaces;
* reads the current supervisor inbox before classification;
* checks only route-relevant executables/instruction files;
* optionally performs one reversible local project write/read-back;
* accepts pre-existing hook/effect evidence without claiming to have created it;
* emits exactly NATIVE / ADAPTED / DEGRADED / BLOCKED.

NATIVE is reserved for declared project-native CLI routes with real host presence,
local write/read-back and supplied hook evidence. Hermes/web/generic have no native
project lifecycle contract in v1, so this probe cannot label them NATIVE.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

HOSTS = (
    "claude-code",
    "codex-cli",
    "hermes-agent",
    "chatgpt-web",
    "claude-web",
    "grok-web",
    "generic",
)
RESULTS = {"NATIVE", "ADAPTED", "DEGRADED", "BLOCKED"}
WEB_HOSTS = {"chatgpt-web", "claude-web", "grok-web"}

MINIMAL_READ_SET = (
    "AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json",
    "HUMAN_READ_THIS/START_HERE.md",
    "DEV_SOURCE_RESEARCH/README.md",
    "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
)


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_object(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"expected JSON object: {path}")
    return data


def repo_local_file(root: Path, raw: str | None) -> Path | None:
    if not raw:
        return None
    candidate = Path(raw)
    candidate = candidate if candidate.is_absolute() else root / candidate
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise ValueError(f"evidence path must stay inside repository: {raw}") from exc
    return resolved


def evidence_file(root: Path, raw: str | None) -> dict[str, Any]:
    path = repo_local_file(root, raw)
    if path is None:
        return {"provided": False, "exists": False, "nonempty": False, "path": None, "sha256": None}
    exists = path.is_file()
    payload = path.read_bytes() if exists else b""
    return {
        "provided": True,
        "exists": exists,
        "nonempty": bool(payload),
        "path": str(path.relative_to(root)) if exists else str(path),
        "sha256": hashlib.sha256(payload).hexdigest() if payload else None,
    }


def current_supervisor(root: Path) -> dict[str, Any]:
    rel = Path("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    data = load_object(root / rel)
    free_only = data.get("free_only") if isinstance(data.get("free_only"), dict) else {}
    frontier = data.get("current_frontier") if isinstance(data.get("current_frontier"), dict) else {}
    return {
        "path": str(rel),
        "read": True,
        "schema_version": data.get("schema_version"),
        "supervisor_delta": data.get("supervisor_delta"),
        "provider_routes_admitted": free_only.get("provider_routes_admitted"),
        "together_forbidden": free_only.get("together_forbidden"),
        "remaining_together_paid_runs_authorized": free_only.get("remaining_together_paid_runs_authorized"),
        "runtime_provider_authority": frontier.get("runtime_provider_authority"),
    }


def reversible_project_write_probe(root: Path) -> dict[str, Any]:
    """Prove local filesystem write/read-back and clean the marker afterward.

    This is NOT proof of a canonical UnifiedDB/EntityOS state commit.
    """
    directory = root / "AI_START_HERE_DO_NOT_SCAN_REPO"
    marker: Path | None = None
    payload = b"FRANKENSTEIN_INSTALL_PROBE_LOCAL_WRITE_READBACK_V1\n"
    try:
        fd, raw_path = tempfile.mkstemp(prefix=".install_probe_", suffix=".tmp", dir=directory)
        marker = Path(raw_path)
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        observed = marker.read_bytes()
        return {
            "attempted": True,
            "passed": observed == payload,
            "scope": "REVERSIBLE_LOCAL_FILESYSTEM_WRITE_READBACK_ONLY",
        }
    except OSError as exc:
        return {
            "attempted": True,
            "passed": False,
            "scope": "REVERSIBLE_LOCAL_FILESYSTEM_WRITE_READBACK_ONLY",
            "error_class": exc.__class__.__name__,
        }
    finally:
        if marker is not None:
            try:
                marker.unlink(missing_ok=True)
            except OSError:
                pass


def find_executable(candidates: list[str]) -> str | None:
    for name in candidates:
        found = shutil.which(name)
        if found:
            return found
    return None


def configured_hook_surface(root: Path, host: str) -> dict[str, Any]:
    """Detect configuration, never confuse it with observed firing."""
    if host != "claude-code":
        return {"configured": False, "surface": None}
    path = root / ".claude/settings.json"
    if not path.is_file():
        return {"configured": False, "surface": ".claude/settings.json"}
    try:
        data = load_object(path)
    except (OSError, ValueError, json.JSONDecodeError):
        return {"configured": False, "surface": ".claude/settings.json", "parse_error": True}
    hooks = data.get("hooks")
    return {"configured": isinstance(hooks, dict) and bool(hooks), "surface": ".claude/settings.json"}


def classify(
    host: str,
    *,
    instruction_surface: str | None,
    instruction_present: bool,
    executable: str | None,
    write_passed: bool,
    hook_evidence_ok: bool,
    observed_capabilities: set[str],
) -> tuple[str, list[str]]:
    if host in {"claude-code", "codex-cli"}:
        if not instruction_surface or not instruction_present:
            return "BLOCKED", ["required_project_instruction_surface_missing"]
        if executable is None:
            return "BLOCKED", ["host_executable_not_found"]
        if write_passed and hook_evidence_ok:
            return "NATIVE", ["native_instruction_host_write_readback_and_hook_evidence_present"]
        if write_passed:
            return "ADAPTED", ["native_host_present_but_real_hook_firing_not_verified"]
        return "DEGRADED", ["native_host_present_but_local_project_write_readback_not_proven"]

    if host == "hermes-agent":
        if executable is None:
            return "BLOCKED", ["hermes_executable_not_found"]
        if write_passed:
            return "ADAPTED", ["hermes_present_no_project_native_lifecycle_contract_declared"]
        return "DEGRADED", ["hermes_present_but_local_project_write_readback_not_proven"]

    if host in WEB_HOSTS:
        write_cap = bool({"repo-write", "project-write", "state-write"} & observed_capabilities)
        if write_cap and write_passed:
            return "ADAPTED", ["connected_write_declared_and_local_write_readback_present_no_native_web_contract"]
        return "DEGRADED", ["web_context_or_read_access_without_proven_install_lifecycle"]

    # Generic is adaptable at best: no native project lifecycle contract exists.
    if write_passed:
        return "ADAPTED", ["generic_host_local_project_write_readback_present"]
    return "DEGRADED", ["generic_context_only_or_project_write_unavailable"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Non-networking Project Frankenstein AI install probe")
    parser.add_argument("--host", required=True, choices=HOSTS)
    parser.add_argument(
        "--capability",
        action="append",
        default=[],
        help="Observed connected capability for web/generic routes, e.g. repo-write; repeatable.",
    )
    parser.add_argument(
        "--hook-evidence",
        help="Repo-local pre-existing evidence file from a harmless real lifecycle/hook firing.",
    )
    parser.add_argument(
        "--effect-receipt",
        help="Repo-local pre-existing result/effect receipt when the installation test actually exercised effects.",
    )
    parser.add_argument(
        "--no-write-probe",
        action="store_true",
        help="Disable the reversible local filesystem write/read-back test.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = repo_root()
    report: dict[str, Any] = {
        "schema": "FRANKENSTEIN_AI_INSTALL_PROBE_RESULT/v1",
        "host": args.host,
        "repo_root": str(root),
        "repo_resolved_dynamically": True,
        "repo_scanned": False,
        "network_calls_performed": 0,
        "provider_calls_performed": 0,
        "secret_lookups_performed": 0,
    }

    missing = [rel for rel in MINIMAL_READ_SET if not (root / rel).is_file()]
    report["minimal_read_set_missing"] = missing
    if missing:
        report["result"] = "BLOCKED"
        report["reasons"] = ["required_bootstrap_surface_missing"]
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    try:
        contract = load_object(root / "AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json")
        supervisor = current_supervisor(root)
        hook_evidence = evidence_file(root, args.hook_evidence)
        effect_receipt = evidence_file(root, args.effect_receipt)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        report["result"] = "BLOCKED"
        report["reasons"] = [f"bootstrap_or_evidence_parse_failed:{exc.__class__.__name__}"]
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    report["contract_schema"] = contract.get("schema")
    report["supervisor"] = supervisor
    report["hook_evidence"] = hook_evidence
    report["effect_receipt"] = effect_receipt

    route = (contract.get("host_routes") or {}).get(args.host)
    if not isinstance(route, dict):
        report["result"] = "BLOCKED"
        report["reasons"] = ["host_route_missing_from_contract"]
        print(json.dumps(report, indent=2, sort_keys=True))
        return 2

    instruction_surface = route.get("instruction_surface")
    instruction_present = bool(instruction_surface and (root / instruction_surface).is_file())
    executable = find_executable(list(route.get("executable_candidates") or []))
    hook_surface = configured_hook_surface(root, args.host)

    if args.no_write_probe:
        write_probe = {"attempted": False, "passed": False, "scope": "DISABLED_BY_USER"}
    else:
        write_probe = reversible_project_write_probe(root)

    observed_capabilities = {str(item).strip().lower() for item in args.capability if str(item).strip()}
    hook_evidence_ok = bool(hook_evidence["provided"] and hook_evidence["exists"] and hook_evidence["nonempty"])

    result, reasons = classify(
        args.host,
        instruction_surface=instruction_surface,
        instruction_present=instruction_present,
        executable=executable,
        write_passed=bool(write_probe.get("passed")),
        hook_evidence_ok=hook_evidence_ok,
        observed_capabilities=observed_capabilities,
    )
    if result not in RESULTS:
        raise AssertionError(result)

    report.update(
        {
            "instruction_surface": instruction_surface,
            "instruction_surface_present": instruction_present,
            "host_executable": executable,
            "hook_surface": hook_surface,
            "write_probe": write_probe,
            "observed_capabilities_declared": sorted(observed_capabilities),
            "result": result,
            "reasons": reasons,
            "evidence_boundary": (
                "Install evidence only. This does not establish EntityOS/HCU runtime acceptance, "
                "provider authority, model behavior, training success, or real-effect success."
            ),
        }
    )

    if supervisor.get("provider_routes_admitted") is False:
        report["provider_execution"] = "BLOCKED_BY_CURRENT_AUTHORITY"
    else:
        report["provider_execution"] = "NOT_TESTED_BY_INSTALL_PROBE"

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if result != "BLOCKED" else 2


if __name__ == "__main__":
    sys.exit(main())
