import hashlib
import sqlite3
import time

import pytest

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import SCHEMA, StaleGeneration, UnifiedDB


def _open_episode(db, *, causal_id='causal:test'):
    db.ensure_user('gabriel', 'Gabriel')
    session_id = db.ensure_session('gabriel', 'gabriel-terminal')
    turn_id = db.append_turn(session_id, 'gabriel', 'user', 'alpha')
    episode_id = 'episode:test'
    db.db.execute(
        'INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES(?,?,?,?,?,?,?,?)',
        (episode_id, session_id, time.time(), turn_id, 1.0, '[]', None, '{}'),
    )
    return session_id, turn_id, episode_id, causal_id, db.entity_generation()


def test_replay_identity_binds_budget_and_limit(tmp_path):
    db = UnifiedDB(tmp_path / 'u.db')
    try:
        session_id, turn_id, episode_id, causal_id, generation = _open_episode(db)
        db.add_memory('fact', 'topic:alpha', 'alpha memory', None, 'gabriel', {'source': 'test'})
        organ = MicroClayRetrieval(db)
        first = organ.retrieve(
            query='alpha', user_id='gabriel', session_id=session_id,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
            generation=generation, limit=5, budget_chars=1024,
        )
        assert first['receipt']['status'] == 'PRESENT'
        row = db.db.execute('SELECT budget_chars,limit_count FROM retrieval_episodes WHERE causal_id=?', (causal_id,)).fetchone()
        assert (int(row['budget_chars']), int(row['limit_count'])) == (1024, 5)

        replay = organ.retrieve(
            query='alpha', user_id='gabriel', session_id=session_id,
            turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
            generation=generation, limit=5, budget_chars=1024,
        )
        assert replay['receipt']['replayed'] is True

        with pytest.raises(StaleGeneration, match='retrieval_identity'):
            organ.retrieve(
                query='alpha', user_id='gabriel', session_id=session_id,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation, limit=5, budget_chars=256,
            )
        with pytest.raises(StaleGeneration, match='retrieval_identity'):
            organ.retrieve(
                query='alpha', user_id='gabriel', session_id=session_id,
                turn_id=turn_id, episode_id=episode_id, causal_id=causal_id,
                generation=generation, limit=4, budget_chars=1024,
            )
    finally:
        db.close()


def test_schema_v6_receipt_migrates_fail_closed(tmp_path):
    path = tmp_path / 'legacy.db'
    old_schema = SCHEMA.replace(',limit_count INTEGER NOT NULL DEFAULT -1', '')
    conn = sqlite3.connect(path)
    conn.executescript(old_schema)
    now = time.time()
    conn.execute("INSERT INTO users(user_id,display_name) VALUES('gabriel','Gabriel')")
    conn.execute("INSERT INTO sessions(session_id,user_id,created_at,updated_at,generation,terminal_name) VALUES('session:gabriel','gabriel',?,?,1,'gabriel-terminal')", (now, now))
    conn.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content) VALUES('turn:old','session:gabriel','gabriel',1,?,'user','alpha')", (now,))
    conn.execute("INSERT INTO workspace_episodes(episode_id,session_id,ts,observation_turn_id,salience,alternatives,selected,state) VALUES('episode:old','session:gabriel',?,'turn:old',1.0,'[]',NULL,'{}')", (now,))
    conn.execute(
        "INSERT INTO retrieval_episodes(retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,shadow_memory_ids,entry_keys,budget_chars,chars_selected,status,ts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ('retrieval:old','turn:old','episode:old','causal:old','session:gabriel','gabriel',1,1,'SHADOW',hashlib.sha256(b'alpha').hexdigest(),'[]','[]','[]','[]',1024,0,'UNKNOWN',now),
    )
    conn.commit(); conn.close()

    db = UnifiedDB(path)
    try:
        columns = {row['name'] for row in db.db.execute('PRAGMA table_info(retrieval_episodes)').fetchall()}
        assert 'limit_count' in columns
        assert db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == '7'
        assert db.db.execute("SELECT limit_count FROM retrieval_episodes WHERE causal_id='causal:old'").fetchone()[0] == -1
        organ = MicroClayRetrieval(db)
        with pytest.raises(StaleGeneration, match='retrieval_identity'):
            organ.retrieve(
                query='alpha', user_id='gabriel', session_id='session:gabriel',
                turn_id='turn:old', episode_id='episode:old', causal_id='causal:old',
                generation=1, limit=5, budget_chars=1024,
            )
    finally:
        db.close()
