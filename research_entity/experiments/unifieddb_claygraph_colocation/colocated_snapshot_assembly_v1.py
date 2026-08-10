from __future__ import annotations

"""Same-file snapshot adapter for existing UnifiedDB + ClayGraph assembly semantics.

No new truth model is introduced here. StateLedger/UnifiedDB remains canonical, ClayGraph
remains derived, and UnifiedClayContextAssembler remains the semantic gate. This adapter only
ensures that the state QueryReceipt, verified graph projection receipt and bounded graph rows
are observed inside one SQLite database snapshot when the physical co-location candidate is
used.
"""
from typing import Callable

from research_entity.harness.reference.state_ledger import StateLedger
from research_entity.harness.reference.unifieddb_query_plane import QuerySpec, SelectionPolicy, UnifiedDBQueryPlane
from research_entity.harness.reference.unifieddb_claygraph_assembly import (
    AmbiguousGraphProjection, GraphProjectionReceipt, UnifiedClayContextAssembler,
    graph_rows_hash,
)


class CoLocatedSnapshotAssembler:
    def __init__(self, ledger: StateLedger):
        self.ledger=ledger
        self.query_plane=UnifiedDBQueryPlane(ledger)
        self.assembler=UnifiedClayContextAssembler(self.query_plane)

    def assemble(self, *, assembly_id: str, query_spec: QuerySpec, source_logical_id: str,
                 graph_limit: int = 32, policy: SelectionPolicy = SelectionPolicy(),
                 test_after_state_hook: Callable[[],None] | None = None):
        if graph_limit <= 0 or graph_limit > 4096: raise ValueError('invalid graph_limit')
        if not source_logical_id.strip(): raise ValueError('source_logical_id required')
        con=self.ledger.conn
        if con.in_transaction: raise RuntimeError('co-located snapshot assembler requires caller-neutral transaction state')
        con.execute('BEGIN')
        try:
            basis=self.ledger.epoch
            # Force the state query to the snapshot basis observed above.
            spec=QuerySpec(
                query_id=query_spec.query_id,
                domains=query_spec.domains,
                keys=query_spec.keys,
                statuses=query_spec.statuses,
                epistemic=query_spec.epistemic,
                limit=query_spec.limit,
                basis_epoch=basis,
                purpose=query_spec.purpose,
            )
            query_receipt=self.query_plane.query(spec)
            if test_after_state_hook is not None:
                # Test-only concurrency hook: a separate connection may commit here. Because state
                # and graph are one physical DB, subsequent graph reads must remain on this snapshot.
                test_after_state_hook()

            ambiguous=int(con.execute(
                'SELECT (SELECT COUNT(*) FROM v_graph_projection_ambiguous_node_epochs) + '
                '(SELECT COUNT(*) FROM v_graph_projection_ambiguous_edge_epochs)'
            ).fetchone()[0])
            if ambiguous:
                raise AmbiguousGraphProjection(f'ambiguous_heads={ambiguous}')

            projection=con.execute('''SELECT projection_id,graph_epoch,source_epoch,verified_equal
                FROM graph_current_projection_receipts
                WHERE verified_equal=1 AND source_epoch=?
                ORDER BY graph_epoch DESC,projection_id DESC LIMIT 1''',(basis,)).fetchone()
            if projection is None:
                raise RuntimeError(f'no verified ClayGraph projection for StateLedger epoch {basis}')

            rows=[]
            for r in con.execute('''SELECT logical_edge_id,edge_version_id,graph_epoch,source_epoch,
                    source_logical_id,target_logical_id,relation_type,weight,confidence,
                    provenance_clay,admissibility_clay,causal_class,source_status
                FROM v_graph_current_edges_fast
                WHERE source_logical_id=?
                ORDER BY weight DESC,relation_type,target_logical_id,logical_edge_id
                LIMIT ?''',(source_logical_id,graph_limit)):
                rows.append({
                    'logical_edge_id':r[0],'edge_version_id':r[1],'graph_epoch':int(r[2]),
                    'source_epoch':int(r[3]),'source_logical_id':r[4],'target_logical_id':r[5],
                    'relation_type':r[6],'weight':r[7],'confidence':r[8],
                    'provenance_clay':r[9],'admissibility_clay':r[10],
                    'causal_class':r[11],'source_status':r[12],
                })
            graph_receipt=GraphProjectionReceipt(
                projection_id=str(projection[0]),
                graph_epoch=int(projection[1]),
                source_epoch=int(projection[2]),
                rows_hash=graph_rows_hash(rows),
                row_count=len(rows),
                ambiguous_heads=0,
                verified_equal=bool(projection[3]),
                projection_kind='COLOCATED_V3_BOUNDED_EDGE_SLICE',
            )
            return self.assembler.assemble(
                assembly_id=assembly_id,
                query_receipt=query_receipt,
                graph_receipt=graph_receipt,
                graph_rows=rows,
                policy=policy,
                require_exact_graph_epoch=True,
            )
        finally:
            con.rollback()
