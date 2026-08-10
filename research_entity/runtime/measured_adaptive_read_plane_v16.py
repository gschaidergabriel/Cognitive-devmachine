"""Clay U16 candidate: measured adaptive semantic read plane.

U16 preserves U14 routing semantics but makes every deterministic route attempt observable.
The purpose is not to add another retrieval mechanism. It creates the execution evidence
needed to decide later whether exact, compiled-semantic, entity-resolution, compositional,
graph or conventional fallback stages should be reordered/skipped for a measured query
class.

Safety laws:
- read basis verification happens before every route;
- route telemetry is context/runtime evidence, never truth/effect authority;
- final refs remain bounded by request.limit;
- latency values are deliberately EXCLUDED from route_trace_hash so replay identity does
  not depend on wall-clock timing;
- exceptions from a mechanism are not hidden as misses.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Sequence
import hashlib
import time

from .adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest,
    VerifiedReadBasis,
    ReadBasisError,
    UnverifiedReadBasis,
    StaleReadBasis,
)


@dataclass(frozen=True)
class RouteAttemptReceipt:
    ordinal: int
    mode: str
    status: str
    result_count: int
    sufficient: bool
    latency_ns: int


@dataclass(frozen=True)
class MeasuredAdaptiveReadReceipt:
    query_id: str
    query_hash: str
    mode: str
    refs: tuple[str, ...]
    resolved_logical_id: str | None
    sufficient: bool
    lexical_padding_used: bool
    source_epoch: int
    graph_epoch: int
    read_basis_id: str
    derivation_hash: str
    latency_ns: int
    attempts: tuple[RouteAttemptReceipt, ...]
    route_trace_hash: str
    authority: str = 'ASSEMBLY_CONTEXT_ONLY'


def _trace_hash(attempts: Sequence[RouteAttemptReceipt]) -> str:
    # Replay identity binds deterministic control-flow/result shape only.
    body = "\n".join(
        f"{a.ordinal}|{a.mode}|{a.status}|{a.result_count}|{int(a.sufficient)}"
        for a in attempts
    )
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


class MeasuredAdaptiveSemanticReadPlaneV16:
    """U14-compatible adaptive read cascade with per-stage execution receipts."""

    def __init__(
        self,
        *,
        verify_read_basis: Callable[[AdaptiveReadRequest], VerifiedReadBasis],
        exact_lookup: Callable[[str, VerifiedReadBasis, int], Sequence[str]],
        compiled_semantic_lookup: Callable[[str, VerifiedReadBasis, int], Sequence[str]],
        resolve_entity: Callable[[str, VerifiedReadBasis], str | None],
        graph_lookup: Callable[[str, str, VerifiedReadBasis, int], Sequence[str]],
        compositional_lookup: Callable[[str, VerifiedReadBasis, int], Sequence[str]],
        fallback_lookup: Callable[[str, VerifiedReadBasis, int], Sequence[str]],
    ):
        self.verify_read_basis = verify_read_basis
        self.exact_lookup = exact_lookup
        self.compiled_semantic_lookup = compiled_semantic_lookup
        self.resolve_entity = resolve_entity
        self.graph_lookup = graph_lookup
        self.compositional_lookup = compositional_lookup
        self.fallback_lookup = fallback_lookup

    def _basis(self, request: AdaptiveReadRequest) -> VerifiedReadBasis:
        basis = self.verify_read_basis(request)
        if not isinstance(basis, VerifiedReadBasis) or not basis.verified:
            raise UnverifiedReadBasis(request.query_id)
        if basis.source_epoch != request.source_epoch or basis.graph_epoch != request.graph_epoch:
            raise StaleReadBasis(
                f'basis {basis.source_epoch}/{basis.graph_epoch} != request '
                f'{request.source_epoch}/{request.graph_epoch}'
            )
        if not basis.basis_id.strip() or not basis.derivation_hash.strip():
            raise UnverifiedReadBasis('basis identity/hash required')
        return basis

    @staticmethod
    def _attempt(
        attempts: list[RouteAttemptReceipt],
        mode: str,
        fn: Callable[[], Sequence[str] | str | None],
        *,
        sufficient_on_hit: bool,
    ) -> tuple[str, ...] | str | None:
        started = time.perf_counter_ns()
        try:
            value = fn()
        except Exception:
            latency = time.perf_counter_ns() - started
            attempts.append(
                RouteAttemptReceipt(
                    ordinal=len(attempts),
                    mode=mode,
                    status='ERROR',
                    result_count=0,
                    sufficient=False,
                    latency_ns=latency,
                )
            )
            raise
        latency = time.perf_counter_ns() - started
        if isinstance(value, str):
            hit = bool(value)
            count = 1 if hit else 0
        elif value is None:
            hit = False
            count = 0
        else:
            value = tuple(value)
            hit = bool(value)
            count = len(value)
        attempts.append(
            RouteAttemptReceipt(
                ordinal=len(attempts),
                mode=mode,
                status='HIT' if hit else 'MISS',
                result_count=count,
                sufficient=bool(hit and sufficient_on_hit),
                latency_ns=latency,
            )
        )
        return value

    def query(self, request: AdaptiveReadRequest) -> MeasuredAdaptiveReadReceipt:
        if not request.query_id.strip() or not request.text.strip():
            raise ValueError('query_id/text required')
        if request.limit <= 0 or request.limit > 128:
            raise ValueError('invalid limit')

        started = time.perf_counter_ns()
        basis = self._basis(request)
        attempts: list[RouteAttemptReceipt] = []
        resolved: str | None = None

        if request.exact_normalized_key:
            refs = self._attempt(
                attempts,
                'EXACT_INDEX_LOOKUP',
                lambda: self.exact_lookup(request.exact_normalized_key or '', basis, request.limit),
                sufficient_on_hit=True,
            )
            assert not isinstance(refs, str)
            if refs:
                return self._receipt(request, basis, 'EXACT_INDEX_LOOKUP', refs, None, True, started, attempts)

        refs = self._attempt(
            attempts,
            'VERIFIED_SEMANTIC_SUFFICIENCY_STOP',
            lambda: self.compiled_semantic_lookup(request.text, basis, request.limit),
            sufficient_on_hit=True,
        )
        assert not isinstance(refs, str)
        if refs:
            return self._receipt(
                request, basis, 'VERIFIED_SEMANTIC_SUFFICIENCY_STOP', refs, None, True, started, attempts
            )

        resolution = self._attempt(
            attempts,
            'ENTITY_RESOLUTION',
            lambda: self.resolve_entity(request.text, basis),
            sufficient_on_hit=False,
        )
        resolved = resolution if isinstance(resolution, str) and resolution else None

        if request.compositional:
            refs = self._attempt(
                attempts,
                'COMPOSITIONAL_PARETO_FRONTIER',
                lambda: self.compositional_lookup(request.text, basis, request.limit),
                sufficient_on_hit=True,
            )
            assert not isinstance(refs, str)
            if refs:
                return self._receipt(
                    request, basis, 'COMPOSITIONAL_PARETO_FRONTIER', refs, resolved, True, started, attempts
                )

        if resolved:
            refs = self._attempt(
                attempts,
                'ENTITY_RESOLVED_CLAYGRAPH',
                lambda: self.graph_lookup(resolved or '', request.text, basis, request.limit),
                sufficient_on_hit=True,
            )
            assert not isinstance(refs, str)
            if refs:
                return self._receipt(
                    request, basis, 'ENTITY_RESOLVED_CLAYGRAPH', refs, resolved, True, started, attempts
                )

        refs = self._attempt(
            attempts,
            'CONVENTIONAL_FALLBACK',
            lambda: self.fallback_lookup(request.text, basis, request.limit),
            sufficient_on_hit=False,
        )
        assert not isinstance(refs, str)
        return self._receipt(
            request,
            basis,
            'CONVENTIONAL_FALLBACK' if refs else 'MISS',
            refs,
            resolved,
            False,
            started,
            attempts,
        )

    @staticmethod
    def _receipt(
        request: AdaptiveReadRequest,
        basis: VerifiedReadBasis,
        mode: str,
        refs: Sequence[str],
        resolved: str | None,
        sufficient: bool,
        started: int,
        attempts: Sequence[RouteAttemptReceipt],
    ) -> MeasuredAdaptiveReadReceipt:
        bounded = tuple(refs[: request.limit])
        frozen_attempts = tuple(attempts)
        return MeasuredAdaptiveReadReceipt(
            query_id=request.query_id,
            query_hash=hashlib.sha256(request.text.encode()).hexdigest(),
            mode=mode,
            refs=bounded,
            resolved_logical_id=resolved,
            sufficient=sufficient,
            lexical_padding_used=False,
            source_epoch=request.source_epoch,
            graph_epoch=request.graph_epoch,
            read_basis_id=basis.basis_id,
            derivation_hash=basis.derivation_hash,
            latency_ns=time.perf_counter_ns() - started,
            attempts=frozen_attempts,
            route_trace_hash=_trace_hash(frozen_attempts),
        )


def aggregate_route_telemetry(receipts: Sequence[MeasuredAdaptiveReadReceipt]) -> dict[str, dict[str, float | int]]:
    """Aggregate deterministic runtime telemetry without making routing decisions.

    This intentionally returns measurements only. Any later cost-based planner must be a
    separately tested candidate and must preserve U14/U16 safety gates.
    """
    out: dict[str, dict[str, float | int]] = {}
    for receipt in receipts:
        for attempt in receipt.attempts:
            row = out.setdefault(
                attempt.mode,
                {
                    'attempts': 0,
                    'hits': 0,
                    'misses': 0,
                    'errors': 0,
                    'total_latency_ns': 0,
                    'total_result_count': 0,
                },
            )
            row['attempts'] = int(row['attempts']) + 1
            if attempt.status == 'HIT':
                row['hits'] = int(row['hits']) + 1
            elif attempt.status == 'MISS':
                row['misses'] = int(row['misses']) + 1
            elif attempt.status == 'ERROR':
                row['errors'] = int(row['errors']) + 1
            row['total_latency_ns'] = int(row['total_latency_ns']) + attempt.latency_ns
            row['total_result_count'] = int(row['total_result_count']) + attempt.result_count
    for row in out.values():
        n = max(1, int(row['attempts']))
        row['hit_rate'] = int(row['hits']) / n
        row['mean_latency_ns'] = int(row['total_latency_ns']) / n
        row['mean_result_count'] = int(row['total_result_count']) / n
    return out
