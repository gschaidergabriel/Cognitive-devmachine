from __future__ import annotations
from typing import Any

from .frank_h1_organism_runtime import FrankH1OrganismRuntime
from .state_ledger import h

class FrankH1LoopOfLoopsRuntime:
    """Multi-timescale H1 controller: fast organism cycles + slow state consolidation/re-entry.

    The fast loop is the full pixel->GWT organism. The slow loop writes a compact
    control-state receipt into the same ledger; subsequent fast loops may retrieve that
    state through ClayGraph memory support. Recurrence decisions are made by the same
    loop_dynamics_controller method used by the core spine.
    """
    def __init__(self,effect_root:str,ledger_path=':memory:'):
        self.organism=FrankH1OrganismRuntime(effect_root,ledger_path)
    @property
    def ledger(self): return self.organism.ledger
    @property
    def spine(self): return self.organism.pixel.full.spine
    def close(self): self.organism.close()
    def learn_visual(self,*args,**kwargs): return self.organism.learn_visual(*args,**kwargs)

    @staticmethod
    def _behavior_signature(out:dict[str,Any]):
        full=out['visual']['full_runtime']; cycle=full['cycle']; fam=out['visual']['familiarity']
        return {
            'familiarity_outcome':fam.outcome,
            'familiarity_label':fam.candidate_label,
            'workspace_selected':cycle['workspace']['selected'],
            'workspace_ignition':cycle['workspace']['ignition'],
            'proposal_kind':cycle['proposal']['kind'],
            'effect_status':cycle['effect']['status'],
            'model_authority':cycle['proposal']['authority'],
        }

    @staticmethod
    def _pressure(out:dict[str,Any]):
        fam=out['visual']['familiarity'].outcome
        route=out['visual']['visual_percept']['routing_decision']
        if fam in {'CONFLICT','AMBIGUOUS'}: return .9
        if fam=='UNKNOWN' or route=='DEEP_PERCEPTION_ESCALATION': return .8
        if not out['organism_audit']['pass']: return 1.0
        return .1

    def _slow_consolidate(self,episode_id:str,fast_index:int,decision:dict[str,Any],behavior:dict[str,Any],pressure:float,delta:float):
        base=self.ledger.epoch; key=f'episode:{episode_id}'
        value={
            'episode_id':episode_id,'last_fast_index':fast_index,'decision':decision['decision'],
            'pressure':round(pressure,6),'state_delta':round(delta,6),'behavior_hash':h(behavior),
            'semantic_state_hash_before_control_write':self.ledger.semantic_state_hash,
            'authority':'CONTROL_STATE_ONLY','emergence_claim':False,
        }
        eid=f'loop-control:{episode_id}:{fast_index}:{base+1}'
        self.ledger.append_event(event_id=eid,idem=eid,base_epoch=base,event_type='LOOP_SLOW_CONSOLIDATION',writer='frank-h1-loop-of-loops',ops=[{'op':'SET','domain':'loop_control','key':key,'value':value,'epistemic':'KNOWN','status':'CURRENT'}],provenance={'component':'loop_dynamics_controller'},source={'kind':'fast_loop_receipt'},execution={})
        snap=self.ledger.snapshot(f'loop:{episode_id}:{fast_index}')
        return {'key':key,'value':value,'snapshot':snap}

    def run_episode(self,*,episode_id:str,text:str,images:list[Any],source_id:str='screen',options:list[dict[str,Any]]|None=None,
                    max_fast_cycles:int=6,slow_period:int=1,mode='instruct',context_prior=None,
                    peer_capability=None,peer_semantics_factory=None):
        if not episode_id.strip(): raise ValueError('episode_id required')
        if not images: raise ValueError('at least one image required')
        if max_fast_cycles<1 or max_fast_cycles>128: raise ValueError('invalid max_fast_cycles')
        if slow_period<1: raise ValueError('invalid slow_period')
        base_options=list(options or [{'name':'local_work','salience':.8}])
        fast=[]; slow=[]; prev_behavior=None; terminal='CONTINUE'; slow_key=f'loop_control:episode:{episode_id}'
        for i in range(1,max_fast_cycles+1):
            opts=list(base_options)
            if self.ledger.get('loop_control',f'episode:{episode_id}') is not None:
                opts.append({'name':'slow_loop_reentry','salience':.46,'memory_key':slow_key})
            peer_semantics=None if peer_semantics_factory is None else peer_semantics_factory(i)
            out=self.organism.run(text=f'{text} [fast={i}]',image=images[min(i-1,len(images)-1)],source_id=source_id,capture_epoch=i,options=opts,mode=mode,context_prior=context_prior,peer_capability=peer_capability,peer_semantics=peer_semantics)
            behavior=self._behavior_signature(out); bh=h(behavior)
            delta=.5 if prev_behavior is None else (.02 if behavior==prev_behavior else .5)
            pressure=self._pressure(out); utility=.05 if out['organism_audit']['pass'] else 0.0
            decision=self.spine.recurrence(delta=delta,pressure=pressure,count=i,budget=max_fast_cycles,utility=utility)
            memory_used=bool(out['visual']['full_runtime']['cycle']['alternatives'].get('memory_context_used'))
            fast.append({'index':i,'behavior':behavior,'behavior_hash':bh,'state_delta':delta,'pressure':pressure,'utility':utility,'decision':decision,'slow_memory_reentry_used':memory_used,'semantic_state_hash':self.ledger.semantic_state_hash,'trace_root_hash':self.ledger.trace_root_hash})
            terminal=decision['decision']; prev_behavior=behavior
            if i%slow_period==0 or terminal!='CONTINUE':
                slow.append(self._slow_consolidate(episode_id,i,decision,behavior,pressure,delta))
            if terminal!='CONTINUE': break
        result={
            'episode_id':episode_id,'fast_cycles':fast,'slow_cycles':slow,'terminal_decision':terminal,
            'fast_cycle_count':len(fast),'slow_cycle_count':len(slow),
            'slow_reentry_observed':any(x['slow_memory_reentry_used'] for x in fast[1:]),
            'emergence_claim':False,'semantic_state_hash':self.ledger.semantic_state_hash,'trace_root_hash':self.ledger.trace_root_hash,
        }
        result['episode_hash']=h({k:v for k,v in result.items() if k!='episode_hash'})
        return result

    def recovery(self): return self.organism.recovery()
