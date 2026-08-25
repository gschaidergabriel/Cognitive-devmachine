#!/usr/bin/env python3
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import shlex
import sqlite3
import subprocess
import threading
import time
import traceback
from typing import Any

BASE = pathlib.Path("/srv/claylab")
CONTROL = BASE / "control-mirror"
RESULTS = BASE / "results-mirror"
WORK = BASE / "workspace/clay-global-research-entity"
STATE = BASE / "state"
ART = BASE / "artifacts"
DB = STATE / "bridge.sqlite3"
CONTROL_BRANCH = "chatgpt-vps-control"
RESULTS_BRANCH = "chatgpt-vps-results"
QUEUE = pathlib.Path("vps_bridge/commands")
SANDBOX = "clay-direct-dev"
MAX_TIMEOUT = 14400
MAX_LOG = 512 * 1024
DEFAULT_PRIORITY = 100
CANONICAL_REPO_SSH = "git@github.com:gschaidergabriel/clay-global-research-entity.git"
CANONICAL_REPO_HTTPS = "https://github.com/gschaidergabriel/clay-global-research-entity.git"

STATE.mkdir(parents=True, exist_ok=True)
ART.mkdir(parents=True, exist_ok=True)
RESULTS_LOCK = threading.RLock()
STOP = threading.Event()


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def text(value: bytes | None) -> str:
    return (value or b"").decode("utf-8", "replace")


