import copy
import hashlib
import json
import unittest

from entry_fabric_v1 import admit_ingress
from route_identity_v1 import RouteIdentityError, bind_route_identity, resolve_engine


def payload_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest(), len(raw)


def packet(causal="c:1", payload=None):
    payload = {"x": 1} if payload is None else payload
    sha, size = payload_digest(payload)
    req = {
        "schema":"XENO_INGRESS_REQUEST/v1",
        "causal_id":causal,
        "entity_generation":7,
        "source":"intrinsic_event",
        "provenance":["test:route"],
        "modality":"application/json",
        "observed_at":"2026-08-23T16:00:00Z",
        "received_at":"2026-08-23T16:00:00Z",
        "permissions":[],
        "capability_scope":[],
        "resource_budget":{"max_model_calls":1},
        "payload_ref":"test:payload",
        "payload_sha256":sha,
        "payload_size_bytes":size,
    }
    return admit_ingress(req,current_generation=7)


def policy():
    a = "a" * 64
    b = "b" * 64
    return {
        "schema":"XENO_ENGINE_ADMISSION_POLICY/v1",
        "engines":{
            "local-primary":{"canonical_id":"xcu:qwen08b:primary","engine_class":"LOCAL_SHARED_MODEL","artifact_sha256":a},
            "local-alias":{"canonical_id":"xcu:qwen08b:primary","engine_class":"LOCAL_SHARED_MODEL","artifact_sha256":a},
            "local-critic":{"canonical_id":"xcu:qwen08b:critic","engine_class":"LOCAL_SHARED_MODEL","artifact_sha256":b},
            "script":{"canonical_id":"xpu:deterministic-script","engine_class":"DETERMINISTIC_SCRIPT","artifact_sha256":None},
        }
    }


class RouteIdentityTests(unittest.TestCase):
    def test_unknown_engine_fails_closed(self):
        with self.assertRaisesRegex(RouteIdentityError,"ENGINE_NOT_POSITIVELY_ADMITTED"):
            resolve_engine("nvidia",policy())

    def test_explicit_aliases_resolve_to_same_canonical_engine(self):
        a=resolve_engine("local-primary",policy())
        b=resolve_engine("local-alias",policy())
        self.assertEqual(a.canonical_id,b.canonical_id)
        self.assertEqual(a.artifact_sha256,b.artifact_sha256)
        self.assertEqual(a.admission_policy_sha256,b.admission_policy_sha256)

    def test_distinct_canonical_engines_change_route_identity(self):
        p=packet()
        routing={"lanes":["world","critic"],"projection":True}
        policy_sha="c"*64
        a=bind_route_identity(p,resolve_engine("local-primary",policy()),router_policy_sha256=policy_sha,routing_result=routing)
        b=bind_route_identity(p,resolve_engine("local-critic",policy()),router_policy_sha256=policy_sha,routing_result=routing)
        self.assertNotEqual(a.route_sha256,b.route_sha256)

    def test_distinct_ingress_changes_route_identity_even_same_result(self):
        routing={"lanes":["world","critic"],"projection":True}
        e=resolve_engine("local-primary",policy())
        a=bind_route_identity(packet(causal="c:1",payload={"x":1}),e,router_policy_sha256="c"*64,routing_result=routing)
        b=bind_route_identity(packet(causal="c:2",payload={"x":2}),e,router_policy_sha256="c"*64,routing_result=routing)
        self.assertNotEqual(a.route_sha256,b.route_sha256)

    def test_same_exact_replay_is_deterministic(self):
        p=packet(); e=resolve_engine("local-primary",policy()); routing={"lanes":["world"]}
        a=bind_route_identity(p,e,router_policy_sha256="c"*64,routing_result=routing)
        b=bind_route_identity(p,e,router_policy_sha256="c"*64,routing_result=copy.deepcopy(routing))
        self.assertEqual(a,b)

    def test_router_policy_change_changes_route_identity(self):
        p=packet(); e=resolve_engine("script",policy()); routing={"lanes":[]}
        a=bind_route_identity(p,e,router_policy_sha256="c"*64,routing_result=routing)
        b=bind_route_identity(p,e,router_policy_sha256="d"*64,routing_result=routing)
        self.assertNotEqual(a.route_sha256,b.route_sha256)

    def test_routing_result_change_changes_route_identity(self):
        p=packet(); e=resolve_engine("script",policy())
        a=bind_route_identity(p,e,router_policy_sha256="c"*64,routing_result={"lanes":[]})
        b=bind_route_identity(p,e,router_policy_sha256="c"*64,routing_result={"lanes":["critic"]})
        self.assertNotEqual(a.route_sha256,b.route_sha256)

    def test_policy_mutation_changes_admission_and_route_identity(self):
        p=packet(); routing={"lanes":["world"]}
        pa=policy(); pb=copy.deepcopy(pa); pb["engines"]["local-primary"]["engine_class"]="LOCAL_SHARED_MODEL_V2"
        ea=resolve_engine("local-primary",pa); eb=resolve_engine("local-primary",pb)
        self.assertNotEqual(ea.admission_policy_sha256,eb.admission_policy_sha256)
        a=bind_route_identity(p,ea,router_policy_sha256="c"*64,routing_result=routing)
        b=bind_route_identity(p,eb,router_policy_sha256="c"*64,routing_result=routing)
        self.assertNotEqual(a.route_sha256,b.route_sha256)


if __name__ == "__main__": unittest.main()
