import json
import tempfile
from pathlib import Path

from omega.grid_runtime_v2 import _now
from omega.grid_runtime_v3 import Runtime


ROOT = Path(__file__).resolve().parents[1]


def _router(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "allow_multi_organ_coalitions": True,
                "central_organ": "omega-vps",
                "telemetry_max_age_seconds": 180,
                "min_heavy_host_headroom": 0.10,
                "weights": {
                    "capability_fit": 1.0,
                    "data_locality": 0.9,
                    "state_freshness": 0.9,
                    "information_gain": 0.85,
                    "independence_for_falsification": 0.7,
                    "compute_availability": 0.6,
                    "latency": 0.45,
                    "bridge_health": 0.9,
                    "host_resource_headroom": 0.9,
                    "effect_risk": -1.0,
                    "duplicate_work": -0.7,
                },
                "organs": [
                    {
                        "organ_id": "omega-vps",
                        "kind": "central_runtime",
                        "owner_id": "omega",
                        "capabilities": ["shell", "files"],
                    },
                    {
                        "organ_id": "host:ai-core-node",
                        "kind": "host_frankenstein",
                        "owner_id": "gabriel",
                        "machine_id": "ai-core-node",
                        "capabilities": ["shell", "files", "local_state"],
                        "control_branch": "c",
                        "results_branch": "r",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


def _runtime(td: str) -> tuple[Runtime, Path]:
    root = Path(td) / "state"
    cfg = Path(td) / "router.json"
    db = Path(td) / "omega.db"
    _router(cfg)
    return Runtime(root, 0.01, cfg, db, ROOT), root


def _master_outbox(root: Path) -> list[dict]:
    rows = []
    for path in sorted((root / "outbox").glob("msg_*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        if payload.get("kind") == "MASTER_COGNITION_UPDATE":
            rows.append(payload)
    return rows


def test_planning_only_task_goes_to_master_once_instead_of_spinning():
    with tempfile.TemporaryDirectory() as td:
        rt, root = _runtime(td)
        (root / "inbox" / "planning.json").write_text(
            json.dumps(
                {
                    "task_id": "task_plan_only",
                    "goal": "resolve the next evidence-bound implementation step",
                }
            ),
            encoding="utf-8",
        )

        epoch = rt.start_epoch()
        rt.frame(epoch, "TEST")

        status = json.loads((root / "STATUS.json").read_text(encoding="utf-8"))
        assert status["selected"]["cell_id"] == "MASTER_BRIDGE"
        assert status["result"]["task_id"] == "task_plan_only"
        with rt.connect() as con:
            state = con.execute(
                "select state from task where task_id='task_plan_only'"
            ).fetchone()[0]
        assert state == "WAITING_MASTER"
        assert len(_master_outbox(root)) == 1
        assert not list((root / "outbox").glob("effect_*.json"))

        rt.frame(epoch, "SECOND")
        assert len(_master_outbox(root)) == 1
        assert not list((root / "outbox").glob("effect_*.json"))


def test_host_hints_without_effect_are_not_minted_as_fake_effects():
    with tempfile.TemporaryDirectory() as td:
        rt, root = _runtime(td)
        (root / "inbox" / "inspect.json").write_text(
            json.dumps(
                {
                    "task_id": "task_host_hint_only",
                    "required_capabilities": ["local_state"],
                    "preferred_data_domains": ["gabriel-local"],
                    "goal": "inspect current host evidence and decide what exact readback is needed",
                }
            ),
            encoding="utf-8",
        )
        epoch = rt.start_epoch()
        rt.frame(epoch, "TEST")
        status = json.loads((root / "STATUS.json").read_text(encoding="utf-8"))
        assert status["selected"]["cell_id"] == "MASTER_BRIDGE"
        assert len(_master_outbox(root)) == 1
        assert not list((root / "outbox").glob("effect_*.json"))


def test_executable_task_still_beats_periodic_master_cognition():
    with tempfile.TemporaryDirectory() as td:
        rt, root = _runtime(td)
        (root / "telemetry" / "gabriel.json").write_text(
            json.dumps(
                {
                    "organ_id": "host:ai-core-node",
                    "observed_at": _now(),
                    "health": "GREEN",
                    "capabilities": ["shell", "files", "local_state"],
                    "data_domains": ["gabriel-local"],
                    "cpu_load": 0.1,
                    "ram_load": 0.2,
                    "bridge_health": 1.0,
                }
            ),
            encoding="utf-8",
        )
        (root / "inbox" / "effect.json").write_text(
            json.dumps(
                {
                    "task_id": "task_effect_priority",
                    "required_capabilities": ["local_state"],
                    "preferred_data_domains": ["gabriel-local"],
                    "effect": {"op": "status"},
                }
            ),
            encoding="utf-8",
        )
        epoch = rt.start_epoch()
        rt.frame(epoch, "TEST")
        status = json.loads((root / "STATUS.json").read_text(encoding="utf-8"))
        assert status["selected"]["cell_id"] == "HOST_SCOUT"
        assert len(list((root / "outbox").glob("effect_*.json"))) == 1
        assert len(_master_outbox(root)) == 0
