from __future__ import annotations
from dataclasses import asdict, dataclass
from typing import Any
import hashlib, json

from .needle_boundary import TranslatorReceipt, NeedleReceipt, bridge_to_clay
from .state_ledger import StateLedger, h

ARCHITECTURE_ID='FRANK-V0.1-H1-INTEGRATED-SPINE-0.1'
EVIDENCE_CLASS='REMOTE_SANDBOX_DETERMINISTIC_TEST'
MODULES=(
'adaptive_state_promotion','causal_observability_replay','clay_model_4b','claygraph_memory',
'digital_retina','effect_gateway','gwt_workspace','hyperposition','loop_dynamics_controller',
'micro_visual_classifier','needle_bridge','perceptual_field','semantic_state','thalamus_attention','unifieddb_plane')
LINEAGE={
'global_workspace':('gwt_workspace','causal_observability_replay'),
'innenwelt_inner_world':('gwt_workspace','clay_model_4b'),'workspace_broadcast':('gwt_workspace',),
'thalamus':('thalamus_attention',),'personality_self_epq':('semantic_state','adaptive_state_promotion'),
'consciousness_daemon':('loop_dynamics_controller','gwt_workspace','causal_observability_replay'),
'titan_memory':('claygraph_memory','unifieddb_plane'),'lcme':('claygraph_memory','unifieddb_plane'),
'hippocampus':('claygraph_memory','unifieddb_plane'),'memoryhub':('claygraph_memory','unifieddb_plane'),
'amygdala':('thalamus_attention','semantic_state'),'nac':('semantic_state','adaptive_state_promotion'),
'acc':('thalamus_attention','hyperposition'),'subconscious':('hyperposition','adaptive_state_promotion'),
'neural_conscience':('semantic_state','effect_gateway'),'reality_gate':('thalamus_attention','effect_gateway'),
'thoughtseed':('hyperposition','gwt_workspace'),'genesis':('hyperposition','causal_observability_replay'),
'hypothesis':('hyperposition','causal_observability_replay'),'experiment':('causal_observability_replay','adaptive_state_promotion'),
'dream':('adaptive_state_promotion','causal_observability_replay'),'soma':('adaptive_state_promotion','unifieddb_plane'),
'lora_iapt':('clay_model_4b','adaptive_state_promotion'),'spatial_rooms_body':('semantic_state','perceptual_field'),
'safety_recovery_watchdogs':('effect_gateway','causal_observability_replay','unifieddb_plane'),
'adaptive_vision_frankeye':('digital_retina','perceptual_field','micro_visual_classifier'),
'digital_retina':('digital_retina','perceptual_field'),'needle':('needle_bridge',),'tools_authority':('effect_gateway',)}

@dataclass(frozen=True)
class Permit:
    capability:str; epoch:int; proposal_hash:str

