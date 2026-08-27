import copy
import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "tools" / "xeno_recursive_physical_scaling_bridge_acceptance_v1.py"
spec = importlib.util.spec_from_file_location("bridge", P)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def receipt():
    packets = []
    for i in range(10):
        d = f"{i+1:064x}"
        packets.append({
            "packet_digest": d,
            "source_kind": "ORDINARY_NODE",
            "s1_write_intent": False,
            "raw_payload_bytes": 1024,
            "hot_payload_bytes": 128,
        })
    return {
        "schema": "XENO_PHYSICAL_GRID10_FUSED_ACCEPTANCE/v1",
        "pass": True,
        "physical_packet_evidence": packets,
        "coordinator_consumed_packet_digests": [p["packet_digest"] for p in packets],
    }


def test_bridge_passes_and_bounds_fanin():
    out = mod.bridge(receipt(), 4)
    assert out["pass"] is True
    assert out["root"]["leaf_count"] == 10
    assert out["max_fanin"] == 4


def test_tampered_fanin_set_rejected():
    r = receipt()
    r["coordinator_consumed_packet_digests"][0] = "f" * 64
    try:
        mod.bridge(r, 4)
    except ValueError as exc:
        assert str(exc) == "PHYSICAL_TO_RECURSIVE_PACKET_SET_MISMATCH"
    else:
        raise AssertionError("tampered packet set passed")


def test_ordinary_write_intent_rejected():
    r = receipt()
    r["physical_packet_evidence"][3]["s1_write_intent"] = True
    try:
        mod.bridge(r, 4)
    except ValueError as exc:
        assert str(exc) == "ORDINARY_NODE_WRITE_INTENT_FORBIDDEN"
    else:
        raise AssertionError("ordinary-node write intent passed")


def test_duplicate_packet_digest_rejected():
    r = receipt()
    r["physical_packet_evidence"][1]["packet_digest"] = r["physical_packet_evidence"][0]["packet_digest"]
    r["coordinator_consumed_packet_digests"][1] = r["coordinator_consumed_packet_digests"][0]
    try:
        mod.bridge(r, 4)
    except ValueError as exc:
        assert str(exc) == "PHYSICAL_PACKET_DIGEST_CARDINALITY_INVALID"
    else:
        raise AssertionError("duplicate digest passed")


def test_nonpass_physical_receipt_rejected():
    r = receipt()
    r["pass"] = False
    try:
        mod.bridge(r, 4)
    except ValueError as exc:
        assert str(exc) == "PHYSICAL_RECEIPT_NOT_PASS"
    else:
        raise AssertionError("nonpass physical receipt passed")
