from tools.xeno_recursive_coordinator_scaling_acceptance_v1 import build_tree, leaf_packet, coordinator_summary, Lease, run


def test_scales_pass_core_invariants():
    result = run(8)
    assert result["pass"] is True
    assert result["whole_hcu_credit"] == 0
    assert result["physical_scale_credit"] == 0


def test_bounded_fanin_and_leaf_accounting():
    for n in (10, 100, 1000, 10000):
        r = build_tree(n, 8)
        assert r["max_observed_fanin"] <= 8
        assert r["root_leaf_count"] == n
        assert r["root_is_coordinator_write"] is True


def test_ordinary_nodes_are_read_only():
    assert all(leaf_packet(i).s1_write_intent is False for i in range(100))


def test_invalid_lease_rejected():
    try:
        coordinator_summary(Lease("bad", 1, "scope", False), [leaf_packet(0), leaf_packet(1)])
    except ValueError as exc:
        assert str(exc) == "COORDINATOR_LEASE_INVALID"
    else:
        raise AssertionError("invalid coordinator lease was accepted")


def test_recursive_compression_beats_leaf_raw_payload_at_large_scale():
    r = build_tree(10000, 8)
    assert r["root_hot_payload_bytes"] < r["root_raw_payload_bytes"]
    assert r["root_compression_ratio"] > 1.0
