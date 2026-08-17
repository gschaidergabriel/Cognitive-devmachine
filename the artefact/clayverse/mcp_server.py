from __future__ import annotations

import json
import os
from pathlib import Path

from .autonomy import AutonomyController
from .autonomy_context import bounded_autonomy_context


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP for effects only; turns are owned deterministically by ClayVerse lifecycle."""

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self.db = lifecycle.db
        self.user_id = lifecycle.user_id
        self.session_id = lifecycle.session_id
        self.autonomy = AutonomyController(self.db)

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB
        from .turn_lifecycle import TurnLifecycle

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(root / "unified.db")
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()

        entityos = None
        enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
        sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
        if enable_exec:
            if not path or not sha256 or not os.path.isabs(path):
                db.close()
                raise BridgeStateError("EntityOS execution enabled without complete digest binding")
            entityos = EntityOSBridge(path=path, sha256=sha256)
            entityos.verify()
        return cls(TurnLifecycle(db, user_id, session_id, entityos_bridge=entityos))

    def _active_autonomy_identity(self) -> tuple[str, str] | None:
        with self.db.tx() as db:
            row = db.execute(
                "SELECT t.provenance FROM active_turns a "
                "JOIN turns t ON t.turn_id=a.turn_id "
                "WHERE a.session_id=? AND a.user_id=?",
                (self.session_id, self.user_id),
            ).fetchone()
            if row is None:
                return None
            try:
                provenance = self.autonomy._loads(row["provenance"] or "{}")
            except Exception as exc:
                raise BridgeStateError("active turn provenance malformed") from exc
            if provenance.get("source") != "clayverse-autonomy:goal-step":
                return None
            goal_id = provenance.get("goal_id")
            step_id = provenance.get("autonomy_step_id")
            if not isinstance(goal_id, str) or not goal_id or not isinstance(step_id, str) or not step_id:
                raise BridgeStateError("autonomous active turn identity missing")
            return goal_id, step_id

    def _admitted_autonomy_effect(self, goal_id: str, step_id: str) -> tuple[dict, dict]:
        goal_id = str(goal_id).strip()
        step_id = str(step_id).strip()
        if not goal_id or not step_id or len(goal_id) > 256 or len(step_id) > 256 or "\x00" in goal_id or "\x00" in step_id:
            raise ValueError("invalid autonomy goal/step identity")
        with self.db.tx() as db:
            _state, goal = self.autonomy._goal(db, goal_id)
            step = goal.get("current_step")
            if (
                not isinstance(step, dict)
                or step.get("step_id") != step_id
                or step.get("kind") != "effect"
                or step.get("status") != "ADMITTED"
                or not isinstance(step.get("effect"), dict)
            ):
                raise BridgeStateError("autonomy effect step is not exactly admitted")
            row = db.execute(
                "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,a.user_id,"
                "t.session_id AS turn_session_id,t.user_id AS turn_user_id,t.provenance "
                "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
                "WHERE a.session_id=? AND a.user_id=?",
                (self.session_id, self.user_id),
            ).fetchone()
            if row is None:
                raise BridgeStateError("no active autonomous turn")
            try:
                provenance = self.autonomy._loads(row["provenance"] or "{}")
                entity_generation = int(provenance.get("entity_generation"))
                session_generation = int(provenance.get("session_generation"))
            except Exception as exc:
                raise BridgeStateError("autonomous turn provenance malformed") from exc
            if (
                provenance.get("source") != "clayverse-autonomy:goal-step"
                or provenance.get("goal_id") != goal_id
                or provenance.get("autonomy_step_id") != step_id
                or provenance.get("causal_id") != row["causal_id"]
                or row["turn_session_id"] != self.session_id
                or row["turn_user_id"] != self.user_id
                or int(row["generation"]) != int(goal["generation"])
                or entity_generation != int(goal["generation"])
                or session_generation != int(goal["generation"])
            ):
                raise PermissionError("active turn is not the exact admitted autonomy goal step")
            return dict(step["effect"]), {
                "turn_id": row["turn_id"],
                "episode_id": row["episode_id"],
                "causal_id": row["causal_id"],
                "generation": int(row["generation"]),
            }

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        if self._active_autonomy_identity() is not None:
            raise PermissionError("autonomous turns must dispatch the exact admitted step through request_autonomy_effect")
        if capability not in {"entityos.exec", "state.noop"}:
            raise PermissionError("capability denied")
        if not isinstance(target, str) or not target or len(target) > 2048 or "\x00" in target:
            raise ValueError("invalid effect target")
        if capability == "entityos.exec":
            if not isinstance(argv, list) or not argv or len(argv) > 128:
                raise ValueError("entityos.exec requires bounded argv")
            if any(not isinstance(x, str) or not x or len(x) > 8192 or "\x00" in x for x in argv):
                raise ValueError("invalid effect argv")
        elif argv not in (None, []):
            raise ValueError("state.noop does not accept argv")
        else:
            argv = None
        result = self.lifecycle.request_effect(capability, target, argv)
        result["boundary"] = "ClayVerse EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse EffectGate"
        return result

    def request_autonomy_effect(self, goal_id: str, step_id: str) -> dict:
        """Dispatch the stored admitted effect intent; callers cannot resupply target/argv."""
        effect, binding = self._admitted_autonomy_effect(goal_id, step_id)
        result = self.lifecycle.request_effect(effect["capability"], effect["target"], effect.get("argv"))
        effect_id = result.get("effect_id")
        if not isinstance(effect_id, str) or not effect_id:
            raise BridgeStateError("canonical lifecycle returned no effect identity")
        autonomy_result = self.autonomy.record_effect_result(goal_id, step_id, effect_id)
        result["autonomy"] = autonomy_result
        result["autonomy_binding"] = binding
        result["boundary"] = (
            "AutonomyController -> ClayVerse EffectGate -> EntityOS"
            if effect["capability"] == "entityos.exec"
            else "AutonomyController -> ClayVerse EffectGate"
        )
        return result

    def session_state(self) -> dict:
        active = self.lifecycle.active()
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_turn": {
                "turn_id": active["turn_id"],
                "episode_id": active["episode_id"],
                "causal_id": active["causal_id"],
                "generation": int(active["generation"]),
                "effect_id": active["effect_id"],
            } if active else None,
            "autonomy": bounded_autonomy_context(self.db, self.user_id),
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
            "turn_ingestion": "automatic_claude_hooks",
        }


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseEffectBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions=(
            "UserPromptSubmit and Stop hooks own interactive turn ingestion/context/completion automatically. "
            "Use request_effect only for ordinary real/state-changing actions. "
            "Use request_autonomy_effect only for an already-admitted durable autonomy effect step so exact goal/step/turn/episode/causal identity remains bound. "
            "Never bypass EffectGate with host execution and never claim success without a verified returned outcome."
        ),
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=effectful)
    def request_autonomy_effect(goal_id: str, step_id: str) -> dict:
        return bridge.request_autonomy_effect(goal_id, step_id)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return bridge.session_state()

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
