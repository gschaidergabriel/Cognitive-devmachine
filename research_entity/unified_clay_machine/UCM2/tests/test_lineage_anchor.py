from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from lineage_anchor import LineageAnchor, assess_stream_against_anchor  # noqa: E402

ROOT = "UCM2_CORE"


def event_hash(epoch, event_type, object_id, payload, prev_hash, created_at):
    raw = json.dumps(
        [epoch, event_type, object_id, payload, prev_hash, created_at],
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(raw.encode()).hexdigest()


def append_event(stream, event_type, object_id, payload):
    seq = len(stream) + 1
    epoch = seq - 1
    prev_hash = stream[-1]["event_hash"] if stream else ""
    created_at = f"2026-08-15T13:00:{seq:02d}+00:00"
    digest = event_hash(epoch, event_type, object_id, payload, prev_hash, created_at)
    stream.append({
        "seq": seq,
        "epoch": epoch,
        "event_type": event_type,
        "object_id": object_id,
        "payload": payload,
        "prev_hash": prev_hash,
        "event_hash": digest,
        "created_at": created_at,
    })


def verify(stream):
    prev = ""
    for index, event in enumerate(stream, start=1):
        assert int(event["seq"]) == index
        assert int(event["epoch"]) == index - 1
        assert event["prev_hash"] == prev
        expected = event_hash(
            int(event["epoch"]), event["event_type"], event["object_id"],
            event["payload"], event["prev_hash"], event["created_at"],
        )
        if expected != event["event_hash"]:
            raise RuntimeError("EVENT_HASH_MISMATCH")
        prev = expected
    return prev


def rehash_from(stream, index):
    prev = stream[index - 1]["event_hash"] if index else ""
    for event in stream[index:]:
        event["prev_hash"] = prev
        event["event_hash"] = event_hash(
            int(event["epoch"]), event["event_type"], event["object_id"],
            event["payload"], event["prev_hash"], event["created_at"],
        )
        prev = event["event_hash"]


def expect_runtime_error(code, fn):
    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == code, (str(exc), code)
    else:
        raise AssertionError(f"expected {code}")


def main():
    stream = []
    append_event(stream, "BOOTSTRAP_ROOT", ROOT, {
        "object_id": ROOT, "root_module": ROOT,
        "kind": "clay_machine_key_module", "status": "ACTIVE",
        "payload": {"identity": "ClayMachine2"}, "version": 1, "updated_at": "t0",
    })
    append_event(stream, "UPSERT", "world.main", {
        "object_id": "world.main", "root_module": ROOT,
        "kind": "world_model", "status": "ACTIVE",
        "payload": {"main_repo": "trusted-main"}, "version": 1, "updated_at": "t1",
    })
    append_event(stream, "UPSERT", "wiki.ucm", {
        "object_id": "wiki.ucm", "root_module": ROOT,
        "kind": "wiki", "status": "ACTIVE",
        "payload": {"summary": "one root"}, "version": 1, "updated_at": "t2",
    })
    verify(stream)

    anchor = LineageAnchor(
        anchor_id="owner-recovery-anchor-g7",
        root_module=ROOT,
        seq=3,
        epoch=2,
        event_hash=stream[-1]["event_hash"],
        authority_generation=7,
    )
    exact = assess_stream_against_anchor(stream, anchor, verifier=verify, mode="RECOVER_EXACT")
    assert exact.decision == "ADMIT_EXACT_RECOVERY"

    # The unusual sibling-rehash counterexample was already executed in UCM2-000004.
    # This is an ordinary regression proving the proposed gate rejects that known class.
    sibling = deepcopy(stream)
    sibling[1]["payload"]["payload"]["main_repo"] = "plausible-sibling-main"
    rehash_from(sibling, 1)
    assert verify(sibling) == sibling[-1]["event_hash"]
    expect_runtime_error(
        "LINEAGE_ANCHOR_HASH_MISMATCH",
        lambda: assess_stream_against_anchor(sibling, anchor, verifier=verify, mode="RECOVER_EXACT"),
    )

    extended = deepcopy(stream)
    append_event(extended, "UPSERT", "state.attention", {
        "object_id": "state.attention", "root_module": ROOT,
        "kind": "state", "status": "ACTIVE",
        "payload": {"focus": "lineage"}, "version": 1, "updated_at": "t3",
    })
    candidate = assess_stream_against_anchor(
        extended, anchor, verifier=verify, mode="EXTEND_FROM_ANCHOR"
    )
    assert candidate.decision == "CANDIDATE_SUCCESSOR"
    expect_runtime_error(
        "LINEAGE_EXACT_HEAD_REQUIRED",
        lambda: assess_stream_against_anchor(extended, anchor, verifier=verify, mode="RECOVER_EXACT"),
    )

    successor_anchor = LineageAnchor(
        anchor_id="owner-recovery-anchor-g8",
        root_module=ROOT,
        seq=4,
        epoch=3,
        event_hash=extended[-1]["event_hash"],
        authority_generation=8,
    )
    successor = assess_stream_against_anchor(
        extended, successor_anchor, verifier=verify, mode="RECOVER_EXACT"
    )
    assert successor.decision == "ADMIT_EXACT_RECOVERY"

    expect_runtime_error(
        "LINEAGE_ANCHOR_NOT_PRESENT",
        lambda: assess_stream_against_anchor(stream, successor_anchor, verifier=verify, mode="RECOVER_EXACT"),
    )

    # Explicit nonclaim: if an attacker can issue the anchor itself, the sibling can
    # be blessed. Anchor provenance/authentication must remain outside candidate state.
    forged_anchor = LineageAnchor(
        anchor_id="untrusted-self-issued",
        root_module=ROOT,
        seq=3,
        epoch=2,
        event_hash=sibling[-1]["event_hash"],
        authority_generation=999,
    )
    forged = assess_stream_against_anchor(
        sibling, forged_anchor, verifier=verify, mode="RECOVER_EXACT"
    )
    assert forged.decision == "ADMIT_EXACT_RECOVERY"

    print("UCM2_LINEAGE_ANCHOR_UNIT_PASS")
    print("UCM2_SIBLING_REJECTED_BY_TRUSTED_ANCHOR_PASS")
    print("UCM2_SUCCESSOR_REQUIRES_ANCHOR_ADVANCE_PASS")
    print("UCM2_ANCHOR_PROVENANCE_REMAINS_EXTERNAL_AUTHORITY_BOUNDARY")


if __name__ == "__main__":
    main()
