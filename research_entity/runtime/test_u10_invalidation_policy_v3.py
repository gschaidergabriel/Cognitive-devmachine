from u10_invalidation_policy_v3 import InvalidationModeProfile, choose_invalidation_mode


def measured_profile(**overrides):
    values = dict(
        bfs_lookup_ms=0.007421,
        bfs_update_ms=0.000491,
        prepared_lookup_ms=0.000601,
        prepared_update_ms=0.012919,
        prepared_build_ms=128.368954,
        prepared_extra_bytes=36_477_456,
        expected_reads_per_mutation=1.0,
        expected_mutations_per_prepared_build=1000.0,
        memory_budget_bytes=128 * 1024 * 1024,
    )
    values.update(overrides)
    return InvalidationModeProfile(**values)


def test_current_single_invalidation_read_regime_selects_bfs():
    decision = choose_invalidation_mode(measured_profile())
    assert decision.mode == "ON_DEMAND_BFS"
    assert decision.bfs_expected_ms_per_mutation < decision.prepared_expected_ms_per_mutation
    assert decision.latency_break_even_reads_per_mutation > 20


def test_many_reads_and_long_build_amortization_can_select_prepared():
    decision = choose_invalidation_mode(measured_profile(
        expected_reads_per_mutation=100,
        expected_mutations_per_prepared_build=100_000,
    ))
    assert decision.mode == "PREPARED_MASK"
    assert decision.prepared_expected_ms_per_mutation < decision.bfs_expected_ms_per_mutation


def test_memory_budget_can_force_low_memory_bfs_even_when_latency_prefers_prepared():
    decision = choose_invalidation_mode(measured_profile(
        expected_reads_per_mutation=100,
        expected_mutations_per_prepared_build=100_000,
        memory_budget_bytes=8 * 1024 * 1024,
    ))
    assert decision.mode == "ON_DEMAND_BFS"
    assert not decision.memory_admissible


def test_invalid_profile_is_rejected():
    try:
        choose_invalidation_mode(measured_profile(expected_mutations_per_prepared_build=0))
        assert False, "invalid amortization accepted"
    except ValueError:
        pass
