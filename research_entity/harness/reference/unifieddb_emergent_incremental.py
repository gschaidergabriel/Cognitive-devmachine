from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from .unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    UnifiedDBEmergentPlane,
)

_INCREMENTAL_LAYER_VERSION = 'EAP-INCREMENTAL-1.4'


class IncrementalEmergentAssemblyPreprocessor(EmergentAssemblyPreprocessor):
    """EAP traversal semantics with transaction-coupled dependency delta maintenance.

    The canonical ledger is still the only source of truth. This layer only avoids a full
    transient-topology rebuild when the caller can prove that the EAP cache exactly matched
    the ledger immediately before a committed transaction. External/stale writes fall back
    to the base rebuild path automatically. The reverse dependency map is lazy so ordinary
    read boot keeps the same topology-build path as base EAP.
    """

    def __init__(self, ledger):
        super().__init__(ledger)
        self._edges_by_dependency: dict[
            str, tuple[tuple[str, tuple[str, float, str, str]], ...]
        ] = {}
        self._edge_map_state_hash: str | None = None

    def _invalidate(self) -> None:
        super()._invalidate()
        self._edges_by_dependency = {}
        self._edge_map_state_hash = None

    def _ensure_preprocessor(self) -> None:
        prior_state_hash = self._compiled_state_hash
        super()._ensure_preprocessor()
        if prior_state_hash != self._compiled_state_hash:
            # Full topology rebuild happened. Reverse-map creation is deferred until a
            # transaction-coupled dependency write actually needs it.
            self._edges_by_dependency = {}
            self._edge_map_state_hash = None

    def _rebuild_dependency_edge_map(self) -> None:
        by_dependency: dict[
            str, list[tuple[str, tuple[str, float, str, str]]]
        ] = defaultdict(list)
        for source, edges in self._adj.items():
            for edge in edges:
                by_dependency[edge[3]].append((source, edge))
        self._edges_by_dependency = {
            dep_ref: tuple(items) for dep_ref, items in by_dependency.items()
        }
        self._edge_map_state_hash = self._compiled_state_hash

    def _remove_dependency_edges(self, dependency_ref: str) -> None:
        old = self._edges_by_dependency.pop(dependency_ref, ())
        if not old:
            return
        affected_sources = {source for source, _edge in old}
        for source in affected_sources:
            remaining = tuple(
                edge for edge in self._adj.get(source, ()) if edge[3] != dependency_ref
            )
            if remaining:
                self._adj[source] = remaining
            else:
                self._adj.pop(source, None)
        self._edge_count -= len(old)
        if self._edge_count < 0:
            self._invalidate()
            raise RuntimeError('incremental edge count underflow')

    def _dependency_edges_from_row(
        self, dependency_ref: str, row: dict[str, Any]
    ) -> tuple[tuple[str, tuple[str, float, str, str]], ...]:
        if row['status'].upper() != 'CURRENT' or row['epistemic'].upper() != 'KNOWN':
            return ()
        value = row.get('value')
        if not isinstance(value, dict):
            return ()
        source = self._dep_ref(value, 'source')
        target = self._dep_ref(value, 'target')
        if source is None or target is None:
            return ()
        raw_weight = value.get('strength', value.get('weight', 1.0))
        raw_confidence = value.get('confidence', 1.0)
        try:
            weight = max(0.0, min(1.0, float(raw_weight) * float(raw_confidence)))
        except (TypeError, ValueError):
            return ()
        relation = str(value.get('relation_type', value.get('relation', 'SEMANTIC_DEPENDENCY')))
        edges = [(source, (target, weight, relation, dependency_ref))]
        if bool(value.get('bidirectional', False)):
            edges.append((target, (source, weight, relation, dependency_ref)))
        return tuple(edges)

    def _add_dependency_edges(
        self,
        dependency_ref: str,
        edges: tuple[tuple[str, tuple[str, float, str, str]], ...],
    ) -> None:
        if not edges:
            self._edges_by_dependency.pop(dependency_ref, None)
            return
        touched: dict[str, list[tuple[str, float, str, str]]] = {}
        for source, edge in edges:
            touched.setdefault(source, list(self._adj.get(source, ())))
            touched[source].append(edge)
        for source, source_edges in touched.items():
            self._adj[source] = tuple(
                sorted(source_edges, key=lambda edge: (edge[0], edge[2], edge[3]))
            )
        self._edges_by_dependency[dependency_ref] = edges
        self._edge_count += len(edges)

    def _ledger_row(self, domain: str, key: str) -> dict[str, Any] | None:
        current = self.ledger.get(domain, key)
        if current is None:
            return None
        return {
            'domain': domain,
            'key': key,
            'value': current['value'],
            'epistemic': current['epistemic'],
            'status': current['status'],
            'domain_epoch': current['domain_epoch'],
            'semantic_hash': current['semantic_hash'],
        }

    def refresh_after_committed_ops(
        self,
        ops: Iterable[dict[str, Any]],
        *,
        old_epoch: int,
        old_semantic_state_hash: str,
    ) -> bool:
        """Patch exact transaction deltas when the pre-commit cache basis is proven exact.

        Any precondition failure returns False without claiming incremental coherence. The
        next query then uses the base class epoch/hash check and performs a safe full rebuild.
        """
        ops = list(ops)
        if (
            self._compiled_epoch != old_epoch
            or self._compiled_state_hash != old_semantic_state_hash
        ):
            return False
        if any(str(op.get('domain', '')).strip() == 'dependency' for op in ops):
            if self._edge_map_state_hash != old_semantic_state_hash:
                # Safe: adjacency is still the pre-commit compiled topology. The ledger has
                # advanced, but reverse mapping is derived only from this old adjacency.
                self._rebuild_dependency_edge_map()
            if self._edge_map_state_hash != old_semantic_state_hash:
                return False

        lexical_dirty = False
        try:
            for op in ops:
                domain = str(op.get('domain', '')).strip()
                key = str(op.get('key', '')).strip()
                if not domain or not key:
                    self._invalidate()
                    return False
                row = self._ledger_row(domain, key)
                if row is None:
                    self._invalidate()
                    return False
                ref = f'{domain}:{key}'
                self._rows_by_ref[ref] = row

                if domain == 'dependency':
                    self._remove_dependency_edges(ref)
                    new_edges = self._dependency_edges_from_row(ref, row)
                    self._add_dependency_edges(ref, new_edges)
                else:
                    lexical_dirty = True

            old_token_index_epoch = self._token_index_epoch
            self._refresh_compiled_identity()
            if lexical_dirty:
                self._token_index = {}
                self._token_index_epoch = None
            elif old_token_index_epoch == old_epoch:
                # Dependency-only mutations do not change lexical contents.
                self._token_index_epoch = self._compiled_epoch

            if any(str(op.get('domain', '')).strip() == 'dependency' for op in ops):
                self._edge_map_state_hash = self._compiled_state_hash
            return True
        except Exception:
            self._invalidate()
            raise

    def compile_active_assembly(self, spec):
        result = super().compile_active_assembly(spec)
        result['incremental_layer_version'] = _INCREMENTAL_LAYER_VERSION
        result['dependency_delta_maintenance'] = True
        result['reverse_dependency_map_policy'] = 'LAZY_ON_FIRST_DEPENDENCY_WRITE'
        return result


class IncrementalUnifiedDBEmergentPlane(UnifiedDBEmergentPlane):
    """UnifiedDB/EAP composition using transaction-coupled incremental ClayGraph deltas."""

    def __init__(self, query_plane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = IncrementalEmergentAssemblyPreprocessor(self.ledger)
