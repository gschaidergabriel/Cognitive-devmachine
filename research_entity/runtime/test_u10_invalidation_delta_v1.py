from __future__ import annotations

from collections import defaultdict
import random

from u10_invalidation_delta_v1 import U10Depth3InvalidationIndex


def reach3(adj: dict[str, set[str]], anchor: str) -> frozenset[str]:
    seen = {anchor}
    frontier = {anchor}
    for _ in range(3):
        nxt: set[str] = set()
        for node in frontier:
            nxt.update(adj.get(node, ()))
        nxt -= seen
        seen |= nxt
        frontier = nxt
        if not frontier:
            break
    return frozenset(seen)


def test_invalidation_frontier_has_no_false_negatives_over_1000_mixed_mutations():
    rng = random.Random(73419)
    refs = [f"n:{i}" for i in range(220)]
    edges: set[tuple[str, str]] = set()
    while len(edges) < 1100:
        u = rng.choice(refs)
        v = rng.choice(refs)
        if u != v:
            edges.add((u, v))

    anchors = tuple(sorted(rng.sample(refs, 24)))
    adj: dict[str, set[str]] = defaultdict(set)
    for u, v in edges:
        adj[u].add(v)

    idx = U10Depth3InvalidationIndex(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        forward_edges=edges,
        active_anchor_refs=anchors,
    )
    source_epoch = graph_epoch = 1

    for _step in range(1000):
        before = {a: reach3(adj, a) for a in anchors}
        if rng.random() < 0.5:
            while True:
                u = rng.choice(refs)
                v = rng.choice(refs)
                if u != v and v not in adj.get(u, ()):
                    break
            ns, ng = source_epoch + 1, graph_epoch + 1
            receipt = idx.add_forward_edge(
                u, v,
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=ns,
                result_graph_epoch=ng,
            )
            adj[u].add(v)
        else:
            sources = [u for u, targets in adj.items() if targets]
            u = rng.choice(sources)
            v = rng.choice(tuple(adj[u]))
            ns, ng = source_epoch + 1, graph_epoch + 1
            receipt = idx.remove_forward_edge(
                u, v,
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=ns,
                result_graph_epoch=ng,
            )
            adj[u].remove(v)

        after = {a: reach3(adj, a) for a in anchors}
        actually_changed = {a for a in anchors if before[a] != after[a]}
        predicted = set(receipt.affected_anchor_refs)
        assert actually_changed <= predicted, (u, v, sorted(actually_changed - predicted))
        assert receipt.reusable_anchor_count == len(anchors) - len(predicted)
        source_epoch, graph_epoch = ns, ng

    exact, bad = idx.reverse.verify_exact()
    assert exact, bad[:10]


def test_unrelated_anchor_is_reusable():
    refs = ["a", "u", "v", "x", "z"]
    idx = U10Depth3InvalidationIndex(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        forward_edges=[("a", "u"), ("x", "z")],
        active_anchor_refs=["a", "x"],
    )
    receipt = idx.add_forward_edge(
        "u", "v",
        basis_source_epoch=1,
        basis_graph_epoch=1,
        result_source_epoch=2,
        result_graph_epoch=2,
    )
    assert receipt.affected_anchor_refs == ("a",)
    assert receipt.reusable_anchor_count == 1
