#!/usr/bin/env python3
"""Frankenstein installer precheck.

Non-networked by design. It does not read provider secrets and does not import
provider clients. It detects only local repository/host capabilities and current
authority pointers needed before a host-specific installation can be classified.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

SCHEMA = "FRANKENSTEIN_INSTALL_PRECHECK/v1"


def repo_root() -> Path:
    # Dynamic relative path from this source file. No CWD/$HOME/Downloads assumption.
    return Path(__file__).resolve().parent.parent


def command(name: str) -> str | None:
    return shutil.which(name)


def readable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.R_OK)


def writable_dir(path: Path) -> bool:
    return path.is_dir() and os.access(path, os.W_OK)


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        value = json.load(f)
    if not isinstance(value, dict):
        raise ValueError(f"expected object in {path}")
    return value


def main() -> int:
    root = repo_root()
    authority = root / "CLAY_EXECUTION_AUTHORITY.md"
    inbox = root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"

    errors: list[str] = []
    steering_rel: str | None = None
    authority_epoch: str | None = None
    provider_hard_off: bool | None = None

    if not readable(authority):
        errors.append("CLAY_EXECUTION_AUTHORITY.md missing/unreadable")
    if not readable(inbox):
        errors.append("SUPERVISOR_INBOX.json missing/unreadable")
    else:
        try:
            inbox_data = load_json(inbox)
            authority_epoch = str(
                inbox_data.get("supervisor_delta")
                or inbox_data.get("schema_version")
                or ""
            )
            steering_value = inbox_data.get("steering")
            if isinstance(steering_value, str) and steering_value:
                steering_rel = steering_value
                steering_path = root / steering_rel
                if not readable(steering_path):
                    errors.append(f"selected steering missing/unreadable: {steering_rel}")
            free_only = inbox_data.get("free_only")
            if isinstance(free_only, dict):
                provider_hard_off = bool(
                    free_only.get("enabled")
                    and free_only.get("provider_routes_admitted") is False
                    and free_only.get("together_forbidden") is True
                    and free_only.get("no_paid_fallback") is True
                )
        except Exception as exc:  # malformed authority fails closed
            errors.append(f"failed to parse supervisor inbox: {exc}")

    detected_commands = {
        name: command(name) for name in ("git", "python3", "claude", "codex", "hermes")
    }
    hosts = [name for name in ("claude", "codex", "hermes") if detected_commands[name]]

    if errors:
        result = "BLOCKED"
        next_required = "repair/resolve current authority files before installation"
    elif hosts:
        result = "ADAPTED"
        next_required = (
            "run host-specific lifecycle hook + durable state + result re-entry "
            "verification before NATIVE"
        )
    else:
        result = "DEGRADED"
        next_required = (
            "use generic file-based route or provide a supported host; "
            "no native lifecycle CLI host detected"
        )

    receipt = {
        "schema": SCHEMA,
        "repo_identity": str(root),
        "authority_epoch": authority_epoch,
        "selected_steering": steering_rel,
        "provider_hard_off_detected": provider_hard_off,
        "capabilities": {
            "repo_read": root.is_dir() and os.access(root, os.R_OK),
            "repo_write": writable_dir(root),
            "commands": detected_commands,
            "detected_cli_hosts": hosts,
        },
        "provider_calls": 0,
        "secret_lookups": 0,
        "result": result,
        "next_required": next_required,
        "errors": errors,
        "note": (
            "Precheck only. NATIVE requires observed host lifecycle/hook, "
            "durable state, and result re-entry probes."
        ),
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 2 if result == "BLOCKED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
