from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

RESEARCH_ROOT = Path(os.environ["CLAY_RESEARCH_ROOT"]).resolve()
IMPL_ROOT = Path(os.environ["ENTITYOS_BOUND_IMPL_ROOT"]).resolve()
BINDING_PATH = RESEARCH_ROOT / "research_entity/continuity/ENTITYOS_EFFECT_AUTHORITY_IMPLEMENTATION_BINDING_V1.json"
ARTEFACT_ROOT = IMPL_ROOT / "the artefact"
sys.path.insert(0, str(ARTEFACT_ROOT))

from clayverse.effect_journal import EffectJournal
from clayverse.effects import EffectGate, EffectRequest
from clayverse.store import UnifiedDB


def git_blob_sha(path: Path) -> str:
    payload = path.read_bytes()
    return hashlib.sha1(f"blob {len(payload)}\0".encode("ascii") + payload).hexdigest()


class FakeEntityOSBridge:
    """In-process no-real-effect stand-in; observes canonical state at call boundary."""

    def __init__(self, db: UnifiedDB, episode_id: str) -> None:
        self.db = db
        self.episode_id = episode_id
        self.sha256 = "f" * 64
        self.calls: list[list[str] | None] = []
        self.pending_effect_ids_seen: list[str] = []

    def run(self, argv):
        self.calls.append(list(argv) if argv is not None else None)
        rows = self.db.db.execute(
            "SELECT effect_id,status FROM effects WHERE episode_id=? ORDER BY ts,effect_id",
            (self.episode_id,),
        ).fetchall()
        if len(rows) != 1 or rows[0]["status"] != "PENDING":
            raise AssertionError("EffectJournal PENDING must exist before EntityOSBridge.run")
        lease_rows = self.db.db.execute(
            "SELECT resource FROM leases WHERE resource=?",
            (EffectGate.ENTITYOS_EFFECT_RESOURCE,),
        ).fetchall()
        if len(lease_rows) != 1:
            raise AssertionError("canonical entityos.exec lease must be live during bridge.run")
        self.pending_effect_ids_seen.append(rows[0]["effect_id"])
        return {"ok": True, "exit": 0}


class BoundEffectTopologyExactSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.binding = json.loads(BINDING_PATH.read_text(encoding="utf-8"))

    def _fixture(self):
        td = tempfile.TemporaryDirectory()
        path = Path(td.name) / "unified.sqlite"
        db = UnifiedDB(path)
        user_id = "u:trigger4"
        db.ensure_user(user_id, "Trigger 4 Exact-Source Test")
        session_id = db.ensure_session(user_id, "trigger4-exact-source")
        generation = db.session_generation(session_id)
        turn_id = db.append_turn(
            session_id,
            user_id,
            "user",
            "deterministic no-real-effect topology discriminator",
        )
        episode_id = "episode:trigger4:bound-effect-topology"
        causal_id = "causal:trigger4:bound-effect-topology"
        now = time.time()
        db.db.execute(
            "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
            (episode_id, session_id, now, turn_id, 1.0, "[]", "request_effect", "SELECTED"),
        )
        db.db.execute(
            "INSERT INTO active_turns(session_id,user_id,turn_id,episode_id,causal_id,generation,resource_refs,effect_id,outcome,workspace_selected,started_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (session_id, user_id, turn_id, episode_id, causal_id, generation, "[]", None, None, 1, now),
        )
        return td, path, db, user_id, session_id, generation, episode_id

    def test_current_binding_pins_exact_loaded_bytes(self) -> None:
        self.assertEqual(
            self.binding["schema"],
            "ENTITYOS_EFFECT_AUTHORITY_IMPLEMENTATION_BINDING/v1",
        )
        self.assertEqual(
            self.binding["status"],
            "CURRENT_EXACT_SOURCE_IDENTITY_BINDING_NO_NEW_AUTHORITY",
        )
        identity = self.binding["implementation_identity"]
        self.assertEqual(
            identity["bound_commit"],
            "2b68aad14bf7824d513b52898904909256e3522d",
        )
        self.assertEqual(
            self.binding["api_contract"]["version"],
            "ENTITYOS_EFFECT_AUTHORITY_PY_API/v1",
        )
        for key in ("effect_gate", "effect_journal", "canonical_state_schema"):
            item = identity[key]
            self.assertEqual(
                git_blob_sha(IMPL_ROOT / item["path"]),
                item["blob_sha"],
                f"exact bound blob mismatch: {key}",
            )

    def test_effectgate_owns_pending_action_finalize_and_blocks_same_episode_replay(self) -> None:
        td, _path, db, user_id, session_id, generation, episode_id = self._fixture()
        self.addCleanup(td.cleanup)
        self.addCleanup(db.close)
        bridge = FakeEntityOSBridge(db, episode_id)
        gate = EffectGate(db, entityos_bridge=bridge)
        request = EffectRequest(
            user_id=user_id,
            session_id=session_id,
            capability="entityos.exec",
            target="fake://no-real-effect",
            argv=["noop"],
            expected_generation=generation,
        )

        effect_id, outcome = gate.execute(request, episode_id=episode_id)

        self.assertEqual(bridge.calls, [["noop"]])
        self.assertEqual(bridge.pending_effect_ids_seen, [effect_id])
        self.assertTrue(outcome["ok"])
        row = db.db.execute(
            "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
        ).fetchone()
        self.assertEqual(row["status"], "VERIFIED")
        lease_count = db.db.execute(
            "SELECT COUNT(*) FROM leases WHERE resource=?",
            (EffectGate.ENTITYOS_EFFECT_RESOURCE,),
        ).fetchone()[0]
        self.assertEqual(lease_count, 0)

        with self.assertRaisesRegex(
            RuntimeError,
            "effect already persisted|causal identity already consumed",
        ):
            gate.execute(request, episode_id=episode_id)
        self.assertEqual(bridge.calls, [["noop"]], "same episode must never dispatch twice")

    def test_restart_pending_becomes_unknown_and_never_blind_replays(self) -> None:
        td, path, db, user_id, session_id, generation, episode_id = self._fixture()
        self.addCleanup(td.cleanup)
        effect_id = EffectJournal(db).begin(
            episode_id,
            session_id,
            user_id,
            "entityos.exec",
            "fake://crash-before-action",
            generation,
            ["noop"],
        )
        db.close()

        reopened = UnifiedDB(path)
        self.addCleanup(reopened.close)
        self.assertEqual(EffectJournal(reopened).recover_pending(), 1)
        row = reopened.db.execute(
            "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
        ).fetchone()
        self.assertEqual(row["status"], "UNKNOWN_AFTER_RESTART")

        bridge = FakeEntityOSBridge(reopened, episode_id)
        gate = EffectGate(reopened, entityos_bridge=bridge)
        request = EffectRequest(
            user_id=user_id,
            session_id=session_id,
            capability="entityos.exec",
            target="fake://crash-before-action",
            argv=["noop"],
            expected_generation=generation,
        )
        with self.assertRaisesRegex(
            RuntimeError,
            "effect already persisted|causal identity already consumed",
        ):
            gate.execute(request, episode_id=episode_id)
        self.assertEqual(bridge.calls, [], "UNKNOWN_AFTER_RESTART must not auto-replay")


if __name__ == "__main__":
    unittest.main(verbosity=2)
