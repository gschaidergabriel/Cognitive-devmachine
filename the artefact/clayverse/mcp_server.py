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

    def _active(self):
        row = self.db.db.execute(
            "SELECT a.*, w.state AS workspace_state FROM active_turns a "
            "JOIN workspace_episodes w ON w.episode_id=a.episode_id "
            "WHERE a.session_id=? AND a.user_id=? LIMIT 1",
            (self.session_id, self.user_id),
        ).fetchone()
        if row is None:
            raise BridgeStateError("no active canonical turn; effect denied")
        try:
            generation = int(row["generation"])
        except (TypeError, ValueError) as exc:
            raise BridgeStateError("active turn generation is invalid") from exc
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
        if active["effect_id"] is not None:
            raise BridgeStateError("only one effect admitted per turn in candidate contract")
        prior = self.db.db.execute(
            "SELECT effect_id FROM effects WHERE episode_id=? ORDER BY ts,effect_id LIMIT 1",
            (active["episode_id"],),
        ).fetchone()
        if prior is not None:
            raise BridgeStateError("effect already persisted for active turn; automatic replay denied")
        if active["workspace_state"] == "OPEN":
            self.workspace.select(active["episode_id"], "request_effect")
        elif active["workspace_state"] != "SELECTED":
            raise BridgeStateError("active turn workspace is not effect-admissible")

        req = EffectRequest(
            self.user_id,
            self.session_id,
            capability,
            target,
            argv,
            generation,
        )
        effect_id, outcome = self.effects.execute(req, active["episode_id"])
        cur = self.db.db.execute(
            "UPDATE active_turns SET effect_id=?, outcome=?, workspace_selected=1 "
            "WHERE session_id=? AND causal_id=? AND effect_id IS NULL",
            (effect_id, json.dumps(outcome, sort_keys=True), self.session_id, active["causal_id"]),
        )
        if cur.rowcount != 1:
            raise BridgeStateError("effect persisted but active turn changed; recovery required")
        return {
            "effect_id": effect_id,
            "causal_id": active["causal_id"],
            "verified": bool(isinstance(outcome, dict) and outcome.get("ok") is True),
            "outcome": outcome,
            "boundary": "ClayVerse EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse EffectGate",
        }

    def session_state(self) -> dict:
        active = self.db.db.execute(
            "SELECT a.episode_id,a.causal_id,a.generation,a.effect_id,w.state "
            "FROM active_turns a JOIN workspace_episodes w ON w.episode_id=a.episode_id "
            "WHERE a.session_id=? AND a.user_id=? LIMIT 1",
            (self.session_id, self.user_id),
        ).fetchone()
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_turn": dict(active) if active else None,
            "capabilities": self.effects.available_capabilities(),
            "entityos_execution_enabled": self.effects.entityos_bridge is not None,
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
