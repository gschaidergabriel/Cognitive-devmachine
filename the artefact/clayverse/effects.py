from __future__ import annotations
import hashlib,json,os,subprocess
from pathlib import Path
from dataclasses import dataclass
from .store import UnifiedDB,Lease

@dataclass(frozen=True)
class EffectRequest:
    user_id:str; session_id:str; capability:str; target:str; argv:list[str]|None=None

class EntityOSBridgeError(RuntimeError): pass

class EntityOSProcessExecutor:
    """Fail-closed ClayVerse -> EntityOS process-effect bridge.

    This adapter may launch only the EntityOS executable. It never spawns the requested
    target itself and has no host-process fallback. The provisional stdio contract is
    deliberately versioned; until the selected EntityOS artifact implements it,
    process effects remain unavailable rather than bypassing EntityOS.
    """
    REQUEST_SCHEMA='ClayVerseEntityOSProcess/v1'
    OUTCOME_SCHEMA='ClayVerseEntityOSProcessOutcome/v1'
    COMMAND='clayverse-process-v1'
    def __init__(self,binary=None,timeout=15):
        self.binary=binary or os.environ.get('ENTITYOS_BIN','/opt/clayverse/EntityOS')
        self.timeout=float(timeout)
    def execute_process(self,req:EffectRequest,lease:Lease):
        path=Path(self.binary)
        if not path.is_file() or not os.access(path,os.X_OK):
            raise EntityOSBridgeError('EntityOS bridge unavailable; host fallback forbidden')
        payload={
            'schema':self.REQUEST_SCHEMA,
            'user_id':req.user_id,
            'session_id':req.session_id,
            'capability':req.capability,
            'target':req.target,
            'argv':list(req.argv or []),
            'resource':lease.resource,
            'generation':lease.generation,
            'lease_nonce':lease.nonce,
        }
        try:
            cp=subprocess.run(
                [str(path),self.COMMAND],
                input=json.dumps(payload,sort_keys=True,separators=(',',':')).encode(),
                shell=False,capture_output=True,timeout=self.timeout,check=False,
                env={'PATH':os.environ.get('PATH','/usr/bin:/bin')},
            )
        except (OSError,subprocess.TimeoutExpired) as exc:
            raise EntityOSBridgeError('EntityOS bridge launch failed') from exc
        if cp.returncode!=0:
            raise EntityOSBridgeError(f'EntityOS rejected effect rc={cp.returncode}')
        try: outcome=json.loads(cp.stdout)
        except json.JSONDecodeError as exc: raise EntityOSBridgeError('EntityOS returned non-JSON outcome') from exc
        if not isinstance(outcome,dict) or outcome.get('schema')!=self.OUTCOME_SCHEMA:
            raise EntityOSBridgeError('EntityOS outcome schema mismatch')
        if int(outcome.get('generation',-1))!=lease.generation or outcome.get('resource')!=lease.resource:
            raise EntityOSBridgeError('EntityOS outcome generation/resource mismatch')
        return outcome

class EffectGate:
    ALLOWED={'process.exec','state.noop'}
    SHELL_NAMES={'sh','bash','dash','zsh','fish','ksh','csh','tcsh'}
    def __init__(self,db:UnifiedDB,allow_process=False,entityos=None):
        self.db=db; self.allow_process=allow_process; self.entityos=entityos or EntityOSProcessExecutor()
    def execute(self,req:EffectRequest,episode_id=None,lease:Lease|None=None):
        if req.capability not in self.ALLOWED: raise PermissionError('capability denied')
        if req.capability=='state.noop':
            generation=self.db.session_generation(req.session_id); outcome={'ok':True,'target':req.target,'boundary':'internal'}
        else:
            if not self.allow_process: raise PermissionError('process execution disabled')
            if lease is None: raise PermissionError('process execution requires a fenced resource lease')
            self.db.assert_lease(lease)
            if lease.resource!=req.target: raise PermissionError('effect target must equal leased resource')
            if not req.argv or not isinstance(req.argv,list) or any(not isinstance(x,str) or '\x00' in x for x in req.argv): raise ValueError('explicit valid argv required')
            if Path(req.argv[0]).name in self.SHELL_NAMES: raise PermissionError('shell requires a separate explicit capability contract')
            generation=lease.generation
            try: outcome=self.entityos.execute_process(req,lease)
            except EntityOSBridgeError as exc: raise PermissionError(str(exc)) from exc
            if not isinstance(outcome,dict): raise RuntimeError('EntityOS outcome must be an object')
            outcome=dict(outcome)
            outcome.setdefault('ok',False)
            outcome['boundary']='EntityOS'
            outcome['outcome_sha256']=hashlib.sha256(json.dumps(outcome,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        eid=self.db.record_effect(episode_id,req.user_id,req.capability,req.target,generation,'VERIFIED',req.argv,outcome); return eid,outcome
