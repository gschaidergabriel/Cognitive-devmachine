from __future__ import annotations
import hashlib,json,time,uuid
from .store import UnifiedDB,StaleGeneration,Lease

class EffectJournal:
    """Transactional causal journal inside UnifiedDB; never a second state authority."""
    FINAL={'VERIFIED','DENIED','FAILED','STALE_OUTCOME','UNKNOWN_AFTER_RESTART'}
    SAFE_OUTCOME_FIELDS=('ok','exit','boundary','entityos_sha256','denied','reason','error','certainty')
    REUSABLE={'VERIFIED','DENIED'}
    AMBIGUOUS={'PENDING','FAILED','STALE_OUTCOME','UNKNOWN_AFTER_RESTART'}
    def __init__(self,db:UnifiedDB):
        self.db=db
        self.recover_pending()
    @staticmethod
    def _payload(outcome): return json.dumps(outcome,sort_keys=True,separators=(',',':'))
    @staticmethod
    def _credit(status,outcome): return 1.0 if status=='VERIFIED' and isinstance(outcome,dict) and outcome.get('ok') is True else 0.0
    @classmethod
    def _argv_receipt(cls,argv):
        if not argv: return None
        raw=json.dumps(argv,ensure_ascii=False,separators=(',',':')).encode()
        return {'audit':'redacted-argv-v1','argc':len(argv),'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    @classmethod
    def _outcome_receipt(cls,outcome):
        payload=cls._payload(outcome).encode()
        receipt={'audit':'redacted-outcome-v1','sha256':hashlib.sha256(payload).hexdigest(),'bytes':len(payload)}
        if isinstance(outcome,dict):
            for key in cls.SAFE_OUTCOME_FIELDS:
                if key in outcome and isinstance(outcome[key],(str,int,float,bool,type(None))): receipt[key]=outcome[key]
        return receipt
    @staticmethod
    def _decode_receipt(payload):
        try: value=json.loads(payload) if payload else {}
        except Exception: value={}
        if not isinstance(value,dict): value={}
        value=dict(value); value['replayed']=True
        return value
    @staticmethod
    def _assert_lease_tx(db,lease:Lease):
        lr=db.execute('SELECT holder,generation,expires_at,nonce FROM leases WHERE resource=?',(lease.resource,)).fetchone()
        if not lr or lr['holder']!=lease.holder or int(lr['generation'])!=lease.generation or lr['nonce']!=lease.nonce or float(lr['expires_at'])<=time.time():
            raise StaleGeneration(lease.resource)
    @classmethod
    def _check_identity_tx(cls,db,session_id,user_id,generation,lease):
        row=db.execute('SELECT generation FROM sessions WHERE session_id=? AND user_id=?',(session_id,user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        if int(row[0])!=int(generation): raise StaleGeneration(session_id)
        if lease is not None: cls._assert_lease_tx(db,lease)
    def _insert_pending_tx(self,db,eid,episode_id,user_id,capability,target,generation,argv,request_key=None,request_hash=None):
        audit_argv=self._argv_receipt(argv)
        db.execute("INSERT INTO effects(effect_id,episode_id,user_id,capability,target,argv,requested_generation,status,outcome,ts,verified_at,request_key,request_hash) VALUES(?,?,?,?,?,?,?,'PENDING',NULL,?,NULL,?,?)",(eid,episode_id,user_id,capability,target,json.dumps(audit_argv,sort_keys=True,separators=(',',':')) if audit_argv else None,generation,time.time(),request_key,request_hash))
    def begin(self,episode_id,session_id,user_id,capability,target,generation,argv=None,lease:Lease|None=None):
        eid=str(uuid.uuid4())
        with self.db.tx() as db:
            self._check_identity_tx(db,session_id,user_id,generation,lease)
            self._insert_pending_tx(db,eid,episode_id,user_id,capability,target,generation,argv)
        return eid
    def begin_once(self,episode_id,session_id,user_id,capability,target,generation,argv,request_key,request_hash,lease:Lease|None=None):
        if not isinstance(request_key,str) or not request_key or len(request_key)>512: raise ValueError('invalid effect request key')
        if not isinstance(request_hash,str) or len(request_hash)!=64: raise ValueError('invalid effect request hash')
        eid=str(uuid.uuid4())
        with self.db.tx() as db:
            self._check_identity_tx(db,session_id,user_id,generation,lease)
            prior=db.execute('SELECT effect_id,status,outcome,request_hash FROM effects WHERE request_key=?',(request_key,)).fetchone()
            if prior:
                if prior['request_hash']!=request_hash: raise RuntimeError('EFFECT_REQUEST_CONFLICT')
                status=prior['status']
                if status in self.REUSABLE: return prior['effect_id'],self._decode_receipt(prior['outcome'])
                if status in self.AMBIGUOUS: raise RuntimeError(f'EFFECT_REEXECUTION_BLOCKED:{status}')
                raise RuntimeError(f'EFFECT_STATUS_INVALID:{status}')
            self._insert_pending_tx(db,eid,episode_id,user_id,capability,target,generation,argv,request_key,request_hash)
        return eid,None
    def _reenter_tx(self,db,effect_id,status,outcome):
        row=db.execute('SELECT causal_id FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1',(effect_id,)).fetchone()
        if row: return row[0]
        effect=db.execute('SELECT episode_id FROM effects WHERE effect_id=?',(effect_id,)).fetchone()
        if not effect: raise KeyError(effect_id)
        episode_id=effect['episode_id']; observation_turn_id=None
        if episode_id:
            ws=db.execute('SELECT observation_turn_id FROM workspace_episodes WHERE episode_id=?',(episode_id,)).fetchone(); observation_turn_id=ws[0] if ws else None
        active=db.execute('SELECT causal_id FROM active_turns WHERE episode_id=?',(episode_id,)).fetchone() if episode_id else None
        cid=active['causal_id'] if active else str(uuid.uuid4())
        existing=db.execute('SELECT effect_id FROM causal_episodes WHERE causal_id=?',(cid,)).fetchone()
        if existing:
            raise RuntimeError('predeclared causal identity already consumed')
        payload=self._payload(outcome)
        db.execute('INSERT INTO causal_episodes(causal_id,episode_id,effect_id,observation_turn_id,outcome_hash,credit,reentered,ts) VALUES(?,?,?,?,?,?,1,?)',(cid,episode_id,effect_id,observation_turn_id,hashlib.sha256(payload.encode()).hexdigest(),self._credit(status,outcome),time.time()))
        return cid
    def _finish_tx(self,db,effect_id,outcome,status):
        row=db.execute('SELECT status FROM effects WHERE effect_id=?',(effect_id,)).fetchone()
        if not row: raise KeyError(effect_id)
        if row['status']!='PENDING': raise RuntimeError(f"effect is not pending: {row['status']}")
        audit_outcome=self._outcome_receipt(outcome)
        db.execute('UPDATE effects SET status=?,outcome=?,verified_at=? WHERE effect_id=?',(status,self._payload(audit_outcome),time.time(),effect_id))
        return self._reenter_tx(db,effect_id,status,outcome)
    def complete(self,effect_id,outcome,status):
        if status not in self.FINAL-{'VERIFIED'}: raise ValueError(status)
        with self.db.tx() as db: return self._finish_tx(db,effect_id,outcome,status)
    def complete_verified(self,effect_id,outcome,session_id,user_id,generation,lease:Lease|None=None):
        stale=None
        with self.db.tx() as db:
            row=db.execute('SELECT generation FROM sessions WHERE session_id=? AND user_id=?',(session_id,user_id)).fetchone()
            if not row: stale=PermissionError('session owner mismatch')
            elif int(row[0])!=int(generation): stale=StaleGeneration(session_id)
            if stale is None and lease is not None:
                try: self._assert_lease_tx(db,lease)
                except StaleGeneration as exc: stale=exc
            status='STALE_OUTCOME' if stale else 'VERIFIED'
            cid=self._finish_tx(db,effect_id,outcome,status)
        if stale: raise stale
        return cid
    def recover_pending(self):
        rows=self.db.db.execute("SELECT effect_id FROM effects WHERE status='PENDING' ORDER BY ts").fetchall()
        if not rows: return 0
        outcome={'ok':False,'certainty':'unknown','reason':'restart_before_verified_outcome'}
        with self.db.tx() as db:
            for row in rows:
                self._finish_tx(db,row['effect_id'],outcome,'UNKNOWN_AFTER_RESTART')
        return len(rows)
    def causal_for(self,effect_id):
        row=self.db.db.execute('SELECT causal_id FROM causal_episodes WHERE effect_id=? ORDER BY ts DESC LIMIT 1',(effect_id,)).fetchone(); return row[0] if row else None
