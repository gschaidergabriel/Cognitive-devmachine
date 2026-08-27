from __future__ import annotations
from typing import Any

from .frank_integrated_spine import FrankIntegratedSpine
from .frank_peer_integrated_runtime import FrankPeerIntegratedRuntime
from .claude_peer_fabric import ClaudeCapability
from .unifieddb_query_plane import UnifiedDBQueryPlane, QuerySpec, SelectionPolicy
from .h1_claygraph import static_architecture_graph, validate_static_graph, dynamic_run_graph, validate_dynamic_graph
from .state_ledger import h

class FrankH1FullRuntime:
    """Executable H1 integration surface for the current FRANK v0.1 target semantics.

    It is intentionally reference-oriented: semantic distinctions remain visible even
    where H3 may physically collapse them into one module/binary.
    """
    def __init__(self, path=':memory:'):
        self.peer_runtime = FrankPeerIntegratedRuntime(path)
        self.spine: FrankIntegratedSpine = self.peer_runtime.spine
        self.udb = UnifiedDBQueryPlane(self.spine.ledger)
        self.static_graph = static_architecture_graph()
        sv = validate_static_graph(self.static_graph)
        if not sv['pass']:
            raise RuntimeError(f'static ClayGraph invalid: {sv}')

    def close(self):
        self.peer_runtime.close()

    def run(self, *, text:str, visual:dict[str,Any], options:list[dict[str,Any]], mode='instruct',
            peer_capability:ClaudeCapability|None=None, peer_semantics:dict[str,Any]|None=None,
            peer_raw_prose:str=''):
        peer = None
        if peer_capability is not None:
            if peer_semantics is None:
                raise ValueError('peer_semantics required when peer_capability is provided')
            peer = self.peer_runtime.cycle_with_peer(
                text=text, visual=visual, base_options=options, capability=peer_capability,
                result_semantics=peer_semantics, raw_prose=peer_raw_prose, mode=mode,
            )
            cycle = peer['cycle']
        else:
            cycle = self.spine.cycle(text, visual, options, mode=mode)

        query = self.udb.query(QuerySpec(
            query_id=f'assembly-{self.spine.ledger.epoch}',
            domains=('semantic','visual','peer','capability'),
            statuses=('CURRENT',),
            epistemic=('KNOWN','UNKNOWN','CONFLICT'),
            basis_epoch=self.spine.ledger.epoch,
            limit=96,
            purpose='POST_CYCLE_ACTIVE_ASSEMBLY_AUDIT',
        ))
        assembly = self.udb.select_for_assembly(
            query, SelectionPolicy(allow_epistemic=('KNOWN',), include_conflicts=False, max_items=24)
        )
        capability_view = self.udb.capability_view()
        run_graph = dynamic_run_graph(cycle=cycle, trace_id=f'cycle-{self.spine.ledger.epoch}')
        if peer is not None:
            run_graph['peer_causal_path'] = {
                'accepted': peer['peer_accept']['status'],
                'selected_by_workspace': peer['peer_selected_by_workspace'],
                'backflow_authority': peer['peer_backflow']['authority'],
                'detail_ref': peer['peer_backflow']['detail_ref'],
                'context_metric': peer['peer_context_metric'],
            }
            run_graph['run_graph_hash'] = h({k:v for k,v in run_graph.items() if k!='run_graph_hash'})
        dynamic_validation = validate_dynamic_graph(run_graph)
        static_validation = validate_static_graph(self.static_graph)
        audit = {
            'all_current_modules_exercised': bool(cycle['all_modules_exercised']),
            'historical_lineage_coverage_pass': bool(cycle['lineage_coverage']['pass']),
            'static_claygraph_pass': static_validation['pass'],
            'dynamic_claygraph_pass': dynamic_validation['pass'],
            'assembly_authority': assembly['authority'],
            'capability_view_authority': capability_view['authority'],
            'model_authority': cycle['proposal']['authority'],
            'effect_status': cycle['effect']['status'],
            'peer_authority': None if peer is None else peer['peer_backflow']['authority'],
        }
        audit['pass'] = (
            audit['all_current_modules_exercised'] and audit['historical_lineage_coverage_pass'] and
            audit['static_claygraph_pass'] and audit['dynamic_claygraph_pass'] and
            audit['assembly_authority']=='ASSEMBLY_CONTEXT_ONLY' and
            audit['capability_view_authority']=='NON_AUTHORITATIVE_PROJECTION' and
            audit['model_authority']=='NONE' and audit['effect_status']=='COMMITTED' and
            (audit['peer_authority'] in {None,'NONE'})
        )
        return {
            'cycle':cycle,
            'peer':peer,
            'unifieddb_query_receipt':query,
            'active_assembly':assembly,
            'capability_view':capability_view,
            'static_claygraph_validation':static_validation,
            'dynamic_run_claygraph':run_graph,
            'dynamic_claygraph_validation':dynamic_validation,
            'integration_audit':audit,
            'semantic_state_hash':self.spine.ledger.semantic_state_hash,
            'trace_root_hash':self.spine.ledger.trace_root_hash,
        }

    def recovery(self):
        return self.spine.recovery()
