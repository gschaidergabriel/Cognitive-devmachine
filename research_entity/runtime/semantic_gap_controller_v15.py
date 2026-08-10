from __future__ import annotations

"""Clay U15 sufficiency-gap controller for the model-facing possibility preprocessor.

This is a derived context controller, not a database, truth source, or effect-authority
surface.  It sits *above* U14/V13 access: a coherent compiled field is consumed first;
query-aware graph deepening is allowed only for explicitly unresolved evidence gaps.

Design basis:
- measured Clay negative result: unconditional extra depth added latency with no recall gain;
- measured Clay result: padding a sufficient compiled field reduced precision;
- external primary research: coverage/commitment separation and per-step query-aware gating.

No model judgement is required for the deterministic core.  Requirements are typed by the
calling Clay assembly policy and coverage is proven only by evidence-bound tags/refs.
"""

from dataclasses import dataclass
import hashlib
import time
from typing import Callable, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class EvidenceRequirement:
    requirement_id: str
    required_tags: frozenset[str] = frozenset()
    required_refs: frozenset[str] = frozenset()
    min_items: int = 1


@dataclass(frozen=True)
class EvidenceItem:
    ref: str
    tags: frozenset[str]
    provenance_valid: bool = True
    status: str = "CURRENT"


@dataclass(frozen=True)
class Gap:
    requirement_id: str
    missing_tags: tuple[str, ...]
    missing_refs: tuple[str, ...]
    observed_items: int
    required_items: int


@dataclass(frozen=True)
class GapControlledReceipt:
    query_id: str
    query_hash: str
    source_epoch: int
    graph_epoch: int
    selected_refs: tuple[str, ...]
    initial_sufficient: bool
    final_sufficient: bool
    deepening_used: bool
    deepening_rounds: int
    initial_gaps: tuple[Gap, ...]
    final_gaps: tuple[Gap, ...]
    latency_ns: int
    authority: str = "ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY"


def _admissible(items: Iterable[EvidenceItem]) -> list[EvidenceItem]:
    return [
        item
        for item in items
        if item.provenance_valid and item.status in {"CURRENT", "SUPPORTED"}
    ]


def gaps(requirements: Sequence[EvidenceRequirement], items: Sequence[EvidenceItem]) -> tuple[Gap, ...]:
    """Compute typed evidence gaps without promoting activation/ranking into truth."""
    usable = _admissible(items)
    by_ref = {item.ref: item for item in usable}
    all_tags = set().union(*(item.tags for item in usable)) if usable else set()
    out: list[Gap] = []
    for req in requirements:
        missing_tags = tuple(sorted(set(req.required_tags) - all_tags))
        missing_refs = tuple(sorted(set(req.required_refs) - set(by_ref)))
        matching = 0
        for item in usable:
            tag_ok = not req.required_tags or bool(set(item.tags) & set(req.required_tags))
            ref_ok = not req.required_refs or item.ref in req.required_refs
            if tag_ok and ref_ok:
                matching += 1
        if missing_tags or missing_refs or matching < req.min_items:
            out.append(
                Gap(
                    requirement_id=req.requirement_id,
                    missing_tags=missing_tags,
                    missing_refs=missing_refs,
                    observed_items=matching,
                    required_items=req.min_items,
                )
            )
    return tuple(out)


def gap_terms(gs: Sequence[Gap]) -> tuple[str, ...]:
    terms: list[str] = []
    for g in gs:
        terms.extend(g.missing_tags)
        terms.extend(g.missing_refs)
        if g.observed_items < g.required_items:
            terms.append(g.requirement_id)
    return tuple(dict.fromkeys(term for term in terms if term))


class SufficiencyGapControllerV15:
    """Consume compiled context first; deepen only to close explicit unresolved gaps.

    `expand` is intentionally injected.  A ClayGraph implementation can use per-step
    semantic gating against `query_text + gap_terms`; a conventional SQL/graph engine can
    implement the same contract for matched-baseline tests.
    """

    def __init__(
        self,
        *,
        expand: Callable[[str, tuple[str, ...], tuple[str, ...], int, int, int], Sequence[EvidenceItem]],
        max_rounds: int = 2,
        max_items: int = 16,
    ):
        if max_rounds < 0 or max_rounds > 8:
            raise ValueError("max_rounds out of bounds")
        if max_items <= 0 or max_items > 256:
            raise ValueError("max_items out of bounds")
        self.expand = expand
        self.max_rounds = max_rounds
        self.max_items = max_items

    def assemble(
        self,
        *,
        query_id: str,
        query_text: str,
        source_epoch: int,
        graph_epoch: int,
        initial_items: Sequence[EvidenceItem],
        requirements: Sequence[EvidenceRequirement],
    ) -> GapControlledReceipt:
        if not query_id.strip() or not query_text.strip():
            raise ValueError("query_id/query_text required")
        if source_epoch < 0 or graph_epoch < 0:
            raise ValueError("invalid epoch")
        started = time.perf_counter_ns()
        selected: dict[str, EvidenceItem] = {
            item.ref: item for item in initial_items[: self.max_items]
        }
        initial = gaps(requirements, tuple(selected.values()))
        if not initial:
            return self._receipt(
                query_id,
                query_text,
                source_epoch,
                graph_epoch,
                selected,
                initial,
                initial,
                0,
                started,
            )

        current = initial
        rounds = 0
        while current and rounds < self.max_rounds and len(selected) < self.max_items:
            terms = gap_terms(current)
            if not terms:
                break
            additions = self.expand(
                query_text,
                terms,
                tuple(selected),
                source_epoch,
                graph_epoch,
                self.max_items - len(selected),
            )
            rounds += 1
            before = len(selected)
            for item in additions:
                if len(selected) >= self.max_items:
                    break
                selected.setdefault(item.ref, item)
            current = gaps(requirements, tuple(selected.values()))
            # Anti-stagnation/anti-overthinking: no novel evidence means stop immediately.
            if len(selected) == before:
                break

        return self._receipt(
            query_id,
            query_text,
            source_epoch,
            graph_epoch,
            selected,
            initial,
            current,
            rounds,
            started,
        )

    @staticmethod
    def _receipt(
        query_id: str,
        query_text: str,
        source_epoch: int,
        graph_epoch: int,
        selected: Mapping[str, EvidenceItem],
        initial: tuple[Gap, ...],
        final: tuple[Gap, ...],
        rounds: int,
        started: int,
    ) -> GapControlledReceipt:
        return GapControlledReceipt(
            query_id=query_id,
            query_hash=hashlib.sha256(query_text.encode("utf-8")).hexdigest(),
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            selected_refs=tuple(selected),
            initial_sufficient=not initial,
            final_sufficient=not final,
            deepening_used=rounds > 0,
            deepening_rounds=rounds,
            initial_gaps=initial,
            final_gaps=final,
            latency_ns=time.perf_counter_ns() - started,
        )
