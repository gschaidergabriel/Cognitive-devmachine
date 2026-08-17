from __future__ import annotations
import os,subprocess,hashlib
from dataclasses import dataclass
from .store import UnifiedDB,Lease,StaleGeneration
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None
class EffectGate:
    ALLOWED={'process.exec','state.noop'}
    def __init__(self,db:UnifiedDB,allow_process=False): self.db=db; self.allow_process=allow_process
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        if req.capability=='process.exec':
            if not self.allow_process: raise PermissionError('process execution disabled')
            if not req.argv or not isinstance(req.argv,list): raise ValueError('explicit argv required')
        generation=self.db.session_generation(req.session_id)
        if lease: self.db.assert_lease(lease)
        effect_id=self.db.begin_effect(episode_id,req.user_id,req.capability,req.target,generation,req.argv)
        try:
            if req.capability=='state.noop': outcome={'ok':True,'target':req.target}
            else:
                cp=subprocess.run(req.argv,shell=False,capture_output=True,text=False,timeout=10,env={'PATH':os.environ.get('PATH','/usr/bin:/bin')}); outcome={'ok':cp.returncode==0,'exit':cp.returncode,'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(cp.stderr).hexdigest(),'stdout':cp.stdout[:4096].decode(errors='replace'),'stderr':cp.stderr[:4096].decode(errors='replace')}
        except Exception as exc:
            self.db.complete_effect(effect_id,{'ok':False,'error':type(exc).__name__},status='FAILED')
            raise
        try:
            self.db.assert_user_generation(req.user_id,generation)
            if lease: self.db.assert_lease(lease)
        except StaleGeneration:
            self.db.complete_effect(effect_id,outcome,status='STALE_OUTCOME')
            raise
        self.db.complete_effect(effect_id,outcome,status='VERIFIED')
        return effect_id,outcome
