from __future__ import annotations
import hashlib,json,uuid
from dataclasses import dataclass
from .store import UnifiedDB,Lease,StaleGeneration
from .entityos_bridge import EntityOSBridge
from .effect_journal import EffectJournal
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None; expected_generation:int|None=None; request_key:str|None=None
class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    AUTO_LEASE_TTL=300.0
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge; self.journal=EffectJournal(db)
    def available_capabilities(self):
        capabilities={'state.noop'}
        if self.entityos_bridge is not None: capabilities.add('entityos.exec')
        return tuple(sorted(capabilities))
    def causal_for_effect(self,effect_id): return self.journal.causal_for(effect_id)
    @staticmethod
    def _lease_resource(req:EffectRequest):
        payload=f'{req.capability}\0{req.target}'.encode('utf-8')
        return 'effect:'+hashlib.sha256(payload).hexdigest()
    @staticmethod
    def _request_hash(req:EffectRequest,generation:int):
        payload={'user_id':req.user_id,'session_id':req.session_id,'capability':req.capability,'target':req.target,'argv':req.argv,'generation':generation}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
    def _causal_request_key(self,episode_id):
        if not episode_id: return None
        row=self.db.db.execute('SELECT causal_id FROM active_turns WHERE episode_id=?',(episode_id,)).fetchone()
        return f"causal:{row['causal_id']}:effect:0" if row else None
    def _release_exact_lease(self,lease:Lease):
        with self.db.tx() as db:
            db.execute('DELETE FROM leases WHERE resource=? AND holder=? AND generation=? AND nonce=?',(lease.resource,lease.holder,lease.generation,lease.nonce))
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute("SELECT generation FROM sessions WHERE session_id=? AND user_id=?",(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is not None and req.expected_generation != generation: raise StaleGeneration(req.session_id)
        if lease: self.db.assert_lease(lease)
        if req.capability=='process.exec':
            raise PermissionError('direct host process execution forbidden; no admitted generic EntityOS process contract')
        request_key=req.request_key or self._causal_request_key(episode_id)
        auto_lease=False
        if req.capability=='entityos.exec' and lease is None:
            holder=f'{req.session_id}:{uuid.uuid4().hex}'
            lease=self.db.acquire_lease(self._lease_resource(req),holder,ttl=self.AUTO_LEASE_TTL)
            auto_lease=True
        try:
            if request_key is None:
                effect_id=self.journal.begin(episode_id,req.session_id,req.user_id,req.capability,req.target,generation,req.argv,lease=lease); replayed=None
            else:
                effect_id,replayed=self.journal.begin_once(episode_id,req.session_id,req.user_id,req.capability,req.target,generation,req.argv,request_key,self._request_hash(req,generation),lease=lease)
            if replayed is not None: return effect_id,replayed
            if req.capability=='state.noop':
                outcome={'ok':True,'target':req.target,'boundary':'internal'}
                self.journal.complete_verified(effect_id,outcome,req.session_id,req.user_id,generation,lease)
                return effect_id,outcome
            if not self.entityos_bridge:
                outcome={'ok':False,'denied':True,'reason':'entityos_unavailable','target':req.target,'boundary':'EntityOS'}
                self.journal.complete(effect_id,outcome,'DENIED')
                return effect_id,outcome
            try:
                outcome=dict(self.entityos_bridge.run(req.argv)); outcome['boundary']='EntityOS'; outcome['entityos_sha256']=self.entityos_bridge.sha256.lower()
            except Exception as exc:
                self.journal.complete(effect_id,{'ok':False,'error':type(exc).__name__,'boundary':'EntityOS'},'FAILED')
                raise
            self.journal.complete_verified(effect_id,outcome,req.session_id,req.user_id,generation,lease)
            return effect_id,outcome
        finally:
            if auto_lease and lease is not None:
                self._release_exact_lease(lease)
