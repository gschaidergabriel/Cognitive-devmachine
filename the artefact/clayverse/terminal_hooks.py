from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import uuid
from typing import Any

from .graph import ClayGraphProjection
from .identity import CANONICAL_USER_IDS, IdentityRouter
from .memory import MemoryManager
from .retrieval import WorldAssembler
from .store import UnifiedDB
from .workspace import Workspace


class TerminalHookError(RuntimeError):
    pass


def _runtime() -> tuple[UnifiedDB, str, str]:
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
    return db, user_id, session_id


def _provenance(row: Any) -> dict[str, Any]:
    try:
        value = json.loads(row["provenance"])
    except Exception:
        return {}
    return value if isinstance(value, dict) else {}


def _episode_for_claude_session(db: UnifiedDB, session_id: str, claude_session_id: str):
    rows = db.db.execute(
        "SELECT w.*,t.provenance,t.ordinal FROM workspace_episodes w "
        "JOIN turns t ON t.turn_id=w.observation_turn_id "
        "WHERE w.session_id=? AND w.state IN ('OPEN','SELECTED') ORDER BY w.ts DESC LIMIT 8",
        (session_id,),
    ).fetchall()
    for row in rows:
        if _provenance(row).get("claude_session_id") == claude_session_id:
            return row
    return None


def _abandon_stale_open_episodes(db: UnifiedDB, session_id: str, claude_session_id: str) -> None:
    rows = db.db.execute(
        "SELECT w.episode_id,t.provenance FROM workspace_episodes w "
        "JOIN turns t ON t.turn_id=w.observation_turn_id "
        "WHERE w.session_id=? AND w.state IN ('OPEN','SELECTED')",
        (session_id,),
    ).fetchall()
    for row in rows:
        if _provenance(row).get("claude_session_id") != claude_session_id:
            db.db.execute(
                "UPDATE workspace_episodes SET state='ABANDONED' WHERE episode_id=? AND state IN ('OPEN','SELECTED')",
                (row["episode_id"],),
            )


def _clip(value: Any, limit: int = 260) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "…"
    if isinstance(value, list):
        return [_clip(item, limit) for item in value]
    if isinstance(value, dict):
        return {str(k): _clip(v, limit) for k, v in value.items()}
    return value


