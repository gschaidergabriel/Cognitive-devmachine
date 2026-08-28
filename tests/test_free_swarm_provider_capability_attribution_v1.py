from tools.free_swarm_provider_capability_attribution_v1 import counter_delta, parse_environ_names


def test_parse_environ_names_never_returns_values():
    raw = b"OPENROUTER_API_KEY=secret-value\0PATH=/bin\0GROQ_API_KEY=another-secret\0"
    assert parse_environ_names(raw) == ["GROQ_API_KEY", "OPENROUTER_API_KEY"]
    joined = " ".join(parse_environ_names(raw))
    assert "secret-value" not in joined
    assert "another-secret" not in joined


def test_parse_environ_names_ignores_unrelated_keys():
    raw = b"PATH=/bin\0HOME=/tmp\0SHELL=/bin/sh\0"
    assert parse_environ_names(raw) == []


def test_counter_delta_is_provider_scoped_and_signed():
    before = {"counters": {"openrouter": {"total_requests": 10, "total_success": 2, "total_429": 7, "total_errors": 1}}}
    after = {"counters": {"openrouter": {"total_requests": 13, "total_success": 2, "total_429": 10, "total_errors": 1}}}
    assert counter_delta(before, after) == {
        "openrouter": {"total_requests": 3, "total_success": 0, "total_429": 3, "total_errors": 0}
    }


def test_counter_delta_handles_new_provider_row_fail_visible():
    before = {"counters": {}}
    after = {"counters": {"mistral": {"total_requests": 1, "total_success": 0, "total_429": 1, "total_errors": 0}}}
    assert counter_delta(before, after)["mistral"]["total_requests"] == 1
