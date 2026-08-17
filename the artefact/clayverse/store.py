from __future__ import annotations

import contextlib
import hashlib
import json
import sqlite3
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

SCHEMA = r'''
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS users(user_id TEXT PRIMARY KEY,display_name TEXT NOT NULL,rights TEXT NOT NULL DEFAULT 'equal',clerk_subject TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS sessions(session_id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(user_id),created_at REAL NOT NULL,updated_at REAL NOT NULL,generation INTEGER NOT NULL DEFAULT 1,terminal_name TEXT NOT NULL UNIQUE);
CREATE TABLE IF NOT EXISTS turns(turn_id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(session_id),user_id TEXT NOT NULL REFERENCES users(user_id),ordinal INTEGER NOT NULL,ts REAL NOT NULL,role TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),content TEXT NOT NULL,fidelity TEXT NOT NULL DEFAULT 'full',compression_generation INTEGER NOT NULL DEFAULT 0,resource_refs TEXT NOT NULL DEFAULT '[]',causal_refs TEXT NOT NULL DEFAULT '[]',provenance TEXT NOT NULL DEFAULT '{}',UNIQUE(session_id, ordinal));
CREATE INDEX IF NOT EXISTS idx_turns_session_ord ON turns(session_id, ordinal DESC);
CREATE TABLE IF NOT EXISTS durable_memory(memory_id TEXT PRIMARY KEY,kind TEXT NOT NULL,subject TEXT NOT NULL,value TEXT NOT NULL,source_turn_id TEXT REFERENCES turns(turn_id),user_id TEXT,ts REAL NOT NULL,provenance TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS workspace_episodes(episode_id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(session_id),ts REAL NOT NULL,observation_turn_id TEXT REFERENCES turns(turn_id),salience REAL NOT NULL,alternatives TEXT NOT NULL,selected TEXT,state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS effects(effect_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),user_id TEXT NOT NULL,capability TEXT NOT NULL,target TEXT NOT NULL,argv TEXT,requested_generation INTEGER NOT NULL,status TEXT NOT NULL,outcome TEXT,ts REAL NOT NULL,verified_at REAL,request_key TEXT,request_hash TEXT);
CREATE TABLE IF NOT EXISTS causal_episodes(causal_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),effect_id TEXT REFERENCES effects(effect_id),observation_turn_id TEXT REFERENCES turns(turn_id),outcome_hash TEXT,credit REAL NOT NULL DEFAULT 0,reentered INTEGER NOT NULL DEFAULT 0,ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS leases(resource TEXT PRIMARY KEY,holder TEXT NOT NULL,generation INTEGER NOT NULL,expires_at REAL NOT NULL,nonce TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY,ts REAL NOT NULL,state_hash TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_nodes(node_id TEXT PRIMARY KEY,kind TEXT NOT NULL,label TEXT NOT NULL,source_table TEXT NOT NULL,source_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_edges(edge_id TEXT PRIMARY KEY,src TEXT NOT NULL,dst TEXT NOT NULL,kind TEXT NOT NULL,provenance TEXT NOT NULL);
'''


@dataclass(frozen=True)
class Lease:
    resource: str
    holder: str
    generation: int
    expires_at: float
    nonce: str


class StaleGeneration(RuntimeError):
    pass


class LeaseConflict(RuntimeError):
    pass


