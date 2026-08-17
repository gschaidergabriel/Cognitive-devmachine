from __future__ import annotations

import json
import os
from pathlib import Path


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP for effects only; turn state is automatic via Claude lifecycle hooks."""

    def __init__(self, db, user_id: str, session_id: str, entityos_bridge=None):
        from .effects import EffectGate
        from .workspace import Workspace

        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise PermissionError("invalid terminal/session binding")
        db.assert_session_owner(session_id, user_id)
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process=False, entityos_bridge=entityos_bridge)

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(root / "unified.db")
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()

        # Artifact presence/integrity and effect authority are distinct contracts.
        # Never infer execution permission merely because a path+digest are present.
        bridge = None
        enable_entityos = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        if enable_entityos:
            path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
            sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
            if not path or not sha256 or not os.path.isabs(path):
                db.close()
                raise BridgeStateError("EntityOS execution enabled but configuration is incomplete")
            bridge = EntityOSBridge(path=path, sha256=sha256)
            bridge.verify()
        return cls(db, user_id, session_id, bridge)

    def _active(self):
        row = self.db.db.execute(
            "SELECT w.*,t.provenance FROM workspace_episodes w "
            "JOIN turns t ON t.turn_id=w.observation_turn_id "
            "WHERE w.session_id=? AND w.state IN ('OPEN','SELECTED') ORDER BY w.ts DESC LIMIT 1",
            (self.session_id,),
        ).fetchone()
        if row is None:
            raise BridgeStateError("no active canonical turn; effect denied")
        try:
            provenance = json.loads(row["provenance"])
        except Exception as exc:
            raise BridgeStateError("active turn provenance is invalid") from exc
        generation = provenance.get("session_generation")
        if not isinstance(generation, int):
            raise BridgeStateError("active turn lacks reasoning-generation provenance")
        return row, generation

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        from .effects import EffectRequest

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

        active, generation = self._active()
        if active["state"] == "OPEN":
            self.workspace.select(active["episode_id"], "request_effect")
        req = EffectRequest(
            self.user_id,
            self.session_id,
            capability,
            target,
            argv,
            generation,
        )
        effect_id, outcome = self.effects.execute(req, active["episode_id"])
        return {
            "effect_id": effect_id,
            "causal_id": self.effects.causal_for_effect(effect_id),
            "verified": bool(isinstance(outcome, dict) and outcome.get("ok") is True),
            "outcome": outcome,
            "boundary": "ClayVerse EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse EffectGate",
        }

    def session_state(self) -> dict:
        active = self.db.db.execute(
            "SELECT episode_id,state FROM workspace_episodes WHERE session_id=? AND state IN ('OPEN','SELECTED') ORDER BY ts DESC LIMIT 1",
            (self.session_id,),
        ).fetchone()
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_episode": dict(active) if active else None,
            "capabilities": self.effects.available_capabilities(),
        }


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseEffectBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions=(
            "Turn ingestion, canonical context injection and completion persistence are automatic via Claude lifecycle hooks. "
            "Use request_effect only for a real external/state-changing action. Never bypass this tool with host execution."
        ),
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return bridge.session_state()

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
