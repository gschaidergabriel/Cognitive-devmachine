from __future__ import annotations

import hashlib
import json
import re
import time
import uuid

from .effects import EffectGate, EffectRequest
from .graph import ClayGraphProjection
from .memory import MemoryManager
from .retrieval import WorldAssembler
from .store import UnifiedDB
from .workspace import Workspace

_EXPLICIT_RESOURCE = re.compile(r"(?i)\b(repo|branch|deploy|machine|task|db|service|file|resource)\s*:\s*([^\s,;]+)")
_PATH = re.compile(r"(?<![\w.-])(?:\.?\.?/|/)?(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+")
_FILE = re.compile(r"(?<![\w.-])[A-Za-z0-9_.-]+\.(?:py|js|jsx|ts|tsx|json|jsonl|ya?ml|toml|md|sql|clay|service|timer|conf|cfg)(?![\w.-])", re.I)


class TurnLifecycleError(RuntimeError):
    pass


def infer_resource_refs(text: str) -> list[str]:
    """Conservative deterministic collision keys from a human prompt.

    This intentionally favors precision over pretending to understand every implicit
    project reference. Explicit typed labels are strongest; obvious paths/files are
    added as secondary keys. Semantic collision extraction remains an open quality gate.
    """
    refs: set[str] = set()
    for kind, value in _EXPLICIT_RESOURCE.findall(text):
        refs.add(f"{kind.lower()}:{value.strip()}")
    for value in _PATH.findall(text):
        refs.add(f"path:{value}")
    for value in _FILE.findall(text):
        refs.add(f"file:{value}")
    return sorted(refs)[:50]


