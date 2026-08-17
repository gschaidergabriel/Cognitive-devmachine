from __future__ import annotations

import json
import os
import uuid
from pathlib import Path


class BridgeStateError(RuntimeError):
    pass


class ClayVerseBridge:
    """Stdio MCP bridge used by each permanent interactive Claude Code terminal."""

    def __init__(self, db, user_id: str, session_id: str, entityos_bridge=None):
        from .effects import EffectGate
        from .graph import ClayGraphProjection
        from .memory import MemoryManager
        from .retrieval import WorldAssembler
        from .workspace import Workspace

        if user_id not in {"gabriel", "andreas"} or session_id != f"session:{user_id}":
            raise PermissionError("invalid terminal/session binding")
        db.assert_session_owner(session_id, user_id)
        self.db = db
        self.user_id = user_id
        self.session_id = session_id
        self.memory = MemoryManager(db)
        self.world = WorldAssembler(db)
        self.workspace = Workspace(db)
        self.effects = EffectGate(db, allow_process=False, entityos_bridge=entityos_bridge)
        self.graph = ClayGraphProjection(db)
        self.current: dict | None = None

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(root / "unified.db")
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "")
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "")

        bridge = None
        path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
        sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
        if path or sha256:
            if not path or not sha256:
                raise BridgeStateError("incomplete EntityOS binding")
            bridge = EntityOSBridge(path=path, sha256=sha256)
            bridge.verify()
        return cls(db, user_id, session_id, bridge)

    def begin_turn(self, text: str, resources: list[str] | None = None) -> dict:
        if self.current is not None:
            raise BridgeStateError("turn already open")
        text = str(text)
        if not text or len(text) > 100_000:
            raise ValueError("invalid turn text")
        resources = sorted(set(resources or []))
        if any(not isinstance(x, str) or len(x) > 1000 for x in resources):
            raise ValueError("invalid resource reference")

        tid = self.db.append_turn(
            self.session_id, self.user_id, "user", text,
            resources=resources,
            provenance={"source": "permanent-claude-terminal", "user_id": self.user_id},
        )
        self.memory.extract_explicit(tid, self.user_id, text)
        self.memory.compact(self.session_id)
        world = self.world.assemble(self.session_id, resources)
        world["runtime_capabilities"] = list(self.effects.available_capabilities())
        ws = self.workspace.open(self.session_id, tid, text, resources)
        causal_id = str(uuid.uuid4())
        generation = self.db.session_generation(self.session_id)
        self.current = {
            "turn_id": tid,
            "episode_id": ws["episode_id"],
            "causal_id": causal_id,
            "generation": generation,
            "resources": resources,
            "effect_id": None,
            "outcome": None,
            "workspace_selected": False,
        }
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "turn_id": tid,
            "causal_id": causal_id,
            "generation": generation,
            "workspace": ws,
            "context": world,
        }

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        from .effects import EffectRequest

        if self.current is None:
            raise BridgeStateError("begin_turn required")
        if self.current["effect_id"] is not None:
            raise BridgeStateError("only one effect admitted per turn in candidate contract")
        if not self.current["workspace_selected"]:
            self.workspace.select(self.current["episode_id"], "request_effect")
            self.current["workspace_selected"] = True
        req = EffectRequest(
            self.user_id,
            self.session_id,
            capability,
            target,
            argv,
            self.current["generation"],
            {
                "source": "permanent-claude-terminal",
                "request_id": uuid.uuid4().hex,
                "causal_id": self.current["causal_id"],
                "episode_id": self.current["episode_id"],
                "observation_turn_id": self.current["turn_id"],
            },
        )
        effect_id, outcome = self.effects.execute(req, self.current["episode_id"])
        self.current["effect_id"] = effect_id
        self.current["outcome"] = outcome
        status = self.db.effect_status(effect_id)
        return {"effect_id": effect_id, "verified": status == "VERIFIED", "status": status, "outcome": outcome}

    def complete_turn(self, response: str) -> dict:
        if self.current is None:
            raise BridgeStateError("begin_turn required")
        response = str(response)
        if len(response) > 200_000:
            raise ValueError("response too large")
        if not self.current["workspace_selected"]:
            self.workspace.select(self.current["episode_id"], "respond")
            self.current["workspace_selected"] = True

        effect_id = self.current["effect_id"]
        outcome = self.current["outcome"]
        assistant_id = self.db.append_turn(
            self.session_id, self.user_id, "assistant", response,
            resources=self.current["resources"],
            causal_refs=[effect_id] if effect_id else [],
            provenance={"source": "permanent-claude-terminal", "causal_id": self.current["causal_id"]},
        )
        credit = 1.0 if isinstance(outcome, dict) and outcome.get("ok") is True else 0.0
        causal_id = self.db.record_causal_episode(
            self.current["episode_id"], effect_id, self.current["turn_id"], credit, self.current["causal_id"]
        )
        self.memory.compact(self.session_id)
        self.graph.rebuild()
        row = self.db.db.execute("SELECT reentered FROM causal_episodes WHERE causal_id=?", (causal_id,)).fetchone()
        result = {
            "assistant_turn_id": assistant_id,
            "causal_id": causal_id,
            "effect_id": effect_id,
            "credit": credit if row and int(row["reentered"]) == 1 else 0.0,
            "reentered": bool(row and int(row["reentered"]) == 1),
        }
        self.current = None
        return result


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseBridge.from_env()
    mcp = MCPServer(
        "ClayVerse",
        instructions="Canonical state/context/effect bridge for the authenticated permanent ClayVerse terminal.",
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    stateful = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=stateful)
    def begin_turn(text: str, resources: list[str] | None = None) -> dict:
        return bridge.begin_turn(text, resources)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=stateful)
    def complete_turn(response: str) -> dict:
        return bridge.complete_turn(response)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return {
            "user_id": bridge.user_id,
            "session_id": bridge.session_id,
            "generation": bridge.db.session_generation(bridge.session_id),
            "turn_open": bridge.current is not None,
        }

    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
