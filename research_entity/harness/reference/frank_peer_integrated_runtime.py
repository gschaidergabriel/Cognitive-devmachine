from __future__ import annotations
from typing import Any

from .frank_integrated_spine import FrankIntegratedSpine
from .claude_peer_fabric import ClaudeCapability, ClaudeCodePeerResult, ClaudePeerFabric

class FrankPeerIntegratedRuntime:
    """H1 wrapper proving typed Claude peer backflow enters the same UnifiedDB/GWT cycle."""
    def __init__(self,path=':memory:'):
        self.spine=FrankIntegratedSpine(path)
        self.peer=ClaudePeerFabric(self.spine.ledger)
    def close(self): self.spine.close()
    def cycle_with_peer(self,*,text:str,visual:dict[str,Any],base_options:list[dict[str,Any]],capability:ClaudeCapability,result_semantics:dict[str,Any],raw_prose:str='',mode='instruct'):
        self.peer.observe(capability)
        req=self.peer.request(request_id=f'peer-{self.spine.ledger.epoch}',goal='improve current task',task='independent peer analysis',required_capabilities=tuple(capability.capabilities[:1]),context_refs=(f'state:{self.spine.ledger.semantic_state_hash}',))
        result=ClaudeCodePeerResult(request_id=req.request_id,responder_instance=capability.responder_instance,status='COMPLETE',result_semantics=result_semantics,evidence_refs=('sandbox:peer-fixture',),artifact_refs=(),execution_receipts=(),unresolved=(),capability_observations=tuple(capability.capabilities),local_effects_claimed=(),basis_epoch=req.basis_epoch,provenance='claude-peer-sandbox-fixture',raw_prose=raw_prose)
        accepted=self.peer.accept(result)
        backflow=self.peer.compact_backflow(req.request_id)
        peer_option={'name':'peer_backflow','salience':.95,'peer_backflow':backflow}
        cycle=self.spine.cycle(text,visual,[peer_option]+list(base_options),mode=mode)
        selected=None
        if cycle['workspace']['selected'] is not None:
            selected=next((c for c in cycle['workspace']['candidates'] if c['id']==cycle['workspace']['selected']),None)
        metric=self.peer.context_cost(result,req.request_id)
        return {'peer_accept':accepted,'peer_backflow':backflow,'peer_context_metric':metric,'cycle':cycle,'peer_selected_by_workspace':bool(selected and selected['payload'].get('name')=='peer_backflow'),'same_unified_ledger':True}
