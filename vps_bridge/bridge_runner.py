#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import traceback

ROOT = Path(os.environ.get("CLAY_BRIDGE_ROOT", "/srv/clay-gpt")).resolve()
CONTROL = ROOT / "control"
REPO = ROOT / "repo"
WORKTREES = ROOT / "worktrees"
CACHE = ROOT / "cache"
MODELS = ROOT / "models"
TOOLS = ROOT / "tools"
LOGS = ROOT / "logs"
STATE = ROOT / "state"
BRANCH = os.environ.get("CLAY_CONTROL_BRANCH", "gpt56sol/vps-chatgpt-bridge-20260824")
REMOTE = os.environ.get("CLAY_REPOSITORY", "https://github.com/gschaidergabriel/clay-global-research-entity.git")
IMAGE = os.environ.get("CLAY_SANDBOX_IMAGE", "localhost/clay-gpt-dev:ubuntu24")
POLL_SECONDS = int(os.environ.get("CLAY_POLL_SECONDS", "20"))
MAX_TAIL = 24000

TASK_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
BASE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_./-]{0,190}$")


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run(argv, *, cwd=None, check=True, capture=True, timeout=None):
    cp = subprocess.run(
        argv,
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
        check=False,
        timeout=timeout,
    )
    if check and cp.returncode != 0:
        raise RuntimeError(
            f"COMMAND_FAILED:{argv!r}:rc={cp.returncode}:stderr={(cp.stderr or '')[-4000:]}"
        )
    return cp


def git(cwd: Path, *args: str, check: bool = True):
    return run(["git", "-C", str(cwd), *args], check=check)


def ensure_dirs() -> None:
    for p in (WORKTREES, CACHE, MODELS, TOOLS, LOGS, STATE):
        p.mkdir(parents=True, exist_ok=True)


def sync_control() -> None:
    git(CONTROL, "fetch", "origin", BRANCH)
    git(CONTROL, "checkout", BRANCH)
    git(CONTROL, "pull", "--rebase", "origin", BRANCH)


def ensure_repo() -> None:
    if not (REPO / ".git").exists():
        run(["git", "clone", REMOTE, str(REPO)], check=True)
    git(REPO, "fetch", "origin", "--prune")


def ensure_image() -> None:
    cp = run(["podman", "image", "exists", IMAGE], check=False)
    if cp.returncode == 0:
        return
    context = CONTROL / "vps_bridge"
    run(["podman", "build", "-t", IMAGE, "-f", str(context / "Containerfile"), str(context)], capture=False)


def safe_task_id(value: object) -> str:
    if not isinstance(value, str) or not TASK_ID_RE.fullmatch(value):
        raise ValueError("INVALID_TASK_ID")
    return value


def parse_task(path: Path) -> dict:
    task = json.loads(path.read_text())
    if task.get("schema") != "CLAY_VPS_TASK/v1":
        raise ValueError("UNSUPPORTED_TASK_SCHEMA")
    task_id = safe_task_id(task.get("task_id"))
    if path.stem != task_id:
        raise ValueError("TASK_ID_FILENAME_MISMATCH")
    command = task.get("command")
    if not isinstance(command, str) or not command.strip() or len(command) > 100_000:
        raise ValueError("INVALID_COMMAND")
    base = task.get("base_ref", "main")
    if not isinstance(base, str) or not BASE_RE.fullmatch(base) or ".." in base:
        raise ValueError("INVALID_BASE_REF")
    timeout_sec = int(task.get("timeout_sec", 3600))
    if not 1 <= timeout_sec <= 21600:
        raise ValueError("INVALID_TIMEOUT")
    cpus = float(task.get("cpus", 4))
    if not 0.25 <= cpus <= 4:
        raise ValueError("INVALID_CPU_LIMIT")
    memory = str(task.get("memory", "12g"))
    if not re.fullmatch(r"[1-9][0-9]*(?:[mMgG])", memory):
        raise ValueError("INVALID_MEMORY_LIMIT")
    pids = int(task.get("pids_limit", 4096))
    if not 64 <= pids <= 8192:
        raise ValueError("INVALID_PIDS_LIMIT")
    min_free_gb = int(task.get("min_free_gb", 20))
    if not 1 <= min_free_gb <= 150:
        raise ValueError("INVALID_DISK_GUARD")
    task.update(
        task_id=task_id,
        command=command,
        base_ref=base,
        timeout_sec=timeout_sec,
        cpus=cpus,
        memory=memory,
        pids_limit=pids,
        min_free_gb=min_free_gb,
        network=bool(task.get("network", True)),
        commit_changes=bool(task.get("commit_changes", True)),
        commit_on_failure=bool(task.get("commit_on_failure", False)),
    )
    return task


