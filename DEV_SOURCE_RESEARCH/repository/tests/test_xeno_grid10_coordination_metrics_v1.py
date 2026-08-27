import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "tools" / "xeno_grid10_coordination_metrics_v1.py"
S = importlib.util.spec_from_file_location("m", P)
m = importlib.util.module_from_spec(S)
assert S.loader
S.loader.exec_module(m)


def d(ch):
    return ch * 64


def good_events():
    out = []
    for i, ch in enumerate("abcdefghij"):
        out.append({"kind":"NODE_RESULT","node_id":f"n{i}","packet_digest":d(ch),"emitted_ns":1000+i*10,"payload_bytes":100})
        out.append({"kind":"COORDINATOR_RECV","coordinator_id":"c0","packet_digest":d(ch),"received_ns":2000+i*10})
    out.append({"kind":"S1_COMMIT","coordinator_id":"c0","input_packet_digests":[d(ch) for ch in "abcdefghij"],"started_ns":3000,"committed_ns":5000,"summary_bytes":250,"cas_attempts":2,"cas_conflicts":1})
    return out


def test_good_trace_measures_without_credit():
    r = m.measure(good_events())
    assert r["pass"] is True
    assert r["counts"]["nodes"] == 10
    assert r["fanin"]["max"] == 10
    assert r["compression"]["aggregate_ratio_raw_over_summary"] == 4.0
    assert r["contention"]["conflict_rate_per_attempt"] == 0.5
    assert r["physical_grid10_credit"] == 0
    assert r["whole_hcu_credit"] == 0


def test_commit_unknown_packet_fails_closed():
    ev = good_events()
    ev[-1]["input_packet_digests"][0] = d("z")
    try:
        m.measure(ev)
    except ValueError as exc:
        assert str(exc).startswith("COMMIT_UNKNOWN_INPUT")
    else:
        assert False


def test_receive_without_emit_fails_closed():
    ev = good_events()
    ev.insert(0,{"kind":"COORDINATOR_RECV","coordinator_id":"c0","packet_digest":d("z"),"received_ns":1})
    try:
        m.measure(ev)
    except ValueError as exc:
        assert str(exc).startswith("RECEIVE_WITHOUT_EMIT")
    else:
        assert False


def test_duplicate_consumption_is_not_pass():
    ev = good_events()
    ev.append({"kind":"S1_COMMIT","coordinator_id":"c1","input_packet_digests":[d("a")],"started_ns":6000,"committed_ns":7000,"summary_bytes":50,"cas_attempts":1,"cas_conflicts":0})
    r = m.measure(ev)
    assert r["pass"] is False
    assert r["tests"]["no_packet_consumed_by_multiple_commits"] is False


def test_unconsumed_packet_is_not_pass():
    ev = good_events()
    ev[-1]["input_packet_digests"] = ev[-1]["input_packet_digests"][:-1]
    r = m.measure(ev)
    assert r["pass"] is False
    assert r["tests"]["all_emitted_packets_consumed"] is False


def test_negative_timing_fails_closed():
    ev = good_events()
    ev[-1]["committed_ns"] = 2999
    try:
        m.measure(ev)
    except ValueError as exc:
        assert str(exc) == "NEGATIVE_COMMIT_LATENCY"
    else:
        assert False
