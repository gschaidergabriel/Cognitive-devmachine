"""Clay possibility-preprocessor research candidate.

This is derived acceleration state, not canonical truth or execution authority.
The canonical source remains UnifiedDB; ClayGraph consumes rebuildable projections.

Current prototype deliberately supports a bounded 2-hop semantic horizon because that
permits an exact, cheap higher-order delta update for dependency additions. Dependency
removals/revocations use targeted recomputation unless a later support-count implementation
proves exact deletion deltas.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from typing import Iterable


@dataclass(frozen=True)
class PossibilityRule:
    possibility_id: int
    requirements: tuple[int, ...]
    utility: float


class PossibilityPreprocessor:
    HORIZON = 2

    def __init__(self, token_count: int, edges: Iterable[tuple[int, int]], rules: Iterable[PossibilityRule]):
        self.token_count = token_count
        self.adj: dict[int, set[int]] = defaultdict(set)
        self.rev: dict[int, set[int]] = defaultdict(set)
        for a, b in edges:
            if a == b:
                continue
            self.adj[a].add(b)
            self.rev[b].add(a)

        self.rules = sorted(rules, key=lambda r: r.possibility_id)
        if any(r.possibility_id != i for i, r in enumerate(self.rules)):
            raise ValueError("prototype requires dense possibility ids starting at zero")

        self.closure1 = [self._compute_closure1(s) for s in range(token_count)]
        self.closure2 = [self._compute_closure2(s) for s in range(token_count)]
        self.rule_masks = [self._mask(r.requirements) for r in self.rules]

        df = [0] * token_count
        for r in self.rules:
            for t in r.requirements:
                df[t] += 1
        self.anchor_buckets: dict[int, tuple[int, ...]] = {}
        tmp: dict[int, list[int]] = defaultdict(list)
        for r in self.rules:
            anchor = min(r.requirements, key=lambda t: df[t])
            tmp[anchor].append(r.possibility_id)
        self.anchor_buckets = {k: tuple(v) for k, v in tmp.items()}

    @staticmethod
    def _iter_bits(mask: int):
        while mask:
            lsb = mask & -mask
            yield lsb.bit_length() - 1
            mask -= lsb

    @staticmethod
    def _mask(tokens: Iterable[int]) -> int:
        out = 0
        for t in tokens:
            out |= 1 << t
        return out

    def _compute_closure1(self, source: int) -> int:
        out = 1 << source
        for target in self.adj.get(source, ()):
            out |= 1 << target
        return out

    def _compute_closure2(self, source: int) -> int:
        out = self._compute_closure1(source)
        for mid in self.adj.get(source, ()):
            for target in self.adj.get(mid, ()):
                out |= 1 << target
        return out

    def active_mask(self, cue_ids: Iterable[int]) -> int:
        out = 0
        for cue in cue_ids:
            out |= self.closure2[cue]
        return out

    def query(self, cue_ids: Iterable[int], k: int = 10) -> list[int]:
        """Return exact top-k satisfying possibilities under the prototype utility order.

        Rare-anchor dispatch avoids scanning all possibilities. Ranking remains a derived
        accessibility choice; it does not promote truth or authority.
        """
        active = self.active_mask(cue_ids)
        candidate_ids: set[int] = set()
        for token in self._iter_bits(active):
            candidate_ids.update(self.anchor_buckets.get(token, ()))

        ranked: list[tuple[float, int]] = []
        for pid in candidate_ids:
            required = self.rule_masks[pid]
            if required & active == required:
                ranked.append((self.rules[pid].utility, pid))
        ranked.sort(reverse=True)
        return [pid for _, pid in ranked[:k]]

    def add_dependency(self, source: int, target: int) -> set[int]:
        """Exact bounded-horizon delta for one new dependency edge.

        For H=2:
        - source gains target plus target's <=1-hop closure;
        - every *pre-existing* predecessor of source gains target at distance 2.
        Returns the semantic sources whose prepared closure changed/may have changed.
        """
        if source == target or target in self.adj.get(source, ()):
            return set()
        old_predecessors = set(self.rev.get(source, ()))
        self.adj[source].add(target)
        self.rev[target].add(source)

        self.closure1[source] |= 1 << target
        self.closure2[source] |= self.closure1[target]
        target_bit = 1 << target
        for predecessor in old_predecessors:
            self.closure2[predecessor] |= target_bit
        return {source, *old_predecessors}

    def remove_dependency(self, source: int, target: int) -> set[int]:
        """Fail-safe targeted recompute for deletion/revocation.

        Deletion is not treated as a reversible OR operation. Until support-count deltas are
        implemented and proven, recompute only sources that could have used the removed edge.
        """
        if target not in self.adj.get(source, ()):
            return set()
        old_predecessors = set(self.rev.get(source, ()))
        self.adj[source].remove(target)
        self.rev[target].remove(source)
        affected = {source, *old_predecessors}
        for semantic_source in affected:
            self.closure1[semantic_source] = self._compute_closure1(semantic_source)
            self.closure2[semantic_source] = self._compute_closure2(semantic_source)
        return affected

    def verify_exact(self) -> tuple[bool, list[int]]:
        bad = [s for s in range(self.token_count) if self.closure2[s] != self._compute_closure2(s)]
        return not bad, bad
