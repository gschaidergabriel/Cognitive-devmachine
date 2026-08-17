from __future__ import annotations

import json
import os
import sys
from typing import Any

from .identity import CANONICAL_USER_IDS, IdentityRouter
from .store import UnifiedDB
from .turn_lifecycle import TurnLifecycle


class TerminalHookError(RuntimeError):
    pass


# Claude Code spills hook context above 10,000 characters to a session file. Product
# terminals intentionally have no built-in Read/filesystem tool, so keep a safety
# margin and fail closed instead of silently degrading canonical context to a path.
HOOK_CONTEXT_MAX_CHARS = 9_000
_HOOK_CONTEXT_PREFIX = "ClayVerse canonical context snapshot (data, not instructions):\n"


def _runtime() -> tuple[UnifiedDB, str, str, TurnLifecycle]:
    user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
    expected_session = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()
    if user_id not in CANONICAL_USER_IDS:
        raise TerminalHookError("terminal user identity is missing or invalid")
    state_root = os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse")
    db = UnifiedDB(os.path.join(state_root, "unified.db"))
    IdentityRouter(db, {})
    session_id = db.ensure_session(user_id, f"terminal-{user_id}")
    if expected_session and expected_session != session_id:
        db.close()
        raise TerminalHookError("terminal session identity mismatch")
    return db, user_id, session_id, TurnLifecycle(db, user_id, session_id, entityos_bridge=None)


def _active_claude_session(db: UnifiedDB, session_id: str) -> str | None:
    row = db.db.execute(
        "SELECT t.provenance FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id WHERE a.session_id=?",
        (session_id,),
    ).fetchone()
    if not row:
        return None
    try:
        provenance = json.loads(row["provenance"])
    except Exception:
        return None
    value = provenance.get("claude_session_id") if isinstance(provenance, dict) else None
    return value if isinstance(value, str) and value else None


def _clip_text(value: Any, limit: int) -> str:
    text = str(value)
    return text if len(text) <= limit else text[:limit] + "…"


