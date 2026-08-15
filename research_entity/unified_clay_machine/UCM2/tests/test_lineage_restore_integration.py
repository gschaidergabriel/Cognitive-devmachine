from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import ROOT_MODULE, UCM2  # noqa: E402
from lineage_anchor import LineageAnchor  # noqa: E402
from recovery_gate import restore_exact_from_anchor  # noqa: E402


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


def expect_runtime_error(code: str, fn) -> None:
    try:
        fn()
    except RuntimeError as exc:
        assert str(exc) == code, (str(exc), code)
    else:
        raise AssertionError(f"expected {code}")


def main() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        source = UCM2(root / "source")
        target = UCM2(root / "target")
        try:
            source.upsert("world.main", "world_model", {"main_repo": "trusted-main"})
            source.upsert("wiki.ucm", "wiki", {"summary": "one root"})
            baseline = source.self_read()
            stream = source.event_stream()
            anchor = LineageAnchor(
                anchor_id="external-g7",
                root_module=ROOT_MODULE,
                seq=int(stream[-1]["seq"]),
                epoch=int(stream[-1]["epoch"]),
                event_hash=stream[-1]["event_hash"],
                authority_generation=7,
            )

            target.upsert("sentinel.local", "state", {"must_survive_rejection": True})
            before_rejection = target.self_read()

            sibling = deepcopy(stream)
            sibling_index = 1
            sibling[sibling_index]["payload"]["payload"]["main_repo"] = "coherent-sibling"
            rehash_from(sibling, sibling_index)
            assert target.verify_event_stream(sibling) == sibling[-1]["event_hash"]

            expect_runtime_error(
                "LINEAGE_ANCHOR_HASH_MISMATCH",
                lambda: restore_exact_from_anchor(target, sibling, anchor),
            )
            assert target.self_read() == before_rejection

            admitted = restore_exact_from_anchor(target, stream, anchor)
            assert admitted.decision == "ADMIT_EXACT_RECOVERY"
            assert target.self_read() == baseline

            source.upsert("state.attention", "state", {"focus": "lineage"})
            extended = source.event_stream()
            extended_state = source.self_read()
            before_extension_rejection = target.self_read()

            expect_runtime_error(
                "LINEAGE_EXACT_HEAD_REQUIRED",
                lambda: restore_exact_from_anchor(target, extended, anchor),
            )
            assert target.self_read() == before_extension_rejection

            successor_anchor = LineageAnchor(
                anchor_id="external-g8",
                root_module=ROOT_MODULE,
                seq=int(extended[-1]["seq"]),
                epoch=int(extended[-1]["epoch"]),
                event_hash=extended[-1]["event_hash"],
                authority_generation=8,
            )
            successor = restore_exact_from_anchor(target, extended, successor_anchor)
            assert successor.decision == "ADMIT_EXACT_RECOVERY"
            assert target.self_read() == extended_state
        finally:
            source.close()
            target.close()

    print("UCM2_LINEAGE_RESTORE_GATE_INTEGRATION_PASS")
    print("UCM2_REJECTED_SIBLING_ZERO_TARGET_MUTATION_PASS")
    print("UCM2_EXTENSION_REQUIRES_EXTERNAL_ANCHOR_ADVANCE_PASS")


if __name__ == "__main__":
    main()
