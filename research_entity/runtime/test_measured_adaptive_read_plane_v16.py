from __future__ import annotations

import unittest

from .adaptive_semantic_read_plane_v14 import (
    AdaptiveReadRequest,
    AdaptiveSemanticReadPlaneV14,
    VerifiedReadBasis,
    StaleReadBasis,
)
from .measured_adaptive_read_plane_v16 import (
    MeasuredAdaptiveSemanticReadPlaneV16,
    aggregate_route_telemetry,
)


def basis_for(r: AdaptiveReadRequest) -> VerifiedReadBasis:
    return VerifiedReadBasis(
        basis_id=f"basis:{r.source_epoch}:{r.graph_epoch}",
        source_epoch=r.source_epoch,
        graph_epoch=r.graph_epoch,
        derivation_hash="d" * 64,
        verified=True,
    )


def exact(key, basis, limit):
    del basis, limit
    return ("exact:1",) if key == "known-key" else ()


def compiled(text, basis, limit):
    del basis, limit
    return ("compiled:1", "compiled:2") if "compiled" in text else ()


def resolve(text, basis):
    del basis
    return "entity:1" if "entity" in text else None


def graph(logical_id, text, basis, limit):
    del basis, limit
    return ("graph:1", "graph:2") if logical_id == "entity:1" and "graph" in text else ()


def composition(text, basis, limit):
    del basis, limit
    return ("pareto:1",) if "compose" in text else ()


def fallback(text, basis, limit):
    del basis, limit
    return ("fallback:1",) if "fallback" in text else ()


def planes():
    kwargs = dict(
        verify_read_basis=basis_for,
        exact_lookup=exact,
        compiled_semantic_lookup=compiled,
        resolve_entity=resolve,
        graph_lookup=graph,
        compositional_lookup=composition,
        fallback_lookup=fallback,
    )
    return AdaptiveSemanticReadPlaneV14(**kwargs), MeasuredAdaptiveSemanticReadPlaneV16(**kwargs)