def resolve_base(base: str) -> str:
    git(REPO, "fetch", "origin", "--prune")
    if base.startswith("pr/"):
        n = base.split("/", 1)[1]
        if not n.isdigit():
            raise ValueError("INVALID_PR_BASE")
        ref = f"refs/remotes/origin/pr/{n}"
        git(REPO, "fetch", "origin", f"+refs/pull/{n}/head:{ref}")
        return ref
    ref = f"refs/remotes/origin/{base}"
    cp = git(REPO, "rev-parse", "--verify", ref, check=False)
    if cp.returncode != 0:
        git(REPO, "fetch", "origin", f"+refs/heads/{base}:{ref}")
    return ref


def create_worktree(task: dict) -> tuple[Path, str]:
    task_id = task["task_id"]
    wt = (WORKTREES / task_id).resolve()
    if WORKTREES not in wt.parents:
        raise RuntimeError("WORKTREE_ESCAPE_REJECTED")
    if wt.exists():
        git(REPO, "worktree", "remove", "--force", str(wt), check=False)
        shutil.rmtree(wt, ignore_errors=True)
    base_ref = resolve_base(task["base_ref"])
    branch = f"vps-task/{task_id}"
    git(REPO, "worktree", "add", "--force", "-B", branch, str(wt), base_ref)
    return wt, branch


def disk_guard(task: dict) -> dict:
    usage = shutil.disk_usage(ROOT)
    free_gb = usage.free / (1024 ** 3)
    if free_gb < task["min_free_gb"]:
        raise RuntimeError(f"DISK_GUARD_FAIL:free_gb={free_gb:.2f}")
    return {"total": usage.total, "used": usage.used, "free": usage.free}


def tail(path: Path, limit: int = MAX_TAIL) -> str:
    if not path.exists():
        return ""
    data = path.read_bytes()
    return data[-limit:].decode("utf-8", "replace")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def execute_container(task: dict, wt: Path) -> dict:
    task_id = task["task_id"]
    stdout_path = LOGS / f"{task_id}.stdout.log"
    stderr_path = LOGS / f"{task_id}.stderr.log"
    container_name = "clay-" + re.sub(r"[^A-Za-z0-9_.-]", "-", task_id)[:80]
    cmd = [
        "podman", "run", "--rm", "--name", container_name,
        "--cpus", str(task["cpus"]),
        "--memory", task["memory"],
        "--pids-limit", str(task["pids_limit"]),
        "--cap-drop=all",
        "--security-opt", "no-new-privileges",
        "-v", f"{wt}:/workspace:rw",
        "-v", f"{CACHE}:/cache:rw",
        "-v", f"{MODELS}:/models:rw",
        "-v", f"{TOOLS}:/tools:rw",
        "-w", "/workspace",
        "-e", f"CLAY_TASK_ID={task_id}",
        "-e", "CLAY_MODELS=/models",
        "-e", "CLAY_CACHE=/cache",
        "-e", "CLAY_TOOLS=/tools",
    ]
    if not task["network"]:
        cmd += ["--network", "none"]
    cmd += [IMAGE, "bash", "-lc", task["command"]]

    started = time.monotonic()
    timed_out = False
    with stdout_path.open("wb") as out, stderr_path.open("wb") as err:
        proc = subprocess.Popen(cmd, stdout=out, stderr=err)
        try:
            rc = proc.wait(timeout=task["timeout_sec"])
        except subprocess.TimeoutExpired:
            timed_out = True
            run(["podman", "kill", container_name], check=False)
            try:
                rc = proc.wait(timeout=20)
            except subprocess.TimeoutExpired:
                proc.kill()
                rc = proc.wait()
    elapsed = time.monotonic() - started
    return {
        "exit_code": rc,
        "timed_out": timed_out,
        "elapsed_s": round(elapsed, 6),
        "stdout_path": str(stdout_path),
        "stdout_sha256": sha256_file(stdout_path),
        "stdout_tail": tail(stdout_path),
        "stderr_path": str(stderr_path),
        "stderr_sha256": sha256_file(stderr_path),
        "stderr_tail": tail(stderr_path),
    }


