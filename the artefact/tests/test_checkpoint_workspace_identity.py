import json
import time

from clayverse.identity import IdentityRouter
from clayverse.store import UnifiedDB


def _seed_workspace(db: UnifiedDB) -> str:
    user_id, session_id = IdentityRouter(db, {"clerk-g": "gabriel"}).resolve("clerk-g")
    turn_id = db.append_turn(session_id, user_id, "user", "checkpoint workspace identity")
    episode_id = "episode-checkpoint-workspace"
    db.db.execute(
        "INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)",
        (
            episode_id,
            session_id,
            time.time(),
            turn_id,
            0.5,
            json.dumps(["answer", "request_effect"]),
            None,
            "OPEN",
        ),
    )
    return episode_id


def test_checkpoint_hash_binds_workspace_episode_state(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        episode_id = _seed_workspace(db)
        _, before = db.checkpoint("before-workspace-transition")
        db.db.execute(
            "UPDATE workspace_episodes SET selected='answer', state='SELECTED' WHERE episode_id=?",
            (episode_id,),
        )
        _, after = db.checkpoint("after-workspace-transition")
        assert before != after
    finally:
        db.close()


def test_checkpoint_hash_excludes_rebuildable_claygraph_projection(tmp_path):
    db = UnifiedDB(tmp_path / "unified.db")
    try:
        _seed_workspace(db)
        _, before = db.checkpoint("before-derived-graph-change")
        db.db.execute(
            "INSERT INTO graph_nodes(node_id,kind,label,source_table,source_id) VALUES(?,?,?,?,?)",
            ("derived-node", "derived", "projection-only", "turns", "synthetic-source"),
        )
        _, after = db.checkpoint("after-derived-graph-change")
        assert before == after
    finally:
        db.close()
