import json
import tempfile
import unittest
from pathlib import Path

from omega.grid_runtime_v2 import Runtime, _now


class GridRuntimeV2Tests(unittest.TestCase):
    def test_idle_runtime_does_not_emit_host_effect_just_because_host_exists(self):
        """Host availability is telemetry, not permission to manufacture work."""
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)/"state"
            cfg=Path(td)/"router.json"
            cfg.write_text(json.dumps({
              "allow_multi_organ_coalitions":True,
              "central_organ":"omega-vps",
              "telemetry_max_age_seconds":180,
              "weights":{"capability_fit":1.0,"data_locality":0.9,"state_freshness":0.9,"information_gain":0.85,"independence_for_falsification":0.7,"compute_availability":0.6,"latency":0.45,"bridge_health":0.9,"host_resource_headroom":0.9,"effect_risk":-1.0,"duplicate_work":-0.7},
              "organs":[
                {"organ_id":"omega-vps","kind":"central_runtime","capabilities":["shell","files"]},
                {"organ_id":"host:ai-core-node","kind":"host_frankenstein","capabilities":["shell","files","local_state"]},
                {"organ_id":"host:andreas-maco","kind":"host_frankenstein","capabilities":["shell","files","local_state"]}
              ]
            }),encoding="utf-8")
            rt=Runtime(root,0.01,cfg)
            (root/"telemetry"/"gabriel.json").write_text(json.dumps({
              "organ_id":"host:ai-core-node","observed_at":_now(),"health":"GREEN",
              "capabilities":["shell","files","local_state"],"data_domains":["gabriel-local"],
              "cpu_load":0.1,"ram_load":0.2,"bridge_health":1.0
            }),encoding="utf-8")
            epoch=rt.start_epoch(); rt.frame(epoch,"TEST")
            status=json.loads((root/"STATUS.json").read_text(encoding="utf-8"))
            self.assertEqual(status["selected"]["cell_id"],"REENTRY")
            self.assertEqual(list((root/"outbox").glob("effect_*.json")),[])


if __name__ == "__main__":
    unittest.main()
