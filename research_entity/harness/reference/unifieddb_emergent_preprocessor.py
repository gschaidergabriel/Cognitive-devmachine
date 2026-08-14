from __future__ import annotations

from dataclasses import dataclass
import heapq
import json
import re
from typing import Any, Iterable

from .state_ledger import StateLedger, StaleEpoch, h
from .unifieddb_query_plane import UnifiedDBQueryPlane

_TOKEN_RE = re.compile(r"[\w-]+", re.UNICODE)
_PREPROCESSOR_VERSION = "EAP-1.3"


@dataclass(frozen=True)
class PossibilitySpec:
    assembly_id: str
    seed_refs: tuple[str, ...] = ()
    query_text: str = ''
    allowed_domains: tuple[str, ...] = ()
    allow_epistemic: tuple[str, ...] = ('KNOWN',)
    allow_status: tuple[str, ...] = ('CURRENT',)
    max_items: int = 12
    max_hops: int = 3
    frontier_budget: int = 512
    min_edge_weight: float = 0.05
    hop_decay: float = 0.88
    lexical_weight: float = 0.42
    basis_epoch: int | None = None
    purpose: str = 'EMERGENT_ACTIVE_ASSEMBLY'


class EmergentAssemblyPreprocessor:
    """Disposable, epoch-bound multi-hop projection over UnifiedDB state.

    This class is an access/assembly preprocessor, not a persistent database. Source
    truth remains the StateLedger. Dependency rows are compiled into transient sparse
    topology; inadmissible epistemic nodes cannot silently relay activation.
    """

    def __init__(self, ledger: StateLedger):
        self.ledger = ledger
        self._compiled_epoch: int | None = None
        self._compiled_state_hash: str | None = None
        self._compiled_index_hash: str | None = None
        self._rows_by_ref: dict[str, dict[str, Any]] = {}
        self._token_index: dict[str, tuple[str, ...]] = {}
        self._token_index_epoch: int | None = None
        self._adj: dict[str, tuple[tuple[str, float, str, str], ...]] = {}
        self._edge_count: int = 0

    @staticmethod
    def _row_ref(row: dict[str, Any]) -> str:
        return f"{row['domain']}:{row['key']}"

    @staticmethod
    def _dep_ref(value: dict[str, Any], side: str) -> str | None:
        direct = value.get(side) or value.get(f'{side}_ref')
        if isinstance(direct, str) and direct.strip():
            return direct.strip()
        kind = value.get(f'{side}_kind')
        ident = value.get(f'{side}_id')
        if kind is not None and ident is not None:
            return f'{kind}:{ident}'
        return None

    @staticmethod
    def _tokens(row: dict[str, Any]) -> set[str]:
        text = row['key'] + ' ' + json.dumps(
            row.get('value'), ensure_ascii=False, sort_keys=True, separators=(',', ':')
        )
        return {token.lower() for token in _TOKEN_RE.findall(text) if len(token) > 1}

    def _refresh_compiled_identity(self) -> None:
        self._compiled_epoch = self.ledger.epoch
        self._compiled_state_hash = self.ledger.semantic_state_hash
        self._compiled_index_hash = h({
            'version': _PREPROCESSOR_VERSION,
            'basis_epoch': self._compiled_epoch,
            'semantic_state_hash': self._compiled_state_hash,
            'node_count': len(self._rows_by_ref),
            'edge_count': self._edge_count,
            'lexical_index': 'LAZY',
        })

    def _invalidate(self) -> None:
        self._compiled_epoch = None
        self._compiled_state_hash = None
        self._compiled_index_hash = None
        self._token_index = {}
        self._token_index_epoch = None

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

    def _ensure_lexical_index(self) -> None:
        self._ensure_preprocessor()
        if self._token_index_epoch == self._compiled_epoch:
            return
        token_index: dict[str, set[str]] = {}
        for ref, row in self._rows_by_ref.items():
            if row['domain'] == 'dependency':
                continue
            for token in self._tokens(row):
                token_index.setdefault(token, set()).add(ref)
        self._token_index = {
            token: tuple(sorted(refs)) for token, refs in token_index.items()
        }
        self._token_index_epoch = self._compiled_epoch

    def _lexical_seed_scores(
        self, query_text: str, lexical_weight: float, cap: int
    ) -> dict[str, float]:
        if query_text.strip():
            self._ensure_lexical_index()
        tokens = {token.lower() for token in _TOKEN_RE.findall(query_text) if len(token) > 1}
        if not tokens:
            return {}
        hits: dict[str, int] = {}
        for token in tokens:
            for ref in self._token_index.get(token, ()):
                hits[ref] = hits.get(ref, 0) + 1
        denominator = max(1, len(tokens))
        ranked = sorted(
            (
                (lexical_weight * count / denominator, ref)
                for ref, count in hits.items()
            ),
            key=lambda item: (-item[0], item[1]),
        )
        return {ref: score for score, ref in ranked[:cap] if score > 0.0}

    def refresh_after_committed_ops(
        self,
        ops: Iterable[dict[str, Any]],
        *,
        old_epoch: int,
        old_semantic_state_hash: str,
    ) -> bool:
        """Incrementally refresh non-structural rows after a caller-owned commit.

        Dependency mutations intentionally invalidate and force a safe rebuild. External
        writes are detected by epoch/hash mismatch on the next compile.
        """
        ops = list(ops)
        if (
            self._compiled_epoch != old_epoch
            or self._compiled_state_hash != old_semantic_state_hash
        ):
            return False
        if any(str(op.get('domain', '')).strip() == 'dependency' for op in ops):
            self._invalidate()
            return False

        for op in ops:
            domain = str(op.get('domain', '')).strip()
            key = str(op.get('key', '')).strip()
            if not domain or not key:
                self._invalidate()
                return False
            current = self.ledger.get(domain, key)
            if current is None:
                self._invalidate()
                return False
            ref = f'{domain}:{key}'
            self._rows_by_ref[ref] = {
                'domain': domain,
                'key': key,
                'value': current['value'],
                'epistemic': current['epistemic'],
                'status': current['status'],
                'domain_epoch': current['domain_epoch'],
                'semantic_hash': current['semantic_hash'],
            }

        self._token_index = {}
        self._token_index_epoch = None
        self._refresh_compiled_identity()
        return True

    def compile_active_assembly(self, spec: PossibilitySpec) -> dict[str, Any]:
        if not spec.assembly_id.strip():
            raise ValueError('assembly_id required')
        if spec.max_items <= 0 or spec.max_items > 4096:
            raise ValueError('invalid max_items')
        if spec.max_hops < 0 or spec.max_hops > 32:
            raise ValueError('invalid max_hops')
        if spec.frontier_budget <= 0 or spec.frontier_budget > 1_000_000:
            raise ValueError('invalid frontier_budget')
        if not 0.0 <= spec.min_edge_weight <= 1.0:
            raise ValueError('invalid min_edge_weight')
        if not 0.0 < spec.hop_decay <= 1.0:
            raise ValueError('invalid hop_decay')
        if not 0.0 <= spec.lexical_weight <= 1.0:
            raise ValueError('invalid lexical_weight')

        basis = self.ledger.epoch
        if spec.basis_epoch is not None and int(spec.basis_epoch) != basis:
            raise StaleEpoch(f'assembly basis {spec.basis_epoch}!={basis}')
        self._ensure_preprocessor()

        allowed_domains = set(spec.allowed_domains)
        allowed_epistemic = {value.upper() for value in spec.allow_epistemic}
        allowed_status = {value.upper() for value in spec.allow_status}

        seed_scores: dict[str, float] = {}
        for ref in spec.seed_refs:
            if ref in self._rows_by_ref and self._rows_by_ref[ref]['domain'] != 'dependency':
                seed_scores[ref] = 1.0
        lexical = self._lexical_seed_scores(
            spec.query_text,
            spec.lexical_weight,
            max(spec.max_items * 4, 16),
        )
        for ref, score in lexical.items():
            seed_scores[ref] = max(seed_scores.get(ref, 0.0), score)

        frontier: list[
            tuple[float, int, str, str | None, str | None, str | None]
        ] = []
        for ref, score in sorted(seed_scores.items()):
            heapq.heappush(frontier, (-score, 0, ref, None, None, None))

        best_score: dict[str, float] = {}
        best_hop: dict[str, int] = {}
        best_via: dict[str, str | None] = {}
        best_relation: dict[str, str | None] = {}
        best_dependency: dict[str, str | None] = {}
        blocked_propagation: set[str] = set()
        expansions = 0

        while frontier and expansions < spec.frontier_budget:
            negative_score, depth, ref, via, relation, dependency_ref = heapq.heappop(
                frontier
            )
            score = -negative_score
            previous = best_score.get(ref)
            if previous is not None and score <= previous + 1e-15:
                continue

            best_score[ref] = score
            best_hop[ref] = depth
            best_via[ref] = via
            best_relation[ref] = relation
            best_dependency[ref] = dependency_ref
            expansions += 1

            row = self._rows_by_ref.get(ref)
            if row is None or depth >= spec.max_hops:
                continue

            # Negative-space guard: if a node is not admissible for this Assembly, it
            # remains observable as suppressed evidence but cannot launder activation
            # into otherwise admissible descendants.
            if (
                row['status'].upper() not in allowed_status
                or row['epistemic'].upper() not in allowed_epistemic
            ):
                blocked_propagation.add(ref)
                continue

            for (
                target,
                edge_weight,
                edge_relation,
                edge_dependency_ref,
            ) in self._adj.get(ref, ()):
                if edge_weight < spec.min_edge_weight:
                    continue
                next_score = score * edge_weight * spec.hop_decay
                if (
                    next_score <= 0.0
                    or next_score <= best_score.get(target, -1.0) + 1e-15
                ):
                    continue
                heapq.heappush(
                    frontier,
                    (
                        -next_score,
                        depth + 1,
                        target,
                        ref,
                        edge_relation,
                        edge_dependency_ref,
                    ),
                )

        candidate_rank = []
        suppressed_rank = []
        for ref, score in best_score.items():
            row = self._rows_by_ref.get(ref)
            if row is None or row['domain'] == 'dependency':
                continue
            rank = (-score, best_hop[ref], ref)
            admissible = (
                (not allowed_domains or row['domain'] in allowed_domains)
                and row['status'].upper() in allowed_status
                and row['epistemic'].upper() in allowed_epistemic
            )
            (candidate_rank if admissible else suppressed_rank).append(rank)

        candidate_rank.sort()
        suppressed_rank.sort()

        def materialize(rank):
            _, _, ref = rank
            row = self._rows_by_ref[ref]
            return {
                'ref': ref,
                'domain': row['domain'],
                'key': row['key'],
                'value': row['value'],
                'epistemic': row['epistemic'],
                'status': row['status'],
                'source_semantic_hash': row['semantic_hash'],
                'domain_epoch': row['domain_epoch'],
                'activation_score': best_score[ref],
                'hop': best_hop[ref],
                'via_ref': best_via[ref],
                'relation_type': best_relation[ref],
                'dependency_ref': best_dependency[ref],
                'authority': 'CONTEXT_ONLY',
            }

        selected = [
            materialize(rank) for rank in candidate_rank[: spec.max_items]
        ]
        suppressed = [
            materialize(rank) for rank in suppressed_rank[: spec.max_items]
        ]
        selection_hash = h({
            'v': _PREPROCESSOR_VERSION,
            'epoch': basis,
            'state': self.ledger.semantic_state_hash,
            'index': self._compiled_index_hash,
            'assembly': spec.assembly_id,
            'seed_refs': tuple(sorted(seed_scores)),
            'query_text': spec.query_text,
            'allowed_domains': spec.allowed_domains,
            'allow_epistemic': spec.allow_epistemic,
            'allow_status': spec.allow_status,
            'max_items': spec.max_items,
            'max_hops': spec.max_hops,
            'frontier_budget': spec.frontier_budget,
            'min_edge_weight': spec.min_edge_weight,
            'hop_decay': spec.hop_decay,
            'lexical_weight': spec.lexical_weight,
            'selected': tuple(
                (
                    item['ref'],
                    item['source_semantic_hash'],
                    item['activation_score'],
                    item['hop'],
                    item['dependency_ref'],
                )
                for item in selected
            ),
        })

        return {
            'assembly_id': spec.assembly_id,
            'basis_epoch': basis,
            'semantic_state_hash': self.ledger.semantic_state_hash,
            'preprocessor_version': _PREPROCESSOR_VERSION,
            'compiled_index_hash': self._compiled_index_hash,
            'seed_refs': tuple(sorted(seed_scores)),
            'selected': selected,
            'suppressed': suppressed,
            'blocked_propagation_refs': tuple(sorted(blocked_propagation)),
            'frontier_expansions': expansions,
            'frontier_exhausted': not frontier,
            'selection_hash': selection_hash,
            'derived': True,
            'persistent_second_store': False,
            'authority': 'ASSEMBLY_CONTEXT_ONLY',
        }


