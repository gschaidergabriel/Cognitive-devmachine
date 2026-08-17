from __future__ import annotations
import subprocess
from dataclasses import dataclass,field
from .store import UnifiedDB,Lease,StaleGeneration,IntegrityFailure
from .entityos_bridge import EntityOSBridge

@dataclass(frozen=True)
class EffectRequest:
    user_id:str
    session_id:str
    capability:str
    target:str
    argv:list[str]|None=None
    expected_generation:int|None=None
    provenance:dict=field(default_factory=dict)

class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge
    @staticmethod
    def _hex64(value): return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdef' for c in value.lower())
    def _verified_contract(self,req,outcome):
        if not isinstance(outcome,dict) or type(outcome.get('ok')) is not bool: return False
        if req.capability=='state.noop': return outcome.get('kind')=='noop' and outcome.get('target')==req.target and outcome.get('boundary')=='internal' and outcome['ok'] is True
        if req.capability!='entityos.exec' or outcome.get('boundary')!='EntityOS' or not self._hex64(outcome.get('entityos_sha256')): return False
        kind=outcome.get('kind','exit')
        if kind in {'timeout','integrity_error','execution_error'}: return outcome['ok'] is False and isinstance(outcome.get('error_class'),str) and bool(outcome['error_class'])
        if kind!='exit' or not isinstance(outcome.get('exit'),int): return False
        return self._hex64(outcome.get('stdout_sha256')) and self._hex64(outcome.get('stderr_sha256')) and isinstance(outcome.get('stdout'),str) and isinstance(outcome.get('stderr'),str) and outcome['ok']==(outcome['exit']==0)
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute("SELECT generation FROM sessions WHERE session_id=? AND user_id=?",(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is not None and req.expected_generation!=generation: raise StaleGeneration(req.session_id)
        if req.capability=='process.exec': raise PermissionError('direct host process execution forbidden; no admitted generic EntityOS process contract')
        if req.capability=='entityos.exec':
            if not self.entityos_bridge: raise PermissionError('EntityOS execution disabled or unpinned')
            if not req.argv or not isinstance(req.argv,list) or any(not isinstance(x,str) or '\x00' in x for x in req.argv): raise ValueError('explicit non-empty string argv required')
        if lease is None: raise PermissionError('effect lease required')
        if not isinstance(req.provenance,dict) or not req.provenance.get('source') or not req.provenance.get('request_id'): raise PermissionError('effect provenance required')
        self.db.assert_lease(lease)
        eid=self.db.prepare_effect(episode_id,req.user_id,req.session_id,req.capability,req.target,req.argv,generation,req.provenance,lease)
        if req.capability=='state.noop':
            outcome={'ok':True,'kind':'noop','target':req.target,'boundary':'internal'}; verifier='internal-noop-contract-v2'
        else:
            try:
                outcome=dict(self.entityos_bridge.run(req.argv)); outcome={'kind':'exit',**outcome,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
            except subprocess.TimeoutExpired as exc:
                outcome={'ok':False,'kind':'timeout','error_class':type(exc).__name__,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
            except Exception as exc:
                outcome={'ok':False,'kind':'integrity_error' if isinstance(exc,PermissionError) else 'execution_error','error_class':type(exc).__name__,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
            verifier='entityos-transport-contract-v2'
        self.db.record_effect_outcome(eid,outcome,lease); verified=self._verified_contract(req,outcome); self.db.verify_effect(eid,lease,verified=verified,verifier=verifier)
        if not verified: raise IntegrityFailure('effect outcome failed verification contract')
        return eid,outcome
