from __future__ import annotations
from dataclasses import dataclass
from .store import UnifiedDB,Lease,StaleGeneration
from .entityos_bridge import EntityOSBridge
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None; expected_generation:int|None=None
class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute("SELECT generation FROM sessions WHERE session_id=? AND user_id=?",(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is None: raise ValueError('expected_generation required')
        if req.expected_generation != generation: raise StaleGeneration(req.session_id)
        if lease: self.db.assert_lease(lease)
        if req.capability=='state.noop': outcome={'ok':True,'target':req.target,'boundary':'internal'}
        elif req.capability=='entityos.exec':
            if not self.entityos_bridge: raise PermissionError('EntityOS execution disabled or unpinned')
            outcome=dict(self.entityos_bridge.run(req.argv)); outcome['boundary']='EntityOS'; outcome['entityos_sha256']=self.entityos_bridge.sha256.lower()
        else:
            raise PermissionError('direct host process execution forbidden; no admitted generic EntityOS process contract')
        if lease: self.db.assert_lease(lease)
        eid=self.db.record_effect(episode_id,req.user_id,req.capability,req.target,req.expected_generation,'VERIFIED',req.argv,outcome); return eid,outcome