class UnifiedDB:
    """Single canonical state authority. ClayGraph tables are rebuildable projections only."""

    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(
            self.path, timeout=30, isolation_level=None, check_same_thread=False
        )
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000")
        self.db.executescript(SCHEMA)
        self._migrate()

    def _migrate(self):
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(effects)")}
        if "request_key" not in columns:
            self.db.execute("ALTER TABLE effects ADD COLUMN request_key TEXT")
        if "request_hash" not in columns:
            self.db.execute("ALTER TABLE effects ADD COLUMN request_hash TEXT")
        self.db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_effects_request_key "
            "ON effects(request_key) WHERE request_key IS NOT NULL"
        )
        self.db.execute(
            "INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','2')"
        )

    def close(self):
        self.db.close()

    @contextlib.contextmanager
    def tx(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield self.db
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        else:
            self.db.execute("COMMIT")

    def ensure_user(self, user_id, display_name, clerk_subject=None):
        self.db.execute(
            "INSERT OR IGNORE INTO users(user_id,display_name,clerk_subject) VALUES(?,?,?)",
            (user_id, display_name, clerk_subject),
        )
        if clerk_subject:
            self.db.execute(
                "UPDATE users SET clerk_subject=? WHERE user_id=?",
                (clerk_subject, user_id),
            )

    def ensure_session(self, user_id, terminal_name):
        row = self.db.execute(
            "SELECT session_id FROM sessions WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            return row[0]
        sid = f"session:{user_id}"
        now = time.time()
        self.db.execute(
            "INSERT INTO sessions(session_id,user_id,created_at,updated_at,terminal_name) VALUES(?,?,?,?,?)",
            (sid, user_id, now, now, terminal_name),
        )
        return sid

    def session_generation(self, session_id):
        row = self.db.execute(
            "SELECT generation FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not row:
            raise KeyError(session_id)
        return int(row[0])

    def bump_generation(self, session_id):
        with self.tx() as db:
            db.execute(
                "UPDATE sessions SET generation=generation+1, updated_at=? WHERE session_id=?",
                (time.time(), session_id),
            )
            return int(
                db.execute(
                    "SELECT generation FROM sessions WHERE session_id=?", (session_id,)
                ).fetchone()[0]
            )

    def append_turn(
        self,
        session_id,
        user_id,
        role,
        content,
        *,
        resources=(),
        causal_refs=(),
        provenance=None,
    ):
        with self.tx() as db:
            ordinal = int(
                db.execute(
                    "SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",
                    (session_id,),
                ).fetchone()[0]
            )
            tid = str(uuid.uuid4())
            now = time.time()
            db.execute(
                "INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",
                (
                    tid,
                    session_id,
                    user_id,
                    ordinal,
                    now,
                    role,
                    content,
                    json.dumps(sorted(set(resources))),
                    json.dumps(list(causal_refs)),
                    json.dumps(provenance or {}, sort_keys=True),
                ),
            )
            db.execute(
                "UPDATE sessions SET updated_at=? WHERE session_id=?", (now, session_id)
            )
        return tid

    def recent_turns(self, session_id, limit=20):
        rows = self.db.execute(
            "SELECT * FROM turns WHERE session_id=? ORDER BY ordinal DESC LIMIT ?",
            (session_id, limit),
        ).fetchall()
        return list(reversed(rows))

    def all_turns(self, session_id):
        return self.db.execute(
            "SELECT * FROM turns WHERE session_id=? ORDER BY ordinal", (session_id,)
        ).fetchall()

    def add_memory(self, kind, subject, value, source_turn_id, user_id, provenance):
        mid = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",
            (
                mid,
                kind,
                subject,
                value,
                source_turn_id,
                user_id,
                time.time(),
                json.dumps(provenance, sort_keys=True),
            ),
        )
        return mid

    def memories(self):
        return self.db.execute("SELECT * FROM durable_memory ORDER BY ts").fetchall()

    def acquire_lease(self, resource, holder, ttl=30.0):
        now = time.time()
        nonce = uuid.uuid4().hex
        with self.tx() as db:
            row = db.execute(
                "SELECT * FROM leases WHERE resource=?", (resource,)
            ).fetchone()
            if row and float(row["expires_at"]) > now and row["holder"] != holder:
                raise LeaseConflict(resource)
            generation = (int(row["generation"]) + 1) if row else 1
            db.execute(
                "INSERT INTO leases(resource,holder,generation,expires_at,nonce) VALUES(?,?,?,?,?) "
                "ON CONFLICT(resource) DO UPDATE SET holder=excluded.holder,generation=excluded.generation,expires_at=excluded.expires_at,nonce=excluded.nonce",
                (resource, holder, generation, now + ttl, nonce),
            )
        return Lease(resource, holder, generation, now + ttl, nonce)

    def assert_lease(self, lease):
        row = self.db.execute(
            "SELECT * FROM leases WHERE resource=?", (lease.resource,)
        ).fetchone()
        if (
            not row
            or row["holder"] != lease.holder
            or int(row["generation"]) != lease.generation
            or row["nonce"] != lease.nonce
            or float(row["expires_at"]) <= time.time()
        ):
            raise StaleGeneration(lease.resource)

    def reserve_effect(
        self,
        *,
        request_key,
        request_hash,
        episode_id,
        user_id,
        capability,
        target,
        requested_generation,
        argv=None,
    ):
        if not request_key or not request_hash:
            raise ValueError("effect request identity required")
        with self.tx() as db:
            prior = db.execute(
                "SELECT * FROM effects WHERE request_key=?", (request_key,)
            ).fetchone()
            if prior is not None:
                return dict(prior), False
            eid = str(uuid.uuid4())
            db.execute(
                "INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at,request_key,request_hash) "
                "VALUES(?,?,?,?,?,?,?,?,NULL,?,NULL,?,?)",
                (
                    eid,
                    episode_id,
                    user_id,
                    capability,
                    target,
                    json.dumps(argv) if argv else None,
                    requested_generation,
                    "PENDING",
                    time.time(),
                    request_key,
                    request_hash,
                ),
            )
            return dict(
                db.execute("SELECT * FROM effects WHERE effect_id=?", (eid,)).fetchone()
            ), True

    def finalize_effect(self, effect_id, *, status, outcome):
        if status not in {"VERIFIED", "FAILED"}:
            raise ValueError("invalid terminal effect status")
        with self.tx() as db:
            row = db.execute(
                "SELECT status FROM effects WHERE effect_id=?", (effect_id,)
            ).fetchone()
            if row is None:
                raise KeyError(effect_id)
            if row["status"] != "PENDING":
                raise RuntimeError("EFFECT_RESERVATION_LOST")
            db.execute(
                "UPDATE effects SET status=?,outcome=?,verified_at=? WHERE effect_id=?",
                (
                    status,
                    json.dumps(outcome, sort_keys=True),
                    time.time() if status == "VERIFIED" else None,
                    effect_id,
                ),
            )

    def record_effect(
        self,
        episode_id,
        user_id,
        capability,
        target,
        requested_generation,
        status,
        argv=None,
        outcome=None,
    ):
        """Legacy non-idempotent writer retained for donor compatibility.

        Canonical EffectGate uses reserve_effect/finalize_effect instead.
        """
        request_key = f"legacy:{uuid.uuid4()}"
        payload = {
            "episode_id": episode_id,
            "user_id": user_id,
            "capability": capability,
            "target": target,
            "requested_generation": requested_generation,
            "argv": argv,
        }
        request_hash = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        row, _ = self.reserve_effect(
            request_key=request_key,
            request_hash=request_hash,
            episode_id=episode_id,
            user_id=user_id,
            capability=capability,
            target=target,
            requested_generation=requested_generation,
            argv=argv,
        )
        self.finalize_effect(row["effect_id"], status=status, outcome=outcome or {})
        return row["effect_id"]

    def checkpoint(self, note):
        payload = []
        for table in (
            "users",
            "sessions",
            "turns",
            "durable_memory",
            "effects",
            "causal_episodes",
            "leases",
        ):
            payload.append(
                (table, [dict(r) for r in self.db.execute(f"SELECT * FROM {table} ORDER BY 1")])
            )
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        cid = str(uuid.uuid4())
        self.db.execute(
            "INSERT INTO checkpoints VALUES(?,?,?,?)", (cid, time.time(), digest, note)
        )
        return cid, digest
