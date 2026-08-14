from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
import hashlib, json

from .state_ledger import StateLedger, h

TOOL_ID='claude_code_peer'
AVAILABLE={'CAN_NOW','CAN_DELEGATE','DEGRADED'}

@dataclass(frozen=True)
class ClaudeCapability:
    responder_instance:str
    state:str
    capabilities:tuple[str,...]
    authority_scope:str='COGNITIVE_PEER_ONLY'
    privacy_scope:str='PROJECT_LOCAL'
    latency_class:str='UNKNOWN'
    cost_class:str='UNKNOWN'
    ttl_epochs:int=3
    provenance:str='sandbox_fixture'

@dataclass(frozen=True)
class ClaudeCodePeerRequest:
    request_id:str
    requester_instance:str
    goal:str
    task:str
    context_refs:tuple[str,...]
    required_capabilities:tuple[str,...]
    desired_outputs:tuple[str,...]
    write_scope:str
    execution_scope:str
    completion_test:str
    privacy_class:str
    budget:dict[str,Any]
    basis_epoch:int
    provenance:str

@dataclass(frozen=True)
class ClaudeCodePeerResult:
    request_id:str
    responder_instance:str
    status:str
    result_semantics:dict[str,Any]
    evidence_refs:tuple[str,...]
    artifact_refs:tuple[str,...]
    execution_receipts:tuple[dict[str,Any],...]
    unresolved:tuple[str,...]
    capability_observations:tuple[str,...]
    local_effects_claimed:tuple[str,...]
    basis_epoch:int
    provenance:str
    raw_prose:str=''

class PeerFabricError(ValueError): pass

