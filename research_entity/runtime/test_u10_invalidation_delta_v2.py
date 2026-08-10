from __future__ import annotations

from collections import defaultdict
import random

from u10_invalidation_delta_v2 import U10Depth3InvalidationIndexV2


def reach3(adj: dict[int, set[int]], anchor: int) -> frozenset[int]:
    seen = {anchor}
    frontier = {anchor}
    for _ in range(3):
        nxt: set[int] = set()
        for node in frontier:
            nxt.update(adj.get(node, ()))
        nxt -= seen
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return frozenset(seen)


def build(seed=9917, n=180, edge_count=900, anchor_count=24):
    rng = random.Random(seed)
    refs = [f"n:{i}" for i in range(n)]
    edges: set[tuple[int, int]] = set()
    while len(edges) < edge_count:
        u, v = rng.randrange(n), rng.randrange(n)
        if u != v:
            edges.add((u, v))
    anchors = tuple(sorted(rng.sample(range(n), anchor_count)))
    edge_refs = [(refs[u], refs[v]) for u, v in edges]
    return rng, refs, edges, anchors, edge_refs


def test_prepared_mask_matches_bfs_for_every_source():
    _, refs, _, anchors, edge_refs = build()
    prepared = U10Depth3InvalidationIndexV2(
        source_epoch=1, graph_epoch=1, semantic_refs=refs, forward_edges=edge_refs,
        active_anchor_refs=[refs[i] for i in anchors], mode="PREPARED_MASK",
    )
    bfs = U10Depth3InvalidationIndexV2(
        source_epoch=1, graph_epoch=1, semantic_refs=refs, forward_edges=edge_refs,
        active_anchor_refs=[refs[i] for i in anchors], mode="ON_DEMAND_BFS",
    )
    for ref in refs:
        a = set(prepared.affected_anchors_before_edge_mutation(
            ref, basis_source_epoch=1, basis_graph_epoch=1))
        b = set(bfs.affected_anchors_before_edge_mutation(
            ref, basis_source_epoch=1, basis_graph_epoch=1))
        assert a == b, (ref, a ^ b)


def test_both_modes_have_zero_false_negative_invalidations_over_1000_mutations():
    rng, refs, edges, anchors, edge_refs = build(seed=9918, n=220, edge_count=1100, anchor_count=28)
    prepared = U10Depth3InvalidationIndexV2(
        source_epoch=1, graph_epoch=1, semantic_refs=refs, forward_edges=edge_refs,
        active_anchor_refs=[refs[i] for i in anchors], mode="PREPARED_MASK",
    )
    bfs = U10Depth3InvalidationIndexV2(
        source_epoch=1, graph_epoch=1, semantic_refs=refs, forward_edges=edge_refs,
        active_anchor_refs=[refs[i] for i in anchors], mode="ON_DEMAND_BFS",
    )
    adj: dict[int, set[int]] = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)
    source_epoch = graph_epoch = 1

    for _ in range(1000):
        before = {a: reach3(adj, a) for a in anchors}
        if rng.random() < 0.5:
            while True:
                u, v = rng.randrange(len(refs)), rng.randrange(len(refs))
                if u != v and v not in adj.get(u, ()):
                    break
            op = "add_forward_edge"
        else:
            sources = [u for u, targets in adj.items() if targets]
            u = rng.choice(sources)
            v = rng.choice(tuple(adj[u]))
            op = "remove_forward_edge"

        predicted_prepared = set(prepared.affected_anchors_before_edge_mutation(
            refs[u], basis_source_epoch=source_epoch, basis_graph_epoch=graph_epoch))
        predicted_bfs = set(bfs.affected_anchors_before_edge_mutation(
            refs[u], basis_source_epoch=source_epoch, basis_graph_epoch=graph_epoch))
        assert predicted_prepared == predicted_bfs

        ns, ng = source_epoch + 1, graph_epoch + 1
        kwargs = dict(
            basis_source_epoch=source_epoch, basis_graph_epoch=graph_epoch,
            result_source_epoch=ns, result_graph_epoch=ng,
        )
        getattr(prepared, op)(refs[u], refs[v], **kwargs)
        getattr(bfs, op)(refs[u], refs[v], **kwargs)
        if op.startswith("add"):
            adj[u].add(v)
        else:
            adj[u].remove(v)

        after = {a: reach3(adj, a) for a in anchors}
        actually_changed = {refs[a] for a in anchors if before[a] != after[a]}
        assert actually_changed <= predicted_prepared, sorted(actually_changed - predicted_prepared)
        source_epoch, graph_epoch = ns, ng

    exact, bad = prepared.reverse.verify_exact()
    assert exact, bad[:10]


def test_modes_preserve_same_epoch_fail_closed_contract():
    _, refs, _, anchors, edge_refs = build(n=64, edge_count=160, anchor_count=8)
    for mode in ("PREPARED_MASK", "ON_DEMAND_BFS"):
        idx = U10Depth3InvalidationIndexV2(
            source_epoch=3, graph_epoch=5, semantic_refs=refs, forward_edges=edge_refs,
            active_anchor_refs=[refs[i] for i in anchors], mode=mode,
        )
        try:
            idx.affected_anchors_before_edge_mutation(
                refs[0], basis_source_epoch=2, basis_graph_epoch=5)
            assert False, "stale basis accepted"
        except ValueError:
            pass
