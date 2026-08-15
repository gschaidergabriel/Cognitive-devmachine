from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import UCM2  # noqa: E402
from ucm2_event_head_anchor_v1 import (  # noqa: E402
    capture_event_head,
    parse_anchor,
    verify_machine_against_anchor,
)


def main() -> None:
    with TemporaryDirectory() as tmp:
        source = UCM2(Path(tmp) / "source")
        source.upsert(
            "world.main",
            "world_model",
            {"main_repo": "b0518b68", "freshness": "VPS_FRESHNESS_GAP"},
        )
        source.upsert(
            "wiki.anchor",
            "wiki",
            {"summary": "external head receipt binds admitted replay branch"},
        )
        stream = source.event_stream()
        anchor = capture_event_head(
            source,
            provenance={"scope": "ucm2-event-head-admission-discriminator"},
        )
        assert verify_machine_against_anchor(source, anchor) == anchor.event_hash

        # Deterministic regression of the already-observed tail-amputation class:
        # the shortened prefix is internally valid, but cannot satisfy the
        # previously admitted later event head.
        prefix = deepcopy(stream[:-1])
        rolled = UCM2(Path(tmp) / "rolled")
        rolled.restore_from_event_stream(prefix)
        assert rolled.verify_event_stream() == prefix[-1]["event_hash"]
        try:
            verify_machine_against_anchor(rolled, anchor)
        except RuntimeError as exc:
            assert str(exc) in {
                "EVENT_HEAD_ANCHOR_SEQ_MISMATCH",
                "EVENT_HEAD_ANCHOR_EPOCH_MISMATCH",
                "EVENT_HEAD_ANCHOR_HASH_MISMATCH",
            }
        else:
            raise AssertionError("internally valid rollback prefix matched later external head")

        forged = anchor.as_dict()
        forged["event_hash"] = "0" * 64
        try:
            parse_anchor(forged)
        except RuntimeError as exc:
            assert str(exc) == "EVENT_HEAD_ANCHOR_RECEIPT_HASH_MISMATCH"
        else:
            raise AssertionError("mutated anchor receipt accepted without recomputing receipt hash")

        rolled.close()
        source.close()

    print("UCM2_EVENT_HEAD_ANCHOR_V1_PASS")


if __name__ == "__main__":
    main()
