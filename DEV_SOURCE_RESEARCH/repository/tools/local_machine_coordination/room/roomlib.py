"""
Shared helpers for clay-room-{join,heartbeat,note,status,leave}.

WHY: multiple independent Claude Code / "Frankenstein" sessions run in
PARALLEL on this one machine (ai-core-node). Without coordination they
collide (proven incident: two sessions drove the same shared Chrome tab
for ChatGPT at once, unaware of each other). "room" is ONE single local
registry (not multiple topic-rooms like the GitHub research_room.py) that:
  - lets every session announce what it's doing ("lane")
  - keeps every session's view of the others fresh (bulletin notes)
  - elects one session "CHIEF" to hold the overview / resolve conflicts

Runs silently in the background via a PostToolUse hook (no user-visible
prompts, no notify-send). Pattern copied 1:1 from
~/.claude/browser_lock/tablib.py (session-id resolution + flock'd JSON
registry) — don't diverge from that pattern without reason.
"""
import os
import json
import fcntl
import socket
from datetime import datetime, timezone

ROOM_DIR = os.path.expanduser("~/.claude/room")
STATE_FILE = os.path.join(ROOM_DIR, "state.json")
GUARD_FILE = os.path.join(ROOM_DIR, ".room_guard")

SCHEMA_VERSION = "1.0"

CHIEF_STALE_SECS = 5 * 60      # chief considered dead if heartbeat older than this
SESSION_STALE_SECS = 15 * 60   # session pruned entirely if heartbeat older than this
MAX_BULLETIN_NOTES = 50        # cap so bulletin.notes doesn't grow unbounded

# NOTE on pid liveness: the pid recorded for a session is captured from
# os.getppid() at hook-call time. Depending on exactly how the harness
# spawns PostToolUse hook commands, that pid can be a short-lived wrapper
# process that exits the instant the single hook invocation finishes --
# it is NOT reliably "the session's long-lived process" on every possible
# harness/shell configuration. Treating a dead pid as an INSTANT kill
# signal is therefore unsafe (a session mid-way between two heartbeats
# could get falsely pruned by another session's heartbeat call). So a
# dead pid only counts once combined with a grace period of no heartbeat
# refresh -- it speeds up detection of genuinely crashed sessions without
# risking false-prune of a live, merely-quiet-for-a-moment session.
PID_DEATH_GRACE_SECS = 30


def now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso(s):
    try:
        return datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except Exception:
        return None


def age_secs(iso_ts):
    """Seconds since iso_ts, or a huge number if unparseable/missing."""
    dt = parse_iso(iso_ts) if iso_ts else None
    if dt is None:
        return float("inf")
    return (datetime.now(timezone.utc) - dt).total_seconds()


def resolve_session_id():
    """
    Stable identifier for 'this Claude Code instance', same precedence
    pattern as tablib.resolve_session_id():
      1. CLAY_ROOM_SESSION_ID env override (manual/testing use)
      2. CLAUDE_CODE_SESSION_ID env var (harness-set, stable per session)
      3. fallback: hostname-PPID
    """
    sid = os.environ.get("CLAY_ROOM_SESSION_ID")
    if sid:
        return sid
    sid = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if sid:
        return sid
    return f"{socket.gethostname()}-{os.getppid()}"


def pid_alive(pid):
    """True if pid exists on THIS host. Cross-host sessions (none currently
    expected — room is single-machine) are never treated as dead by pid."""
    if not pid:
        return False
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True  # exists, just not ours
    except Exception:
        return False
    return True


def default_state():
    return {
        "schema_version": SCHEMA_VERSION,
        "chief_session_id": None,
        "sessions": {},
        "bulletin": {
            "updated_at": None,
            "updated_by": None,
            "notes": [],
        },
    }


def load_state():
    if not os.path.exists(STATE_FILE):
        return default_state()
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
        if not isinstance(data, dict) or "sessions" not in data:
            return default_state()
        data.setdefault("schema_version", SCHEMA_VERSION)
        data.setdefault("chief_session_id", None)
        data.setdefault("sessions", {})
        data.setdefault("bulletin", {"updated_at": None, "updated_by": None, "notes": []})
        return data
    except Exception:
        return default_state()


