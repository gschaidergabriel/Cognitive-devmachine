#!/usr/bin/env python3
"""local_bridge_daemon.py -- GitHub-Bruecke fuer die Forschungsentitaet, LOKAL
auf dieser Maschine (ai-core-node), Protokoll analog zu bridge_daemon.py auf
dem VPS, aber echte Shell/Datei-/Screenshot-Zugriffe auf dem realen Host statt
in einer Sandbox. Nutzt die bereits existierenden, bisher unbedienten Branches
`chatgpt-local-control` (Befehle) / `chatgpt-local-results` (Ergebnisse) im
Repo gschaidergabriel/clay-global-research-entity -- Gabriel selbst hatte
diese Branches am 2026-08-24 manuell mit Testbefehlen bestueckt, aber es lief
nie ein Daemon dagegen; dieses Skript ist der fehlende Teil.

Gabriel, 2026-09-12: die Forschungsentitaet soll hier genauso einsatzfaehig
sein wie Claude Code -- echte Werkzeuge, echte Dateizugriffe, echte
Screenshots, alles ueber diese Bruecke.

Sicherheits-Hygiene: kein Klartext-Secret wird je geschrieben/geloggt.
Ein knapper Deny-Filter blockt nur eindeutig katastrophale Befehle (analog zu
den deny-Regeln, die schon fuer Andreas' Claude Code existieren), sonst echte
Handlungsfaehigkeit.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import shlex
import sqlite3
import subprocess
import time
import traceback

# Attributions-Pflicht: dieselbe Bridge-Datei kann auf mehreren Hosts laufen,
# aber jeder Receipt muss Herkunft explizit tragen und jeder Host bekommt
# standardmaessig eigene Control/Result-Branches.
MACHINE_ID = os.environ.get("LOCAL_BRIDGE_MACHINE_ID", "ai-core-node")
OWNER = os.environ.get("LOCAL_BRIDGE_OWNER", "gabriel")

STATE_DIR = pathlib.Path(
    os.environ.get("LOCAL_BRIDGE_STATE_DIR",
                    str(pathlib.Path.home() / ".claude/star/local_bridge_state")))
REPO = STATE_DIR / "repo"
DB = STATE_DIR / "bridge.sqlite3"
SHOTS = STATE_DIR / "screenshots"
CONTROL_BRANCH = os.environ.get("LOCAL_BRIDGE_CONTROL_BRANCH", f"chatgpt-local-{MACHINE_ID}-control")
RESULTS_BRANCH = os.environ.get("LOCAL_BRIDGE_RESULTS_BRANCH", f"chatgpt-local-{MACHINE_ID}-results")
QUEUE = pathlib.Path("local_bridge/commands")
RESULTS_PATH = pathlib.Path("local_bridge/results")
MAX_TIMEOUT = 3600
MAX_LOG = 256 * 1024

DENY_PATTERNS = [
    r"rm\s+-rf\s+/(\s|$)", r"rm\s+-rf\s+/\*", r"mkfs\.", r"dd\s+.*of=/dev/",
    r":\(\)\{\s*:\|:&\s*\};:",
    r"chmod\s+-R\s+000\s+/", r">\s*/dev/sd[a-z]",
]


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def text(b: bytes) -> str:
    return b.decode("utf-8", errors="replace")


def _db() -> sqlite3.Connection:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(DB)
    c.execute("CREATE TABLE IF NOT EXISTS done(id TEXT PRIMARY KEY, sha TEXT, at TEXT, code INT)")
    c.commit()
    return c


def _git(*args, cwd=REPO, timeout=300, check=True):
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, timeout=timeout)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {args} failed: {text(p.stderr)}")
    return p


def sync_control():
    _git("fetch", "origin", f"refs/heads/{CONTROL_BRANCH}:refs/remotes/origin/{CONTROL_BRANCH}", check=False)


def sync_and_push_results(message: str):
    _git("add", "-A")
    diff = _git("diff", "--cached", "--quiet", check=False)
    if diff.returncode != 0:
        _git("commit", "-m", message)
    _git("push", "-u", "origin", f"HEAD:{RESULTS_BRANCH}", timeout=180)


def is_denied(command: str) -> str | None:
    for pat in DENY_PATTERNS:
        if re.search(pat, command):
            return pat
    return None


def op_exec(cmd: str, cwd: str, timeout: int):
    denied = is_denied(cmd)
    if denied:
        raise ValueError(f"DENIED_PATTERN:{denied}")
    workdir = cwd or str(pathlib.Path.home())
    return subprocess.run(["bash", "-lc", cmd], cwd=workdir, capture_output=True,
                           timeout=min(max(timeout, 1), MAX_TIMEOUT))


def op_status():
    payload = {
        "host": MACHINE_ID, "owner": OWNER, "time": now(),
        "cwd": str(pathlib.Path.home()),
    }
    b = json.dumps(payload, indent=2).encode()
    return subprocess.CompletedProcess(["status"], 0, b, b""), {}


def op_read_file(path: str):
    p = pathlib.Path(path).expanduser()
    data = p.read_bytes()
    return subprocess.CompletedProcess(["read_file"], 0, data[:MAX_LOG], b""), \
        {"sha256": sha(data), "bytes": len(data), "truncated": len(data) > MAX_LOG}


def op_write_text(path: str, content: str):
    p = pathlib.Path(path).expanduser()
    p.parent.mkdir(parents=True, exist_ok=True)
    data = content.encode()
    p.write_bytes(data)
    return subprocess.CompletedProcess(["write_text"], 0, f"WROTE {p}\n".encode(), b""), \
        {"sha256": sha(data), "bytes": len(data)}


def op_screenshot(name: str | None = None):
    """Echter Vollbild-Screenshot des realen Desktops via scrot."""
    SHOTS.mkdir(parents=True, exist_ok=True)
    fname = f"{name or 'shot'}_{int(time.time())}.png"
    dest = SHOTS / fname
    p = subprocess.run(["scrot", "-o", str(dest)], capture_output=True, timeout=15)
    if p.returncode != 0 or not dest.exists():
        raise RuntimeError(f"scrot failed rc={p.returncode} stderr={text(p.stderr)}")
    data = dest.read_bytes()
    out = subprocess.CompletedProcess(["screenshot"], 0, f"SCREENSHOT {dest}\n".encode(), b"")
    return out, {"path": str(dest), "sha256": sha(data), "bytes": len(data)}


def operate(s: dict):
    op = str(s.get("op", "exec"))
    timeout = min(max(int(s.get("timeout_seconds", 120)), 1), MAX_TIMEOUT)
    if op == "exec":
        return op_exec(str(s["command"]), str(s.get("cwd", "")), timeout), {}
    if op == "status":
        return op_status()
    if op == "read_file":
        return op_read_file(str(s["path"]))
    if op == "write_text":
        return op_write_text(str(s["path"]), str(s.get("content", "")))
    if op == "screenshot":
        return op_screenshot(s.get("name"))
    raise ValueError("UNSUPPORTED_OP:" + op)


def publish_receipt(receipt: dict, stdout: bytes, stderr: bytes):
    d = REPO / RESULTS_PATH
    (d / "receipts").mkdir(parents=True, exist_ok=True)
    (d / "logs").mkdir(parents=True, exist_ok=True)
    cid = receipt["command_id"]
    (d / "receipts" / f"{cid}.json").write_text(json.dumps(receipt, indent=2) + "\n")
    (d / "logs" / f"{cid}.stdout.txt").write_bytes(stdout[-MAX_LOG:])
    (d / "logs" / f"{cid}.stderr.txt").write_bytes(stderr[-MAX_LOG:])
    (d / "LATEST.json").write_text(json.dumps(receipt, indent=2) + "\n")


def execute(path: pathlib.Path) -> bool:
    raw = path.read_bytes()
    try:
        s = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"skip malformed command file {path.name}: {e}")
        c = _db()
        c.execute("INSERT OR IGNORE INTO done VALUES(?,?,?,?)", (f"malformed:{sha(raw)}", sha(raw), now(), -1))
        c.commit(); c.close()
        return False
    if s.get("schema") not in ("CLAY_LOCAL_COMMAND/v1",):
        print(f"skip unsupported schema in {path.name}: {s.get('schema')!r}")
        return False
    cid = str(s["command_id"])
    c = _db()
    if c.execute("SELECT 1 FROM done WHERE id=?", (cid,)).fetchone():
        c.close()
        return False
    started = now()
    stdout = stderr = b""
    meta = {}
    try:
        p, meta = operate(s)
        code = p.returncode
        stdout = p.stdout or b""
        stderr = p.stderr or b""
        st = "PASS" if code == 0 else "FAIL"
    except subprocess.TimeoutExpired as e:
        code, st = 124, "TIMEOUT"
        stdout = e.stdout or b""
        stderr = (e.stderr or b"") + repr(e).encode()
    except Exception as e:
        code, st = 125, "ERROR"
        stderr = (repr(e) + "\n" + traceback.format_exc()).encode()
    receipt = {
        "schema": "CLAY_LOCAL_RECEIPT/v1",
        "command_id": cid,
        "command_sha256": sha(raw),
        "host": MACHINE_ID,
        "owner": OWNER,
        "machine_id": MACHINE_ID,
        "started_at": started, "finished_at": now(),
        "status": st, "exit_code": code, "op": s.get("op", "exec"),
        "stdout_sha256": sha(stdout), "stderr_sha256": sha(stderr),
        "stdout_tail": text(stdout)[-24000:], "stderr_tail": text(stderr)[-24000:],
        "meta": meta,
        "execution_boundary": f"REAL_LOCAL_HOST_{MACHINE_ID.upper().replace('-', '_')}_NOT_SANDBOXED",
    }
    publish_receipt(receipt, stdout, stderr)
    c.execute("INSERT INTO done VALUES(?,?,?,?)", (cid, sha(raw), now(), code))
    c.commit()
    c.close()
    return True


def poll_once() -> int:
    """Ein Durchlauf: Control-Branch holen, neue Befehle ausfuehren, Ergebnisse pushen."""
    sync_control()
    _git("checkout", "-B", RESULTS_BRANCH, f"origin/{RESULTS_BRANCH}", check=False)
    cmd_dir = REPO / QUEUE
    processed = 0
    p = subprocess.run(["git", "-C", str(REPO), "ls-tree", "-r", "--name-only",
                        f"origin/{CONTROL_BRANCH}"], capture_output=True)
    names = [n for n in text(p.stdout).splitlines() if n.startswith(str(QUEUE) + "/") and n.endswith(".json")]
    for n in names:
        show = subprocess.run(["git", "-C", str(REPO), "show", f"origin/{CONTROL_BRANCH}:{n}"],
                               capture_output=True)
        if show.returncode != 0:
            continue
        cmd_dir.mkdir(parents=True, exist_ok=True)
        tmp = cmd_dir / pathlib.Path(n).name
        tmp.write_bytes(show.stdout)
        if execute(tmp):
            processed += 1
        tmp.unlink(missing_ok=True)
    if processed:
        sync_and_push_results(f"local bridge: {processed} command(s) executed on {MACHINE_ID}")
    return processed


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "poll-once":
        n = poll_once()
        print(f"processed={n}")
    else:
        while True:
            try:
                poll_once()
            except Exception as e:
                print("poll error:", e)
            time.sleep(20)
