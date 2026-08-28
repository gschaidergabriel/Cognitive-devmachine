#!/usr/bin/env python3
"""taetigkeit_hook.py — PostToolUse / PostToolUseFailure hook.

Zero model calls. Zero network. A shell command the Claude Code harness
runs after every tool call; it appends ONE compact JSON line describing
that call to a local stream file and exits. It never reads or writes
prompt text, model text, or tool output/content — only the same
structural fields taetigkeit.py extracts retroactively from transcripts:
tool name, target path, truncated Bash command, ok/error, session id,
provenance (host + transcript path if given).

Confirmed against two REAL, already-working hook installs found on this
machine (not guessed):
  - /opt/clayverse/werkzeug/tor_hook.py (frank-api, PreToolUse) confirms
    the stdin keys tool_name, tool_input, cwd, session_id.
  - ChanMeng666_claude-code-audio-hooks (a real published Claude Code
    plugin, vendored locally under ~/.local/share/frank/sandbox/) confirms
    PostToolUse and PostToolUseFailure are two SEPARATE, native Claude
    Code hook events -- that is the ok/error signal used below, not any
    parsing of tool_response content. It also confirms transcript_path is
    a stdin field.

NOT confirmed anywhere locally: a stable "tool_use_id" in the PostToolUse
stdin payload. Because of that this hook's roh_hash is NOT guaranteed to
collide with the retroactive walker's hash for the same real event (that
one hashes the tool_use id found inside the transcript JSON). See the
install notes for the operational consequence and the recommended
non-overlap policy.

Must NEVER throw, NEVER block, NEVER print anything that would look like
tool output to the transcript. Always exits 0.
"""
import hashlib
import json
import os
import re
import socket
import sys
import time
from datetime import datetime, timezone

MAX_CMD = 200
STREAM_PATH = os.environ.get(
    "TAETIGKEIT_STREAM",
    os.path.expanduser("~/.claude/taetigkeit-stream.jsonl"),
)


def extract_ziel_pfad(name, inp):
    if not isinstance(inp, dict):
        return None
    for key in ("file_path", "path", "notebook_path"):
        v = inp.get(key)
        if isinstance(v, str):
            return v
    if name == "Bash" and isinstance(inp.get("command"), str):
        m = re.search(r"(/[A-Za-z0-9_\-./]+)", inp["command"])
        if m:
            return m.group(1)
    if name == "WebFetch" and isinstance(inp.get("url"), str):
        return inp["url"]
    return None


def extract_aktion(name, inp):
    if not isinstance(inp, dict):
        return None
    if name == "Bash" and isinstance(inp.get("command"), str):
        return inp["command"][:MAX_CMD]
    return None


def main():
    try:
        raw = sys.stdin.read()
        d = json.loads(raw) if raw.strip() else {}
    except Exception:
        return 0  # unreadable call: log nothing, never block

    try:
        ev = d.get("hook_event_name", "")
        if ev not in ("PostToolUse", "PostToolUseFailure"):
            return 0

        tool_name = d.get("tool_name")
        tool_input = d.get("tool_input") or {}
        ziel = extract_ziel_pfad(tool_name, tool_input)
        aktion = extract_aktion(tool_name, tool_input)
        sitzung = d.get("session_id")
        instanz = d.get("agent_id") or d.get("agentId") or "haupt"
        quelle = d.get("transcript_path") or ""
        wirt = socket.gethostname()
        zeit = datetime.now(timezone.utc).isoformat()
        ergebnis = "ok" if ev == "PostToolUse" else "error"

        # No confirmed stable per-call id in this payload (see module
        # docstring) -> hash a composite of what IS in the payload plus
        # a high-resolution local clock, so at minimum concurrent hook
        # firings within one process never collide with each other.
        basis = "|".join([
            sitzung or "", str(tool_name), str(ziel), str(aktion),
            str(time.time_ns()),
        ])
        roh_hash = hashlib.sha256(("livehook:" + basis).encode("utf-8", "replace")).hexdigest()

        row = {
            "wirt": wirt,
            "instanz": instanz,
            "sitzung": sitzung,
            "zeit": zeit,
            "werkzeug": tool_name,
            "ziel_pfad": ziel,
            "aktion": aktion,
            "ergebnis": ergebnis,
            "quelle": quelle,
            "zeile_nr": None,
            "roh_hash": roh_hash,
        }

        os.makedirs(os.path.dirname(STREAM_PATH), exist_ok=True)
        line = json.dumps(row, ensure_ascii=False) + "\n"
        with open(STREAM_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except Exception:
        # A logging hook must never be the reason a session breaks.
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
