#!/usr/bin/env python3
"""Produce bounded central RAE state context for Claude Code lifecycle adapters."""
from __future__ import annotations
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", pathlib.Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(ROOT / "research_entity/runtime"))
from rae_state_runtime import RAEStateRuntime
from interaction_persona_runtime import init_tables as init_interaction_persona, summary as interaction_persona_summary

ACTOR = "claude-code-lead"


def trigger_of(prompt: str):
    p = prompt.strip().lower()
    try:
        reg = json.loads((ROOT / "research_entity/global/RESEARCH_TRIGGER_REGISTRY.json").read_text(encoding="utf-8"))
        return p if p in (reg.get("triggers") or {}) else None
    except Exception:
        return None


def home_room(trigger):
    if not trigger: return None
    if trigger in {"fusion", "hypofusion"}: return "center"
    if trigger == "dump": return "intake"
    return trigger


def context(event: str, prompt: str, session_id: str, model: str):
    node = f"claude-code:{session_id}"
    rt = RAEStateRuntime()
    try:
        init_interaction_persona(rt)
        trig = trigger_of(prompt) if event == "UserPromptSubmit" else None
        cycle = rt.begin_cycle(prompt or f"{event}:{session_id}", node, ACTOR, "Anthropic", model, event,
                               session_id=session_id, home_room=home_room(trig), trigger=trig)
        cap = rt.capsule(node, ACTOR, cycle, event)
        cap["interaction_persona_research"] = interaction_persona_summary(rt)
        cap["interaction_persona_invariants"] = [
            "improve relationship quality through reliability, understanding, continuity, calibrated warmth and repair",
            "do not optimize covert attachment, dependency, guilt, exclusivity or engagement retention",
            "simulated personality authenticity means causal consistency with declared persona state, not consciousness evidence",
            "cross-node Frank persona consistency is a testable Harness property",
            "person-specific preferences remain personal/configurable state; general architecture promotion requires evidence",
        ]
        rt.record_injection(cycle, node, event, cap)
        return cap
    finally:
        rt.close()


def close_cycle(session_id: str):
    node = f"claude-code:{session_id}"
    rt = RAEStateRuntime()
    try:
        row = rt.u.execute("SELECT cycle_id FROM prompt_cycles WHERE node_id=? AND status='ACTIVE' ORDER BY started_at DESC LIMIT 1", (node,)).fetchone()
        if row: rt.end_cycle(row[0], node)
    finally:
        rt.close()


def refresh():
    rt = RAEStateRuntime()
    try:
        init_interaction_persona(rt)
        rt.materialize_repo_sources()
    finally: rt.close()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("context")
    c.add_argument("--event", required=True); c.add_argument("--prompt", default="")
    c.add_argument("--session-id", default="unknown-session"); c.add_argument("--model", default="claude-unknown")
    x = sub.add_parser("close"); x.add_argument("--session-id", default="unknown-session")
    sub.add_parser("refresh")
    args = ap.parse_args()
    if args.cmd == "context": print(json.dumps(context(args.event, args.prompt, args.session_id, args.model), ensure_ascii=False, indent=2))
    elif args.cmd == "close": close_cycle(args.session_id); print("{}")
    else: refresh(); print("{}")

if __name__ == "__main__": main()
