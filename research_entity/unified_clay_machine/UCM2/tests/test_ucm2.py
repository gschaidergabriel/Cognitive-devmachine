from pathlib import Path
from tempfile import TemporaryDirectory
import sys

RUNTIME = Path(__file__).resolve().parents[1] / "runtime"
sys.path.insert(0, str(RUNTIME))

from ucm2 import ROOT_MODULE, UCM2  # noqa: E402


def main() -> None:
    with TemporaryDirectory() as tmp:
        machine = UCM2(tmp)
        try:
            assert machine.self_read()["root_module"] == ROOT_MODULE

            e1 = machine.upsert(
                "state.attention",
                "state",
                {"focus": "Unified Clay Machine", "energy": 0.8},
            )
            e2 = machine.upsert(
                "world.main",
                "world_model",
                {"main_repo": "b0518b68", "freshness": "VPS_FRESHNESS_GAP"},
            )
            e3 = machine.upsert(
                "hp.storage",
                "hyperposition",
                {
                    "alternatives": ["sqlite-only", "sqlite+derived-graph"],
                    "selected": None,
                },
            )
            e4 = machine.upsert(
                "wiki.ucm",
                "wiki",
                {
                    "summary": "UnifiedDB + states + world + hyperposition live under one key module"
                },
            )
            e5 = machine.link("hp.storage", "informs", "world.main")
            exp_id, e6 = machine.record_experience(
                "frontier-worker-A",
                "self-read shows all cognitive surfaces under one root module",
                "epoch should advance monotonically",
                "PASS",
                "single-root representation is inspectable",
                "OBSERVED",
            )

            state = machine.self_read()
            assert state["epoch"] == 6
            assert {obj["kind"] for obj in state["objects"]} >= {
                "clay_machine_key_module",
                "state",
                "world_model",
                "hyperposition",
                "wiki",
            }
            assert len(state["experiences"]) == 1
            assert state["experiences"][0]["exp_id"] == exp_id
            assert [e1, e2, e3, e4, e5, e6] == [1, 2, 3, 4, 5, 6]
        finally:
            machine.close()

    print("UCM2_PROTO_PASS")


if __name__ == "__main__":
    main()
