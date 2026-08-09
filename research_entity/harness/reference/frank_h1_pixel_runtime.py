from __future__ import annotations
from typing import Any

from .frank_h1_full_runtime import FrankH1FullRuntime
from .digital_retina_runtime import DigitalRetinaRuntime
from .unifieddb_query_plane import QuerySpec, SelectionPolicy
from .state_ledger import h

class FrankH1PixelRuntime:
    """Real pixel ingress -> dissolved Retina/MVC -> same FRANK H1 FullRuntime."""
    def __init__(self,path=':memory:'):
        self.full=FrankH1FullRuntime(path)
        self.retina=DigitalRetinaRuntime(self.full.spine.ledger)
    @property
    def ledger(self): return self.full.spine.ledger
    def close(self): self.full.close()

    def learn(self,label,image,*,source_id='screen',capture_epoch=1,tier='GOLD',evidence_ref='sandbox:label'):
        ev,metrics=self.retina.capture(image,source_id=source_id,capture_epoch=capture_epoch)
        trained=self.retina.admit_example(label,ev,tier=tier,evidence_ref=evidence_ref)
        return {'evidence':ev,'metrics':metrics,'training':trained}

    def run_image(self,*,text:str,image,source_id:str,capture_epoch:int,options:list[dict[str,Any]],mode='instruct',context_prior=None,peer_capability=None,peer_semantics=None):
        ev,metrics=self.retina.capture(image,source_id=source_id,capture_epoch=capture_epoch)
        fam=self.retina.classify(ev,context_prior=context_prior)
        percept=self.retina.materialize_visual_percept(ev,fam,context_prior=context_prior)
        base=self.ledger.epoch
        self.ledger.append_event(event_id=f'visual-percept:{ev.frame_hash[:12]}:{base+1}',idem=f'visual-percept:{ev.frame_hash[:12]}:{base+1}',base_epoch=base,event_type='VISUAL_PERCEPT_MATERIALIZATION',writer='frank-h1-pixel-runtime',ops=[{'op':'SET','domain':'visual_percept','key':f'{source_id}:{capture_epoch}','value':percept,'epistemic':percept['epistemic_state'],'status':'CURRENT'}],provenance={'frame_hash':ev.frame_hash,'feature_version':ev.feature_version},source={'kind':'pixel_frame','source_id':source_id},execution={})
        out=self.full.run(text=text,visual=self.retina.to_spine_visual(ev,fam),options=options,mode=mode,peer_capability=peer_capability,peer_semantics=peer_semantics)
        q=self.full.udb.query(QuerySpec(query_id=f'visual-reentry-{self.ledger.epoch}',domains=('visual_percept',),keys=(f'{source_id}:{capture_epoch}',),epistemic=('KNOWN','UNKNOWN','CONFLICT'),basis_epoch=self.ledger.epoch,limit=4,purpose='PIXEL_PERCEPT_AUDIT'))
        selected=self.full.udb.select_for_assembly(q,SelectionPolicy(allow_epistemic=('KNOWN','UNKNOWN'),include_conflicts=True,max_items=4))
        result={'pixel_evidence':ev,'familiarity':fam,'visual_percept':percept,'retina_metrics':metrics,'full_runtime':out,'visual_reentry':selected}
        result['pass']=bool(out['integration_audit']['pass'] and any(x['key']==f'{source_id}:{capture_epoch}' for x in selected['selected']) and fam.authority=='FAMILIARITY_ROUTING_ONLY' and percept['authority']=='OBSERVATION_ONLY')
        result['result_hash']=h({'frame_hash':ev.frame_hash,'familiarity':fam.__dict__,'full_state':out['semantic_state_hash'],'pass':result['pass']})
        return result