class UnifiedDBEmergentPlane:
    """Composition facade: current UnifiedDB query plane + emergent Assembly compiler."""

    def __init__(self, query_plane: UnifiedDBQueryPlane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = EmergentAssemblyPreprocessor(self.ledger)

    def query(self, *args, **kwargs):
        return self.query_plane.query(*args, **kwargs)

    def select_for_assembly(self, *args, **kwargs):
        return self.query_plane.select_for_assembly(*args, **kwargs)

    def capability_view(self):
        return self.query_plane.capability_view()

    def compile_active_assembly(self, spec: PossibilitySpec):
        return self.preprocessor.compile_active_assembly(spec)

    def transact(
        self,
        *,
        event_id: str,
        idem: str,
        base_epoch: int,
        event_type: str,
        writer: str,
        ops: Iterable[dict[str, Any]],
        provenance=None,
        source=None,
        execution=None,
    ):
        ops = list(ops)
        old_epoch = self.ledger.epoch
        old_hash = self.ledger.semantic_state_hash
        result = self.query_plane.transact(
            event_id=event_id,
            idem=idem,
            base_epoch=base_epoch,
            event_type=event_type,
            writer=writer,
            ops=ops,
            provenance=provenance,
            source=source,
            execution=execution,
        )
        if result.get('status') == 'COMMITTED':
            self.preprocessor.refresh_after_committed_ops(
                ops,
                old_epoch=old_epoch,
                old_semantic_state_hash=old_hash,
            )
        return result
