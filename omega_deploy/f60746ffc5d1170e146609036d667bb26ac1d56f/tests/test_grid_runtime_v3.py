import json
import tempfile
from pathlib import Path

from omega.grid_runtime_v3 import Runtime
from omega.grid_runtime_v2 import _now


ROOT = Path(__file__).resolve().parents[1]


def _router(path: Path) -> None:
    path.write_text(json.dumps({
        "allow_multi_organ_coalitions": True,
        "central_organ": "omega-vps",
        "telemetry_max_age_seconds": 180,
        "min_heavy_host_headroom": 0.10,
        "weights": {"capability_fit":1.0,"data_locality":0.9,"state_freshness":0.9,"information_gain":0.85,"independence_for_falsification":0.7,"compute_availability":0.6,"latency":0.45,"bridge_health":0.9,"host_resource_headroom":0.9,"effect_risk":-1.0,"duplicate_work":-0.7},
        "organs": [
            {"organ_id":"omega-vps","kind":"central_runtime","owner_id":"omega","capabilities":["shell","files"]},
            {"organ_id":"host:ai-core-node","kind":"host_frankenstein","owner_id":"gabriel","machine_id":"ai-core-node","capabilities":["shell","files","local_state"],"control_branch":"c","results_branch":"r"}
        ]
    }), encoding="utf-8")


def test_executable_task_routes_once_and_becomes_dispatched():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"state"; cfg=Path(td)/"router.json"; db=Path(td)/"omega.db"; _router(cfg)
        rt=Runtime(root,0.01,cfg,db,ROOT)
        (root/"telemetry"/"gabriel.json").write_text(json.dumps({
            "organ_id":"host:ai-core-node","observed_at":_now(),"health":"GREEN",
            "capabilities":["shell","files","local_state"],"data_domains":["gabriel-local"],
            "cpu_load":0.1,"ram_load":0.2,"bridge_health":1.0
        }),encoding="utf-8")
        (root/"inbox"/"task.json").write_text(json.dumps({
            "task_id":"task_effect_once","required_capabilities":["local_state"],
            "preferred_data_domains":["gabriel-local"],
            "effect":{"op":"status"}
        }),encoding="utf-8")
        epoch=rt.start_epoch(); rt.frame(epoch,"TEST")
        status=json.loads((root/"STATUS.json").read_text(encoding="utf-8"))
        assert status["selected"]["cell_id"] == "HOST_SCOUT"
        assert status["result"]["route"]["selected_organs"] == ["host:ai-core-node"]
        intents=list((root/"outbox").glob("effect_*.json")); assert len(intents)==1
        with rt.connect() as con:
            assert con.execute("select state from task where task_id='task_effect_once'").fetchone()[0] == "DISPATCHED"
        rt.frame(epoch,"SECOND")
        assert len(list((root/"outbox").glob("effect_*.json"))) == 1


def test_unknown_relay_result_never_reopens_task():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/"state"; cfg=Path(td)/"router.json"; db=Path(td)/"omega.db"; _router(cfg)
        rt=Runtime(root,0.01,cfg,db,ROOT)
        (root/"telemetry"/"gabriel.json").write_text(json.dumps({"organ_id":"host:ai-core-node","observed_at":_now(),"health":"GREEN","cpu_load":0.1,"ram_load":0.2}),encoding="utf-8")
        (root/"inbox"/"task.json").write_text(json.dumps({"task_id":"task_unknown","required_capabilities":["local_state"],"effect":{"op":"status"}}),encoding="utf-8")
        epoch=rt.start_epoch(); rt.frame(epoch,"TEST")
        intent_path=next((root/"outbox").glob("effect_*.json")); effect_id=json.loads(intent_path.read_text())["effect_id"]
        (root/"relay_results").mkdir(exist_ok=True)
        (root/"relay_results"/f"{effect_id}.json").write_text(json.dumps({"effect_id":effect_id,"state":"UNKNOWN"}),encoding="utf-8")
        rt.reconcile_relay_results()
        with rt.connect() as con:
            assert con.execute("select state from task where task_id='task_unknown'").fetchone()[0] == "EFFECT_UNKNOWN"
        rt.frame(epoch,"SECOND")
        assert len(list((root/"outbox").glob("effect_*.json"))) == 1