def save_state(state):
    os.makedirs(ROOM_DIR, exist_ok=True)
    tmp = STATE_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_FILE)


def prune_dead_sessions(state, stale_secs=SESSION_STALE_SECS):
    """Remove sessions whose heartbeat is too old, OR whose pid is dead on
    this host AND has gone unrefreshed past PID_DEATH_GRACE_SECS (see note
    above -- pid death alone, within the grace window, is not trusted).
    Returns removed dict {sid: entry}."""
    removed = {}
    kept = {}
    for sid, entry in state.get("sessions", {}).items():
        hb_age = age_secs(entry.get("last_heartbeat"))
        too_old = hb_age > stale_secs
        dead_pid_confirmed = (not pid_alive(entry.get("pid"))) and hb_age > PID_DEATH_GRACE_SECS
        if too_old or dead_pid_confirmed:
            removed[sid] = entry
        else:
            kept[sid] = entry
    state["sessions"] = kept
    return removed


def active_sessions(state):
    """Sessions considered alive right now: fresh heartbeat, and (pid alive
    OR still within the death-confirmation grace period)."""
    result = {}
    for sid, e in state.get("sessions", {}).items():
        hb_age = age_secs(e.get("last_heartbeat"))
        if hb_age > SESSION_STALE_SECS:
            continue
        if not pid_alive(e.get("pid")) and hb_age > PID_DEATH_GRACE_SECS:
            continue
        result[sid] = e
    return result


def elect_chief(state):
    """
    Deterministic election: oldest joined_at among currently active
    sessions wins (NOT random, NOT last-write-wins). Updates
    state['chief_session_id'] and each session's 'role'. Returns the
    winning session_id, or None if no active sessions.
    """
    actives = active_sessions(state)
    if not actives:
        state["chief_session_id"] = None
        return None

    def sort_key(item):
        sid, entry = item
        dt = parse_iso(entry.get("joined_at"))
        # unparseable joined_at sorts last (treated as newest, least eligible)
        return (dt is None, dt or datetime.max.replace(tzinfo=timezone.utc), sid)

    winner_sid, _ = sorted(actives.items(), key=sort_key)[0]
    state["chief_session_id"] = winner_sid
    for sid, entry in state.get("sessions", {}).items():
        entry["role"] = "CHIEF" if sid == winner_sid else "WORKER"
    return winner_sid


def chief_is_fresh(state):
    """True iff there's a chief_session_id, it's present+active, has
    role CHIEF, and heartbeat within CHIEF_STALE_SECS."""
    cid = state.get("chief_session_id")
    if not cid:
        return False
    entry = state.get("sessions", {}).get(cid)
    if not entry:
        return False
    hb_age = age_secs(entry.get("last_heartbeat"))
    if hb_age > CHIEF_STALE_SECS:
        return False
    if not pid_alive(entry.get("pid")) and hb_age > PID_DEATH_GRACE_SECS:
        return False
    return True


def ensure_chief(state):
    """Call after any join/heartbeat/leave: if no fresh chief exists,
    elect one deterministically. Returns current chief_session_id."""
    if not chief_is_fresh(state):
        elect_chief(state)
    return state.get("chief_session_id")


def add_note(state, session_id, text, max_notes=MAX_BULLETIN_NOTES):
    entry = {"at": now_iso(), "session_id": session_id, "text": text}
    notes = state.setdefault("bulletin", {}).setdefault("notes", [])
    notes.insert(0, entry)  # newest first
    del notes[max_notes:]
    state["bulletin"]["updated_at"] = now_iso()
    state["bulletin"]["updated_by"] = session_id


class Guard:
    """flock-based mutual exclusion for read-modify-write on state.json.
    Same pattern as tablib.Guard."""

    def __enter__(self):
        os.makedirs(ROOM_DIR, exist_ok=True)
        self.f = open(GUARD_FILE, "a+")
        fcntl.flock(self.f.fileno(), fcntl.LOCK_EX)
        return self

    def __exit__(self, *exc):
        fcntl.flock(self.f.fileno(), fcntl.LOCK_UN)
        self.f.close()
