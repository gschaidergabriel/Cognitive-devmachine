from __future__ import annotations
import contextlib, hashlib, json, sqlite3, time, uuid
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
CREATE TABLE IF NOT EXISTS effects(effect_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),user_id TEXT NOT NULL,session_id TEXT,capability TEXT NOT NULL,target TEXT NOT NULL,argv TEXT,requested_generation INTEGER NOT NULL,status TEXT NOT NULL,outcome TEXT,ts REAL NOT NULL,verified_at REAL,request_id TEXT,request_hash TEXT,request_provenance TEXT,lease_resource TEXT,lease_generation INTEGER,lease_nonce TEXT,outcome_hash TEXT,verifier TEXT);
CREATE UNIQUE INDEX IF NOT EXISTS idx_effects_request_id ON effects(request_id) WHERE request_id IS NOT NULL;
CREATE TABLE IF NOT EXISTS causal_episodes(causal_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),effect_id TEXT REFERENCES effects(effect_id),observation_turn_id TEXT REFERENCES turns(turn_id),outcome_hash TEXT,credit REAL NOT NULL DEFAULT 0,reentered INTEGER NOT NULL DEFAULT 0,ts REAL NOT NULL);
CREATE TABLE IF NOT EXISTS leases(resource TEXT PRIMARY KEY,holder TEXT NOT NULL,generation INTEGER NOT NULL,expires_at REAL NOT NULL,nonce TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints(checkpoint_id TEXT PRIMARY KEY,ts REAL NOT NULL,state_hash TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_nodes(node_id TEXT PRIMARY KEY,kind TEXT NOT NULL,label TEXT NOT NULL,source_table TEXT NOT NULL,source_id TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS graph_edges(edge_id TEXT PRIMARY KEY,src TEXT NOT NULL,dst TEXT NOT NULL,kind TEXT NOT NULL,provenance TEXT NOT NULL);
'''


def _canonical(value): return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False)
def _sha(value): return hashlib.sha256(value.encode() if isinstance(value,str) else value).hexdigest()

@dataclass(frozen=True)
class Lease:
    resource: str; holder: str; generation: int; expires_at: float; nonce: str
class StaleGeneration(RuntimeError): pass
class LeaseConflict(RuntimeError): pass
class IntegrityFailure(RuntimeError): pass
class ReplayDetected(PermissionError): pass

class UnifiedDB:
    """Single canonical state authority. ClayGraph tables are rebuildable projections only."""
    def __init__(self,path):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(self.path,timeout=30,isolation_level=None,check_same_thread=False); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA busy_timeout=30000"); self.db.executescript(SCHEMA); self._migrate(); self.db.execute("INSERT OR REPLACE INTO meta(key,value) VALUES('schema_version','2')"); self.verify_effect_integrity()
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
        self.db.execute("BEGIN IMMEDIATE")
        try: yield self.db
        except Exception: self.db.execute("ROLLBACK"); raise
        else: self.db.execute("COMMIT")
    def ensure_user(self,user_id,display_name,clerk_subject=None):
        self.db.execute("INSERT OR IGNORE INTO users(user_id,display_name,clerk_subject) VALUES(?,?,?)",(user_id,display_name,clerk_subject))
        if clerk_subject: self.db.execute("UPDATE users SET clerk_subject=? WHERE user_id=?",(clerk_subject,user_id))
    def ensure_session(self,user_id,terminal_name):
        row=self.db.execute("SELECT session_id FROM sessions WHERE user_id=?",(user_id,)).fetchone()
        if row: return row[0]
        sid=f"session:{user_id}"; now=time.time(); self.db.execute("INSERT INTO sessions(session_id,user_id,created_at,updated_at,terminal_name) VALUES(?,?,?,?,?)",(sid,user_id,now,now,terminal_name)); return sid
    def assert_session_owner(self,session_id,user_id):
        row=self.db.execute("SELECT user_id FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if not row: raise KeyError(session_id)
        if row[0] != user_id: raise PermissionError('session/user identity mismatch')
        return True
    def session_generation(self,session_id):
        row=self.db.execute("SELECT generation FROM sessions WHERE session_id=?",(session_id,)).fetchone()
        if not row: raise KeyError(session_id)
        return int(row[0])
    def bump_generation(self,session_id):
        with self.tx() as db:
            db.execute("UPDATE sessions SET generation=generation+1, updated_at=? WHERE session_id=?",(time.time(),session_id)); return int(db.execute("SELECT generation FROM sessions WHERE session_id=?",(session_id,)).fetchone()[0])
    def append_turn(self,session_id,user_id,role,content,*,resources=(),causal_refs=(),provenance=None):
        self.assert_session_owner(session_id,user_id)
        with self.tx() as db:
            ordinal=int(db.execute("SELECT COALESCE(MAX(ordinal),0)+1 FROM turns WHERE session_id=?",(session_id,)).fetchone()[0]); tid=str(uuid.uuid4()); now=time.time()
            db.execute("INSERT INTO turns(turn_id,session_id,user_id,ordinal,ts,role,content,resource_refs,causal_refs,provenance) VALUES(?,?,?,?,?,?,?,?,?,?)",(tid,session_id,user_id,ordinal,now,role,content,json.dumps(sorted(set(resources))),json.dumps(list(causal_refs)),json.dumps(provenance or {},sort_keys=True))); db.execute("UPDATE sessions SET updated_at=? WHERE session_id=?",(now,session_id))
        return tid
    def recent_turns(self,session_id,limit=20):
        rows=self.db.execute("SELECT * FROM turns WHERE session_id=? ORDER BY ordinal DESC LIMIT ?",(session_id,limit)).fetchall(); return list(reversed(rows))
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
    def _validate_effect_context(self,episode_id,user_id,session_id,generation):
        self.assert_session_owner(session_id,user_id)
        if self.session_generation(session_id)!=int(generation): raise StaleGeneration(session_id)
        if episode_id:
            row=self.db.execute("SELECT session_id FROM workspace_episodes WHERE episode_id=?",(episode_id,)).fetchone()
            if not row or row['session_id']!=session_id: raise PermissionError('workspace/session mismatch')
    @staticmethod
    def _require_provenance(provenance):
        if not isinstance(provenance,dict) or not provenance.get('source') or not provenance.get('request_id'): raise PermissionError('effect provenance requires source and request_id')
        request_id=str(provenance['request_id'])
        if not request_id or len(request_id)>200: raise PermissionError('invalid effect request_id')
        return request_id
    def prepare_effect(self,episode_id,user_id,session_id,capability,target,argv,generation,provenance,lease):
        request_id=self._require_provenance(provenance); self._validate_effect_context(episode_id,user_id,session_id,generation); self.assert_lease(lease)
        request={'episode_id':episode_id,'user_id':user_id,'session_id':session_id,'capability':capability,'target':target,'argv':argv,'requested_generation':int(generation),'provenance':provenance,'lease':{'resource':lease.resource,'holder':lease.holder,'generation':lease.generation,'nonce':lease.nonce}}
        eid=str(uuid.uuid4())
        try:
            self.db.execute("INSERT INTO effects(effect_id,episode_id,user_id,session_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at,request_id,request_hash,request_provenance,lease_resource,lease_generation,lease_nonce,outcome_hash,verifier) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,episode_id,user_id,session_id,capability,target,json.dumps(argv) if argv is not None else None,generation,'REQUESTED',None,time.time(),None,request_id,_sha(_canonical(request)),_canonical(provenance),lease.resource,lease.generation,lease.nonce,None,None))
        except sqlite3.IntegrityError as exc: raise ReplayDetected('duplicate effect request_id') from exc
        return eid
    def record_denied_effect(self,episode_id,user_id,session_id,capability,target,argv,generation,provenance,outcome):
        request_id=self._require_provenance(provenance); self._validate_effect_context(episode_id,user_id,session_id,generation); request={'episode_id':episode_id,'user_id':user_id,'session_id':session_id,'capability':capability,'target':target,'argv':argv,'requested_generation':int(generation),'provenance':provenance}; eid=str(uuid.uuid4()); outcome_json=_canonical(outcome)
        try:
            self.db.execute("INSERT INTO effects(effect_id,episode_id,user_id,session_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at,request_id,request_hash,request_provenance,lease_resource,lease_generation,lease_nonce,outcome_hash,verifier) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(eid,episode_id,user_id,session_id,capability,target,json.dumps(argv) if argv is not None else None,generation,'DENIED',outcome_json,time.time(),None,request_id,_sha(_canonical(request)),_canonical(provenance),None,None,None,_sha(outcome_json),None))
        except sqlite3.IntegrityError as exc: raise ReplayDetected('duplicate effect request_id') from exc
        return eid
    def _effect_fence(self,effect,lease):
        self.assert_lease(lease)
        if effect['lease_resource']!=lease.resource or int(effect['lease_generation'])!=lease.generation or effect['lease_nonce']!=lease.nonce: raise StaleGeneration('effect lease mismatch')
        if self.session_generation(effect['session_id'])!=int(effect['requested_generation']): raise StaleGeneration(effect['session_id'])
    def record_effect_outcome(self,effect_id,outcome,lease):
        effect=self.db.execute("SELECT * FROM effects WHERE effect_id=?",(effect_id,)).fetchone()
        if not effect or effect['status']!='REQUESTED': raise StaleGeneration('effect not in REQUESTED state')
        self._effect_fence(effect,lease); outcome_json=_canonical(outcome); outcome_hash=_sha(outcome_json); self.db.execute("UPDATE effects SET outcome=?,outcome_hash=?,status='OBSERVED' WHERE effect_id=?",(outcome_json,outcome_hash,effect_id)); return outcome_hash
    def verify_effect(self,effect_id,lease,*,verified,verifier):
        if type(verified) is not bool or not verifier: raise ValueError('explicit verified boolean and verifier required')
        effect=self.db.execute("SELECT * FROM effects WHERE effect_id=?",(effect_id,)).fetchone()
        if not effect or effect['status']!='OBSERVED': raise StaleGeneration('effect not in OBSERVED state')
        self._effect_fence(effect,lease); status='VERIFIED' if verified else 'REJECTED'; self.db.execute("UPDATE effects SET status=?,verified_at=?,verifier=? WHERE effect_id=?",(status,time.time(),verifier,effect_id)); return status
    def effect_status(self,effect_id):
        row=self.db.execute("SELECT status FROM effects WHERE effect_id=?",(effect_id,)).fetchone(); return row[0] if row else None
    def record_causal_episode(self,episode_id,effect_id,observation_turn_id,credit=0.0,causal_id=None):
        ws=self.db.execute("SELECT observation_turn_id FROM workspace_episodes WHERE episode_id=?",(episode_id,)).fetchone()
        if not ws or ws['observation_turn_id']!=observation_turn_id: raise IntegrityFailure('causal episode observation mismatch')
        out_hash=None; reentered=0; final_credit=0.0
        if effect_id:
            effect=self.db.execute("SELECT status,outcome,outcome_hash FROM effects WHERE effect_id=? AND episode_id=?",(effect_id,episode_id)).fetchone()
            if not effect: raise IntegrityFailure('causal episode effect mismatch')
            out_hash=effect['outcome_hash']
            if effect['status']=='VERIFIED':
                if not effect['outcome'] or not out_hash or _sha(effect['outcome'])!=out_hash: raise IntegrityFailure('verified effect outcome integrity failure')
                reentered=1; final_credit=float(credit)
        cid=causal_id or str(uuid.uuid4()); self.db.execute("INSERT INTO causal_episodes VALUES(?,?,?,?,?,?,?,?)",(cid,episode_id,effect_id,observation_turn_id,out_hash,final_credit,reentered,time.time())); return cid
    def record_effect(self,episode_id,user_id,capability,target,requested_generation,status,argv=None,outcome=None):
        safe_status='LEGACY_UNVERIFIED' if status=='VERIFIED' else status; eid=str(uuid.uuid4()); self.db.execute("INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)",(eid,episode_id,user_id,capability,target,json.dumps(argv) if argv else None,requested_generation,safe_status,json.dumps(outcome,sort_keys=True) if outcome else None,time.time(),None)); return eid
    def verify_effect_integrity(self):
        for row in self.db.execute("SELECT effect_id,outcome,outcome_hash,verified_at,verifier FROM effects WHERE status='VERIFIED'"):
            if not row['outcome'] or not row['outcome_hash'] or _sha(row['outcome'])!=row['outcome_hash'] or not row['verified_at'] or not row['verifier']: raise IntegrityFailure(f"verified effect integrity failure: {row['effect_id']}")
        if self.db.execute("SELECT 1 FROM causal_episodes WHERE reentered=1 AND effect_id IS NULL LIMIT 1").fetchone(): raise IntegrityFailure('effectless causal re-entry')
        for row in self.db.execute("SELECT c.causal_id,c.outcome_hash,e.status,e.outcome_hash AS effect_hash FROM causal_episodes c JOIN effects e ON e.effect_id=c.effect_id WHERE c.reentered=1"):
            if row['status']!='VERIFIED' or not row['outcome_hash'] or row['outcome_hash']!=row['effect_hash']: raise IntegrityFailure(f"unverified causal re-entry: {row['causal_id']}")
        return True
    def checkpoint(self,note):
        payload=[]
        for table in ("users","sessions","turns","durable_memory","effects","causal_episodes","leases"): payload.append((table,[dict(r) for r in self.db.execute(f"SELECT * FROM {table} ORDER BY 1")]))
        digest=hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest(); cid=str(uuid.uuid4()); self.db.execute("INSERT INTO checkpoints VALUES(?,?,?,?)",(cid,time.time(),digest,note)); return cid,digest
