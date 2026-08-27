#!/usr/bin/env python3
"""Fail-closed Project Frankenstein host capability probe.

No network. No provider calls. No secret lookup. No repository-wide scan.

The probe proves only observable host integration facts:
- curated entry files are readable;
- exact Git identity when available;
- a state write survives a fresh Python process;
- a supplied hook receipt has required identity fields;
- a supplied effect receipt keeps request/result identities distinct.

An installed CLI binary is never treated as proof that lifecycle hooks fired.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid

START_FILES = (
    "AI_START_HERE_DO_NOT_SCAN_REPO/README.md",
    "DEV_SOURCE_RESEARCH/README.md",
    "DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_SOURCE_INDEX.json",
    "DEV_SOURCE_RESEARCH/repository/CURRENT_AUTHORITY_AND_EVIDENCE.md",
)

HOST_COMMANDS = {
    "claude-code": ("claude",),
    "codex-cli": ("codex",),
    "hermes-agent": ("hermes", "hermes-agent"),
}
WEB_HOSTS = {"chatgpt-web", "claude-web", "grok-web"}


class ProbeError(RuntimeError):
    pass


def read_json_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProbeError(f"missing receipt: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProbeError(f"invalid JSON receipt: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProbeError(f"receipt must be one JSON object: {path}")
    return value


def resolve_repo(raw: str) -> Path:
    repo = Path(raw).expanduser().resolve()
    if not repo.is_dir():
        raise ProbeError(f"repo path is not a directory: {repo}")
    missing = [rel for rel in START_FILES if not (repo / rel).is_file()]
    if missing:
        raise ProbeError("curated entry layer incomplete; missing=" + ",".join(missing))
    return repo


def git_identity(repo: Path) -> tuple[str | None, str | None]:
    git = shutil.which("git")
    if not git:
        return None, None
    try:
        head = subprocess.run(
            [git, "-C", str(repo), "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        branch = subprocess.run(
            [git, "-C", str(repo), "rev-parse", "--abbrev-ref", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        return head or None, branch or None
    except (OSError, subprocess.SubprocessError):
        return None, None


def detect_host_command(host: str) -> tuple[str | None, str]:
    if host in WEB_HOSTS:
        return None, "ABSENT"
    names = HOST_COMMANDS.get(host)
    if names is None:
        return None, "UNKNOWN"
    for name in names:
        path = shutil.which(name)
        if path:
            return path, "PRESENT"
    return None, "ABSENT"


def prove_durable_state(state_dir: Path, repo_head: str | None, host: str, run_id: str) -> dict:
    state_dir = state_dir.expanduser().resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    token = uuid.uuid4().hex
    receipt = state_dir / f"frankenstein_probe_{run_id}.json"
    payload = {
        "schema": "FRANKENSTEIN_HOST_PROBE_STATE/v1",
        "run_id": run_id,
        "host": host,
        "repo_head": repo_head,
        "token": token,
        "written_unix_ns": time.time_ns(),
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    with receipt.open("w", encoding="utf-8") as handle:
        handle.write(encoded)
        handle.flush()
        os.fsync(handle.fileno())

    # Read through a fresh process so success does not depend on this interpreter's memory.
    reader = (
        "import json,sys;"
        "d=json.load(open(sys.argv[1],encoding='utf-8'));"
        "sys.stdout.write(str(d.get('token','')))"
    )
    proc = subprocess.run(
        [sys.executable, "-c", reader, str(receipt)],
        check=False,
        capture_output=True,
        text=True,
        timeout=10,
    )
    passed = proc.returncode == 0 and proc.stdout == token
    return {
        "status": "PRESENT" if passed else "ABSENT",
        "proof": "FRESH_PROCESS_EXACT_READBACK" if passed else "READBACK_FAILED",
        "receipt": str(receipt),
        "token_match": passed,
    }


def validate_hook_receipt(path: Path | None, repo_head: str | None) -> dict:
    if path is None:
        return {"status": "UNKNOWN", "reason": "no --hook-receipt supplied"}
    try:
        data = read_json_object(path.expanduser().resolve())
    except ProbeError as exc:
        return {"status": "ABSENT", "reason": str(exc)}
    required = ("run_id", "host", "hook_name", "time", "repo_identity")
    missing = [key for key in required if not data.get(key)]
    if missing:
        return {"status": "ABSENT", "reason": "missing fields: " + ",".join(missing)}
    repo_match = None
    if repo_head:
        repo_match = repo_head in str(data.get("repo_identity"))
    return {
        "status": "PRESENT" if repo_match is not False else "ABSENT",
        "reason": "receipt fields valid" if repo_match is not False else "repo_identity does not match current HEAD",
        "repo_identity_matches_head": repo_match,
        "receipt": str(path),
    }


def validate_effect_receipt(path: Path | None) -> dict:
    if path is None:
        return {"status": "UNKNOWN", "reason": "no --effect-receipt supplied"}
    try:
        data = read_json_object(path.expanduser().resolve())
    except ProbeError as exc:
        return {"status": "ABSENT", "reason": str(exc)}
    request_id = data.get("request_id")
    result_id = data.get("result_id")
    result_for = data.get("result_for_request_id")
    valid = bool(request_id and result_id and request_id != result_id and result_for == request_id)
    return {
        "status": "PRESENT" if valid else "ABSENT",
        "reason": "request/result identities distinct and linked" if valid else "need distinct request_id/result_id and result_for_request_id == request_id",
        "receipt": str(path),
    }


def classify(host: str, host_command: str, durable: str, hook: str, effect: str, adapter: bool) -> str:
    evidence = (durable, hook, effect)
    if any(value == "ABSENT" for value in evidence):
        return "DEGRADED"
    all_present = all(value == "PRESENT" for value in evidence)
    if host in HOST_COMMANDS and host_command == "PRESENT" and all_present:
        return "NATIVE"
    if all_present and adapter:
        return "ADAPTED"
    if host in WEB_HOSTS:
        return "DEGRADED"
    if host in HOST_COMMANDS and host_command == "ABSENT":
        return "DEGRADED"
    return "ADAPTED" if all_present and adapter else "DEGRADED"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Probe Project Frankenstein host capabilities without repo scan/network/provider calls"
    )
    parser.add_argument("--repo", required=True, help="real repository root path")
    parser.add_argument(
        "--host",
        required=True,
        choices=(
            "claude-code",
            "codex-cli",
            "hermes-agent",
            "chatgpt-web",
            "claude-web",
            "grok-web",
            "generic",
        ),
    )
    parser.add_argument("--state-dir", help="real writable directory for fresh-process state proof")
    parser.add_argument("--hook-receipt", type=Path, help="JSON receipt produced by an actually fired hook")
    parser.add_argument("--effect-receipt", type=Path, help="JSON receipt for one harmless request/result pair")
    parser.add_argument("--adapter", action="store_true", help="explicitly evaluate a connected-tool/host adapter")
    args = parser.parse_args()

    run_id = uuid.uuid4().hex
    try:
        repo = resolve_repo(args.repo)
    except ProbeError as exc:
        print(json.dumps({
            "schema": "FRANKENSTEIN_HOST_PROBE/v1",
            "result": "BLOCKED",
            "error": str(exc),
        }, indent=2, sort_keys=True))
        return 2

    head, branch = git_identity(repo)
    command_path, command_status = detect_host_command(args.host)

    if args.state_dir:
        try:
            durable = prove_durable_state(Path(args.state_dir), head, args.host, run_id)
        except (OSError, subprocess.SubprocessError) as exc:
            durable = {"status": "ABSENT", "reason": f"state proof failed: {exc}"}
    else:
        durable = {"status": "UNKNOWN", "reason": "no --state-dir supplied"}

    hook = validate_hook_receipt(args.hook_receipt, head)
    effect = validate_effect_receipt(args.effect_receipt)
    result = classify(
        args.host,
        command_status,
        durable["status"],
        hook["status"],
        effect["status"],
        args.adapter,
    )

    output = {
        "schema": "FRANKENSTEIN_HOST_PROBE/v1",
        "run_id": run_id,
        "result": result,
        "host": args.host,
        "repo": str(repo),
        "repo_identity": {
            "head": head,
            "branch": branch,
            "status": "PRESENT" if head else "UNKNOWN",
        },
        "capabilities": {
            "READ_SOURCE": "PRESENT",
            "WRITE_SOURCE": "PRESENT" if os.access(repo, os.W_OK) else "UNKNOWN",
            "RUN_CODE": "PRESENT",
            "DURABLE_STATE": durable["status"],
            "LIFECYCLE_HOOK": hook["status"],
            "TOOL_EFFECT": effect["status"],
            "RESULT_RECEIPT": effect["status"],
            "GIT_IDENTITY": "PRESENT" if head else "UNKNOWN",
            "HOST_COMMAND": command_status,
        },
        "host_command_path": command_path,
        "proofs": {
            "durable_state": durable,
            "hook": hook,
            "effect_result": effect,
        },
        "notes": [
            "UNKNOWN is never promoted to PRESENT.",
            "CLI binary presence does not prove lifecycle hooks are active.",
            "No network/provider/secret lookup is performed by this probe.",
            "Web hosts require an explicit adapter plus receipts for ADAPTED and cannot become NATIVE through this local probe.",
        ],
    }
    print(json.dumps(output, indent=2, sort_keys=True))
    return 0 if result in {"NATIVE", "ADAPTED"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
