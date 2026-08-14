from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any

from .frank_integrated_spine import MODULES, LINEAGE, ARCHITECTURE_ID
from .state_ledger import h

FREEZE_SEMANTIC_HASH='b92521a77690fcee8e6e247597e091c1478f790d38f780381d899b1200e85a0f'
GRAPH_SCHEMA='h1-reference-claygraph-0.1'

EDGE_SPECS=(
('observation','semantic_state','feed_forward'),
('semantic_state','claygraph_memory','persistence'),
('claygraph_memory','gwt_workspace','gating'),
('hyperposition','gwt_workspace','candidate'),
('gwt_workspace','clay_model_4b','broadcast'),
('clay_model_4b','semantic_state','feedback'),
('semantic_state','loop_dynamics_controller','recurrent'),
('loop_dynamics_controller','gwt_workspace','re_entry'),
('gwt_workspace','effect_gateway','authority_resource'),
('effect_gateway','outcome_receipt','effect_receipt'),
('outcome_receipt','semantic_state','re_entry'),
('outcome_receipt','unifieddb_plane','persistence'),
('outcome_receipt','claygraph_memory','reward_credit'),
('visual_source','digital_retina','feed_forward'),
('digital_retina','perceptual_field','feed_forward'),
('perceptual_field','micro_visual_classifier','modulation'),
('micro_visual_classifier','thalamus_attention','gating'),
('perceptual_field','thalamus_attention','feed_forward'),
('thalamus_attention','gwt_workspace','gating'),
('outcome_receipt','perceptual_field','re_entry'),
('outcome_receipt','adaptive_state_promotion','reward_credit'),
('claude_code_peer','unifieddb_plane','provenance'),
('unifieddb_plane','gwt_workspace','candidate'),
)

AUX_NODES={'observation','outcome_receipt','visual_source','claude_code_peer'}

class ClayGraphError(ValueError): pass


def static_architecture_graph():
    nodes=[]
    for m in MODULES:
        nodes.append({
            'id':m,'kind':'module','architecture_id':ARCHITECTURE_ID,
            'intervention_handle':f'lesion:{m}','source':'REFERENCE_HARNESS_ARCHITECTURE_FREEZE',
            'provenance':{'freeze_semantic_hash':FREEZE_SEMANTIC_HASH},
        })
    for n in sorted(AUX_NODES):
        nodes.append({'id':n,'kind':'external_or_state_boundary','architecture_id':ARCHITECTURE_ID,'intervention_handle':f'lesion:{n}','source':'H1_INTEGRATION_OVERLAY'})
    edges=[]
    for i,(a,b,kind) in enumerate(EDGE_SPECS):
        edges.append({
            'id':f'e{i:02d}:{a}->{b}','source':a,'target':b,'edge_class':kind,
            'delay_class':'SAME_EPISODE' if kind not in {'re_entry','feedback','recurrent'} else 'RECURRENT_OR_NEXT_STEP',
            'intervention_handle':f'lesion-edge:e{i:02d}',
            'provenance':{'architecture_id':ARCHITECTURE_ID,'freeze_semantic_hash':FREEZE_SEMANTIC_HASH},
        })
    graph={
        'schema_version':GRAPH_SCHEMA,
        'graph_kind':'STATIC_ARCHITECTURE_CLAYGRAPH_CANDIDATE',
        'release_claim':'NOT_H1_RELEASE_PASS',
        'architecture_id':ARCHITECTURE_ID,
        'executed_architecture_module_hash':h(sorted(MODULES)),
        'declared_architecture_module_hash':h(sorted(n['id'] for n in nodes if n['kind']=='module')),
        'nodes':nodes,
        'edges':edges,
        'lineage':{k:list(v) for k,v in sorted(LINEAGE.items())},
    }
    graph['graph_hash']=h({k:v for k,v in graph.items() if k!='graph_hash'})
    return graph