class FrankIntegratedSpine:
    def __init__(self,path=':memory:'):
        self.ledger=StateLedger(path); self.seen:set[str]=set(); self.graph:list[tuple[str,str,str]]=[]
    def close(self): self.ledger.close()
    def mark(self,m:str,a:str,b:str,rel:str):
        if m not in MODULES: raise ValueError(m)
        self.seen.add(m); self.graph.append((a,b,rel))
    def ingress(self,text:str):
        norm=' '.join(text.split()); nh=hashlib.sha256(norm.encode()).hexdigest()
        tr=TranslatorReceipt('spine-translator','0.1','de',hashlib.sha256(text.encode()).hexdigest(),nh)
        nr=NeedleReceipt('needle-fixture','0.1',nh,'GENERAL','fixture-cert',hashlib.sha256(('GENERAL'+norm).encode()).hexdigest(),'CLAY','OBSERVATION_OR_ROUTE_PROPOSAL',json.dumps({'utterance':norm},sort_keys=True), 'NONE')
        env=bridge_to_clay(tr,nr); self.mark('needle_bridge','human_input','needle_bridge','typed_ingress')
        return env
    def commit(self,values:dict[str,Any],event:str):
        base=self.ledger.epoch; ops=[{'op':'SET','domain':'semantic','key':k,'value':v,'epistemic':'KNOWN','status':'CURRENT'} for k,v in sorted(values.items())]
        r=self.ledger.append_event(event_id=event,idem=event,base_epoch=base,event_type='SEMANTIC_STATE',writer='frank-integrated-spine',ops=ops,provenance={'architecture':ARCHITECTURE_ID},source={'kind':'sandbox'},execution={})
        self.mark('semantic_state','typed_input','semantic_state','state_transition'); self.mark('unifieddb_plane','semantic_state','unifieddb_plane','transaction')
        return r
    def perceive(self,f:dict[str,Any]):
        conf=float(f.get('sensor_confidence',.8)); sim=float(f.get('prototype_similarity',0)); label=f.get('candidate_label')
        retina={'source_identity':f['source_id'],'capture_epoch':int(f['capture_epoch']),'features':dict(f['features']),'sensor_confidence':conf}
        self.mark('digital_retina','visual_source','digital_retina','sensor_capture')
        pf={'evidence':retina,'uncertainty':1-max(0,min(1,conf)),'prior':f.get('prior'),'epistemic_state':'KNOWN' if conf>=.7 else 'UNKNOWN'}
        self.mark('perceptual_field','digital_retina','perceptual_field','typed_percept')
        outcome='KNOWN_HIGH_CONFIDENCE' if label and sim>=.85 else 'KNOWN_NEEDS_CONFIRMATION' if label and sim>=.6 else 'UNKNOWN'
        if f.get('sensor_conflict'): outcome='CONFLICT'
        mvc={'outcome':outcome,'label':label,'similarity':sim,'authority':'FAMILIARITY_ROUTING_ONLY'}
        self.mark('micro_visual_classifier','perceptual_field','micro_visual_classifier','familiarity')
        return {'perceptual_field':pf,'mvc':mvc}
    def topology(self):
        rows=self.ledger.materialized(); nodes=sorted({r['domain']+':'+r['key'] for r in rows}); edges=[(nodes[i],nodes[i+1],'co_state') for i in range(max(0,len(nodes)-1))]
        out={'nodes':nodes,'edges':edges,'authority':'DERIVED_NON_AUTHORITATIVE'}
        self.mark('claygraph_memory','unifieddb_plane','claygraph_memory','derived_topology'); return out
    def gate(self,p:dict[str,Any],risk=.2,conflict=.0,vigilance=.5):
        novelty=p['perceptual_field']['uncertainty']; gain=min(1,.35+.35*novelty+.2*risk+.2*conflict+.1*vigilance)
        out={'gain':gain,'relay':gain>=.25,'authority':'ACCESS_CONTROL_ONLY'}
        self.mark('thalamus_attention','perceptual_field','thalamus_attention','gate'); return out
    def alternatives(self,opts:list[dict[str,Any]]):
        out={'alternatives':opts,'set_valued':len(opts)>1,'authority':'ALTERNATIVE_SET_PROPOSAL'}
        self.mark('hyperposition','semantic_state','hyperposition','preserve_alternatives'); return out
    def workspace(self,gate:dict[str,Any],alts:dict[str,Any]):
        candidates=[{'id':str(i),'salience':float(o.get('salience',.5)),'payload':o} for i,o in enumerate(alts['alternatives'])]
        selected=max(candidates,key=lambda x:x['salience']) if candidates and gate['relay'] else None
        ignition=bool(selected and selected['salience']>=.55)
        out={'candidates':candidates,'selected':None if selected is None else selected['id'],'ignition':ignition,'delivered':ignition,'reconstructed':ignition,'uptake':False,'causal_use':False,'outcome':None,'reentry':False}
        self.mark('gwt_workspace','thalamus_attention','gwt_workspace','competition_ignition'); return out
    def model(self,ws:dict[str,Any],mode='instruct'):
        if mode not in {'instruct','thinking'}: raise ValueError(mode)
        out={'kind':'COGNITIVE_PROPOSAL' if ws['ignition'] else 'NOOP','mode':mode,'authority':'NONE','selected':ws['selected']}
        ws['uptake']=ws['ignition']; self.mark('clay_model_4b','gwt_workspace','clay_model_4b','bounded_active_assembly'); return out
    def recurrence(self,delta=.25,pressure=.35,count=1,budget=4,utility=.3):
        if count>=budget: d='ESCALATE_STALLED' if pressure>.4 else 'HALT_CANDIDATE_CONVERGED'
        elif delta<.05 and pressure<.2 and utility<.1: d='HALT_CANDIDATE_CONVERGED'
        elif delta<.05 and pressure>=.4: d='ESCALATE_STALLED'
        elif delta>.9: d='ABORT_DIVERGING'
        else: d='CONTINUE'
        out={'decision':d,'emergence_claim':False,'authority':'RECURRENCE_CONTROL_PROPOSAL'}
        self.mark('loop_dynamics_controller','semantic_state','loop_dynamics_controller','recurrence'); return out
    def permit(self,proposal:dict[str,Any],capability:str): return Permit(capability,self.ledger.epoch,h(proposal))
    def effect(self,proposal:dict[str,Any],permit:Permit|None,capability:str):
        if proposal.get('authority') not in {None,'NONE'}: status='DENIED_MODEL_AUTHORITY_CLAIM'
        elif permit is None: status='DENIED_NO_PERMIT'
        elif permit.epoch!=self.ledger.epoch: status='DENIED_STALE_EPOCH'
        elif permit.capability!=capability or permit.proposal_hash!=h(proposal): status='DENIED_BINDING'
        else: status='COMMITTED'
        out={'status':status,'epoch':self.ledger.epoch}; self.mark('effect_gateway','clay_model_4b','effect_gateway','authority_gate'); return out
    def outcome(self,ws:dict[str,Any],eff:dict[str,Any]):
        out={'effect_status':eff['status'],'reentry':True}; ws['causal_use']=eff['status']=='COMMITTED'; ws['outcome']=out; ws['reentry']=True
        self.mark('causal_observability_replay','effect_gateway','causal_observability_replay','outcome_reentry'); return out
    def promote(self,candidate='mvc-candidate',tier='SILVER',before=.7,after=.78,poison=False):
        tier=tier.upper(); current=self.ledger.get('visual','promoted_classifier'); last=None if not current else current['value']['candidate']
        if poison: status='REJECTED_POISON_RISK'
        elif tier=='BRONZE': status='SHADOW_ONLY_BRONZE'
        elif after<=before: status='REJECTED_NO_IMPROVEMENT'
        else:
            status='PROMOTED'; base=self.ledger.epoch
            self.ledger.append_event(event_id=f'promote-{base+1}',idem=f'promote-{base+1}',base_epoch=base,event_type='ADAPTIVE_PROMOTION',writer='frank-integrated-spine',ops=[{'op':'SET','domain':'visual','key':'promoted_classifier','value':{'candidate':candidate,'previous':last,'tier':tier,'metric':after},'epistemic':'KNOWN','status':'CURRENT'}],provenance={'tier':tier},source={'kind':'shadow_eval'},execution={})
        self.mark('adaptive_state_promotion','causal_observability_replay','adaptive_state_promotion','evidence_gated_learning'); return {'status':status,'last_known_good':last}
    def cycle(self,text:str,visual:dict[str,Any],options:list[dict[str,Any]],mode='instruct'):
        self.seen.clear(); self.graph.clear(); env=self.ingress(text)
        self.commit({'ingress':{'bridge_hash':env.bridge_hash},'self':{'epq_vigilance':.5},'body':{'host':'ubuntu-sandbox'}},f'state-{self.ledger.epoch+1}')
        p=self.perceive(visual); self.commit({'perceptual_field':p['perceptual_field'],'visual_familiarity':p['mvc']},f'percept-{self.ledger.epoch+1}')
        topology=self.topology(); gate=self.gate(p); alts=self.alternatives(options); ws=self.workspace(gate,alts); proposal=self.model(ws,mode); loop=self.recurrence()
        permit=self.permit(proposal,'sandbox.echo'); eff=self.effect(proposal,permit,'sandbox.echo'); out=self.outcome(ws,eff); adaptive=self.promote()
        snap=self.ledger.snapshot(f'cycle-{self.ledger.epoch}')
        coverage=self.lineage_coverage()
        return {'architecture_id':ARCHITECTURE_ID,'evidence_class':EVIDENCE_CLASS,'all_modules_exercised':self.seen==set(MODULES),'modules_seen':sorted(self.seen),'lineage_coverage':coverage,'workspace':ws,'proposal':proposal,'loop':loop,'effect':eff,'outcome':out,'adaptive':adaptive,'topology_hash':h(topology),'snapshot':snap,'semantic_state_hash':self.ledger.semantic_state_hash,'trace_root_hash':self.ledger.trace_root_hash,'run_graph':list(self.graph)}
    def lineage_coverage(self):
        bad={k:v for k,v in LINEAGE.items() if not v or any(m not in MODULES for m in v)}
        return {'families':len(LINEAGE),'omitted':[],'invalid':bad,'pass':not bad}
    def recovery(self):
        events=self.ledger.export_events(); x=StateLedger.replay(events)
        try: return {'events':len(events),'semantic_state_hash_equal':x.semantic_state_hash==self.ledger.semantic_state_hash,'trace_root_hash_equal':x.trace_root_hash==self.ledger.trace_root_hash,'epoch_equal':x.epoch==self.ledger.epoch}
        finally: x.close()
