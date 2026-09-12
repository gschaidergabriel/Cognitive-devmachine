import datetime as dt
import unittest

from omega.router import DynamicOrganRouter, OrganTelemetry, TaskRequest


CFG={
 "allow_multi_organ_coalitions":True,
 "central_organ":"omega-vps",
 "telemetry_max_age_seconds":180,
 "weights":{
   "capability_fit":1.0,"data_locality":0.9,"state_freshness":0.9,
   "information_gain":0.85,"independence_for_falsification":0.7,
   "compute_availability":0.6,"latency":0.45,"bridge_health":0.9,
   "host_resource_headroom":0.9,"effect_risk":-1.0,"duplicate_work":-0.7
 },
 "organs":[
  {"organ_id":"omega-vps","kind":"central_runtime","capabilities":["shell","files","internet","research"]},
  {"organ_id":"host:ai-core-node","kind":"host_frankenstein","capabilities":["shell","files","desktop","browser","avatar","gpu","local_state"]},
  {"organ_id":"host:andreas-maco","kind":"host_frankenstein","capabilities":["shell","files","entityos","self_integration","local_state"]}
 ]
}


def ts(seconds_ago=0):
    return (dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=seconds_ago)).isoformat()


class RouterTests(unittest.TestCase):
    def setUp(self):
        self.router=DynamicOrganRouter(CFG)

    def test_data_locality_can_select_gabriel(self):
        task=TaskRequest("t1",frozenset({"avatar"}),frozenset({"production-avatar"}))
        telemetry=[
          OrganTelemetry("omega-vps",ts(),health="GREEN",capabilities=frozenset({"shell"})),
          OrganTelemetry("host:ai-core-node",ts(),health="GREEN",data_domains=frozenset({"production-avatar"}),cpu_load=.2,ram_load=.3,bridge_health=1.0),
          OrganTelemetry("host:andreas-maco",ts(),health="GREEN",data_domains=frozenset({"andreas-local"}),cpu_load=.2,ram_load=.2),
        ]
        decision=self.router.choose(task,telemetry)
        self.assertEqual(decision.selected_organs,("host:ai-core-node",))

    def test_heavy_stale_host_fails_closed(self):
        task=TaskRequest("t2",frozenset({"local_state"}),heavy=True)
        telemetry=[
          OrganTelemetry("host:ai-core-node",ts(1000),health="GREEN"),
          OrganTelemetry("host:andreas-maco",ts(),health="GREEN",cpu_load=.1,ram_load=.1),
        ]
        decision=self.router.choose(task,telemetry)
        self.assertEqual(decision.selected_organs,("host:andreas-maco",))
        stale=next(x for x in decision.ranking if x.organ_id=="host:ai-core-node")
        self.assertFalse(stale.eligible)

    def test_independent_falsifier_forms_coalition(self):
        task=TaskRequest("t3",frozenset({"shell"}),wants_independent_falsifier=True,max_organs=1)
        telemetry=[
          OrganTelemetry("omega-vps",ts(),health="GREEN",independence=.3),
          OrganTelemetry("host:ai-core-node",ts(),health="GREEN",independence=.9,cpu_load=.1,ram_load=.1),
          OrganTelemetry("host:andreas-maco",ts(),health="GREEN",independence=.8,cpu_load=.1,ram_load=.1),
        ]
        decision=self.router.choose(task,telemetry)
        self.assertEqual(len(decision.selected_organs),2)


if __name__ == "__main__":
    unittest.main()