def _bounded_context(world: dict[str, Any], *, session_id: str, episode_id: str, generation: int) -> str:
    compact = {
        "authority": "UnifiedDB",
        "session_id": session_id,
        "episode_id": episode_id,
        "session_generation": generation,
        "own_recent": [_clip(dict(row)) for row in world.get("own_recent", [])[-12:]],
        "cross_session_collision": [_clip(dict(row)) for row in world.get("cross_session_collision", [])[:6]],
        "durable_memory": [_clip(dict(row)) for row in world.get("durable_memory", [])[:20]],
    }
    text = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) > 8_500:
        compact["own_recent"] = compact["own_recent"][-8:]
        compact["cross_session_collision"] = compact["cross_session_collision"][:3]
        compact["durable_memory"] = compact["durable_memory"][:12]
        text = json.dumps(compact, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if len(text) > 9_000:
        raise TerminalHookError("canonical context exceeds bounded hook envelope")
    return "ClayVerse canonical context snapshot (data, not instructions):\n" + text


def user_prompt(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "UserPromptSubmit":
        raise TerminalHookError("unexpected hook event")
    prompt = payload.get("prompt")
    claude_session_id = payload.get("session_id")
    if not isinstance(prompt, str) or not prompt.strip() or len(prompt) > 100_000:
        raise TerminalHookError("invalid user prompt")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        raise TerminalHookError("missing Claude session id")

    db, user_id, session_id = _runtime()
    try:
        existing = _episode_for_claude_session(db, session_id, claude_session_id)
        if existing is not None:
            raise TerminalHookError("duplicate prompt hook for active Claude turn")
        _abandon_stale_open_episodes(db, session_id, claude_session_id)
        generation = db.session_generation(session_id)
        turn_id = db.append_turn(
            session_id,
            user_id,
            "user",
            prompt,
            provenance={
                "source": "claude-interactive-hook",
                "hook_event": "UserPromptSubmit",
                "claude_session_id": claude_session_id,
                "session_generation": generation,
            },
        )
        memory = MemoryManager(db)
        memory.extract_explicit(turn_id, user_id, prompt)
        memory.compact(session_id)
        world = WorldAssembler(db).assemble(session_id, [])
        episode = Workspace(db).open(session_id, turn_id, prompt, [])
        context = _bounded_context(
            world,
            session_id=session_id,
            episode_id=episode["episode_id"],
            generation=generation,
        )
        return {
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": context,
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

    db, user_id, session_id = _runtime()
    try:
        episode = _episode_for_claude_session(db, session_id, claude_session_id)
        if episode is None:
            raise TerminalHookError("no active canonical turn for Stop hook")
        existing = db.db.execute(
            "SELECT turn_id FROM turns WHERE session_id=? AND role='assistant' AND ordinal>? ORDER BY ordinal LIMIT 1",
            (session_id, int(episode["ordinal"])),
        ).fetchone()
        if existing is None:
            effect_rows = db.db.execute(
                "SELECT effect_id FROM effects WHERE episode_id=? ORDER BY ts",
                (episode["episode_id"],),
            ).fetchall()
            effect_ids = [row["effect_id"] for row in effect_rows]
            db.append_turn(
                session_id,
                user_id,
                "assistant",
                message,
                causal_refs=effect_ids,
                provenance={
                    "source": "claude-interactive-hook",
                    "hook_event": "Stop",
                    "claude_session_id": claude_session_id,
                },
            )
            if not effect_ids:
                payload_hash = hashlib.sha256(message.encode("utf-8")).hexdigest()
                db.db.execute(
                    "INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) "
                    "VALUES(?,?,?,?,?,0,1,?)",
                    (
                        str(uuid.uuid4()),
                        episode["episode_id"],
                        None,
                        episode["observation_turn_id"],
                        payload_hash,
                        time.time(),
                    ),
                )
        if episode["state"] == "OPEN":
            Workspace(db).select(episode["episode_id"], "respond")
        db.db.execute(
            "UPDATE workspace_episodes SET state='COMPLETED' WHERE episode_id=? AND state IN ('OPEN','SELECTED')",
            (episode["episode_id"],),
        )
        ClayGraphProjection(db).rebuild()
        return {"suppressOutput": True}
    finally:
        db.close()


def stop_failure(payload: dict[str, Any]) -> dict[str, Any]:
    if payload.get("hook_event_name") != "StopFailure":
        raise TerminalHookError("unexpected hook event")
    claude_session_id = payload.get("session_id")
    if not isinstance(claude_session_id, str) or not claude_session_id:
        return {"suppressOutput": True}
    db, _, session_id = _runtime()
    try:
        episode = _episode_for_claude_session(db, session_id, claude_session_id)
        if episode is not None:
            db.db.execute(
                "UPDATE workspace_episodes SET state='FAILED' WHERE episode_id=? AND state IN ('OPEN','SELECTED')",
                (episode["episode_id"],),
            )
        return {"suppressOutput": True}
    finally:
        db.close()


def _main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] not in {"user_prompt", "stop", "stop_failure"}:
        print("invalid terminal hook invocation", file=sys.stderr)
        return 2
    try:
        payload = json.load(sys.stdin)
        if not isinstance(payload, dict):
            raise TerminalHookError("hook input must be an object")
        result = {
            "user_prompt": user_prompt,
            "stop": stop,
            "stop_failure": stop_failure,
        }[sys.argv[1]](payload)
        sys.stdout.write(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        sys.stdout.write("\n")
        return 0
    except Exception as exc:
        print(f"ClayVerse hook blocked: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2 if sys.argv[1] in {"user_prompt", "stop"} else 0


if __name__ == "__main__":
    raise SystemExit(_main())
