#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Terminal surface for the canonical FranKenstein ChatGPT organ.

This is deliberately thin. It owns no memory/database/browser state. Every
line is handed to f2wp1207_chatgpt_organ.execute_terminal_turn(), which uses
the existing GRID10 + stern.py harness + unified.db paths.
"""
from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import uuid
from pathlib import Path

os.environ.setdefault("FRANK_OWNER", "gabriel")

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import stern
from f2wp1207_chatgpt_organ import execute_terminal_turn
from f2wp1207_chatgpt_exact_backend import ExactChatGPTBackend

_BACKEND = ExactChatGPTBackend(stern)
stern.chatgpt_senden = _BACKEND.send
stern.chatgpt_ernten = _BACKEND.harvest


def _session_id(explicit: str | None) -> str:
    if explicit:
        return explicit
    return f"terminal-chatgpt-{socket.gethostname()}-{uuid.uuid4().hex[:12]}"


def run_once(text: str, session_id: str) -> int:
    result = execute_terminal_turn(text, session_id=session_id, stern_module=stern)
    if result.get("ok"):
        print(result.get("response") or "")
        meta = {k: result.get(k) for k in (
            "run_id", "user_frame_id", "response_frame_id", "runtime_epoch_id", "workers"
        )}
        print("\n[FRANK/GRID10 " + json.dumps(meta, ensure_ascii=False, separators=(",", ":")) + "]",
              file=sys.stderr)
        return 0
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str), file=sys.stderr)
    return 1


def main() -> int:
    ap = argparse.ArgumentParser(description="FranKenstein terminal -> GRID10 -> ChatGPT organ -> GRID10")
    ap.add_argument("text", nargs="*", help="single turn; omit for interactive REPL")
    ap.add_argument("--session-id", default=None)
    args = ap.parse_args()
    sid = _session_id(args.session_id)
    if args.text:
        return run_once(" ".join(args.text), sid)

    print(f"FranKenstein ChatGPT organ | host={socket.gethostname()} | session={sid}")
    print("GRID10 owns turns. /exit beendet nur dieses Terminal.\n")
    while True:
        try:
            text = input("frank> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return 0
        if not text:
            continue
        if text.lower() in {"/exit", "/quit", "exit", "quit"}:
            return 0
        run_once(text, sid)


if __name__ == "__main__":
    raise SystemExit(main())