def validate_static_graph(graph:dict[str,Any]):
    ids={n['id'] for n in graph.get('nodes',[])}
    modules={n['id'] for n in graph.get('nodes',[]) if n.get('kind')=='module'}
    errors=[]
    if modules != set(MODULES): errors.append({'module_set_mismatch':{'missing':sorted(set(MODULES)-modules),'extra':sorted(modules-set(MODULES))}})
    for e in graph.get('edges',[]):
        if e.get('source') not in ids: errors.append({'unknown_source':e.get('id')})
        if e.get('target') not in ids: errors.append({'unknown_target':e.get('id')})
        if not e.get('intervention_handle'): errors.append({'missing_edge_intervention':e.get('id')})
    bad_lineage={k:v for k,v in graph.get('lineage',{}).items() if not v or any(x not in modules for x in v)}
    if bad_lineage: errors.append({'bad_lineage':bad_lineage})
    if graph.get('executed_architecture_module_hash') != graph.get('declared_architecture_module_hash'):
        errors.append({'architecture_hash_mismatch':True})
    expected=h({k:v for k,v in graph.items() if k!='graph_hash'})
    if graph.get('graph_hash') != expected: errors.append({'graph_hash_mismatch':True})
    return {'pass':not errors,'errors':errors,'module_count':len(modules),'edge_count':len(graph.get('edges',[])),'lineage_family_count':len(graph.get('lineage',{}))}


def dynamic_run_graph(*, cycle:dict[str,Any], trace_id:str, interventions=()):
    active=[]
    for seq,item in enumerate(cycle.get('run_graph',[])):
        if not isinstance(item,(list,tuple)) or len(item)!=3: continue
        src,dst,rel=item
        active.append({'seq':seq,'source':src,'target':dst,'relation':rel,'active':True})
    w=cycle.get('workspace',{})
    stages={
        'candidate_count':len(w.get('candidates',[])),
        'selected':w.get('selected'),
        'ignition':bool(w.get('ignition')),
        'delivered':bool(w.get('delivered')),
        'reconstructed':bool(w.get('reconstructed')),
        'uptake':bool(w.get('uptake')),
        'causal_use':bool(w.get('causal_use')),
        'outcome_present':w.get('outcome') is not None,
        'reentry':bool(w.get('reentry')),
    }
    out={
        'schema_version':GRAPH_SCHEMA,
        'graph_kind':'DYNAMIC_RUN_CLAYGRAPH',
        'trace_id':trace_id,
        'architecture_id':cycle.get('architecture_id'),
        'pre_post_identity':{'post_semantic_state_hash':cycle.get('semantic_state_hash'),'post_trace_root_hash':cycle.get('trace_root_hash')},
        'active_edges':active,
        'gwt_stages':stages,
        'effect':cycle.get('effect'),
        'outcome':cycle.get('outcome'),
        'interventions':list(interventions),
        'evidence_class':cycle.get('evidence_class'),
    }
    out['run_graph_hash']=h({k:v for k,v in out.items() if k!='run_graph_hash'})
    return out


def validate_dynamic_graph(graph:dict[str,Any]):
    errors=[]
    seqs=[e.get('seq') for e in graph.get('active_edges',[])]
    if seqs != list(range(len(seqs))): errors.append('non_contiguous_order')
    s=graph.get('gwt_stages',{})
    if s.get('causal_use') and not s.get('uptake'): errors.append('causal_use_without_uptake')
    if s.get('uptake') and not s.get('delivered'): errors.append('uptake_without_delivery')
    if s.get('reentry') and not s.get('outcome_present'): errors.append('reentry_without_outcome')
    expected=h({k:v for k,v in graph.items() if k!='run_graph_hash'})
    if graph.get('run_graph_hash')!=expected: errors.append('run_graph_hash_mismatch')
    return {'pass':not errors,'errors':errors,'active_edge_count':len(graph.get('active_edges',[]))}