class MeasuredAdaptiveReadPlaneV16Tests(unittest.TestCase):
    def test_final_semantics_match_v14_across_routes(self):
        v14, v16 = planes()
        cases = [
            AdaptiveReadRequest("q1", "whatever", 7, 9, exact_normalized_key="known-key"),
            AdaptiveReadRequest("q2", "compiled question", 7, 9),
            AdaptiveReadRequest("q3", "entity compose", 7, 9, compositional=True),
            AdaptiveReadRequest("q4", "entity graph", 7, 9),
            AdaptiveReadRequest("q5", "fallback unknown", 7, 9),
            AdaptiveReadRequest("q6", "total miss", 7, 9),
            AdaptiveReadRequest("q7", "entity fallback", 7, 9),
            AdaptiveReadRequest("q8", "whatever", 7, 9, exact_normalized_key="missing-key"),
        ]
        for request in cases:
            with self.subTest(request=request.query_id):
                old = v14.query(request)
                new = v16.query(request)
                self.assertEqual(old.query_id, new.query_id)
                self.assertEqual(old.query_hash, new.query_hash)
                self.assertEqual(old.mode, new.mode)
                self.assertEqual(old.refs, new.refs)
                self.assertEqual(old.resolved_logical_id, new.resolved_logical_id)
                self.assertEqual(old.sufficient, new.sufficient)
                self.assertEqual(old.lexical_padding_used, new.lexical_padding_used)
                self.assertEqual(old.source_epoch, new.source_epoch)
                self.assertEqual(old.graph_epoch, new.graph_epoch)
                self.assertEqual(old.read_basis_id, new.read_basis_id)
                self.assertEqual(old.derivation_hash, new.derivation_hash)
                self.assertTrue(new.attempts)

    def test_trace_hash_excludes_wall_clock_latency(self):
        _, v16 = planes()
        request = AdaptiveReadRequest("q", "entity graph", 3, 4)
        a = v16.query(request)
        b = v16.query(request)
        self.assertEqual(a.route_trace_hash, b.route_trace_hash)
        self.assertEqual(
            [(x.mode, x.status, x.result_count, x.sufficient) for x in a.attempts],
            [(x.mode, x.status, x.result_count, x.sufficient) for x in b.attempts],
        )

    def test_sufficiency_stop_records_no_padding(self):
        _, v16 = planes()
        receipt = v16.query(AdaptiveReadRequest("q", "compiled entity graph fallback", 1, 1))
        self.assertEqual("VERIFIED_SEMANTIC_SUFFICIENCY_STOP", receipt.mode)
        self.assertEqual(1, len(receipt.attempts))
        self.assertEqual("HIT", receipt.attempts[0].status)
        self.assertTrue(receipt.attempts[0].sufficient)
        self.assertFalse(receipt.lexical_padding_used)

    def test_entity_resolution_miss_is_explicit_attempt(self):
        _, v16 = planes()
        receipt = v16.query(AdaptiveReadRequest("q", "fallback", 1, 1))
        modes = [x.mode for x in receipt.attempts]
        self.assertEqual(
            ["VERIFIED_SEMANTIC_SUFFICIENCY_STOP", "ENTITY_RESOLUTION", "CONVENTIONAL_FALLBACK"],
            modes,
        )
        self.assertEqual("MISS", receipt.attempts[1].status)
        self.assertEqual("HIT", receipt.attempts[2].status)

    def test_stale_basis_fails_before_any_mechanism(self):
        called = []
        def stale_basis(r):
            return VerifiedReadBasis("b", r.source_epoch - 1, r.graph_epoch, "h", True)
        def unexpected(*args):
            called.append(args)
            return ()
        v16 = MeasuredAdaptiveSemanticReadPlaneV16(
            verify_read_basis=stale_basis,
            exact_lookup=unexpected,
            compiled_semantic_lookup=unexpected,
            resolve_entity=lambda *args: called.append(args) or None,
            graph_lookup=unexpected,
            compositional_lookup=unexpected,
            fallback_lookup=unexpected,
        )
        with self.assertRaises(StaleReadBasis):
            v16.query(AdaptiveReadRequest("q", "text", 8, 9, exact_normalized_key="x"))
        self.assertEqual([], called)

    def test_mechanism_error_is_not_laundered_into_miss(self):
        def explode(*args):
            raise RuntimeError("boom")
        v16 = MeasuredAdaptiveSemanticReadPlaneV16(
            verify_read_basis=basis_for,
            exact_lookup=exact,
            compiled_semantic_lookup=explode,
            resolve_entity=resolve,
            graph_lookup=graph,
            compositional_lookup=composition,
            fallback_lookup=fallback,
        )
        with self.assertRaisesRegex(RuntimeError, "boom"):
            v16.query(AdaptiveReadRequest("q", "text", 1, 1))

    def test_aggregate_telemetry_separates_hit_and_miss_cost(self):
        _, v16 = planes()
        receipts = [
            v16.query(AdaptiveReadRequest("q1", "compiled", 1, 1)),
            v16.query(AdaptiveReadRequest("q2", "entity graph", 1, 1)),
            v16.query(AdaptiveReadRequest("q3", "fallback", 1, 1)),
        ]
        agg = aggregate_route_telemetry(receipts)
        self.assertEqual(3, agg["VERIFIED_SEMANTIC_SUFFICIENCY_STOP"]["attempts"])
        self.assertEqual(1, agg["VERIFIED_SEMANTIC_SUFFICIENCY_STOP"]["hits"])
        self.assertEqual(2, agg["VERIFIED_SEMANTIC_SUFFICIENCY_STOP"]["misses"])
        self.assertEqual(2, agg["ENTITY_RESOLUTION"]["attempts"])
        self.assertEqual(1, agg["ENTITY_RESOLUTION"]["hits"])
        self.assertEqual(1, agg["ENTITY_RESOLUTION"]["misses"])
        self.assertGreaterEqual(agg["ENTITY_RESOLUTION"]["mean_latency_ns"], 0)


if __name__ == "__main__":
    unittest.main()
