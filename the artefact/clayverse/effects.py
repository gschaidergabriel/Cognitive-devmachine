from __future__ import annotations
import subprocess, uuid
from dataclasses import dataclass,field
from .store import UnifiedDB,Lease,StaleGeneration,IntegrityFailure
from .entityos_bridge import EntityOSBridge

@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None; expected_generation:int|None=None; provenance:dict=field(default_factory=dict)

class EffectGate:
    ALLOWED={'entityos.exec','process.exec','state.noop'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos_bridge:EntityOSBridge|None=None):
        self.db=db; self.allow_process=allow_process; self.entityos_bridge=entityos_bridge
    def available_capabilities(self):
        capabilities={'state.noop'}
        if self.entityos_bridge is not None: capabilities.add('entityos.exec')
        return tuple(sorted(capabilities))
    @staticmethod
    def _hex64(value): return isinstance(value,str) and len(value)==64 and all(c in '0123456789abcdefABCDEF' for c in value)
    def _verified_contract(self,req,outcome):
        if not isinstance(outcome,dict) or type(outcome.get('ok')) is not bool: return False
        if req.capability=='state.noop': return outcome.get('kind')=='noop' and outcome.get('target')==req.target and outcome.get('boundary')=='internal' and outcome['ok'] is True
        if req.capability!='entityos.exec' or outcome.get('boundary')!='EntityOS' or not self._hex64(outcome.get('entityos_sha256')): return False
        if outcome.get('kind') in {'timeout','integrity_error','execution_error'}: return outcome['ok'] is False and isinstance(outcome.get('error_class'),str) and bool(outcome['error_class'])
        return outcome.get('kind')=='exit' and isinstance(outcome.get('exit'),int) and self._hex64(outcome.get('stdout_sha256')) and self._hex64(outcome.get('stderr_sha256')) and isinstance(outcome.get('stdout'),str) and isinstance(outcome.get('stderr'),str) and outcome['ok']==(outcome['exit']==0)
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        row=self.db.db.execute("SELECT generation FROM sessions WHERE session_id=? AND user_id=?",(req.session_id,req.user_id)).fetchone()
        if not row: raise PermissionError('session owner mismatch')
        generation=int(row[0])
        if req.expected_generation is not None and req.expected_generation!=generation: raise StaleGeneration(req.session_id)
        if req.capability=='process.exec': raise PermissionError('direct host process execution forbidden; no admitted generic EntityOS process contract')
        if not isinstance(req.provenance,dict) or not req.provenance.get('source') or not req.provenance.get('request_id'): raise PermissionError('effect provenance required')
        if req.capability=='entityos.exec' and self.entityos_bridge is None:
            outcome={'ok':False,'denied':True,'reason':'entityos_unavailable','target':req.target,'boundary':'EntityOS'}
            eid=self.db.record_denied_effect(episode_id,req.user_id,req.session_id,req.capability,req.target,req.argv,generation,req.provenance,outcome); return eid,outcome
        if req.capability=='entityos.exec' and (not isinstance(req.argv,list) or not req.argv or any(not isinstance(x,str) or '\x00' in x for x in req.argv)): raise ValueError('explicit non-empty string argv required')
        owned_lease=False
        if lease is None:
            lease=self.db.acquire_lease(f"effect:{req.capability}:{req.target}",f"{req.user_id}:{req.provenance['request_id']}",ttl=30.0); owned_lease=True
        try:
            eid=self.db.prepare_effect(episode_id,req.user_id,req.session_id,req.capability,req.target,req.argv,generation,req.provenance,lease)
            if req.capability=='state.noop':
                outcome={'ok':True,'kind':'noop','target':req.target,'boundary':'internal'}; verifier='internal-noop-contract-v2'
            else:
                try:
                    outcome={'kind':'exit',**dict(self.entityos_bridge.run(req.argv)),'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
                except subprocess.TimeoutExpired as exc:
                    outcome={'ok':False,'kind':'timeout','error_class':type(exc).__name__,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
                except PermissionError as exc:
                    outcome={'ok':False,'kind':'integrity_error','error_class':type(exc).__name__,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
                except OSError as exc:
                    outcome={'ok':False,'kind':'execution_error','error_class':type(exc).__name__,'boundary':'EntityOS','entityos_sha256':self.entityos_bridge.sha256.lower()}
                verifier='entityos-transport-contract-v2'
            self.db.record_effect_outcome(eid,outcome,lease); verified=self._verified_contract(req,outcome); self.db.verify_effect(eid,lease,verified=verified,verifier=verifier)
            if not verified: raise IntegrityFailure('effect outcome failed verification contract')
            return eid,outcome
        finally:
            if owned_lease:
                try: self.db.release_lease(lease)
                except StaleGeneration: pass
