from __future__ import annotations
from typing import Any

from .frank_integrated_spine import FrankIntegratedSpine, MODULES
from .h1_claygraph import static_architecture_graph
from .state_ledger import h

DEFAULT_VISUAL={
    'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},
    'sensor_confidence':.92,'candidate_label':'cup','prototype_similarity':.9,
}
DEFAULT_OPTIONS=[{'name':'low','salience':.4},{'name':'high','salience':.9}]
CRITICAL={'needle_bridge','semantic_state','unifieddb_plane'}


def signature(out:dict[str,Any]):
    return {
        'percept_epistemic':out['perception']['perceptual_field']['epistemic_state'],
        'mvc_outcome':out['perception']['mvc']['outcome'],
        'topology_nodes':len(out['topology']['nodes']),
        'gate_gain':round(float(out['gate']['gain']),6),
        'gate_relay':bool(out['gate']['relay']),
        'alternative_count':len(out['alternatives']['alternatives']),
        'memory_context_used':bool(out['alternatives'].get('memory_context_used')),
        'selected':out['workspace']['selected'],
        'ignition':bool(out['workspace']['ignition']),
        'uptake':bool(out['workspace']['uptake']),
        'causal_use':bool(out['workspace']['causal_use']),
        'reentry':bool(out['workspace']['reentry']),
        'proposal_kind':out['proposal']['kind'],
        'loop_decision':out['loop']['decision'],
        'effect_status':out['effect']['status'],
        'adaptive_status':out['adaptive']['status'],
        'semantic_state_hash':out['semantic_state_hash'],
        'trace_root_hash':out['trace_root_hash'],
    }


def run_once(module:str|None=None, *, visual=None, options=None):
    r=FrankIntegratedSpine()
    try:
        if module: r.lesion(module)
        try:
            out=r.cycle('intervention',visual or DEFAULT_VISUAL,options or DEFAULT_OPTIONS)
            return {'module':module or 'BASELINE','status':'COMPLETED','signature':signature(out),'lesions':out['lesions']}
        except RuntimeError as e:
            if module in CRITICAL and str(e).startswith('LESIONED_CRITICAL_'):
                return {'module':module,'status':'SYSTEM_UNAVAILABLE','error':str(e)}
            raise
    finally:
        r.close()


def rescue_equivalence(module:str):
    a=FrankIntegratedSpine(); b=FrankIntegratedSpine()
    try:
        baseline=a.cycle('intervention',DEFAULT_VISUAL,DEFAULT_OPTIONS)
        b.lesion(module); b.rescue(module); rescued=b.cycle('intervention',DEFAULT_VISUAL,DEFAULT_OPTIONS)
        return {
            'module':module,
            'semantic_state_hash_equal':baseline['semantic_state_hash']==rescued['semantic_state_hash'],
            'trace_root_hash_equal':baseline['trace_root_hash']==rescued['trace_root_hash'],
            'signature_equal':signature(baseline)==signature(rescued),
        }
    finally:
        a.close(); b.close()


def graph_handle_coverage():
    graph=static_architecture_graph()
    handles={n.get('intervention_handle') for n in graph['nodes'] if n.get('kind')=='module'}
    expected={f'lesion:{m}' for m in MODULES}
    return {'pass':handles==expected,'expected':sorted(expected),'observed':sorted(handles),'missing':sorted(expected-handles),'extra':sorted(handles-expected)}


def run_lesion_matrix():
    baseline=run_once()
    rows=[]
    for m in MODULES:
        probe_options=[{'name':'memory_candidate','salience':.52,'memory_key':'semantic:self'}] if m=='claygraph_memory' else DEFAULT_OPTIONS
        lesion=run_once(m, options=probe_options)
        rescue=rescue_equivalence(m)
        rows.append({'module':m,'lesion':lesion,'rescue':rescue})
    return {
        'schema_version':'frank-h1-lesion-matrix-0.1',
        'baseline':baseline,
        'rows':rows,
        'graph_handle_coverage':graph_handle_coverage(),
        'matrix_hash':h({'baseline':baseline,'rows':rows,'graph_handle_coverage':graph_handle_coverage()}),
    }
