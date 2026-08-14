from __future__ import annotations

import heapq
from typing import Any

from .state_ledger import StaleEpoch, h
from .unifieddb_emergent_preprocessor import (
    EmergentAssemblyPreprocessor,
    PossibilitySpec,
    UnifiedDBEmergentPlane,
)
from .unifieddb_emergent_incremental import (
    IncrementalEmergentAssemblyPreprocessor,
    IncrementalUnifiedDBEmergentPlane,
)

_OPTIMIZER_VERSION = 'EAP-EXACT-TOPK-1.5'


class ExactTopKAssemblyMixin:
    """Exact best-first Top-K stop for EAP's monotone activation score.

    Because edge weights and hop decay are bounded to (0, 1], every descendant score is
    <= its frontier ancestor score. Once K admissible visited candidates have a Kth score
    strictly greater than the best remaining frontier score, no unseen candidate can enter
    the final Top-K. Equal-score frontiers are deliberately not stopped so depth/ref tie
    ordering remains exact.
    """

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
        admissible_visited_scores: list[float] = []
        expansions = 0
        stop_reason = 'FRONTIER_EXHAUSTED'

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
            if row is not None and row['domain'] != 'dependency':
                admissible = (
                    (not allowed_domains or row['domain'] in allowed_domains)
                    and row['status'].upper() in allowed_status
                    and row['epistemic'].upper() in allowed_epistemic
                )
                if admissible:
                    admissible_visited_scores.append(score)

            if row is not None and depth < spec.max_hops:
                if (
                    row['status'].upper() not in allowed_status
                    or row['epistemic'].upper() not in allowed_epistemic
                ):
                    blocked_propagation.add(ref)
                else:
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

            if len(admissible_visited_scores) >= spec.max_items and frontier:
                kth_score = sorted(admissible_visited_scores, reverse=True)[spec.max_items - 1]
                frontier_upper_bound = -frontier[0][0]
                if kth_score > frontier_upper_bound + 1e-15:
                    stop_reason = 'EXACT_TOP_K_SCORE_BOUND'
                    break

        if expansions >= spec.frontier_budget and frontier:
            stop_reason = 'FRONTIER_BUDGET'
        elif not frontier:
            stop_reason = 'FRONTIER_EXHAUSTED'

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
            _, _, item_ref = rank
            row = self._rows_by_ref[item_ref]
            return {
                'ref': item_ref,
                'domain': row['domain'],
                'key': row['key'],
                'value': row['value'],
                'epistemic': row['epistemic'],
                'status': row['status'],
                'source_semantic_hash': row['semantic_hash'],
                'domain_epoch': row['domain_epoch'],
                'activation_score': best_score[item_ref],
                'hop': best_hop[item_ref],
                'via_ref': best_via[item_ref],
                'relation_type': best_relation[item_ref],
                'dependency_ref': best_dependency[item_ref],
                'authority': 'CONTEXT_ONLY',
            }

        selected = [materialize(rank) for rank in candidate_rank[: spec.max_items]]
        suppressed = [materialize(rank) for rank in suppressed_rank[: spec.max_items]]
        selection_hash = h({
            'v': _OPTIMIZER_VERSION,
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
            'optimizer': _OPTIMIZER_VERSION,
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
            'preprocessor_version': _OPTIMIZER_VERSION,
            'base_compiled_index_hash': self._compiled_index_hash,
            'seed_refs': tuple(sorted(seed_scores)),
            'selected': selected,
            'suppressed': suppressed,
            'blocked_propagation_refs': tuple(sorted(blocked_propagation)),
            'frontier_expansions': expansions,
            'frontier_exhausted': not frontier,
            'frontier_stop_reason': stop_reason,
            'selection_hash': selection_hash,
            'exact_top_k_stop': True,
            'derived': True,
            'persistent_second_store': False,
            'authority': 'ASSEMBLY_CONTEXT_ONLY',
        }


class ExactTopKEmergentAssemblyPreprocessor(
    ExactTopKAssemblyMixin, EmergentAssemblyPreprocessor
):
    pass


class IncrementalExactTopKEmergentAssemblyPreprocessor(
    ExactTopKAssemblyMixin, IncrementalEmergentAssemblyPreprocessor
):
    pass


class ExactTopKUnifiedDBEmergentPlane(UnifiedDBEmergentPlane):
    def __init__(self, query_plane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = ExactTopKEmergentAssemblyPreprocessor(self.ledger)


class IncrementalExactTopKUnifiedDBEmergentPlane(IncrementalUnifiedDBEmergentPlane):
    def __init__(self, query_plane):
        self.query_plane = query_plane
        self.ledger = query_plane.ledger
        self.preprocessor = IncrementalExactTopKEmergentAssemblyPreprocessor(self.ledger)
