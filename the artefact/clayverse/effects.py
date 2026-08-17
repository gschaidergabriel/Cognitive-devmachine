from __future__ import annotations
import os,subprocess,hashlib
from pathlib import Path
from dataclasses import dataclass
from .store import UnifiedDB,Lease
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None
class EffectGate:
    ALLOWED={'process.exec','state.noop'}
    SHELL_NAMES={'sh','bash','dash','zsh','fish','ksh','csh','tcsh'}
    def __init__(self,db:UnifiedDB,allow_process=False): self.db=db; self.allow_process=allow_process
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        generation=self.db.session_generation(req.session_id)
        if lease: self.db.assert_lease(lease)
        if req.capability=='state.noop': outcome={'ok':True,'target':req.target}
        else:
            if not self.allow_process: raise PermissionError('process execution disabled')
            if not req.argv or not isinstance(req.argv,list) or any(not isinstance(x,str) or '\x00' in x for x in req.argv): raise ValueError('explicit valid argv required')
            executable=str(Path(req.argv[0]).resolve())
            if Path(executable).name in self.SHELL_NAMES: raise PermissionError('shell requires a separate explicit capability contract')
            cp=subprocess.run([executable,*req.argv[1:]],shell=False,capture_output=True,text=False,timeout=10,env={'PATH':os.environ.get('PATH','/usr/bin:/bin')}); outcome={'ok':cp.returncode==0,'exit':cp.returncode,'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(cp.stderr).hexdigest(),'stdout':cp.stdout[:4096].decode(errors='replace'),'stderr':cp.stderr[:4096].decode(errors='replace')}
        eid=self.db.record_effect(episode_id,req.user_id,req.capability,req.target,generation,'VERIFIED',req.argv,outcome); return eid,outcome
