from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Iterable

from .state_ledger import StaleEpoch, canon, h
from .unifieddb_query_plane import QueryReceipt, SelectionPolicy, UnifiedDBQueryPlane

class GraphProjectionError(RuntimeError): pass
class StaleGraphProjection(GraphProjectionError): pass
class AmbiguousGraphProjection(GraphProjectionError): pass
class UnverifiedGraphProjection(GraphProjectionError): pass
class GraphProjectionIntegrityError(GraphProjectionError): pass

@dataclass(frozen=True)
class GraphProjectionReceipt:
    projection_id: str
    graph_epoch: int
    source_epoch: int
    rows_hash: str
    row_count: int
    ambiguous_heads: int = 0
    verified_equal: bool = False
    projection_kind: str = 'CLAYGRAPH_CURRENT_DERIVED'
    authority: str = 'NON_AUTHORITATIVE_DERIVED_TOPOLOGY'

@dataclass(frozen=True)
class UnifiedClayAssemblyReceipt:
    assembly_id: str
    basis_epoch: int
    semantic_state_hash: str
    query_hash: str
    graph_epoch: int
    graph_source_epoch: int
    graph_rows_hash: str
    state_selection_hash: str
    assembly_hash: str
    state_items: tuple[dict[str,Any], ...]
    graph_rows: tuple[dict[str,Any], ...]
    conflicts_present: int
    authority: str = 'CONTEXT_ONLY_NO_EFFECT_AUTHORITY'


def graph_rows_hash(rows: Iterable[dict[str,Any]]) -> str:
    # Canonicalize a copy so input mapping order cannot become receipt identity.
    return h(tuple(canon(dict(row)) for row in rows))


class UnifiedClayContextAssembler:
    """Bind UnifiedDB semantic state and derived ClayGraph context at one source epoch.

    The graph remains non-authoritative. This layer grants no effect authority and creates
    no second semantic store; it only rejects stale/ambiguous/unverified mixed context and
    returns a deterministic assembly receipt.
    """
    def __init__(self, query_plane: UnifiedDBQueryPlane):
        self.query_plane=query_plane

    def assemble(self, *, assembly_id: str, query_receipt: QueryReceipt,
                 graph_receipt: GraphProjectionReceipt, graph_rows: Iterable[dict[str,Any]],
                 policy: SelectionPolicy = SelectionPolicy(), require_exact_graph_epoch: bool = True):
        if not assembly_id.strip(): raise ValueError('assembly_id required')

        # select_for_assembly performs current ledger epoch + semantic_state_hash staleness checks.
        state=self.query_plane.select_for_assembly(query_receipt,policy)

        if graph_receipt.ambiguous_heads:
            raise AmbiguousGraphProjection(f'ambiguous_heads={graph_receipt.ambiguous_heads}')
        if not graph_receipt.verified_equal:
            raise UnverifiedGraphProjection(graph_receipt.projection_id)
        if graph_receipt.source_epoch > query_receipt.basis_epoch:
            raise StaleGraphProjection(f'graph source epoch {graph_receipt.source_epoch} is newer than state basis {query_receipt.basis_epoch}')
        if require_exact_graph_epoch and graph_receipt.source_epoch != query_receipt.basis_epoch:
            raise StaleGraphProjection(f'graph source epoch {graph_receipt.source_epoch}!={query_receipt.basis_epoch}')

        rows=tuple(canon(dict(row)) for row in graph_rows)
        actual_hash=h(rows)
        if len(rows)!=graph_receipt.row_count:
            raise GraphProjectionIntegrityError(f'row_count {len(rows)}!={graph_receipt.row_count}')
        if actual_hash!=graph_receipt.rows_hash:
            raise GraphProjectionIntegrityError('graph rows hash mismatch')

        body={
            'assembly_id':assembly_id,
            'basis_epoch':query_receipt.basis_epoch,
            'semantic_state_hash':query_receipt.semantic_state_hash,
            'query_hash':query_receipt.query_hash,
            'graph_epoch':graph_receipt.graph_epoch,
            'graph_source_epoch':graph_receipt.source_epoch,
            'graph_rows_hash':graph_receipt.rows_hash,
            'state_selection_hash':state['selection_hash'],
            'state_items':state['selected'],
            'graph_rows':rows,
            'conflicts_present':state['conflicts_present'],
            'authority':'CONTEXT_ONLY_NO_EFFECT_AUTHORITY',
        }
        ah=h(body)
        return UnifiedClayAssemblyReceipt(
            assembly_id=assembly_id,
            basis_epoch=query_receipt.basis_epoch,
            semantic_state_hash=query_receipt.semantic_state_hash,
            query_hash=query_receipt.query_hash,
            graph_epoch=graph_receipt.graph_epoch,
            graph_source_epoch=graph_receipt.source_epoch,
            graph_rows_hash=graph_receipt.rows_hash,
            state_selection_hash=state['selection_hash'],
            assembly_hash=ah,
            state_items=tuple(state['selected']),
            graph_rows=rows,
            conflicts_present=state['conflicts_present'],
        )
