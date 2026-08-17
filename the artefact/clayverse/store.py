from __future__ import annotations

import contextlib
import hashlib
import hmac
import json
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from pathlib import Path

ZERO_HASH = "0" * 64

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
CREATE TABLE IF NOT EXISTS effects(effect_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),user_id TEXT NOT NULL,session_id TEXT,capability TEXT NOT NULL,target TEXT NOT NULL,argv TEXT,requested_generation INTEGER NOT NULL,status TEXT NOT NULL,outcome TEXT,ts REAL NOT NULL,verified_at REAL,request_id TEXT,request_hash TEXT,request_provenance TEXT,lease_resource TEXT,lease_generation INTEGER,lease_nonce TEXT,outcome_hash TEXT,verifier TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS idx_effects_request_id ON effects(request_id) WHERE request_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS causal_episodes(causal_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),effect_id TEXT REFERENCES effects(effect_id),observation_turn_id TEXT REFERENCES turns(turn_id),outcome_hash TEXT,credit REAL NOT NULL DEFAULT 0,reentered INTEGER NOT NULL DEFAULT 0,ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS leases(resource TEXT PRIMARY KEY,holder TEXT NOT NULL,generation INTEGER NOT NULL,expires_at REAL NOT NULL,nonce TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY,ts REAL NOT NULL,state_hash TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_nodes(node_id TEXT PRIMARY KEY,kind TEXT NOT NULL,label TEXT NOT NULL,source_table TEXT NOT NULL,source_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_edges(edge_id TEXT PRIMARY KEY,src TEXT NOT NULL,dst TEXT NOT NULL,kind TEXT NOT NULL,provenance TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS causal_events(seq INTEGER PRIMARY KEY AUTOINCREMENT,event_id TEXT NOT NULL UNIQUE,kind TEXT NOT NULL,entity_id TEXT NOT NULL,payload TEXT NOT NULL,prev_hash TEXT NOT NULL,event_hash TEXT NOT NULL UNIQUE,ts_ns INTEGER NOT NULL);
'''


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value):
    if isinstance(value, str):
        value = value.encode()
    return hashlib.sha256(value).hexdigest()


class _LockedCursor:
    def __init__(self, cursor: sqlite3.Cursor, lock: threading.RLock):
        self._cursor = cursor
        self._lock = lock
    def fetchone(self):
        with self._lock: return self._cursor.fetchone()
    def fetchall(self):
        with self._lock: return self._cursor.fetchall()
    def __iter__(self):
        with self._lock: return iter(self._cursor.fetchall())
    def __getattr__(self, name): return getattr(self._cursor, name)


class _LockedConnection:
    """Serialize access to the one in-process canonical SQLite connection."""
    def __init__(self, connection: sqlite3.Connection, lock: threading.RLock):
        self._connection = connection
        self._lock = lock
    def execute(self, *args, **kwargs):
        with self._lock: return _LockedCursor(self._connection.execute(*args, **kwargs), self._lock)
    def executescript(self, *args, **kwargs):
        with self._lock: return _LockedCursor(self._connection.executescript(*args, **kwargs), self._lock)
    def close(self):
        with self._lock: return self._connection.close()
    def __getattr__(self, name): return getattr(self._connection, name)


@dataclass(frozen=True)
class Lease:
    resource: str
    holder: str
    generation: int
    expires_at: float
    nonce: str


class StaleGeneration(RuntimeError): pass
class LeaseConflict(RuntimeError): pass
class IntegrityFailure(RuntimeError): pass
class ReplayDetected(PermissionError): pass


class UnifiedDB:
    """Single canonical state authority. ClayGraph is a rebuildable projection only."""
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True); self._lock=threading.RLock()
        raw=sqlite3.connect(self.path,timeout=30,isolation_level=None,check_same_thread=False); raw.row_factory=sqlite3.Row
        self.db=_LockedConnection(raw,self._lock); self.db.execute("PRAGMA busy_timeout=30000"); self.db.executescript(SCHEMA); self._migrate()
        self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','2')"); self.db.execute("INSERT OR IGNORE INTO meta(key,value) VALUES('causal_event_head',?)",(ZERO_HASH,)); self.integrity_check()
    def _migrate(self):
        existing={r[1] for r in self.db.execute("PRAGMA table_info(effects)").fetchall()}; added=False
        for name,typ in {'session_id':'TEXT','request_id':'TEXT','request_hash':'TEXT','request_provenance':'TEXT','lease_resource':'TEXT','lease_generation':'INTEGER','lease_nonce':'TEXT','outcome_hash':'TEXT','verifier':'TEXT'}.items():
            if name not in existing: self.db.execute(f"ALTER TABLE effects ADD COLUMN {name} {typ}"); added=True
        self.db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_effects_request_id ON effects(request_id) WHERE request_id IS NOT NULL")
        if added: self.db.execute("UPDATE effects SET status='LEGACY_UNVERIFIED',verified_at=NULL WHERE status='VERIFIED'")
        self.db.execute("UPDATE causal_episodes SET reentered=0,credit=0 WHERE effect_id IS NULL AND reentered<>0")
        self.db.execute("UPDATE causal_episodes SET reentered=0,credit=0 WHERE effect_id IN (SELECT effect_id FROM effects WHERE status<>'VERIFIED') AND reentered<>0")
    def close(self): self.db.close()
    @contextlib.contextmanager
    def tx(self):
        with self._lock:
            self.db.execute("BEGIN IMMEDIATE")
            try: yield self.db
            except Exception: self.db.execute("ROLLBACK"); raise
            else: self.db.execute("COMMIT")
    def ensure_user(self,user_id,display_name,clerk_subject=None):
        with self.tx() as db:
            db.execute("INSERT OR IGNORE INTO users(user_id,display_name,clerk_subject) VALUES(?,?,?)",(user_id,display_name,clerk_subject))
            if clerk_subject: db.execute("UPDATE users SET clerk_subject=? WHERE user_id=?",(clerk_subject,user_id))
    def ensure_session(self,user_id,terminal_name):
        sid=f"session:{user_id}"; now=time.time()
        with self.tx() as db:
            db.execute("INSERT OR IGNORE INTO sessions(session_id,user_id,created_at,updated_at,terminal_name) VALUES(?,?,?,?,?)",(sid,user_id,now,now,terminal_name)); row=db.execute("SELECT session_id FROM sessions WHERE user_id=?",(user_id,)).fetchone()
            if not row: raise KeyError(user_id)
            return row[0]
    def assert_session_owner(self,session_id,user_id):
        row=self.db.execute("SELECT user_id FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if not row: raise KeyError(session_id)
        if row[0]!=user_id: raise PermissionError('session/user identity mismatch')
        return True
    def session_generation(self,session_id):
        row=self.db.execute("SELECT generation FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if not row: raise KeyError(session_id)
        return int(row[0])
    def bump_generation(self,session_id):
        with self.tx() as db:
            row=db.execute("SELECT generation FROM sessions WHERE session_id=?",(session_id,)).fetchone()
            if not row: raise KeyError(session_id)
            db.execute("UPDATE sessions SET generation=generation+1,updated_at=? WHERE session_id=?",(time.time(),session_id)); return int(db.execute("SELECT generation FROM sessions WHERE session_id=?",(session_id,)).fetchone()[0])
    def append_turn(self,session_id,user_id,role,content,*,resources=(),causal_refs=(),provenance=None):
        if not isinstance(content,str): raise TypeError('turn content must be text')
        self.assert_session_owner(session_id,user_id)
        with self.tx() as db:
            ordinal=int(db.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",(session_id,)).fetchone()[0]); tid=str(uuid.uuid4()); now=time.time()
            db.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,session_id,user_id,ordinal,now,role,content,json.dumps(sorted(set(resources))),json.dumps(list(causal_refs)),json.dumps(provenance or {},sort_keys=True))); db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,session_id))
        return tid
    def recent_turns(self,session_id,limit=20):
        rows=self.db.execute("SELECT * FROM turns WHERE session_id=? ORDER BY ordinal DESC LIMIT ?",(session_id,max(1,min(int(limit),20)))).fetchall(); return list(reversed(rows))
    def all_turns(self,session_id): return self.db.execute("SELECT * FROM turns WHERE session_id=? ORDER BY ordinal",(session_id,)).fetchall()
    def add_memory(self,kind,subject,value,source_turn_id,user_id,provenance):
        mid=str(uuid.uuid4()); self.db.execute("INSERT INTO durable_memory VALUES(?,?,?,?,?,?,?,?)",(mid,kind,subject,value,source_turn_id,user_id,time.time(),json.dumps(provenance,sort_keys=True))); return mid
    def memories(self): return self.db.execute("SELECT * FROM durable_memory ORDER BY ts").fetchall()
    def acquire_lease(self,resource,holder,ttl=30.0):
        now=time.time(); nonce=uuid.uuid4().hex
        with self.tx() as db:
            row=db.execute("SELECT * FROM leases WHERE resource=?",(resource,)).fetchone()
            if row and float(row['expires_at'])>now and row['holder']!=holder: raise LeaseConflict(resource)
            generation=(int(row['generation'])+1) if row else 1
            db.execute("INSERT INTO leases(resource,holder,generation,expires_at,nonce) VALUES(?,?,?,?,?) ON CONFLICT(resource) DO UPDATE SET holder=excluded.holder,generation=excluded.generation,expires_at=excluded.expires_at,nonce=excluded.nonce",(resource,holder,generation,now+ttl,nonce))
        return Lease(resource,holder,generation,now+ttl,nonce)
    def assert_lease(self,lease):
        row=self.db.execute("SELECT * FROM leases WHERE resource=?",(lease.resource,)).fetchone()
        if not row or row['holder']!=lease.holder or int(row['generation'])!=lease.generation or row['nonce']!=lease.nonce or float(row['expires_at'])<=time.time(): raise StaleGeneration(lease.resource)
    def release_lease(self,lease):
        with self.tx() as db:
            self.assert_lease(lease); db.execute("UPDATE leases SET expires_at=0 WHERE resource=? AND holder=? AND generation=? AND nonce=?",(lease.resource,lease.holder,lease.generation,lease.nonce))
    def _causal_event(self,db,kind,entity_id,payload):
        head=db.execute("SELECT value FROM meta WHERE key='causal_event_head'").fetchone(); prev=head[0] if head else ZERO_HASH; event_id=str(uuid.uuid4()); ts_ns=time.time_ns(); payload_json=_canonical(payload)
        material=_canonical({'event_id':event_id,'kind':kind,'entity_id':entity_id,'payload':json.loads(payload_json),'prev_hash':prev,'ts_ns':ts_ns}); event_hash=_sha(material)
        db.execute("INSERT INTO causal_events(event_id,kind,entity_id,payload,prev_hash,event_hash,ts_ns) VALUES(?,?,?,?,?,?,?)",(event_id,kind,entity_id,payload_json,prev,event_hash,ts_ns)); db.execute("INSERT INTO meta(key,value) VALUES('causal_event_head',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",(event_hash,)); return event_id
    def prepare_effect(self,episode_id,user_id,session_id,capability,target,argv,generation,provenance,lease):
        if not isinstance(provenance,dict) or not provenance.get('source') or not provenance.get('request_id'): raise PermissionError('effect provenance requires source and request_id')
        request_id=str(provenance['request_id'])
        if not request_id or len(request_id)>200: raise PermissionError('invalid effect request_id')
        self.assert_session_owner(session_id,user_id); self.assert_lease(lease)
        if self.session_generation(session_id)!=int(generation): raise StaleGeneration(session_id)
        if episode_id:
            ws=self.db.execute("SELECT session_id FROM workspace_episodes WHERE episode_id=?",(episode_id,)).fetchone()
            if not ws or ws['session_id']!=session_id: raise PermissionError('workspace/session mismatch')
        request={'episode_id':episode_id,'user_id':user_id,'session_id':session_id,'capability':capability,'target':target,'argv':argv,'requested_generation':int(generation),'provenance':provenance,'lease':{'resource':lease.resource,'holder':lease.holder,'generation':lease.generation,'nonce':lease.nonce}}; request_hash=_sha(_canonical(request)); eid=str(uuid.uuid4())
        try:
            with self.tx() as db:
                db.execute("INSERT INTO effects(effect_id,episode_id,user_id,session_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at,request_id,request_hash,request_provenance,lease_resource,lease_generation,lease_nonce,outcome_hash,verifier) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,episode_id,user_id,session_id,capability,target,json.dumps(argv) if argv is not None else None,generation,'REQUESTED',None,time.time(),None,request_id,request_hash,_canonical(provenance),lease.resource,lease.generation,lease.nonce,None,None)); self._causal_event(db,'effect.requested',eid,{'request_id':request_id,'request_hash':request_hash,'generation':generation,'lease_resource':lease.resource,'lease_generation':lease.generation})
        except sqlite3.IntegrityError as exc: raise ReplayDetected('duplicate effect request_id') from exc
        return eid
    def _assert_effect_fence(self,effect,lease):
        self.assert_lease(lease)
        if effect['lease_resource']!=lease.resource or int(effect['lease_generation'])!=lease.generation or effect['lease_nonce']!=lease.nonce: raise StaleGeneration('effect lease mismatch')
        if self.session_generation(effect['session_id'])!=int(effect['requested_generation']): raise StaleGeneration(effect['session_id'])
    def record_effect_outcome(self,effect_id,outcome,lease):
        with self.tx() as db:
            effect=db.execute("SELECT * FROM effects WHERE effect_id=?",(effect_id,)).fetchone()
            if not effect or effect['status']!='REQUESTED': raise StaleGeneration('effect not in REQUESTED state')
            self._assert_effect_fence(effect,lease); outcome_json=_canonical(outcome); outcome_hash=_sha(outcome_json); db.execute("UPDATE effects SET outcome=?,outcome_hash=?,status='OBSERVED' WHERE effect_id=?",(outcome_json,outcome_hash,effect_id)); self._causal_event(db,'effect.outcome.observed',effect_id,{'outcome_hash':outcome_hash,'generation':effect['requested_generation']})
        return outcome_hash
    def verify_effect(self,effect_id,lease,*,verified,verifier):
        if type(verified) is not bool or not verifier: raise ValueError('explicit verified boolean and verifier required')
        with self.tx() as db:
            effect=db.execute("SELECT * FROM effects WHERE effect_id=?",(effect_id,)).fetchone()
            if not effect or effect['status']!='OBSERVED': raise StaleGeneration('effect not in OBSERVED state')
            self._assert_effect_fence(effect,lease); status='VERIFIED' if verified else 'REJECTED'; db.execute("UPDATE effects SET status=?,verified_at=?,verifier=? WHERE effect_id=?",(status,time.time(),verifier,effect_id)); self._causal_event(db,'effect.outcome.verified' if verified else 'effect.outcome.rejected',effect_id,{'outcome_hash':effect['outcome_hash'],'verifier':verifier,'verified':verified})
        return status
    def record_causal_reentry(self,episode_id,effect_id,observation_turn_id,credit=1.0):
        with self.tx() as db:
            effect=db.execute("SELECT * FROM effects WHERE effect_id=?",(effect_id,)).fetchone()
            if not effect or effect['status']!='VERIFIED' or not effect['outcome_hash']: raise IntegrityFailure('causal re-entry requires VERIFIED effect outcome')
            if effect['episode_id']!=episode_id: raise IntegrityFailure('causal re-entry episode mismatch')
            ws=db.execute("SELECT observation_turn_id FROM workspace_episodes WHERE episode_id=?",(episode_id,)).fetchone()
            if not ws or ws['observation_turn_id']!=observation_turn_id: raise IntegrityFailure('causal re-entry observation mismatch')
            causal_id=str(uuid.uuid4()); db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(causal_id,episode_id,effect_id,observation_turn_id,effect['outcome_hash'],float(credit),1,time.time())); self._causal_event(db,'causal.reentry',causal_id,{'effect_id':effect_id,'outcome_hash':effect['outcome_hash'],'credit':float(credit)})
        return causal_id
    def record_observation_episode(self,episode_id,observation_turn_id,effect_id=None):
        effect=self.db.execute("SELECT outcome_hash FROM effects WHERE effect_id=?",(effect_id,)).fetchone() if effect_id else None; cid=str(uuid.uuid4()); self.db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(cid,episode_id,effect_id,observation_turn_id,effect['outcome_hash'] if effect else None,0.0,0,time.time())); return cid
    def record_effect(self,episode_id,user_id,capability,target,requested_generation,status,argv=None,outcome=None):
        eid=str(uuid.uuid4()); self.db.execute("INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,episode_id,user_id,capability,target,json.dumps(argv) if argv else None,requested_generation,status,json.dumps(outcome,sort_keys=True) if outcome else None,time.time(),time.time() if outcome is not None else None)); return eid
    def checkpoint(self,note):
        with self._lock:
            payload=[]
            for table in ('users','sessions','turns','durable_memory','effects','causal_episodes','leases','causal_events'): payload.append((table,[dict(r) for r in self.db.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()]))
            digest=_sha(_canonical(payload)); cid=str(uuid.uuid4()); self.db.execute("INSERT INTO checkpoints VALUES(?,?,?,?)",(cid,time.time(),digest,note)); return cid,digest
    def integrity_check(self):
        with self._lock:
            result=self.db.execute("PRAGMA integrity_check").fetchone()[0]
            if result!='ok': raise IntegrityFailure(f'sqlite integrity_check: {result}')
            if self.db.execute("PRAGMA foreign_key_check").fetchall(): raise IntegrityFailure('foreign key check failed')
            expected=ZERO_HASH; count=0
            for row in self.db.execute("SELECT * FROM causal_events ORDER BY seq"):
                if row['prev_hash']!=expected: raise IntegrityFailure(f"causal event prev_hash mismatch: {row['seq']}")
                material=_canonical({'event_id':row['event_id'],'kind':row['kind'],'entity_id':row['entity_id'],'payload':json.loads(row['payload']),'prev_hash':row['prev_hash'],'ts_ns':row['ts_ns']}); actual=_sha(material)
                if not hmac.compare_digest(actual,row['event_hash']): raise IntegrityFailure(f"causal event hash mismatch: {row['seq']}")
                expected=actual; count+=1
            head=self.db.execute("SELECT value FROM meta WHERE key='causal_event_head'").fetchone()
            if not head or not hmac.compare_digest(head[0],expected): raise IntegrityFailure('causal event head mismatch')
            for row in self.db.execute("SELECT * FROM effects WHERE status IN ('OBSERVED','VERIFIED','REJECTED')"):
                if not row['outcome'] or not row['outcome_hash'] or not hmac.compare_digest(_sha(row['outcome']),row['outcome_hash']): raise IntegrityFailure(f"effect outcome integrity failed: {row['effect_id']}")
                if row['status']=='VERIFIED' and (not row['verified_at'] or not row['verifier']): raise IntegrityFailure(f"effect verification receipt missing: {row['effect_id']}")
            for row in self.db.execute("SELECT c.causal_id,c.outcome_hash,e.status,e.outcome_hash AS effect_hash FROM causal_episodes c JOIN effects e ON e.effect_id=c.effect_id WHERE c.reentered=1"):
                if row['status']!='VERIFIED' or not row['outcome_hash'] or row['outcome_hash']!=row['effect_hash']: raise IntegrityFailure(f"unverified causal re-entry: {row['causal_id']}")
            if self.db.execute("SELECT 1 FROM causal_episodes WHERE reentered=1 AND effect_id IS NULL LIMIT 1").fetchone(): raise IntegrityFailure('effectless causal re-entry')
            return {'ok':True,'causal_events':count,'causal_event_head':expected}
