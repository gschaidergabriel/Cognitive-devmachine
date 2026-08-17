from __future__ import annotations
import hashlib,json
from dataclasses import dataclass
from .store import UnifiedDB,Lease,StaleGeneration
from .entityos_bridge import EntityOSBridge
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None; expected_generation:int|None=None; request_key:str|None=None
class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge
    def available_capabilities(self):
        capabilities={'state.noop'}
        if self.entityos_bridge is not None: capabilities.add('entityos.exec')
        return tuple(sorted(capabilities))
    @staticmethod
    def _request_hash(req,generation):
        payload={'user_id':req.user_id,'session_id':req.session_id,'capability':req.capability,'target':req.target,'argv':req.argv,'generation':generation}
        return hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute("SELECT generation FROM sessions WHERE session_id=? AND user_id=?",(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is not None and req.expected_generation != generation: raise StaleGeneration(req.session_id)
        if lease: self.db.assert_lease(lease)
        if req.capability=='process.exec': raise PermissionError('direct host process execution forbidden; no admitted generic EntityOS process contract')
        if not req.request_key: raise ValueError('effect request_key required')
        request_hash=self._request_hash(req,generation); reservation,created=self.db.reserve_effect_request(req.request_key,request_hash)
        if not created:
            if reservation['request_hash']!=request_hash: raise RuntimeError('EFFECT_REQUEST_CONFLICT')
            if reservation['status']=='PENDING': raise RuntimeError('EFFECT_RECOVERY_REQUIRED')
            if reservation['status']=='FAILED': raise RuntimeError('EFFECT_PREVIOUSLY_FAILED')
            if reservation['status'] not in {'VERIFIED','DENIED'}: raise RuntimeError('EFFECT_STATUS_INVALID')
            effect=self.db.db.execute("SELECT 1 FROM effects WHERE effect_id=?",(reservation['effect_id'],)).fetchone()
            if not effect: raise RuntimeError('EFFECT_RESERVATION_INCONSISTENT')
            return reservation['effect_id'],json.loads(reservation['outcome'] or '{}')
        status='VERIFIED'
        try:
            if req.capability=='state.noop': outcome={'ok':True,'target':req.target,'boundary':'internal'}
            elif not self.entityos_bridge:
                status='DENIED'; outcome={'ok':False,'denied':True,'reason':'entityos_unavailable','target':req.target,'boundary':'EntityOS'}
            else:
                outcome=dict(self.entityos_bridge.run(req.argv)); outcome['boundary']='EntityOS'; outcome['entityos_sha256']=self.entityos_bridge.sha256.lower()
        except Exception as exc:
            error={'ok':False,'error_type':type(exc).__name__,'error':str(exc)}; self.db.fail_reserved_effect(req.request_key,error); raise RuntimeError('EFFECT_EXECUTION_FAILED') from exc
        eid=self.db.complete_reserved_effect(req.request_key,episode_id,req.user_id,req.capability,req.target,generation,req.argv,outcome,status)
        if lease: self.db.assert_lease(lease)
        return eid,outcome
