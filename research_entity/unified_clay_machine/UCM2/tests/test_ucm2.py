from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import ROOT_MODULE, UCM2  # noqa: E402


def rehash_from(stream: list[dict], index: int) -> None:
    prev_hash = stream[index - 1]["event_hash"] if index else ""
    for event in stream[index:]:
        event["prev_hash"] = prev_hash
        event["event_hash"] = UCM2._compute_event_hash(
            int(event["epoch"]),
            event["event_type"],
            event["object_id"],
            event["payload"],
            event["prev_hash"],
            event["created_at"],
        )
        prev_hash = event["event_hash"]


def main() -> None:
    with TemporaryDirectory() as tmp:
        source = UCM2(Path(tmp) / "source")
        try:
            assert source.self_read()["root_module"] == ROOT_MODULE
            assert source.epoch() == 0
            assert source.verify_event_stream() == source.event_stream()[-1]["event_hash"]

            e1 = source.upsert(
                "state.attention",
                "state",
                {"focus": "Unified Clay Machine", "energy": 0.8},
            )
            e2 = source.upsert(
                "world.main",
                "world_model",
                {"main_repo": "b0518b68", "freshness": "VPS_FRESHNESS_GAP"},
            )
            e3 = source.upsert(
                "hp.storage",
                "hyperposition",
                {
                    "alternatives": ["sqlite-only", "sqlite+derived-graph"],
                    "selected": None,
                },
            )
            e4 = source.upsert(
                "wiki.ucm",
                "wiki",
                {
                    "summary": "UnifiedDB + states + world + hyperposition live under one key module"
                },
            )
            e5 = source.link("hp.storage", "informs", "world.main")
            exp_id, e6 = source.record_experience(
                "frontier-worker-A",
                "self-read shows all cognitive surfaces under one root module",
                "epoch should advance monotonically",
                "PASS",
                "single-root representation is inspectable",
                "OBSERVED",
            )

            baseline = source.self_read()
            stream = source.event_stream()
            terminal_hash = source.verify_event_stream(stream)
            assert baseline["epoch"] == 6
            assert len(stream) == 7  # bootstrap epoch 0 + six material mutations
            assert {obj["kind"] for obj in baseline["objects"]} >= {
                "clay_machine_key_module",
                "state",
                "world_model",
                "hyperposition",
                "wiki",
            }
            assert len(baseline["experiences"]) == 1
            assert baseline["experiences"][0]["exp_id"] == exp_id
            assert [e1, e2, e3, e4, e5, e6] == [1, 2, 3, 4, 5, 6]

            # Fresh-database replay must reproduce the same bounded self-read exactly.
            replay = UCM2(Path(tmp) / "replay")
            try:
                assert replay.restore_from_event_stream(stream) == terminal_hash
                assert replay.self_read() == baseline
            finally:
                replay.close()

            # Destroy all materialized semantic views, preserve events, then recover.
            source.db.executescript(
                "DELETE FROM objects; DELETE FROM edges; DELETE FROM experiences;"
            )
            source.db.commit()
            assert source.self_read()["objects"] == []
            assert source.rebuild_materialized_from_events() == terminal_hash
            assert source.self_read() == baseline

            # Ordinary tamper falsifier: changed payload without a new chain must fail.
            tampered = deepcopy(stream)
            tampered[2]["payload"]["payload"]["freshness"] = "FAKE_FRESH"
            try:
                source.verify_event_stream(tampered)
            except RuntimeError as exc:
                assert str(exc) == "EVENT_HASH_MISMATCH"
            else:
                raise AssertionError("tampered event stream was accepted")

            # BOUNDED UNUSUAL EXPERIMENT: a coherent sibling lineage can be fully
            # re-hashed and pass internal integrity while describing a different
            # world. This deliberately proves hash-chain integrity != canonical
            # lineage authority; an external trusted anchor/admission rule remains
            # necessary to select between self-consistent branches.
            sibling = deepcopy(stream)
            sibling_index = 2  # world.main UPSERT
            sibling[sibling_index]["payload"]["payload"]["main_repo"] = "plausible-sibling-main"
            rehash_from(sibling, sibling_index)
            sibling_hash = source.verify_event_stream(sibling)
            assert sibling_hash != terminal_hash

            sibling_machine = UCM2(Path(tmp) / "sibling")
            try:
                sibling_machine.restore_from_event_stream(sibling)
                sibling_state = sibling_machine.self_read()
                assert sibling_state != baseline
                sibling_world = next(
                    obj for obj in sibling_state["objects"] if obj["object_id"] == "world.main"
                )
                assert sibling_world["payload"]["main_repo"] == "plausible-sibling-main"
            finally:
                sibling_machine.close()
        finally:
            source.close()

    print("UCM2_REPLAY_RECOVERY_PASS")
    print("UCM2_SIBLING_LINEAGE_COUNTEREXAMPLE_PASS")


if __name__ == "__main__":
    main()
