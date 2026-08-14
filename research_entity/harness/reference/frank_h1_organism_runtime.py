from __future__ import annotations
from typing import Any

from .frank_h1_pixel_runtime import FrankH1PixelRuntime
from .effect_gateway_runtime import SandboxEffectGateway, SandboxWriteProposal, InjectedCrash
from .unifieddb_query_plane import QuerySpec, SelectionPolicy
from .state_ledger import h

class FrankH1OrganismRuntime:
    """Single H1 reference organism surface over one ledger and one process.

    Pixel evidence, adaptive visual familiarity, optional independent peer evidence,
    workspace/model cognition, host-authorized physical sandbox effect and outcome
    re-entry are joined without granting semantic authority to model/familiarity/peer.
    """
    def __init__(self,effect_root:str,ledger_path=':memory:'):
        self.pixel=FrankH1PixelRuntime(ledger_path)
        self.effect_gateway=SandboxEffectGateway(self.pixel.ledger,effect_root)
    @property
    def ledger(self): return self.pixel.ledger
    def close(self): self.pixel.close()
    def learn_visual(self,*args,**kwargs): return self.pixel.learn(*args,**kwargs)

    def run(self,*,text:str,image,source_id:str,capture_epoch:int,options:list[dict[str,Any]],
            mode='instruct',context_prior=None,peer_capability=None,peer_semantics=None,
            effect_id:str|None=None,relative_path:str|None=None,content:str|None=None,crash_at=None):
        visual=self.pixel.run_image(text=text,image=image,source_id=source_id,capture_epoch=capture_epoch,
                                    options=options,mode=mode,context_prior=context_prior,
                                    peer_capability=peer_capability,peer_semantics=peer_semantics)
        effect=None; effect_reentry=None; crash_injected=False
        if effect_id is not None:
            if relative_path is None or content is None: raise ValueError('effect path/content required')
            proposal=SandboxWriteProposal(effect_id,relative_path,content,authority='NONE')
            permit=self.effect_gateway.issue_permit(proposal,max_bytes=max(1024,len(content.encode())+32))
            try:
                effect=self.effect_gateway.execute(proposal,permit,crash_at=crash_at)
            except InjectedCrash:
                crash_injected=True; effect=self.effect_gateway.recover_pending(effect_id)
            q=self.pixel.full.udb.query(QuerySpec(query_id=f'organism-effect-reentry-{self.ledger.epoch}',domains=('effect',),keys=(effect_id,),epistemic=('KNOWN','UNKNOWN','CONFLICT'),basis_epoch=self.ledger.epoch,limit=4,purpose='ORGANISM_EFFECT_OUTCOME_REENTRY'))
            effect_reentry=self.pixel.full.udb.select_for_assembly(q,SelectionPolicy(allow_epistemic=('KNOWN',),include_conflicts=True,max_items=4))
        cognitive=visual['full_runtime']['integration_audit']
        effect_ok=(effect is None) or (effect.get('status') in {'COMMITTED_VERIFIED','RECOVERED_COMMITTED_VERIFIED','ALREADY_COMMITTED'} and any(x['key']==effect_id for x in effect_reentry['selected']))
        audit={
            'pixel_path_pass':visual['pass'],
            'all_current_modules_exercised':cognitive['all_current_modules_exercised'],
            'historical_lineage_coverage_pass':cognitive['historical_lineage_coverage_pass'],
            'peer_authority':cognitive['peer_authority'],
            'model_authority':cognitive['model_authority'],
            'familiarity_authority':visual['familiarity'].authority,
            'percept_authority':visual['visual_percept']['authority'],
            'effect_requested':effect_id is not None,
            'effect_ok':effect_ok,
            'effect_authority':None if effect is None else effect.get('authority'),
            'static_claygraph_pass':cognitive['static_claygraph_pass'],
            'dynamic_claygraph_pass':cognitive['dynamic_claygraph_pass'],
        }
        audit['pass']=bool(visual['pass'] and effect_ok and cognitive['all_current_modules_exercised'] and cognitive['historical_lineage_coverage_pass'] and cognitive['model_authority']=='NONE' and cognitive['peer_authority'] in {None,'NONE'} and audit['familiarity_authority']=='FAMILIARITY_ROUTING_ONLY' and audit['percept_authority']=='OBSERVATION_ONLY')
        out={'visual':visual,'effect_outcome':effect,'effect_reentry':effect_reentry,'crash_injected':crash_injected,'organism_audit':audit,'semantic_state_hash':self.ledger.semantic_state_hash,'trace_root_hash':self.ledger.trace_root_hash}
        out['result_hash']=h({'audit':audit,'state':out['semantic_state_hash'],'trace':out['trace_root_hash'],'effect':effect})
        return out
    def recovery(self): return self.pixel.full.recovery()
