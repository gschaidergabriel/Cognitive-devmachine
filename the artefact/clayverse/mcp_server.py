from __future__ import annotations

import hashlib
import json
import os
import uuid
from pathlib import Path

from .agency import AgencyState


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP for bounded effects and explicit owner-authorized goal control.

    Turn ingestion remains deterministic in Claude hooks. Operational actions still
    have exactly one authority: EffectGate. Goal/control-plane mutations use the
    separate AgencyState gate below and must bind to an exact quote from the active
    canonical user turn so the model cannot silently invent a human goal decision.
    """

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self.db = lifecycle.db
        self.user_id = lifecycle.user_id
        self.session_id = lifecycle.session_id
        self.agency = AgencyState(self.db)

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
            or not authorization_quote.strip()
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

    def _audit_goal_control(self, turn_id: str, action: str, subject_ref: str, quote: str) -> None:
        quote_hash = hashlib.sha256(quote.encode("utf-8")).hexdigest()
        with self.db.tx() as tx:
            self.agency._event(
                tx,
                "agency.control_admitted",
                "turn",
                f"{turn_id}:{action}:{subject_ref}:{uuid.uuid4().hex}",
                {
                    "turn_id": turn_id,
                    "user_id": self.user_id,
                    "action": action,
                    "subject_ref": subject_ref,
                    "authorization_quote_sha256": quote_hash,
                    "authorization_quote_bytes": len(quote.encode("utf-8")),
                },
            )
            self.agency._refresh_hash(tx)

    @staticmethod
    def _goal_text(value: str, name: str, max_chars: int = 8000) -> str:
        if not isinstance(value, str) or not value.strip() or len(value) > max_chars or "\x00" in value:
            raise ValueError(f"invalid {name}")
        return value.strip()

    def goal_state(self) -> dict:
        return self.agency.snapshot(
            user_id=self.user_id,
            max_goals=20,
            max_attempts_per_milestone=5,
        )

    def goal_create(
        self,
        authorization_quote: str,
        title: str,
        objective: str,
        success_criteria: str,
        priority: int = 0,
    ) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        title = self._goal_text(title, "goal title", 1000)
        objective = self._goal_text(objective, "goal objective")
        success_criteria = self._goal_text(success_criteria, "goal success criteria")
        priority = int(priority)
        if priority < -100 or priority > 100:
            raise ValueError("goal priority must be between -100 and 100")

        goal_id = self.agency.create_goal(
            self.user_id,
            title,
            objective,
            success_criteria,
            priority=priority,
        )
        milestone_ids = [
            self.agency.add_milestone(
                goal_id,
                "CONCEPT",
                "Concept",
                "A reviewable concept is grounded in canonical state and directly supports the goal success criteria: "
                + success_criteria,
            ),
            self.agency.add_milestone(
                goal_id,
                "PROTOTYPE",
                "Prototype",
                "A bounded prototype or equivalent executable evidence demonstrates measurable progress toward: "
                + success_criteria,
            ),
            self.agency.add_milestone(
                goal_id,
                "FINAL",
                "Final",
                "Canonical final evidence is reviewable and satisfies the declared goal success criteria: "
                + success_criteria,
            ),
        ]
        self._audit_goal_control(turn_id, "goal.create", goal_id, quote)
        return {
            "goal_id": goal_id,
            "milestone_ids": milestone_ids,
            "status": "ACTIVE",
            "autonomy_mode": self.agency.policy()["autonomy_mode"],
            "admission_turn_id": turn_id,
        }

    def goal_set_status(
        self,
        authorization_quote: str,
        goal_id: str,
        status: str,
    ) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        if not isinstance(goal_id, str) or not goal_id or len(goal_id) > 128:
            raise ValueError("invalid goal id")
        status = str(status).upper()
        if status not in {"ACTIVE", "PAUSED", "CANCELLED"}:
            raise ValueError("goal status must be ACTIVE, PAUSED or CANCELLED")
        self.agency.set_goal_status(self.user_id, goal_id, status)
        self._audit_goal_control(turn_id, "goal.status", goal_id, quote)
        return {"goal_id": goal_id, "status": status, "admission_turn_id": turn_id}

    def milestone_review(
        self,
        authorization_quote: str,
        milestone_id: str,
        decision: str,
        note: str = "",
    ) -> dict:
        turn_id, quote = self._active_user_authorization(authorization_quote)
        if not isinstance(milestone_id, str) or not milestone_id or len(milestone_id) > 128:
            raise ValueError("invalid milestone id")
        decision = str(decision).upper()
        if decision not in {"PASS", "REOPEN", "BLOCK"}:
            raise ValueError("milestone decision must be PASS, REOPEN or BLOCK")
        if not isinstance(note, str) or len(note) > 2000 or "\x00" in note:
            raise ValueError("invalid milestone review note")
        self.agency.review_milestone(milestone_id, self.user_id, decision, note)
        self._audit_goal_control(turn_id, "milestone.review", milestone_id, quote)
        return {
            "milestone_id": milestone_id,
            "decision": decision,
            "admission_turn_id": turn_id,
        }

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
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
            "turn_ingestion": "automatic_claude_hooks",
            "agency": {
                "autonomy_mode": self.agency.policy()["autonomy_mode"],
                "goal_count": len(self.agency.snapshot(user_id=self.user_id)["active_goals"]),
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
            "Operational effects use request_effect and EffectGate. Goal/control changes use the dedicated goal tools "
            "only when the active human prompt explicitly authorizes that change; pass an exact quote from that prompt."
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
        title: str,
        objective: str,
        success_criteria: str,
        priority: int = 0,
    ) -> dict:
        return bridge.goal_create(
            authorization_quote,
            title,
            objective,
            success_criteria,
            priority,
        )

    @mcp.tool(annotations=control)
    def goal_set_status(authorization_quote: str, goal_id: str, status: str) -> dict:
        return bridge.goal_set_status(authorization_quote, goal_id, status)

    @mcp.tool(annotations=control)
    def milestone_review(
        authorization_quote: str,
        milestone_id: str,
        decision: str,
        note: str = "",
    ) -> dict:
        return bridge.milestone_review(
            authorization_quote,
            milestone_id,
            decision,
            note,
        )

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
