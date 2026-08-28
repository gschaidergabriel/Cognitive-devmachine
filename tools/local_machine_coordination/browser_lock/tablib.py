"""
Shared helpers for clay-browser-tab-{acquire,release,status}.

Model: NOT an exclusive lock. Every Claude Code session gets its OWN tab in
the shared gstack `browse` daemon (headed Chrome on :99). Sessions work in
PARALLEL, each strictly confined to its own tab id — never touching another
session's tab. Registry maps session_id -> tab_id so a session can find its
own tab again across multiple tool calls, and so tools can detect/clean up
orphaned entries (tab closed/crashed without release).
"""
import os
import re
import json
import fcntl
import subprocess
from datetime import datetime, timezone

BROWSE_BIN = os.path.expanduser("~/.claude/skills/gstack/browse/dist/browse")
LOCK_DIR = os.path.expanduser("~/.claude/browser_lock")
REGISTRY_FILE = os.path.join(LOCK_DIR, "session_tabs.json")
GUARD_FILE = os.path.join(LOCK_DIR, ".tab_guard")

TAB_LINE_RE = re.compile(r"^\s*(→)?\s*\[(\d+)\]\s+(.*?)\s+—\s+(\S+)\s*$")


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def resolve_session_id():
    """
    Stable identifier for 'this Claude Code instance', in precedence order:
      1. CLAY_BROWSER_SESSION_ID env override (manual/testing use)
      2. CLAUDE_CODE_SESSION_ID env var (set by the Claude Code harness,
         stable for the lifetime of one session)
      3. fallback: hostname-PPID (stable across calls from the same shell)
    """
    sid = os.environ.get("CLAY_BROWSER_SESSION_ID")
    if sid:
        return sid
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        return sid
    import socket
    return f"{socket.gethostname()}-{os.getppid()}"


def run_browse(*args):
    """Run the browse CLI, return (returncode, stdout, stderr)."""
    proc = subprocess.run(
        [BROWSE_BIN, *args],
        capture_output=True,
        text=True,
        timeout=30,
    )
    return proc.returncode, proc.stdout, proc.stderr


def list_tab_ids():
    """Return set of currently-open tab ids (as ints) from `browse tabs`."""
    rc, out, err = run_browse("tabs")
    ids = set()
    if rc != 0:
        return ids
    for line in out.splitlines():
        m = TAB_LINE_RE.match(line)
        if m:
            ids.add(int(m.group(2)))
    return ids


def load_registry():
    if not os.path.exists(REGISTRY_FILE):
        return {}
    try:
        with open(REGISTRY_FILE) as f:
            return json.load(f)
    except Exception:
        return {}


def save_registry(reg):
    os.makedirs(LOCK_DIR, exist_ok=True)
    tmp = REGISTRY_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(reg, f, indent=2)
    os.replace(tmp, REGISTRY_FILE)


def prune_orphans(reg, live_ids):
    """Remove registry entries whose tab_id no longer exists. Returns (pruned_reg, removed_dict)."""
    removed = {}
    kept = {}
    for sid, entry in reg.items():
        if entry.get("tab_id") in live_ids:
            kept[sid] = entry
        else:
            removed[sid] = entry
    return kept, removed


class Guard:
    """flock-based mutual exclusion for read-modify-write on the registry file."""

    def __enter__(self):
        os.makedirs(LOCK_DIR, exist_ok=True)
        self.f = open(GUARD_FILE, "a+")
        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        self.f.close()
