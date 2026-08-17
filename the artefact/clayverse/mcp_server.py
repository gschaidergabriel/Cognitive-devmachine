from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

from .agency import AgencyView
from .autonomy import AutonomyController, CompletionNotVerified, GoalBudget


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP for bounded effects and explicit owner-authorized goal control."""

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self.db = lifecycle.db
        self.user_id = lifecycle.user_id
        self.session_id = lifecycle.session_id
        self.autonomy = AutonomyController(self.db)
        self.agency = AgencyView(self.db)

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

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
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

    def _active_user_authorization(self, authorization_quote: str) -> tuple[str, str]:
        if (
            not isinstance(authorization_quote, str)
            or len(authorization_quote.strip()) < 8
            or len(authorization_quote) > 1000
            or "\x00" in authorization_quote
        ):
            raise ValueError("invalid authorization quote")
        quote = authorization_quote.strip()
        active = self.lifecycle.active()
        if active is None:
            raise BridgeStateError("goal control requires an active canonical user turn")
        if int(active["generation"]) != self.db.entity_generation():
            raise BridgeStateError("goal control belongs to a stale entity generation")
        turn = self.db.db.execute(
            "SELECT role,content,user_id FROM turns WHERE turn_id=? AND session_id=?",
            (active["turn_id"], self.session_id),
        ).fetchone()
        if not turn or turn["role"] != "user" or turn["user_id"] != self.user_id:
            raise BridgeStateError("active goal authorization turn is invalid")
        if quote not in turn["content"]:
            raise PermissionError("authorization quote is not present in the active user prompt")
        return active["turn_id"], quote

    def _owned_goal(self, goal_id: str) -> dict:
        if not isinstance(goal_id, str) or not goal_id or len(goal_id) > 128:
            raise ValueError("invalid goal id")
        for goal in self.autonomy.snapshot(user_id=self.user_id)["goals"]:
            if goal["goal_id"] == goal_id:
                return goal
        raise PermissionError("goal owner mismatch")

    def _audit_goal_control(self, turn_id: str, action: str, subject_ref: str, quote: str, result: dict) -> None:
        receipt = {
            "agency_control": action,
            "subject_ref": subject_ref,
            "source_turn_id": turn_id,
            "authorization_quote_sha256": hashlib.sha256(quote.encode("utf-8")).hexdigest(),
            "result": result,
        }
        self.db.append_turn(
            self.session_id,
            self.user_id,
            "system",
            json.dumps(receipt, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            provenance={"source": "agency-gate", "phase": "control-receipt"},
        )

    def goal_state(self) -> dict:
        return self.agency.snapshot(user_id=self.user_id)

    def goal_create(
        self,
        authorization_quote: str,
        completion_mode: str = "user_ack",
        required_capability: str | None = None,
        priority: int = 50,
        max_steps: int = 32,
        max_retries_per_step: int = 3,
        max_effects: int = 8,
    ) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        completion_mode = str(completion_mode)
        if completion_mode == "user_ack":
            required_capability = None
        budget = GoalBudget(
            max_steps=int(max_steps),
            max_retries_per_step=int(max_retries_per_step),
            max_effects=int(max_effects),
        ).validate()
        goal = self.autonomy.create_goal_from_turn(
            self.user_id,
            self.session_id,
            turn_id,
            completion_mode=completion_mode,
            required_capability=required_capability,
            priority=int(priority),
            budget=budget,
        )
        result = {
            "goal_id": goal["goal_id"],
            "status": goal["status"],
            "objective_source": "canonical_user_turn",
            "completion_contract": goal["completion_contract"],
            "budget": goal["budget"],
            "admission_turn_id": turn_id,
        }
        self._audit_goal_control(turn_id, "goal.create", goal["goal_id"], quote, result)
        return result

    def goal_set_status(self, authorization_quote: str, goal_id: str, action: str) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        self._owned_goal(goal_id)
        action = str(action).upper()
        if action == "PAUSE":
            result = self.autonomy.block_goal(goal_id, "user_paused")
        elif action == "RESUME":
            result = self.autonomy.resume_goal(goal_id)
        elif action == "CANCEL":
            result = self.autonomy.cancel_goal(goal_id)
        else:
            raise ValueError("goal action must be PAUSE, RESUME or CANCEL")
        self._audit_goal_control(turn_id, f"goal.{action.lower()}", goal_id, quote, result)
        return result

    def goal_acknowledge(self, authorization_quote: str, goal_id: str) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        goal = self._owned_goal(goal_id)
        acknowledgement = self.autonomy.acknowledge_by_user(goal_id, turn_id)
        try:
            verification = self.autonomy.verify_completion(goal_id)
        except CompletionNotVerified:
            verification = {
                "goal_id": goal_id,
                "status": goal["status"],
                "completion_verified": False,
                "reason": "completion_contract_not_satisfied",
            }
        result = {"acknowledgement": acknowledgement, "verification": verification}
        self._audit_goal_control(turn_id, "goal.acknowledge", goal_id, quote, result)
        return result

    def session_state(self) -> dict:
        active = self.lifecycle.active()
        autonomy = self.autonomy.snapshot(user_id=self.user_id)
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
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
            "turn_ingestion": "automatic_claude_hooks",
            "autonomy": {
                "schema": autonomy["schema"],
                "revision": autonomy["revision"],
                "goal_count": len(autonomy["goals"]),
            },
        }


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseEffectBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions=(
            "UserPromptSubmit and Stop hooks own turn ingestion/context/completion automatically. "
            "Operational effects use request_effect and EffectGate. Durable goal changes use the dedicated goal tools "
            "only when the active human prompt explicitly authorizes that change; pass an exact quote from that prompt. "
            "The durable goal objective itself is copied from the canonical user turn and cannot be rewritten by cognition."
        ),
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)
    control = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return bridge.session_state()

    @mcp.tool(annotations=ro)
    def goal_state() -> dict:
        return bridge.goal_state()

    @mcp.tool(annotations=control)
    def goal_create(
        authorization_quote: str,
        completion_mode: str = "user_ack",
        required_capability: str | None = None,
        priority: int = 50,
        max_steps: int = 32,
        max_retries_per_step: int = 3,
        max_effects: int = 8,
    ) -> dict:
        return bridge.goal_create(
            authorization_quote,
            completion_mode,
            required_capability,
            priority,
            max_steps,
            max_retries_per_step,
            max_effects,
        )

    @mcp.tool(annotations=control)
    def goal_set_status(authorization_quote: str, goal_id: str, action: str) -> dict:
        return bridge.goal_set_status(authorization_quote, goal_id, action)

    @mcp.tool(annotations=control)
    def goal_acknowledge(authorization_quote: str, goal_id: str) -> dict:
        return bridge.goal_acknowledge(authorization_quote, goal_id)

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