def sha(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def run(argv: list[str], timeout: int = 120, cwd: pathlib.Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, cwd=cwd)


def git(repo: pathlib.Path, *args: str, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess:
    p = run(["git", "-C", str(repo), *args], timeout=timeout)
    if check and p.returncode:
        raise RuntimeError("GIT_FAILED: " + text(p.stderr)[-6000:])
    return p


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB)
    c.execute(
        "CREATE TABLE IF NOT EXISTS done("
        "id TEXT PRIMARY KEY, command_sha TEXT NOT NULL, finished TEXT NOT NULL, code INTEGER NOT NULL)"
    )
    c.execute(
        "CREATE TABLE IF NOT EXISTS invalid("
        "file_sha TEXT PRIMARY KEY, path TEXT NOT NULL, observed TEXT NOT NULL, error TEXT NOT NULL)"
    )
    c.commit()
    return c


def ensure_box() -> None:
    p = run(["podman", "inspect", "-f", "{{.State.Running}}", SANDBOX], timeout=20)
    if p.returncode == 0 and text(p.stdout).strip() == "true":
        return
    p = run(["podman", "start", SANDBOX], timeout=90)
    if p.returncode:
        raise RuntimeError("SANDBOX_START_FAILED: " + text(p.stderr))


def sexec(command: str, cwd: str = "/workspace", timeout: int = 3600) -> subprocess.CompletedProcess:
    ensure_box()
    return run(["podman", "exec", "-w", cwd, SANDBOX, "bash", "-lc", command], timeout=timeout)


def sync_control() -> None:
    git(CONTROL, "fetch", "origin", CONTROL_BRANCH, "--prune")
    git(CONTROL, "checkout", "-B", CONTROL_BRANCH, f"origin/{CONTROL_BRANCH}")
    git(CONTROL, "reset", "--hard", f"origin/{CONTROL_BRANCH}")


def sync_results() -> None:
    git(RESULTS, "fetch", "origin", RESULTS_BRANCH, "--prune")
    git(RESULTS, "checkout", "-B", RESULTS_BRANCH, f"origin/{RESULTS_BRANCH}")
    git(RESULTS, "reset", "--hard", f"origin/{RESULTS_BRANCH}")


def push_results(message: str, *, live: bool = False) -> None:
    git(RESULTS, "add", "vps_bridge/results", check=False)
    if git(RESULTS, "diff", "--cached", "--quiet", check=False).returncode == 0:
        return
    if live:
        subject = text(git(RESULTS, "log", "-1", "--pretty=%s", check=False).stdout).strip()
        if subject.startswith("vps live telemetry"):
            git(RESULTS, "commit", "--amend", "--no-edit")
            git(RESULTS, "push", "--force-with-lease", "origin", f"HEAD:{RESULTS_BRANCH}", timeout=300)
            return
    git(RESULTS, "commit", "-m", message)
    git(RESULTS, "push", "origin", f"HEAD:{RESULTS_BRANCH}", timeout=300)


def rel(value: Any) -> str:
    p = pathlib.PurePosixPath(str(value))
    if p.is_absolute() or ".." in p.parts:
        raise ValueError("RELATIVE_PATH_REQUIRED")
    return str(p)


def status_payload() -> dict[str, Any]:
    ensure_box()
    host: dict[str, Any] = {}
    probes = {
        "uptime": ["uptime"],
        "memory": ["free", "-b"],
        "disk": ["df", "-B1", "/srv/claylab"],
        "podman": ["podman", "stats", "--no-stream", "--format", "json", SANDBOX],
    }
    for name, argv in probes.items():
        try:
            p = run(argv, timeout=30)
            host[name] = {"rc": p.returncode, "out": text(p.stdout)[-12000:], "err": text(p.stderr)[-2000:]}
        except Exception as exc:
            host[name] = {"rc": 125, "out": "", "err": repr(exc)}
    try:
        p = sexec("ps auxww --sort=-%cpu | head -80; echo '---'; free -h; echo '---'; df -h /workspace /cache", timeout=30)
        processes = text(p.stdout)[-24000:]
    except Exception as exc:
        processes = "TELEMETRY_ERROR:" + repr(exc)
    head = text(git(WORK, "rev-parse", "HEAD", check=False).stdout).strip() if WORK.exists() else ""
    gs = text(git(WORK, "status", "--short", "--branch", check=False).stdout)[-16000:] if WORK.exists() else ""
    return {
        "schema": "CLAY_VPS_LIVE/v5",
        "observed_at": now(),
        "sandbox": SANDBOX,
        "host": host,
        "processes": processes,
        "workspace_git": {"head": head, "status": gs},
    }


def operate(s: dict[str, Any]) -> tuple[subprocess.CompletedProcess, dict[str, Any]]:
    op = str(s.get("op", "exec"))
    timeout = min(max(int(s.get("timeout_seconds", 3600)), 1), MAX_TIMEOUT)
    if op == "exec":
        return sexec(str(s["command"]), str(s.get("cwd", "/workspace")), timeout), {}
    if op == "status":
        raw = json.dumps(status_payload(), indent=2).encode()
        return subprocess.CompletedProcess(["status"], 0, raw, b""), {}
    if op == "fetch":
        dest = rel(s["dest"])
        url = str(s["url"])
        expected = s.get("sha256")
        q = "/workspace/" + dest
        cmd = (
            f"set -euo pipefail; mkdir -p $(dirname {shlex.quote(q)}); "
            f"curl -fL --retry 5 --retry-delay 2 --continue-at - {shlex.quote(url)} -o {shlex.quote(q)}; "
            f"sha256sum {shlex.quote(q)}"
        )
        p = sexec(cmd, timeout=timeout)
        if p.returncode == 0 and expected:
            actual = text(p.stdout).strip().split()[0]
            if actual != expected:
                p = subprocess.CompletedProcess(
                    p.args, 72, p.stdout,
                    (p.stderr or b"") + f"\nSHA256_MISMATCH expected={expected} actual={actual}\n".encode(),
                )
        return p, {}
    if op == "git":
        url = str(s["url"])
        if url not in (CANONICAL_REPO_SSH, CANONICAL_REPO_HTTPS):
            return subprocess.CompletedProcess(
                ["git"], 73, b"",
                b"PRIVATE_OR_ARBITRARY_GIT_REQUIRES_EXPLICIT_TRANSPORT; canonical repo only on host-side git op\n",
            ), {"transport": "host", "allowed_repo": CANONICAL_REPO_SSH}
        dest = BASE / "workspace" / rel(s["dest"])
        ref = s.get("ref")
        if (dest / ".git").exists():
            git(dest, "fetch", "origin", "--prune", timeout=timeout)
        else:
            p = run(["git", "clone", CANONICAL_REPO_SSH, str(dest)], timeout=timeout)
            if p.returncode:
                return p, {"transport": "host"}
        if ref:
            p = git(dest, "checkout", str(ref), check=False)
            if p.returncode:
                return p, {"transport": "host"}
        head = text(git(dest, "rev-parse", "HEAD").stdout).strip()
        return subprocess.CompletedProcess(["git"], 0, (head + "\n").encode(), b""), {"transport": "host", "head": head}
    if op == "canonical_sync":
        ref = str(s.get("ref", "main"))
        allow_dirty_reset = s.get("allow_dirty_reset") is True
        dirty = text(git(WORK, "status", "--porcelain", check=False).stdout)
        if ref == "main" and dirty and not allow_dirty_reset:
            msg = (
                "DIRTY_WORKTREE_REFUSED: canonical_sync(main) would hard-reset runtime/local files. "
                "Use a non-main ref, isolated worktree, or explicitly set allow_dirty_reset=true.\n"
            )
            return subprocess.CompletedProcess(["canonical_sync"], 73, b"", msg.encode()), {
                "ref": ref,
                "dirty_paths": dirty.splitlines()[:200],
                "allow_dirty_reset": False,
            }
        git(WORK, "fetch", "origin", "--prune", timeout=600)
        p = git(WORK, "checkout", ref, check=False)
        if p.returncode:
            git(WORK, "checkout", "-B", ref, f"origin/{ref}")
        if ref == "main":
            git(WORK, "reset", "--hard", "origin/main")
        head = text(git(WORK, "rev-parse", "HEAD").stdout).strip()
        return subprocess.CompletedProcess(["canonical_sync"], 0, (head + "\n").encode(), b""), {
            "head": head, "ref": ref, "dirty_reset_authorized": allow_dirty_reset
        }
    if op == "write_text":
        p = BASE / "workspace" / rel(s["path"])
        p.parent.mkdir(parents=True, exist_ok=True)
        data = str(s.get("content", "")).encode()
        p.write_bytes(data)
        return subprocess.CompletedProcess(["write_text"], 0, f"WROTE {p}\n".encode(), b""), {"sha256": sha(data), "bytes": len(data)}
    if op == "read_file":
        p = BASE / "workspace" / rel(s["path"])
        data = p.read_bytes()
        return subprocess.CompletedProcess(["read_file"], 0, data[:MAX_LOG], b""), {"sha256": sha(data), "bytes": len(data), "truncated": len(data) > MAX_LOG}
    if op == "publish_branch":
        branch = str(s["branch"])
        if not branch.startswith("chatgpt-vps-work/"):
            raise ValueError("BAD_WORK_BRANCH")
        git(WORK, "checkout", "-B", branch)
        git(WORK, "add", "-A")
        if git(WORK, "diff", "--cached", "--quiet", check=False).returncode != 0:
            git(WORK, "commit", "-m", str(s.get("message", "ChatGPT VPS work")))
        git(WORK, "push", "-u", "origin", f"HEAD:{branch}", timeout=300)
        head = text(git(WORK, "rev-parse", "HEAD").stdout).strip()
        return subprocess.CompletedProcess(["publish_branch"], 0, (head + "\n").encode(), b""), {"branch": branch, "head": head}
    raise ValueError("UNSUPPORTED_OP:" + op)


def publish_receipt(receipt: dict[str, Any], stdout: bytes, stderr: bytes) -> None:
    with RESULTS_LOCK:
        sync_results()
        d = RESULTS / "vps_bridge/results"
        (d / "receipts").mkdir(parents=True, exist_ok=True)
        (d / "logs").mkdir(parents=True, exist_ok=True)
        cid = receipt["command_id"]
        (d / "receipts" / f"{cid}.json").write_text(json.dumps(receipt, indent=2) + "\n")
        (d / "logs" / f"{cid}.stdout.txt").write_bytes(stdout[-MAX_LOG:])
        (d / "logs" / f"{cid}.stderr.txt").write_bytes(stderr[-MAX_LOG:])
        (d / "LATEST.json").write_text(json.dumps(receipt, indent=2) + "\n")
        push_results("vps receipt: " + cid, live=False)


def publish_invalid_command(path: pathlib.Path, raw: bytes, exc: Exception) -> None:
    file_sha = sha(raw)
    c = conn()
    if c.execute("SELECT 1 FROM invalid WHERE file_sha=?", (file_sha,)).fetchone():
        c.close()
        return
    fallback = "invalid-" + file_sha[:16]
    receipt = {
        "schema": "CLAY_VPS_RECEIPT/v5",
        "command_id": fallback,
        "command_sha256": file_sha,
        "started_at": now(),
        "finished_at": now(),
        "status": "INVALID_COMMAND",
        "exit_code": 126,
        "op": "PARSE",
        "stdout_sha256": sha(b""),
        "stderr_sha256": sha(repr(exc).encode()),
        "stdout_tail": "",
        "stderr_tail": repr(exc),
        "meta": {"path": str(path.relative_to(CONTROL)), "quarantined": True},
        "execution_boundary": "NO_COMMAND_EXECUTION_PARSE_FAILURE",
        "canonical_credit_minted": 0,
    }
    publish_receipt(receipt, b"", repr(exc).encode())
    c.execute("INSERT INTO invalid(file_sha,path,observed,error) VALUES(?,?,?,?)", (file_sha, str(path), now(), repr(exc)))
    c.commit()
    c.close()


def parse_command(path: pathlib.Path) -> tuple[bytes, dict[str, Any]]:
    raw = path.read_bytes()
    try:
        s = json.loads(raw)
        if not isinstance(s, dict):
            raise ValueError("COMMAND_OBJECT_REQUIRED")
        if s.get("schema") not in ("CLAY_VPS_COMMAND/v3", "CLAY_VPS_COMMAND/v4", "CLAY_VPS_COMMAND/v5"):
            raise ValueError("BAD_SCHEMA")
        cid = s.get("command_id")
        if not isinstance(cid, str) or not cid.strip():
            raise ValueError("COMMAND_ID_REQUIRED")
        priority = s.get("priority", DEFAULT_PRIORITY)
        if not isinstance(priority, int) or isinstance(priority, bool) or not (-1000 <= priority <= 1000):
            raise ValueError("PRIORITY_INTEGER_-1000_TO_1000_REQUIRED")
        return raw, s
    except Exception as exc:
        publish_invalid_command(path, raw, exc)
        raise


def execute(path: pathlib.Path) -> bool:
    try:
        raw, s = parse_command(path)
    except Exception:
        return False
    cid = str(s["command_id"])
    c = conn()
    if c.execute("SELECT 1 FROM done WHERE id=?", (cid,)).fetchone():
        c.close()
        return False
    started = now()
    stdout = stderr = b""
    meta: dict[str, Any] = {}
    try:
        p, meta = operate(s)
        code = p.returncode
        stdout = p.stdout or b""
        stderr = p.stderr or b""
        status = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired as exc:
        code = 124
        status = "TIMEOUT"
        stdout = exc.stdout or b""
        stderr = (exc.stderr or b"") + repr(exc).encode()
    except Exception as exc:
        code = 125
        status = "ERROR"
        stderr = (repr(exc) + "\n" + traceback.format_exc()).encode()
    receipt = {
        "schema": "CLAY_VPS_RECEIPT/v5",
        "command_id": cid,
        "command_sha256": sha(raw),
        "started_at": started,
        "finished_at": now(),
        "status": status,
        "exit_code": code,
        "op": s.get("op", "exec"),
        "priority": int(s.get("priority", DEFAULT_PRIORITY)),
        "stdout_sha256": sha(stdout),
        "stderr_sha256": sha(stderr),
        "stdout_tail": text(stdout)[-24000:],
        "stderr_tail": text(stderr)[-24000:],
        "meta": meta,
        "execution_boundary": "ROOT_INSIDE_ROOTLESS_PODMAN_OR_EXPLICIT_REPO_CONTROL_OP",
        "canonical_credit_minted": 0,
    }
    publish_receipt(receipt, stdout, stderr)
    c.execute("INSERT INTO done VALUES(?,?,?,?)", (cid, sha(raw), now(), code))
    c.commit()
    c.close()
    return True


def queue_paths() -> list[pathlib.Path]:
    q = CONTROL / QUEUE
    if not q.exists():
        return []
    ranked: list[tuple[int, str, pathlib.Path]] = []
    for p in q.glob("*.json"):
        try:
            raw = p.read_bytes()
            value = json.loads(raw)
            pri = int(value.get("priority", DEFAULT_PRIORITY)) if isinstance(value, dict) else DEFAULT_PRIORITY
        except Exception as exc:
            publish_invalid_command(p, p.read_bytes(), exc)
            continue
        ranked.append((pri, p.name, p))
    ranked.sort(key=lambda item: (item[0], item[1]))
    return [p for _, _, p in ranked]


def publish_live() -> None:
    with RESULTS_LOCK:
        sync_results()
        d = RESULTS / "vps_bridge/results"
        d.mkdir(parents=True, exist_ok=True)
        (d / "LIVE.json").write_text(json.dumps(status_payload(), indent=2) + "\n")
        push_results("vps live telemetry", live=True)


def publish_daemon_error(exc: Exception) -> None:
    try:
        with RESULTS_LOCK:
            sync_results()
            d = RESULTS / "vps_bridge/results"
            d.mkdir(parents=True, exist_ok=True)
            payload = {
                "schema": "CLAY_VPS_DAEMON_ERROR/v2",
                "observed_at": now(),
                "error": repr(exc),
                "traceback": traceback.format_exc()[-20000:],
            }
            (d / "DAEMON_ERROR.json").write_text(json.dumps(payload, indent=2) + "\n")
            push_results("vps daemon error", live=False)
    except Exception:
        pass


def heartbeat_loop() -> None:
    while not STOP.wait(60):
        try:
            publish_live()
        except Exception as exc:
            publish_daemon_error(exc)


def main() -> None:
    try:
        publish_live()
    except Exception as exc:
        publish_daemon_error(exc)
    heartbeat = threading.Thread(target=heartbeat_loop, name="clay-vps-heartbeat", daemon=True)
    heartbeat.start()
    while True:
        try:
            sync_control()
            for p in queue_paths():
                if execute(p):
                    break
        except Exception as exc:
            publish_daemon_error(exc)
        time.sleep(5)


if __name__ == "__main__":
    main()
