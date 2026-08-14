from __future__ import annotations

import random

from semantic_reachability_delta_v1 import BoundedReachability2, StaleReachabilityEpoch


def random_fixture(seed: int = 260810, n: int = 96, edge_count: int = 320):
    rng = random.Random(seed)
    refs = [f"s:{i}" for i in range(n)]
    edges: set[tuple[str, str]] = set()
    while len(edges) < edge_count:
        a = rng.randrange(n)
        b = rng.randrange(n)
        if a != b:
            edges.add((refs[a], refs[b]))
    return rng, refs, edges


def test_initial_projection_is_exact():
    _, refs, edges = random_fixture()
    idx = BoundedReachability2(source_epoch=1, graph_epoch=1, semantic_refs=refs, edges=edges)
    assert idx.verify_exact() == (True, ())


def test_alternative_path_survives_revocation():
    refs = ["a", "b", "c", "d"]
    idx = BoundedReachability2(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        edges=[("a", "b"), ("b", "d"), ("a", "c"), ("c", "d")],
    )
    assert "d" in idx.prepared_refs(["a"], basis_source_epoch=1, basis_graph_epoch=1)
    idx.remove_edge(
        "b", "d",
        basis_source_epoch=1,
        basis_graph_epoch=1,
        result_source_epoch=2,
        result_graph_epoch=2,
    )
    # a->c->d is still valid even though a->b->d was revoked.
    assert "d" in idx.prepared_refs(["a"], basis_source_epoch=2, basis_graph_epoch=2)
    assert "d" not in idx.prepared_refs(["b"], basis_source_epoch=2, basis_graph_epoch=2)
    assert idx.verify_exact() == (True, ())


def test_5000_mixed_add_remove_deltas_remain_exact():
    rng, refs, edges = random_fixture(seed=260811, n=128, edge_count=480)
    idx = BoundedReachability2(source_epoch=1, graph_epoch=1, semantic_refs=refs, edges=edges)
    source_epoch = graph_epoch = 1

    for step in range(5000):
        if rng.random() < 0.55:
            while True:
                u = rng.randrange(len(refs))
                v = rng.randrange(len(refs))
                if u != v and v not in idx.adj.get(u, ()):
                    break
            next_source = source_epoch + 1
            next_graph = graph_epoch + 1
            idx.add_edge(
                refs[u], refs[v],
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=next_source,
                result_graph_epoch=next_graph,
            )
        else:
            sources = [u for u, targets in idx.adj.items() if targets]
            u = rng.choice(sources)
            v = rng.choice(tuple(idx.adj[u]))
            next_source = source_epoch + 1
            next_graph = graph_epoch + 1
            idx.remove_edge(
                refs[u], refs[v],
                basis_source_epoch=source_epoch,
                basis_graph_epoch=graph_epoch,
                result_source_epoch=next_source,
                result_graph_epoch=next_graph,
            )
        source_epoch = next_source
        graph_epoch = next_graph

        if step % 100 == 0 or step == 4999:
            exact, bad = idx.verify_exact()
            assert exact, bad[:10]


def test_stale_reader_and_stale_mutation_fail_closed():
    _, refs, edges = random_fixture(n=32, edge_count=70)
    idx = BoundedReachability2(source_epoch=7, graph_epoch=9, semantic_refs=refs, edges=edges)

    try:
        idx.prepared_refs([refs[0]], basis_source_epoch=6, basis_graph_epoch=9)
        assert False, "stale read accepted"
    except StaleReachabilityEpoch:
        pass

    try:
        idx.add_edge(
            refs[0], refs[1],
            basis_source_epoch=7,
            basis_graph_epoch=8,
            result_source_epoch=8,
            result_graph_epoch=10,
        )
        assert False, "stale mutation accepted"
    except StaleReachabilityEpoch:
        pass


def test_identity_is_never_deleted_by_cycle_support_changes():
    refs = ["a", "b"]
    idx = BoundedReachability2(
        source_epoch=1,
        graph_epoch=1,
        semantic_refs=refs,
        edges=[("a", "b"), ("b", "a")],
    )
    idx.remove_edge(
        "a", "b",
        basis_source_epoch=1,
        basis_graph_epoch=1,
        result_source_epoch=2,
        result_graph_epoch=2,
    )
    assert idx.prepared_refs(["a"], basis_source_epoch=2, basis_graph_epoch=2) == ("a",)
    assert idx.verify_exact() == (True, ())
