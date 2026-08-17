from __future__ import annotations
import os,subprocess,hashlib
from pathlib import Path
from dataclasses import dataclass
from .store import UnifiedDB,Lease,StaleGeneration
from .entityos_bridge import EntityOSBridge
from .effect_journal import EffectJournal
@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None; expected_generation:int|None=None
class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    SHELL_NAMES={'sh','bash','dash','zsh','fish','ksh','csh','tcsh'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None): self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge; self.journal=EffectJournal(db)
    def causal_for_effect(self,effect_id): return self.journal.causal_for(effect_id)
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute('SELECT generation FROM sessions WHERE session_id=? AND user_id=?',(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is not None and req.expected_generation != generation: raise StaleGeneration(req.session_id)
        if lease: self.db.assert_lease(lease)
        executable=None
        if req.capability=='entityos.exec':
            if not self.entityos_bridge: raise PermissionError('EntityOS execution disabled or unpinned')
        elif req.capability=='process.exec':
            if not self.allow_process: raise PermissionError('direct process execution disabled')
            if not req.argv or not isinstance(req.argv,list) or any(not isinstance(x,str) or '\x00' in x for x in req.argv): raise ValueError('explicit valid argv required')
            executable=str(Path(req.argv[0]).resolve())
            if Path(executable).name in self.SHELL_NAMES: raise PermissionError('shell requires a separate explicit capability contract')
        effect_id=self.journal.begin(episode_id,req.session_id,req.user_id,req.capability,req.target,generation,req.argv)
        try:
            if req.capability=='state.noop': outcome={'ok':True,'target':req.target}
            elif req.capability=='entityos.exec': outcome=self.entityos_bridge.run(req.argv)
            else:
                cp=subprocess.run([executable,*req.argv[1:]],shell=False,capture_output=True,text=False,timeout=10,env={'PATH':os.environ.get('PATH','/usr/bin:/bin')}); outcome={'ok':cp.returncode==0,'exit':cp.returncode,'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(cp.stderr).hexdigest(),'stdout':cp.stdout[:4096].decode(errors='replace'),'stderr':cp.stderr[:4096].decode(errors='replace')}
        except Exception as exc:
            self.journal.complete(effect_id,{'ok':False,'error':type(exc).__name__},'FAILED'); raise
        self.journal.complete_verified(effect_id,outcome,req.session_id,req.user_id,generation,lease)
        return effect_id,outcome
