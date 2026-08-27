from __future__ import annotations

import copy
import importlib.util
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "xeno_recursive_physical_scaling_bridge_acceptance_v2.py"
spec = importlib.util.spec_from_file_location("bridge_v2", MODULE)
bridge_v2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(bridge_v2)


def fixture() -> dict:
    digests = [f"{i:064x}" for i in range(1, 11)]
    return {
        "schema": bridge_v2.PHYSICAL_SCHEMA,
        "pass": True,
        "tests": {name: True for name in bridge_v2.REQUIRED_PHYSICAL_TESTS},
        "cohort_manifest": {
            "schema": "GRID10_FUSED_COHORT_MANIFEST/v1",
            "members": [
                {"node_id": f"x{i:02d}", "pid": 1000 + i, "packet_digest": digest}
                for i, digest in enumerate(digests, 1)
            ],
            "all_alive_at_barrier": True,
        },
        "receipt": {
            "packet_digests": list(reversed(digests)),
            "canonical_truth": False,
            "effect_authority": False,
        },
        "authority_boundary": {
            "ordinary_node_s1_write": False,
            "coordinator_only_s1_write": True,
        },
    }


def assert_reject(mutator, expected: str) -> None:
    obj = fixture()
    mutator(obj)
    try:
        bridge_v2.bridge(obj)
    except ValueError as exc:
        assert str(exc) == expected
    else:
        raise AssertionError(f"expected {expected}")


def test_exact_physical_packet_set_becomes_recursive_leaves() -> None:
    result = bridge_v2.bridge(fixture(), max_fanin=4)
    assert result["pass"] is True
    assert result["root"]["leaf_count"] == 10
    assert result["tests"]["bounded_recursive_fanin"] is True
    assert result["measurement_boundary"]["compression_ratio_measured_here"] is False


def test_ordinary_node_nonwriting_must_be_proven() -> None:
    assert_reject(
        lambda x: x["tests"].__setitem__("P2_ORDINARY_RESULTS_NONWRITING", False),
        "PHYSICAL_REQUIRED_TEST_NOT_PASS:P2_ORDINARY_RESULTS_NONWRITING",
    )


def test_tampered_manifest_packet_set_rejected() -> None:
    assert_reject(
        lambda x: x["cohort_manifest"]["members"][0].__setitem__("packet_digest", "f" * 64),
        "PHYSICAL_TO_RECURSIVE_PACKET_SET_MISMATCH",
    )


def test_duplicate_manifest_packet_digest_rejected() -> None:
    def mutate(x: dict) -> None:
        x["cohort_manifest"]["members"][1]["packet_digest"] = x["cohort_manifest"]["members"][0]["packet_digest"]
    assert_reject(mutate, "PHYSICAL_PACKET_DIGEST_CARDINALITY_INVALID")


def test_coordinator_cannot_mint_truth_or_effect_authority() -> None:
    assert_reject(
        lambda x: x["receipt"].__setitem__("canonical_truth", True),
        "COORDINATOR_CANONICAL_TRUTH_FORBIDDEN",
    )
    assert_reject(
        lambda x: x["receipt"].__setitem__("effect_authority", True),
        "COORDINATOR_EFFECT_AUTHORITY_FORBIDDEN",
    )


def test_authority_boundary_cannot_grant_worker_write() -> None:
    assert_reject(
        lambda x: x["authority_boundary"].__setitem__("ordinary_node_s1_write", True),
        "ORDINARY_NODE_WRITE_AUTHORITY_FORBIDDEN",
    )


def test_invalid_recursive_coordinator_lease_fails_closed() -> None:
    result = bridge_v2.bridge(fixture())
    assert result["tests"]["invalid_recursive_lease_fails_closed"] is True
