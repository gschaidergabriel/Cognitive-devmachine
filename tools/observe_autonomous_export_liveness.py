#!/usr/bin/env python3
"""Read-only observer for AUTONOMOUS_EXPORT_LIVENESS_RECEIPT/v1.

This tool intentionally does not restart units, write SQLite, mutate git state,
probe paid providers, or push. It gathers a bounded local snapshot so a stalled
evidence producer can be classified before any repair action is attempted.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import sqlite3
import subprocess
from typing import Any

SCHEMA = "AUTONOMOUS_EXPORT_LIVENESS_RECEIPT/v1"
SYSTEMCTL_KEYS = (
    "Id",
    "LoadState",
    "ActiveState",
    "SubState",
    "UnitFileState",
    "Result",
    "ExecMainCode",
    "ExecMainStatus",
    "MainPID",
    "LastTriggerUSec",
    "NextElapseUSecRealtime",
    "ActiveEnterTimestamp",
    "InactiveEnterTimestamp",
)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def run(argv: list[str], cwd: str | None = None, timeout: int = 10) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            text=True,
            capture_output=True,
            timeout=timeout,
            check=False,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C"},
        )
        return {
            "argv": argv,
            "exit_code": proc.returncode,
            "stdout_sha256": sha256_text(proc.stdout),
            "stderr_sha256": sha256_text(proc.stderr),
            "stdout": proc.stdout,
            "stderr": proc.stderr,
        }
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {
            "argv": argv,
            "exit_code": None,
            "stdout_sha256": None,
            "stderr_sha256": None,
            "error": type(exc).__name__,
        }


def parse_kv(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            if key in SYSTEMCTL_KEYS:
                out[key] = value
    return out


def unit_snapshot(unit: str) -> dict[str, Any]:
    show = run(["systemctl", "show", unit, "--property=" + ",".join(SYSTEMCTL_KEYS)])
    journal = run(["journalctl", "-u", unit, "-n", "200", "--no-pager", "-o", "short-iso"])
    fields = parse_kv(show.get("stdout", "")) if show.get("exit_code") == 0 else {}
    return {
        "unit": unit,
        "systemctl_exit_code": show.get("exit_code"),
        "fields": fields,
        "journal_exit_code": journal.get("exit_code"),
        "journal_stdout_sha256": journal.get("stdout_sha256"),
        "journal_stderr_sha256": journal.get("stderr_sha256"),
    }


def git_value(repo: str, argv: list[str]) -> dict[str, Any]:
    result = run(["git", *argv], cwd=repo)
    value = result.get("stdout", "").strip() if result.get("exit_code") == 0 else None
    return {
        "exit_code": result.get("exit_code"),
        "value": value,
        "stderr_sha256": result.get("stderr_sha256"),
    }


def repo_snapshot(repo: str) -> dict[str, Any]:
    status = run(["git", "status", "--porcelain=v1"], cwd=repo)
    porcelain = status.get("stdout", "") if status.get("exit_code") == 0 else ""
    return {
        "path": str(pathlib.Path(repo).resolve()),
        "head": git_value(repo, ["rev-parse", "HEAD"]),
        "branch": git_value(repo, ["rev-parse", "--abbrev-ref", "HEAD"]),
        "worktree_status_exit_code": status.get("exit_code"),
        "worktree_dirty_line_count": len([x for x in porcelain.splitlines() if x.strip()]),
        "worktree_status_sha256": sha256_text(porcelain),
        "agentzero_last_export": git_value(
            repo,
            ["log", "-1", "--format=%H|%cI|%s", "--grep=agentZero-Export"],
        ),
        "rating_last_export": git_value(
            repo,
            ["log", "-1", "--format=%H|%cI|%s", "--grep=eos-bewertung-export"],
        ),
        "remote_names": git_value(repo, ["remote"]),
    }


def disk_snapshot(path: str) -> dict[str, Any]:
    usage = shutil.disk_usage(path)
    stat = os.statvfs(path)
    return {
        "path": str(pathlib.Path(path).resolve()),
        "bytes_total": usage.total,
        "bytes_used": usage.used,
        "bytes_free": usage.free,
        "inodes_total": stat.f_files,
        "inodes_free": stat.f_ffree,
    }


def sqlite_snapshot(path: str | None) -> dict[str, Any]:
    if not path:
        return {"configured": False, "status": "UNKNOWN"}
    p = pathlib.Path(path).resolve()
    uri = f"file:{p.as_posix()}?mode=ro"
    try:
        con = sqlite3.connect(uri, uri=True, timeout=0.0)
        try:
            con.execute("PRAGMA query_only=ON")
            con.execute("SELECT 1").fetchone()
        finally:
            con.close()
        return {"configured": True, "path": str(p), "status": "READABLE_NOT_LOCKED"}
    except sqlite3.OperationalError as exc:
        msg = str(exc).lower()
        status = "DB_LOCKED" if "locked" in msg or "busy" in msg else "READ_ERROR"
        return {
            "configured": True,
            "path": str(p),
            "status": status,
            "error_class": type(exc).__name__,
            "error_sha256": sha256_text(str(exc)),
        }


def classify(timer_units: list[dict[str, Any]], service_units: list[dict[str, Any]], disk: dict[str, Any], db: dict[str, Any]) -> dict[str, Any]:
    if db.get("status") == "DB_LOCKED":
        return {"class": "DB_LOCKED", "confidence": "HIGH"}
    if disk.get("bytes_free") == 0 or disk.get("inodes_free") == 0:
        return {"class": "DISK_FULL", "confidence": "HIGH"}

    for snap in timer_units:
        f = snap.get("fields", {})
        if f.get("LoadState") == "loaded" and (
            f.get("UnitFileState") in {"disabled", "masked"}
            or f.get("ActiveState") in {"inactive", "failed"}
        ):
            return {"class": "TIMER_DISABLED", "confidence": "HIGH", "unit": snap.get("unit")}

    for snap in service_units:
        f = snap.get("fields", {})
        status = f.get("ExecMainStatus")
        if f.get("Result") not in {None, "", "success"} or (status not in {None, "", "0"}):
            return {"class": "RUN_FAILED", "confidence": "MEDIUM", "unit": snap.get("unit")}

    return {
        "class": "UNKNOWN",
        "confidence": "LOW",
        "note": "Read-only snapshot does not justify restart, replay, push, or state mutation.",
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--agentzero-timer", required=True)
    ap.add_argument("--rating-timer", required=True)
    ap.add_argument("--agentzero-service", required=True)
    ap.add_argument("--rating-service", required=True)
    ap.add_argument("--sqlite-db")
    ap.add_argument("--output")
    args = ap.parse_args()

    timers = [unit_snapshot(args.agentzero_timer), unit_snapshot(args.rating_timer)]
    services = [unit_snapshot(args.agentzero_service), unit_snapshot(args.rating_service)]
    disk = disk_snapshot(args.repo)
    db = sqlite_snapshot(args.sqlite_db)
    repo = repo_snapshot(args.repo)

    receipt = {
        "schema": SCHEMA,
        "observed_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "observer_mode": "READ_ONLY_NO_RESTART_NO_PUSH_NO_PROVIDER_NETWORK",
        "timers": timers,
        "services": services,
        "repository": repo,
        "disk": disk,
        "sqlite": db,
        "classification": classify(timers, services, disk, db),
        "required_followup_fields_not_observable_here": [
            "last_successful_run_id_if_not_present_in_journal",
            "explicit_push_result_if_prior_run_did_not_log_it",
            "network_auth_result_if_prior_run_did_not_log_it",
            "generation_before_after_if_not_present_in_local_export metadata",
        ],
    }
    encoded = json.dumps(receipt, sort_keys=True, indent=2) + "\n"
    if args.output:
        pathlib.Path(args.output).write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
