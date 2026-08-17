from __future__ import annotations

import os
from pathlib import Path


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP effect adapter over the same TurnLifecycle used by Claude hooks."""

    def __init__(self, db, user_id: str, session_id: str, entityos_bridge=None):
        from .turn_lifecycle import TurnLifecycle

        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise PermissionError("invalid terminal/session binding")
        db.assert_session_owner(session_id, user_id)
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.lifecycle = TurnLifecycle(db, user_id, session_id, entityos_bridge)

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

        bridge = None
        enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
        sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
        if enable_exec:
            if not path or not sha256 or not os.path.isabs(path):
                db.close()
                raise BridgeStateError("EntityOS execution enabled without complete digest binding")
            bridge = EntityOSBridge(path=path, sha256=sha256)
            bridge.verify()
        return cls(db, user_id, session_id, bridge)

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

        try:
            result = self.lifecycle.request_effect(capability, target, argv)
        except Exception as exc:
            from .turn_lifecycle import TurnLifecycleError
            if isinstance(exc, TurnLifecycleError):
                raise BridgeStateError(str(exc)) from exc
            raise
        result["boundary"] = "ClayVerse TurnLifecycle -> EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse TurnLifecycle -> EffectGate"
        return result

    def session_state(self) -> dict:
        active = self.lifecycle.active()
        active_episode = None
        if active is not None:
            ws = self.db.db.execute(
                "SELECT episode_id,state FROM workspace_episodes WHERE episode_id=?",
                (active["episode_id"],),
            ).fetchone()
            active_episode = dict(ws) if ws else None
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_episode": active_episode,
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
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