class ClaudePeerFabric:
    def __init__(self,ledger:StateLedger):
        self.ledger=ledger; self.pending:dict[str,ClaudeCodePeerRequest]={}; self.seen_results:set[str]=set(); self.lesioned=False
    def _append(self,domain,key,value,event_type,epistemic='KNOWN'):
        base=self.ledger.epoch; eid=f'{event_type.lower()}-{base+1}-{hashlib.sha256((domain+key).encode()).hexdigest()[:8]}'
        return self.ledger.append_event(event_id=eid,idem=eid,base_epoch=base,event_type=event_type,writer='claude-peer-fabric',ops=[{'op':'SET','domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':'CURRENT'}],provenance={'tool':TOOL_ID},source={'kind':'typed_peer_fabric'},execution={})
    def observe(self,obs:ClaudeCapability):
        if obs.state not in {'CAN_NOW','CAN_DELEGATE','DEGRADED','UNAVAILABLE','STALE'}: raise PeerFabricError('bad capability state')
        base=self.ledger.epoch; value={**asdict(obs),'tool_id':TOOL_ID,'observed_epoch':base,'valid_through_epoch':base+1+max(0,obs.ttl_epochs)}
        self._append('capability',TOOL_ID,value,'CAPABILITY_OBSERVATION')
        return value
    def tool_view(self):
        if self.lesioned: return {'tool_id':TOOL_ID,'visible':False,'state':'LESIONED'}
        row=self.ledger.get('capability',TOOL_ID)
        if not row: return {'tool_id':TOOL_ID,'visible':False,'state':'UNKNOWN'}
        v=row['value']; fresh=self.ledger.epoch<=int(v['valid_through_epoch']); state=v['state']
        visible=fresh and state in AVAILABLE
        return {'tool_id':TOOL_ID,'visible':visible,'state':state if fresh else 'STALE','capabilities':v['capabilities'] if visible else [],'authority_scope':v['authority_scope'],'privacy_scope':v['privacy_scope'],'last_observed_epoch':v['observed_epoch']}
    def request(self,*,request_id:str,goal:str,task:str,required_capabilities=(),context_refs=(),desired_outputs=('semantic_delta',),write_scope='NONE',execution_scope='NONE',completion_test='structured_result',privacy_class='PROJECT_LOCAL',budget=None,requester_instance='FRANK_PC_4B'):
        view=self.tool_view()
        if not view['visible']: raise PeerFabricError(f'tool unavailable:{view["state"]}')
        missing=set(required_capabilities)-set(view['capabilities'])
        if missing: raise PeerFabricError('missing capabilities:'+','.join(sorted(missing)))
        if request_id in self.pending: raise PeerFabricError('duplicate request_id')
        req=ClaudeCodePeerRequest(request_id,requester_instance,goal,task,tuple(context_refs),tuple(required_capabilities),tuple(desired_outputs),write_scope,execution_scope,completion_test,privacy_class,budget or {'max_context_chars':4000},self.ledger.epoch,'frank-local-request')
        self.pending[request_id]=req; return req
    def result_fingerprint(self,r:ClaudeCodePeerResult):
        body=asdict(r); body.pop('raw_prose',None); return h(body)
    def _execution_evidence(self,r:ClaudeCodePeerResult):
        scoped=[]
        for rec in r.execution_receipts:
            if not isinstance(rec,dict): continue
            if rec.get('status')=='VERIFIED' and rec.get('effect_id') and rec.get('scope'):
                scoped.append({'effect_id':rec['effect_id'],'scope':rec['scope'],'receipt_hash':h(rec)})
        return scoped
    def accept(self,r:ClaudeCodePeerResult):
        fp=self.result_fingerprint(r)
        if fp in self.seen_results: return {'status':'DUPLICATE_IGNORED','result_hash':fp}
        req=self.pending.get(r.request_id)
        if not req: return {'status':'REJECTED_UNKNOWN_OR_OUT_OF_ORDER_REQUEST'}
        if r.basis_epoch!=req.basis_epoch or self.ledger.epoch!=req.basis_epoch:
            return {'status':'STALE_BASIS_REPLAN','request_basis':req.basis_epoch,'result_basis':r.basis_epoch,'current_epoch':self.ledger.epoch}
        execution=self._execution_evidence(r)
        effect_claims=list(r.local_effects_claimed)
        unsupported=[x for x in effect_claims if not any(e['effect_id']==x for e in execution)]
        semantics=dict(r.result_semantics)
        conflict=None
        claim_key=semantics.get('claim_key')
        if claim_key:
            local=self.ledger.get('semantic',str(claim_key))
            if local and local['status']=='CURRENT' and local['value']!=semantics.get('value'):
                conflict={'local':local['value'],'peer':semantics.get('value'),'claim_key':claim_key}
        persisted={
            'request_id':r.request_id,'responder_instance':r.responder_instance,'status':r.status,
            'result_semantics':semantics,'evidence_refs':list(r.evidence_refs),'artifact_refs':list(r.artifact_refs),
            'verified_execution_receipts':execution,'unsupported_local_effect_claims':unsupported,
            'unresolved':list(r.unresolved),'capability_observations':list(r.capability_observations),
            'basis_epoch':r.basis_epoch,'provenance':r.provenance,'result_hash':fp,
            'raw_prose_hash':hashlib.sha256(r.raw_prose.encode()).hexdigest() if r.raw_prose else None,
            'raw_prose_mirrored':False,'authority':'EVIDENCE_OR_PROPOSAL_ONLY'}
        if conflict: persisted['conflict']=conflict
        self._append('peer',f'{TOOL_ID}:{r.request_id}',persisted,'PEER_RESULT','CONFLICT' if conflict else 'KNOWN')
        self.seen_results.add(fp); self.pending.pop(r.request_id,None)
        return {'status':'ACCEPTED_CONFLICT' if conflict else 'ACCEPTED','result_hash':fp,'conflict':conflict,'verified_execution_receipts':execution,'unsupported_local_effect_claims':unsupported}
    def compact_backflow(self,request_id:str,max_chars=900):
        row=self.ledger.get('peer',f'{TOOL_ID}:{request_id}')
        if not row: raise PeerFabricError('missing accepted result')
        v=row['value']; compact={'peer':v['responder_instance'],'request_id':request_id,'status':v['status'],'semantics':v['result_semantics'],'evidence_refs':v['evidence_refs'][:4],'artifact_refs':v['artifact_refs'][:4],'conflict':v.get('conflict'),'authority':'NONE','detail_ref':f'peer:{TOOL_ID}:{request_id}'}
        raw=json.dumps(compact,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        if len(raw)>max_chars:
            compact['semantics']={'summary_hash':h(v['result_semantics']),'truncated':True}; raw=json.dumps(compact,ensure_ascii=False,sort_keys=True,separators=(',',':'))
        if len(raw)>max_chars: raise PeerFabricError('backflow budget exceeded')
        return compact
    def lesion(self): self.lesioned=True
    def rescue(self): self.lesioned=False
    def context_cost(self,r:ClaudeCodePeerResult,request_id:str):
        compact=json.dumps(self.compact_backflow(request_id),ensure_ascii=False,sort_keys=True)
        full=json.dumps(asdict(r),ensure_ascii=False,sort_keys=True)
        return {'compact_chars':len(compact),'full_chars':len(full),'saved_chars':max(0,len(full)-len(compact)),'compression_ratio':round(len(compact)/max(1,len(full)),4)}
