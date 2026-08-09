#!/usr/bin/env python3
"""Claude Code lifecycle bridge into the single repo-native RAE hive entity."""
from __future__ import annotations
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR", pathlib.Path(__file__).resolve().parents[2])).resolve()
sys.path.insert(0, str(ROOT / "research_entity/runtime"))
from rae_state_runtime import RAEStateRuntime
from interaction_persona_runtime import init_tables as init_interaction_persona, summary as interaction_persona_summary
from rae_hive_runtime import init_tables as init_hive, register_organ, observe_organ, begin_usage_episode, hive_capsule

ACTOR = "claude-code-lead"
ROLE = "REPO_BUILD_EXECUTION_ORGAN"


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


def _capabilities(event: str) -> dict:
    return {
        "repo_local": True,
        "local_runtime": True,
        "code_build_edit": True,
        "shell_execution": True,
        "git_worktree": True,
        "hook_event": event,
    }


def context(event: str, prompt: str, session_id: str, model: str):
    node = f"claude-code:{session_id}"
    rt = RAEStateRuntime()
    try:
        init_interaction_persona(rt)
        init_hive(rt)
        register_organ(
            rt,
            node_id=node,
            actor_id=ACTOR,
            provider="Anthropic",
            model=model,
            role=ROLE,
            session_id=session_id,
            capabilities=_capabilities(event),
            limitations={"provider_context_is_ephemeral": True},
            authority={"evidence_overrides_organ_preference": True},
        )
        observe_organ(
            rt,
            organ_id=node,
            organ_class="LLM_REPO_EXECUTION_ORGAN",
            state={"event": event, "session_id": session_id},
            capabilities=_capabilities(event),
            limitations=["session context is temporary"],
            authority=["repo operations subject to RAE guards"],
            health="OK",
            confidence=1.0,
            evidence_refs=["CURRENT_CLAUDE_CODE_HOOK_EVENT"],
        )
        trig = trigger_of(prompt) if event == "UserPromptSubmit" else None
        cycle = rt.begin_cycle(
            prompt or f"{event}:{session_id}", node, ACTOR, "Anthropic", model, event,
            session_id=session_id, home_room=home_room(trig), trigger=trig,
        )
        begin_usage_episode(
            rt,
            node_id=node,
            cycle_id=cycle,
            task_shape=(trig and f"trigger:{trig}") or event,
        )
        cap = rt.capsule(node, ACTOR, cycle, event)
        cap["hive_entity"] = hive_capsule(rt, ACTOR)
        cap["interaction_persona_research"] = interaction_persona_summary(rt)
        cap["identity_invariants"] = [
            "the persistent identity is frank-project-global-research-entity",
            "Claude Code and ChatGPT are temporary cognition/execution organs of that same entity",
            "provider/model/session/node are provenance and capabilities, not separate identities",
            "durable cross-organ continuation must come from repo-native state, not chat replay",
            "evidence outranks organ preference",
            "every meaningful use adds observable learning evidence; behavioral adaptation is slow and evidence-gated",
        ]
        rt.record_injection(cycle, node, event, cap)
        return cap
    finally:
        rt.close()


def close_cycle(session_id: str):
    node = f"claude-code:{session_id}"
    rt = RAEStateRuntime()
    try:
        init_hive(rt)
        row = rt.u.execute(
            "SELECT cycle_id FROM prompt_cycles WHERE node_id=? AND status='ACTIVE' ORDER BY started_at DESC LIMIT 1",
            (node,),
        ).fetchone()
        if row:
            rt.end_cycle(row[0], node)
        rt.u.execute(
            "UPDATE hive_organs SET lifecycle_state='IDLE',last_pulse_at=? WHERE node_id=?",
            (__import__('datetime').datetime.now(__import__('datetime').timezone.utc).astimezone().isoformat(timespec='seconds'), node),
        )
        rt.u.commit()
    finally:
        rt.close()


def refresh():
    rt = RAEStateRuntime()
    try:
        init_interaction_persona(rt)
        init_hive(rt)
        rt.materialize_repo_sources()
    finally:
        rt.close()


def main():
    import argparse
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("context")
    c.add_argument("--event", required=True)
    c.add_argument("--prompt", default="")
    c.add_argument("--session-id", default="unknown-session")
    c.add_argument("--model", default="claude-unknown")
    x = sub.add_parser("close")
    x.add_argument("--session-id", default="unknown-session")
    sub.add_parser("refresh")
    args = ap.parse_args()
    if args.cmd == "context":
        print(json.dumps(context(args.event, args.prompt, args.session_id, args.model), ensure_ascii=False, indent=2))
    elif args.cmd == "close":
        close_cycle(args.session_id)
        print("{}")
    else:
        refresh()
        print("{}")

if __name__ == "__main__":
    main()