class TurnLifecycle:
    """Deterministic per-turn lifecycle shared by Claude hooks and MCP effects."""

    def __init__(self, db: UnifiedDB, user_id: str, session_id: str, entityos_bridge=None):
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

    def active(self):
        return self.db.db.execute("SELECT * FROM active_turns WHERE session_id=?", (self.session_id,)).fetchone()

    @staticmethod
    def _bound_world(world: dict, max_chars: int = 350_000) -> dict:
        packed = {
            "own_recent": list(world.get("own_recent", [])),
            "cross_session_collision": list(world.get("cross_session_collision", [])),
            "durable_memory": list(world.get("durable_memory", [])),
        }
        def size():
            return len(json.dumps(packed, ensure_ascii=False, sort_keys=True, default=str))
        while size() > max_chars and packed["durable_memory"]:
            packed["durable_memory"].pop()
        while size() > max_chars and len(packed["own_recent"]) > 4:
            packed["own_recent"].pop(0)
        while size() > max_chars and packed["cross_session_collision"]:
            packed["cross_session_collision"].pop()
        if size() > max_chars:
            for item in packed["own_recent"]:
                if len(str(item.get("content", ""))) > 20_000:
                    item["content"] = str(item["content"])[:20_000] + "…[context-truncated]"
        return packed

    def begin(self, prompt: str, resources: list[str] | None = None) -> dict:
        prompt = str(prompt)
        if not prompt or len(prompt) > 100_000:
            raise ValueError("invalid prompt")
        if self.active() is not None:
            self.abort("previous_turn_interrupted_before_next_prompt")
        resource_refs = sorted(set(resources or infer_resource_refs(prompt)))[:50]
        now = time.time()
        turn_id = str(uuid.uuid4())
        episode_id = str(uuid.uuid4())
        causal_id = str(uuid.uuid4())
        generation = self.db.session_generation(self.session_id)
        salience = min(1.0, 0.15 + 0.03 * len(resource_refs) + min(len(prompt), 1200) / 2400)
        alternatives = [
            {"id": "respond", "kind": "reason"},
            {"id": "request_effect", "kind": "effect_intent"},
            {"id": "defer_effect", "kind": "no_effect"},
        ]
        with self.db.tx() as db:
            ordinal = int(db.execute(
                "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?", (self.session_id,)
            ).fetchone()[0])
            db.execute(
                "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (turn_id, self.session_id, self.user_id, ordinal, now, "user", prompt,
                 json.dumps(resource_refs), "[]", json.dumps({"source": "claude-hook:UserPromptSubmit"}, sort_keys=True)),
            )
            db.execute(
                "INSERT INTO workspace_episodes VALUES(?,?,?,?,?,?,?,?)",
                (episode_id, self.session_id, now, turn_id, salience, json.dumps(alternatives), None, "OPEN"),
            )
            db.execute(
                "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (self.session_id, self.user_id, turn_id, episode_id, causal_id, generation,
                 json.dumps(resource_refs), None, None, 0, now),
            )
            db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?", (now, self.session_id))
        self.memory.extract_explicit(turn_id, self.user_id, prompt)
        self.memory.compact(self.session_id)
        world = self._bound_world(self.world.assemble(self.session_id, resource_refs))
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": generation,
            "resources": resource_refs,
            "workspace": {"salience": salience, "alternatives": alternatives},
            "context": world,
        }

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        row = self.active()
        if row is None:
            raise TurnLifecycleError("no active turn; effect denied")
        if row["effect_id"] is not None:
            raise TurnLifecycleError("only one effect admitted per turn in candidate contract")
        if not int(row["workspace_selected"]):
            self.workspace.select(row["episode_id"], "request_effect")
        effect_id, outcome = self.effects.execute(
            EffectRequest(self.user_id, self.session_id, capability, target, argv, int(row["generation"])),
            row["episode_id"],
        )
        self.db.db.execute(
            "UPDATE active_turns SET effect_id=?, outcome=?, workspace_selected=1 WHERE session_id=? AND causal_id=?",
            (effect_id, json.dumps(outcome, sort_keys=True), self.session_id, row["causal_id"]),
        )
        return {"effect_id": effect_id, "verified": True, "outcome": outcome}

    def complete(self, response: str) -> dict:
        row = self.active()
        if row is None:
            return {"completed": False, "reason": "no_active_turn"}
        response = str(response)
        if len(response) > 200_000:
            raise ValueError("assistant response too large")
        if not int(row["workspace_selected"]):
            self.workspace.select(row["episode_id"], "respond")
        effect_id = row["effect_id"]
        outcome = json.loads(row["outcome"]) if row["outcome"] else None
        if effect_id and outcome is None:
            effect = self.db.db.execute("SELECT outcome FROM effects WHERE effect_id=?", (effect_id,)).fetchone()
            outcome = json.loads(effect["outcome"]) if effect and effect["outcome"] else None
        out_hash = hashlib.sha256(json.dumps(outcome, sort_keys=True).encode()).hexdigest() if outcome is not None else None
        credit = 1.0 if isinstance(outcome, dict) and outcome.get("ok") is True else 0.0
        now = time.time()
        assistant_id = str(uuid.uuid4())
        with self.db.tx() as db:
            ordinal = int(db.execute(
                "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?", (self.session_id,)
            ).fetchone()[0])
            db.execute(
                "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (assistant_id, self.session_id, self.user_id, ordinal, now, "assistant", response,
                 row["resource_refs"], json.dumps([effect_id] if effect_id else []),
                 json.dumps({"source": "claude-hook:Stop", "causal_id": row["causal_id"]}, sort_keys=True)),
            )
            db.execute(
                "INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
                (row["causal_id"], row["episode_id"], effect_id, row["turn_id"], out_hash, credit, 1, now),
            )
            db.execute("DELETE FROM active_turns WHERE session_id=? AND causal_id=?", (self.session_id, row["causal_id"]))
            db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?", (now, self.session_id))
        self.memory.compact(self.session_id)
        self.graph.rebuild()
        return {"completed": True, "assistant_turn_id": assistant_id, "causal_id": row["causal_id"], "effect_id": effect_id, "credit": credit}

    def abort(self, reason: str) -> dict:
        row = self.active()
        if row is None:
            return {"aborted": False, "reason": "no_active_turn"}
        try:
            ws = self.db.db.execute("SELECT state FROM workspace_episodes WHERE episode_id=?", (row["episode_id"],)).fetchone()
            if ws and ws["state"] == "OPEN":
                self.workspace.select(row["episode_id"], "defer_effect")
        except Exception:
            pass
        now = time.time()
        system_id = str(uuid.uuid4())
        with self.db.tx() as db:
            ordinal = int(db.execute(
                "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?", (self.session_id,)
            ).fetchone()[0])
            db.execute(
                "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (system_id, self.session_id, self.user_id, ordinal, now, "system", f"TURN_ABORTED:{reason}",
                 row["resource_refs"], json.dumps([row["effect_id"]] if row["effect_id"] else []),
                 json.dumps({"source": "claude-hook:failure"}, sort_keys=True)),
            )
            db.execute(
                "INSERT OR IGNORE INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",
                (row["causal_id"], row["episode_id"], row["effect_id"], row["turn_id"], None, 0.0, 1, now),
            )
            db.execute("DELETE FROM active_turns WHERE session_id=?", (self.session_id,))
        self.memory.compact(self.session_id)
        self.graph.rebuild()
        return {"aborted": True, "causal_id": row["causal_id"], "reason": reason}
