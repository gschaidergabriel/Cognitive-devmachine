from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any
import hashlib, os, tempfile

from .state_ledger import StateLedger, h

class EffectDenied(RuntimeError): pass
class InjectedCrash(RuntimeError): pass

@dataclass(frozen=True)
class EffectPermit:
    permit_id: str
    capability: str
    scope_root: str
    basis_epoch: int
    proposal_hash: str
    max_bytes: int
    authority: str = 'HOST_CAPABILITY_PERMIT'

@dataclass(frozen=True)
class SandboxWriteProposal:
    effect_id: str
    relative_path: str
    content: str
    capability: str = 'sandbox.write_text'
    authority: str = 'NONE'

class SandboxEffectGateway:
    """Real H1 sandbox effect path with explicit authority and recovery receipts.

    Only writes under the configured root. The cognition proposal is inert until a
    host-created permit binds capability, root, epoch, proposal hash and size budget.
    """
    def __init__(self, ledger: StateLedger, root: str | os.PathLike[str]):
        self.ledger=ledger
        self.root=Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def proposal_hash(p: SandboxWriteProposal):
        return h(asdict(p))

    def issue_permit(self, proposal: SandboxWriteProposal, *, max_bytes=65536):
        # This method represents the host/policy side in H1, not model output.
        return EffectPermit(
            permit_id=f'permit:{proposal.effect_id}:{self.ledger.epoch}',
            capability=proposal.capability,
            scope_root=str(self.root),
            basis_epoch=self.ledger.epoch,
            proposal_hash=self.proposal_hash(proposal),
            max_bytes=max_bytes,
        )

    def _target(self, relative_path: str):
        p=(self.root/relative_path).resolve()
        try:
            p.relative_to(self.root)
        except ValueError as e:
            raise EffectDenied('scope escape') from e
        if p == self.root:
            raise EffectDenied('target must be a file')
        return p

    def _validate(self, proposal: SandboxWriteProposal, permit: EffectPermit|None):
        if proposal.authority not in {'NONE',None}:
            raise EffectDenied('model/proposal attempted to mint authority')
        if permit is None:
            raise EffectDenied('missing permit')
        if permit.authority!='HOST_CAPABILITY_PERMIT':
            raise EffectDenied('invalid permit authority class')
        if permit.basis_epoch!=self.ledger.epoch:
            raise EffectDenied('stale permit epoch')
        if permit.capability!=proposal.capability or permit.capability!='sandbox.write_text':
            raise EffectDenied('capability mismatch')
        if Path(permit.scope_root).resolve()!=self.root:
            raise EffectDenied('scope root mismatch')
        if permit.proposal_hash!=self.proposal_hash(proposal):
            raise EffectDenied('proposal binding mismatch')
        payload=proposal.content.encode('utf-8')
        if len(payload)>permit.max_bytes:
            raise EffectDenied('size budget exceeded')
        target=self._target(proposal.relative_path)
        return target,payload

    @staticmethod
    def _file_hash(path: Path):
        if not path.exists(): return None
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def _record(self, *, event_type: str, key: str, value: dict[str,Any]):
        base=self.ledger.epoch
        eid=f'{event_type.lower()}:{key}:{base+1}'
        return self.ledger.append_event(
            event_id=eid, idem=eid, base_epoch=base, event_type=event_type,
            writer='sandbox-effect-gateway',
            ops=[{'op':'SET','domain':'effect','key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'}],
            provenance={'component':'effect_gateway_runtime'}, source={'kind':'sandbox_filesystem'}, execution={}
        )

    def execute(self, proposal: SandboxWriteProposal, permit: EffectPermit|None, *, crash_at: str|None=None):
        target,payload=self._validate(proposal,permit)
        existing=self.ledger.get('effect',proposal.effect_id)
        if existing:
            ev=existing['value']; status=ev.get('status')
            if ev.get('proposal_hash') not in {None,self.proposal_hash(proposal)}:
                raise EffectDenied('effect_id reused with different proposal')
            if status in {'COMMITTED_VERIFIED','RECOVERED_COMMITTED_VERIFIED'}:
                return {**ev,'status':'ALREADY_COMMITTED','idempotent_replay':True}
            if status in {'INTENT_RECORDED','RECOVERY_CONFLICT'}:
                raise EffectDenied('effect has unresolved prior state')
        target.parent.mkdir(parents=True,exist_ok=True)
        normalized_rel=target.relative_to(self.root).as_posix()
        before_hash=self._file_hash(target)
        after_hash=hashlib.sha256(payload).hexdigest()
        intent={
            'effect_id':proposal.effect_id,'status':'INTENT_RECORDED','capability':proposal.capability,
            'relative_path':normalized_rel,'target_identity':f'sandbox:///{normalized_rel}','before_hash':before_hash,
            'after_hash':after_hash,'proposal_hash':self.proposal_hash(proposal),'permit_id':permit.permit_id,
            'intent_basis_epoch':permit.basis_epoch,'content_bytes':len(payload),'authority':'HOST_GATEWAY_ONLY'
        }
        self._record(event_type='EFFECT_INTENT',key=proposal.effect_id,value=intent)
        if crash_at=='after_intent':
            raise InjectedCrash('after_intent')

        fd,tmpname=tempfile.mkstemp(prefix='.frank-effect-',dir=str(target.parent))
        tmp=Path(tmpname)
        try:
            with os.fdopen(fd,'wb') as f:
                f.write(payload); f.flush(); os.fsync(f.fileno())
            if crash_at=='after_temp_fsync':
                raise InjectedCrash('after_temp_fsync')
            os.replace(tmp,target)
            # Best-effort directory durability for the sandbox reference surface.
            dfd=os.open(str(target.parent),os.O_RDONLY)
            try: os.fsync(dfd)
            finally: os.close(dfd)
            if crash_at=='after_replace':
                raise InjectedCrash('after_replace')
        finally:
            if tmp.exists():
                tmp.unlink()

        observed=self._file_hash(target)
        if observed!=after_hash:
            raise RuntimeError('post-effect verification mismatch')
        outcome={**intent,'status':'COMMITTED_VERIFIED','observed_hash':observed,'outcome_epoch_before_record':self.ledger.epoch}
        self._record(event_type='EFFECT_OUTCOME',key=proposal.effect_id,value=outcome)
        return outcome

    def recover_pending(self, effect_id: str):
        row=self.ledger.get('effect',effect_id)
        if not row:
            return {'status':'NO_EFFECT_RECORD'}
        v=row['value']
        if v.get('status')=='COMMITTED_VERIFIED':
            return {'status':'ALREADY_VERIFIED','effect_id':effect_id,'observed_hash':v.get('observed_hash')}
        if v.get('status')!='INTENT_RECORDED':
            return {'status':'UNRECOGNIZED_STATE','effect_id':effect_id}
        target=self._target(v['relative_path'])
        observed=self._file_hash(target)
        if observed==v['after_hash']:
            outcome={**v,'status':'RECOVERED_COMMITTED_VERIFIED','observed_hash':observed,'recovery_basis_epoch':self.ledger.epoch}
            self._record(event_type='EFFECT_RECOVERY',key=effect_id,value=outcome)
            return outcome
        if observed==v['before_hash'] or (observed is None and v['before_hash'] is None):
            outcome={**v,'status':'RECOVERED_NOT_APPLIED','observed_hash':observed,'recovery_basis_epoch':self.ledger.epoch}
            self._record(event_type='EFFECT_RECOVERY',key=effect_id,value=outcome)
            return outcome
        outcome={**v,'status':'RECOVERY_CONFLICT','observed_hash':observed,'recovery_basis_epoch':self.ledger.epoch}
        self._record(event_type='EFFECT_RECOVERY',key=effect_id,value=outcome)
        return outcome
