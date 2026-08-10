from __future__ import annotations

from collections import defaultdict, deque

from semantic_access_pulse_v12 import AccessPath, SegmentedPulseProjection
from u10_invalidation_delta_v2 import U10Depth3InvalidationIndexV2
from u12_bounded_edge_pulse_adapter_v1 import (
    BoundedEdgeImpactProof,
    BoundedImpactProofError,
    advance_invalidation_index,
    apply_u12_bounded_edge_pulse,
    build_bounded_edge_impact_proof,
)


class TinyGraph:
    def __init__(self, refs, edges):
        self.refs = tuple(refs)
        self.adj = defaultdict(set)
        for u, v in edges:
            self.adj[u].add(v)

    def add(self, u, v):
        self.adj[u].add(v)

    def remove(self, u, v):
        self.adj[u].remove(v)

    def paths_for_seed(self, seed: str):
        # Deterministic best-hop path per target, enough to test U12 segmented equivalence.
        best = {seed: (seed,)}
        q = deque([(seed, (seed,))])
        while q:
            node, path = q.popleft()
            if len(path) - 1 >= 3:
                continue
            for target in sorted(self.adj.get(node, ())):
                if target in path:
                    continue
                candidate = path + (target,)
                old = best.get(target)
                if old is None or (len(candidate), candidate) < (len(old), old):
                    best[target] = candidate
                    q.append((target, candidate))
        ordered = sorted(best.items(), key=lambda kv: (len(kv[1]) - 1, kv[0]))
        out = []
        for rank, (target, path) in enumerate(ordered, start=1):
            out.append(AccessPath(
                target_record_id=target,
                target_logical_id=target,
                path_rank=rank,
                hop_count=len(path) - 1,
                path_weight=1.0 / max(1, len(path)),
                authority_rank=1.0,
                path_clay="->".join(path),
                dependencies=tuple(path),
            ))
        return out


def fixture():
    refs = ["a", "b", "c", "d"] + [f"s{i}" for i in range(1, 8)]
    seeds = ["a"] + [f"s{i}" for i in range(1, 8)]
    edges = [("a", "b"), ("b", "c"), ("s1", "s2"), ("s3", "s4")]
    graph = TinyGraph(refs, edges)
    index = U10Depth3InvalidationIndexV2(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        forward_edges=edges,
        active_anchor_refs=seeds,
        mode="ON_DEMAND_BFS",
    )
    return refs, seeds, graph, index


def full_snapshot(graph: TinyGraph, seeds, source_epoch, graph_epoch):
    full = SegmentedPulseProjection()
    try:
        full.bootstrap(
            event_id=f"full-{source_epoch}-{graph_epoch}",
            source_epoch=source_epoch,
            graph_epoch=graph_epoch,
            seeds=seeds,
            recompute_seed=graph.paths_for_seed,
        )
        return full.snapshot()
    finally:
        full.close()


def test_bounded_edge_add_uses_segmented_pulse_and_equals_full_rebuild():
    _refs, seeds, graph, index = fixture()
    projection = SegmentedPulseProjection()
    try:
        projection.bootstrap(
            event_id="boot", source_epoch=1, graph_epoch=1,
            seeds=seeds, recompute_seed=graph.paths_for_seed,
        )
        proof = build_bounded_edge_impact_proof(
            index,
            event_id="add-c-d",
            operation="ADD",
            forward_source_ref="c",
            forward_target_ref="d",
            basis_source_epoch=1,
            basis_graph_epoch=1,
            result_source_epoch=2,
            result_graph_epoch=2,
        )
        assert proof.affected_seed_ids == ("a",)

        graph.add("c", "d")
        advance_invalidation_index(index, proof)
        receipt = apply_u12_bounded_edge_pulse(
            projection,
            proof,
            recompute_seed=graph.paths_for_seed,
            recompute_all_seeds=lambda: seeds,
        )
        assert receipt.original_operation == "ADD"
        assert receipt.u12_change_class == "LOCAL_REWRITE"
        assert receipt.pulse.mode == "SEGMENTED_INCREMENTAL_PULSE"
        assert receipt.pulse.affected_seed_count == 1
        assert receipt.pulse.reused_segment_count >= len(seeds) - 1
        assert projection.snapshot() == full_snapshot(graph, seeds, 2, 2)
    finally:
        projection.close()


def test_bounded_edge_remove_uses_native_edge_remove_and_equals_full_rebuild():
    _refs, seeds, graph, index = fixture()
    projection = SegmentedPulseProjection()
    try:
        projection.bootstrap(
            event_id="boot", source_epoch=1, graph_epoch=1,
            seeds=seeds, recompute_seed=graph.paths_for_seed,
        )
        proof = build_bounded_edge_impact_proof(
            index,
            event_id="remove-b-c",
            operation="REMOVE",
            forward_source_ref="b",
            forward_target_ref="c",
            basis_source_epoch=1,
            basis_graph_epoch=1,
            result_source_epoch=2,
            result_graph_epoch=2,
        )
        assert proof.affected_seed_ids == ("a",)

        graph.remove("b", "c")
        advance_invalidation_index(index, proof)
        receipt = apply_u12_bounded_edge_pulse(
            projection,
            proof,
            recompute_seed=graph.paths_for_seed,
            recompute_all_seeds=lambda: seeds,
        )
        assert receipt.u12_change_class == "EDGE_REMOVE"
        assert receipt.pulse.mode == "SEGMENTED_INCREMENTAL_PULSE"
        assert projection.snapshot() == full_snapshot(graph, seeds, 2, 2)
    finally:
        projection.close()


def test_tampered_proof_is_rejected_before_u12_effect():
    _refs, seeds, graph, index = fixture()
    projection = SegmentedPulseProjection()
    try:
        projection.bootstrap(
            event_id="boot", source_epoch=1, graph_epoch=1,
            seeds=seeds, recompute_seed=graph.paths_for_seed,
        )
        proof = build_bounded_edge_impact_proof(
            index,
            event_id="tamper",
            operation="ADD",
            forward_source_ref="c",
            forward_target_ref="d",
            basis_source_epoch=1,
            basis_graph_epoch=1,
            result_source_epoch=2,
            result_graph_epoch=2,
        )
        tampered = BoundedEdgeImpactProof(**{
            **proof.__dict__,
            "affected_seed_ids": (),
        })
        try:
            apply_u12_bounded_edge_pulse(
                projection, tampered,
                recompute_seed=graph.paths_for_seed,
                recompute_all_seeds=lambda: seeds,
            )
            assert False, "tampered proof accepted"
        except BoundedImpactProofError:
            pass
        assert projection.head_basis()[:2] == (1, 1)
    finally:
        projection.close()
