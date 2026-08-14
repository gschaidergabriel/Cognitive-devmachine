from __future__ import annotations

from typing import Any

from .state_ledger import h
from .unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    UnifiedDBEmergentPlane,
)
from .unifieddb_emergent_incremental import (
    IncrementalEmergentAssemblyPreprocessor,
    IncrementalUnifiedDBEmergentPlane,
)
from .unifieddb_emergent_exact_topk import ExactTopKAssemblyMixin

_COMPACT_VERSION = 'EAP-COMPACT-CACHE-1.6'


class CompactSemanticCacheMixin:
    """Keep model-materializable rows, not redundant dependency row bodies, after compile.

    Dependency rows are consumed while building the transient sparse adjacency. Their
    provenance identity is retained in each edge as dependency_ref; the canonical ledger
    remains the source for full dependency values. This candidate removes a redundant
    Python-object copy without changing graph topology or selected row materialization.
    """

    def _refresh_compiled_identity(self) -> None:
        self._compiled_epoch = self.ledger.epoch
        self._compiled_state_hash = self.ledger.semantic_state_hash
        self._compiled_index_hash = h({
            'version': _COMPACT_VERSION,
            'basis_epoch': self._compiled_epoch,
            'semantic_state_hash': self._compiled_state_hash,
            'materializable_node_count': len(self._rows_by_ref),
            'edge_count': self._edge_count,
            'dependency_row_cache': 'DISCARDED_AFTER_COMPILE',
            'lexical_index': 'LAZY',
        })

    def _ensure_preprocessor(self) -> None:
        basis = self.ledger.epoch
        state_hash = self.ledger.semantic_state_hash
        if self._compiled_epoch == basis and self._compiled_state_hash == state_hash:
            return

        rows = self.ledger.materialized()
        by_ref: dict[str, dict[str, Any]] = {}
        adjacency: dict[str, list[tuple[str, float, str, str]]] = {}
        edge_count = 0

        for row in rows:
            if row['domain'] != 'dependency':
                by_ref[self._row_ref(row)] = row

        for row in rows:
            if row['domain'] != 'dependency':
                continue
            if row['status'].upper() != 'CURRENT' or row['epistemic'].upper() != 'KNOWN':
                continue
            value = row.get('value')
            if not isinstance(value, dict):
                continue
            source = self._dep_ref(value, 'source')
            target = self._dep_ref(value, 'target')
            if source is None or target is None:
                continue
            raw_weight = value.get('strength', value.get('weight', 1.0))
            raw_confidence = value.get('confidence', 1.0)
            try:
                weight = max(0.0, min(1.0, float(raw_weight) * float(raw_confidence)))
            except (TypeError, ValueError):
                continue
            relation = str(value.get('relation_type', value.get('relation', 'SEMANTIC_DEPENDENCY')))
            dependency_ref = self._row_ref(row)
            adjacency.setdefault(source, []).append(
                (target, weight, relation, dependency_ref)
            )
            edge_count += 1
            if bool(value.get('bidirectional', False)):
                adjacency.setdefault(target, []).append(
                    (source, weight, relation, dependency_ref)
                )
                edge_count += 1

        self._rows_by_ref = by_ref
        self._adj = {
            source: tuple(sorted(edges, key=lambda edge: (edge[0], edge[2], edge[3])))
            for source, edges in adjacency.items()
        }
        self._edge_count = edge_count
        self._token_index = {}
        self._token_index_epoch = None
        self._refresh_compiled_identity()

    def compile_active_assembly(self, spec):
        result = super().compile_active_assembly(spec)
        result['compact_cache_version'] = _COMPACT_VERSION
        result['dependency_row_cache'] = 'DISCARDED_AFTER_COMPILE'
        result['persistent_second_store'] = False
        return result


class CompactEmergentAssemblyPreprocessor(
    CompactSemanticCacheMixin, EmergentAssemblyPreprocessor
):
    pass


class CompactExactTopKEmergentAssemblyPreprocessor(
    ExactTopKAssemblyMixin, CompactSemanticCacheMixin, EmergentAssemblyPreprocessor
):
    pass


class CompactIncrementalEmergentAssemblyPreprocessor(
    CompactSemanticCacheMixin, IncrementalEmergentAssemblyPreprocessor
):
    def _ensure_preprocessor(self) -> None:
        prior_state_hash = self._compiled_state_hash
        CompactSemanticCacheMixin._ensure_preprocessor(self)
        if prior_state_hash != self._compiled_state_hash:
            self._edges_by_dependency = {}
            self._edge_map_state_hash = None

    def refresh_after_committed_ops(
        self,
        ops,
        *,
        old_epoch: int,
        old_semantic_state_hash: str,
    ) -> bool:
        ops = list(ops)
        refreshed = IncrementalEmergentAssemblyPreprocessor.refresh_after_committed_ops(
            self,
            ops,
            old_epoch=old_epoch,
            old_semantic_state_hash=old_semantic_state_hash,
        )
        if not refreshed:
            return False
        removed_dependency_cache = False
        for op in ops:
            if str(op.get('domain', '')).strip() == 'dependency':
                key = str(op.get('key', '')).strip()
                if key and self._rows_by_ref.pop(f'dependency:{key}', None) is not None:
                    removed_dependency_cache = True
        if removed_dependency_cache:
            self._refresh_compiled_identity()
        return True


class CompactIncrementalExactTopKEmergentAssemblyPreprocessor(
    ExactTopKAssemblyMixin, CompactIncrementalEmergentAssemblyPreprocessor
):
    pass


class CompactUnifiedDBEmergentPlane(UnifiedDBEmergentPlane):
    def __init__(self, query_plane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = CompactEmergentAssemblyPreprocessor(self.ledger)


class CompactIncrementalUnifiedDBEmergentPlane(IncrementalUnifiedDBEmergentPlane):
    def __init__(self, query_plane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = CompactIncrementalEmergentAssemblyPreprocessor(self.ledger)