def commit_task_changes(task: dict, wt: Path, branch: str, execution: dict) -> dict:
    status = git(wt, "status", "--porcelain").stdout
    changed = bool(status.strip())
    result = {"changed": changed, "status_porcelain": status[-12000:]}
    should_commit = task["commit_changes"] and changed and (
        execution["exit_code"] == 0 or task["commit_on_failure"]
    )
    if not should_commit:
        result["committed"] = False
        return result
    git(wt, "add", "-A")
    git(wt, "commit", "-m", f"vps task: {task['task_id']}")
    sha = git(wt, "rev-parse", "HEAD").stdout.strip()
    git(wt, "push", "--force-with-lease", "-u", "origin", f"HEAD:refs/heads/{branch}")
    result.update(committed=True, branch=branch, commit_sha=sha)
    return result


def push_outbox(task_id: str, result: dict) -> None:
    sync_control()
    outdir = CONTROL / "vps_bridge" / "outbox"
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{task_id}.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    git(CONTROL, "add", str(out.relative_to(CONTROL)))
    cp = git(CONTROL, "diff", "--cached", "--quiet", check=False)
    if cp.returncode == 0:
        return
    git(CONTROL, "commit", "-m", f"vps bridge result: {task_id}")
    for attempt in range(5):
        cp = git(CONTROL, "push", "origin", BRANCH, check=False)
        if cp.returncode == 0:
            return
        git(CONTROL, "pull", "--rebase", "origin", BRANCH, check=False)
        time.sleep(2 + attempt)
    raise RuntimeError("OUTBOX_PUSH_FAILED")


def process(path: Path) -> None:
    task_id = path.stem
    started_at = utcnow()
    base_result = {
        "schema": "CLAY_VPS_TASK_RESULT/v1",
        "task_id": task_id,
        "started_at": started_at,
        "sandbox": {
            "engine": "rootless-podman",
            "image": IMAGE,
            "outbound_network_default": True,
            "host_credentials_mounted": False,
            "host_root_mounted": False,
            "container_socket_mounted": False,
        },
        "canonical_promotion_credit_minted": 0,
    }
    try:
        task = parse_task(path)
        base_result["task"] = {
            k: task[k] for k in (
                "schema", "task_id", "base_ref", "timeout_sec", "cpus", "memory",
                "pids_limit", "min_free_gb", "network", "commit_changes", "commit_on_failure"
            )
        }
        base_result["disk_before"] = disk_guard(task)
        ensure_repo()
        ensure_image()
        wt, branch = create_worktree(task)
        base_result["resolved_base_sha"] = git(wt, "rev-parse", "HEAD").stdout.strip()
        execution = execute_container(task, wt)
        base_result["execution"] = execution
        base_result["git_result"] = commit_task_changes(task, wt, branch, execution)
        base_result["status"] = "PASS" if execution["exit_code"] == 0 and not execution["timed_out"] else "FAIL"
    except Exception as exc:
        base_result["status"] = "BRIDGE_ERROR"
        base_result["bridge_error"] = f"{type(exc).__name__}:{exc}"
        base_result["traceback_tail"] = traceback.format_exc()[-12000:]
    base_result["finished_at"] = utcnow()
    push_outbox(task_id, base_result)
    (STATE / f"{task_id}.done").write_text(base_result["finished_at"] + "\n")


def loop() -> None:
    ensure_dirs()
    ensure_repo()
    ensure_image()
    while True:
        try:
            sync_control()
            inbox = CONTROL / "vps_bridge" / "inbox"
            outbox = CONTROL / "vps_bridge" / "outbox"
            inbox.mkdir(parents=True, exist_ok=True)
            outbox.mkdir(parents=True, exist_ok=True)
            for path in sorted(inbox.glob("*.json")):
                task_id = path.stem
                if (outbox / f"{task_id}.json").exists() or (STATE / f"{task_id}.done").exists():
                    continue
                process(path)
        except Exception:
            err = traceback.format_exc()
            (LOGS / "bridge-loop-error.log").write_text(f"{utcnow()}\n{err}\n")
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    loop()