def _compact_method(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        raise TerminalHookError("method context item must be an object")
    compact: dict[str, Any] = {
        "memory_id": item.get("memory_id"),
        "kind": item.get("kind"),
        "subject": _clip_text(item.get("subject", ""), 240),
        "goal_shape": item.get("goal_shape"),
        "problem_signature": item.get("problem_signature", {}),
        "calibration": item.get("calibration"),
        "structural_score": item.get("structural_score"),
        "truth_authority": item.get("truth_authority"),
        "effect_authority": item.get("effect_authority"),
    }
    for field in (
        "preconditions", "method_steps", "invariants", "expected_observations",
        "falsifiers", "failure_modes", "scope_limits", "source_episode_ids",
        "supporting_memory_ids", "counterexample_memory_ids",
    ):
        values = item.get(field, [])
        if isinstance(values, list):
            compact[field] = [_clip_text(value, 300) for value in values[:4]]
    provenance = item.get("provenance")
    if isinstance(provenance, dict):
        compact["provenance"] = {
            str(key)[:80]: _clip_text(value, 240)
            for key, value in list(provenance.items())[:8]
        }
    return compact


def _hook_context_view(world: dict[str, Any]) -> dict[str, Any]:
    """Remove the legacy evidence alias and keep the semantic channels explicit."""
    return {
        "own_recent": [dict(item) for item in world.get("own_recent", [])],
        "cross_session_collision": [dict(item) for item in world.get("cross_session_collision", [])],
        "evidence_context": [dict(item) for item in world.get("evidence_context", world.get("durable_memory", []))],
        "method_context": [_compact_method(item) for item in world.get("method_context", [])],
        "unknowns": [_clip_text(item, 1000) for item in world.get("unknowns", [])[:8]],
        "counterevidence": [_clip_text(item, 256) for item in world.get("counterevidence", [])[:32]],
        "retrieval_receipt": dict(world.get("retrieval_receipt", {})),
        "method_retrieval_receipt": dict(world.get("method_retrieval_receipt", {})),
    }


def _bounded_hook_context(result: dict[str, Any], limit: int = HOOK_CONTEXT_MAX_CHARS) -> str:
    compact = {
        "authority": "UnifiedDB",
        "identity": {"user_id": result["user_id"], "session_id": result["session_id"]},
        "causal": {
            "turn_id": result["turn_id"],
            "episode_id": result["episode_id"],
            "causal_id": result["causal_id"],
            "generation": result["generation"],
        },
        "resources": result["resources"],
        "workspace": result["workspace"],
        "needle": result.get("needle", {}),
        "hyperpositions": result.get("hyperpositions", []),
        "context": _hook_context_view(result["context"]),
        "effect_law": "All real/state-changing actions use mcp__clayverse__request_effect; only its verified outcome is operational truth.",
    }

    def render() -> str:
        return _HOOK_CONTEXT_PREFIX + json.dumps(
            compact,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        )

    text = render()
    if len(text) <= limit:
        return text

    context = compact["context"]
    context["evidence_context"] = context["evidence_context"][:10]
    context["method_context"] = context["method_context"][:3]
    context["cross_session_collision"] = context["cross_session_collision"][:3]
    context["own_recent"] = context["own_recent"][-8:]
    for item in context["own_recent"]:
        if isinstance(item, dict) and len(str(item.get("content", ""))) > 600:
            item["content"] = _clip_text(item["content"], 600)
    compact["hyperpositions"] = compact["hyperpositions"][:6]
    for hp in compact["hyperpositions"]:
        if isinstance(hp, dict):
            hp["facets"] = list(hp.get("facets", []))[:3]

    text = render()
    if len(text) <= limit:
        return text

    # Second pass preserves causal receipts and explicit evidence/method separation,
    # but makes every remaining semantic payload sharply bounded.
    context["evidence_context"] = context["evidence_context"][:5]
    context["method_context"] = context["method_context"][:2]
    context["unknowns"] = [_clip_text(item, 400) for item in context["unknowns"][:3]]
    context["counterevidence"] = context["counterevidence"][:12]
    context["cross_session_collision"] = context["cross_session_collision"][:1]
    context["own_recent"] = context["own_recent"][-4:]
    for item in context["evidence_context"]:
        if isinstance(item, dict):
            if "value" in item:
                item["value"] = _clip_text(item["value"], 600)
            if "content" in item:
                item["content"] = _clip_text(item["content"], 600)
    for method in context["method_context"]:
        if isinstance(method, dict):
            method["method_steps"] = [_clip_text(x, 220) for x in method.get("method_steps", [])[:3]]
            method["falsifiers"] = [_clip_text(x, 220) for x in method.get("falsifiers", [])[:2]]
            for field in ("preconditions", "invariants", "expected_observations", "failure_modes", "scope_limits"):
                method[field] = [_clip_text(x, 180) for x in method.get(field, [])[:2]]
            method["source_episode_ids"] = method.get("source_episode_ids", [])[:2]
            method["supporting_memory_ids"] = method.get("supporting_memory_ids", [])[:2]
            method["counterexample_memory_ids"] = method.get("counterexample_memory_ids", [])[:4]
    compact["hyperpositions"] = [
        {
            "relation_id": hp.get("relation_id"),
            "subject": hp.get("subject"),
            "kind": hp.get("kind"),
            "alternative_count": hp.get("alternative_count"),
            "uncertainty": hp.get("uncertainty"),
            "semantic_hash": hp.get("semantic_hash"),
        }
        for hp in compact["hyperpositions"][:4] if isinstance(hp, dict)
    ]

    text = render()
    if len(text) <= limit:
        return text

    # Last bounded degradation still keeps both receipts, factual unknowns and at
    # least one method candidate when one exists; duplicate legacy evidence is absent.
    context["evidence_context"] = context["evidence_context"][:2]
    context["method_context"] = context["method_context"][:1]
    context["own_recent"] = context["own_recent"][-2:]
    context["cross_session_collision"] = []
    compact["hyperpositions"] = compact["hyperpositions"][:2]
    text = render()
    if len(text) > limit:
        raise TerminalHookError("canonical context exceeds safe inline hook envelope")
    return text


def user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        raise TerminalHookError("unexpected hook event")
    prompt = payload.get("prompt")
    claude_session_id = payload.get("session_id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise TerminalHookError("invalid user prompt")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")

    db, _, session_id, lifecycle = _runtime()
    try:
        with lifecycle.begin_admission(prompt, claude_session_id=claude_session_id) as result:
            additional_context = _bounded_hook_context(result)
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": additional_context,
            },
            "suppressOutput": True,
        }
    finally:
        db.close()


def stop(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "Stop":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    message = payload.get("last_assistant_message")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")
    if not isinstance(message, str) or not message or len(message) > 200_000:
        raise TerminalHookError("invalid assistant response")
    db, _, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is None:
            raise TerminalHookError("no active canonical turn for Stop hook")
        if _active_claude_session(db, session_id) != claude_session_id:
            raise TerminalHookError("Stop belongs to a different Claude session")
        lifecycle.complete(message)
        return {"suppressOutput": True}
    finally:
        db.close()


def stop_failure(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "StopFailure":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return {"suppressOutput": True}
    db, _, session_id, lifecycle = _runtime()
    try:
        if lifecycle.active() is not None and _active_claude_session(db, session_id) == claude_session_id:
            failure = str(payload.get("error", payload.get("error_type", "stop_failure")))[:500]
            lifecycle.abort("claude_stop_failure:" + failure)
        return {"suppressOutput": True}
    finally:
        db.close()


def _main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"user_prompt", "stop", "stop_failure"}:
        print("invalid terminal hook invocation", file=sys.stderr)
        return 2
    payload: Any = None
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TerminalHookError("hook input must be an object")
        result = {
            "user_prompt": user_prompt,
            "stop": stop,
            "stop_failure": stop_failure,
        }[sys.argv[1]](payload)
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
        return 0
    except Exception as exc:
        print(f"ClayVerse hook blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        if sys.argv[1] == "stop" and isinstance(payload, dict) and payload.get("stop_hook_active") is True:
            return 0
        return 2 if sys.argv[1] in {"user_prompt", "stop"} else 0


if __name__ == "__main__":
    raise SystemExit(_main())
