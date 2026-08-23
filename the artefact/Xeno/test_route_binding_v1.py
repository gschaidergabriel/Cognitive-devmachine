import unittest

from entry_fabric_v1 import admit_ingress
from route_binding_v1 import RouteBindingError, admit_engine_binding, bind_route_decision


PAYLOAD_A = "a" * 64
PAYLOAD_B = "b" * 64
CHECKPOINT_A = "1" * 64
CHECKPOINT_B = "2" * 64


def packet(payload_sha=PAYLOAD_A):
    return admit_ingress({
        "schema": "XENO_INGRESS_PACKET/v1",
        "causal_id": "cause-route",
        "entity_generation": 11,
        "source": "intrinsic_system_event",
        "provenance": {"kind": "test", "ref": "route"},
        "modality": "json",
        "observed_at_ns": 300,
        "received_at_ns": 310,
        "permissions": ["state.read"],
        "capability_scope": [],
        "resource_budget": {
            "max_wall_ms": 1000,
            "max_model_calls": 4,
            "max_context_tokens": 4096,
            "max_logical_cells": 10,
        },
        "payload_ref": "unifieddb:event:route",
        "payload_sha256": payload_sha,
    }, current_generation=11)


def engine(engine_id="hcu-local-a", checkpoint=CHECKPOINT_A):
    return admit_engine_binding({
        "schema": "XENO_ENGINE_BINDING/v1",
        "engine_id": engine_id,
        "engine_class": "LOCAL_SHARED_WEIGHT_INFERENCE",
        "provider_class": "INTERNAL_LOCAL",
        "runtime_identity": "llama.cpp:v-current",
        "checkpoint_sha256": checkpoint,
    })


ROUTING = {"model_lanes": ["world", "critic"], "zero_projection": False}


class RouteBindingTests(unittest.TestCase):
    def test_model_activation_requires_positive_engine_binding(self):
        with self.assertRaisesRegex(RouteBindingError, "REQUIRES_ADMITTED_ENGINE"):
            bind_route_decision(packet(), ROUTING, model_activation=True, engine=None)

    def test_unknown_provider_class_fails_closed(self):
        raw = {
            "schema": "XENO_ENGINE_BINDING/v1",
            "engine_id": "remote-x",
            "engine_class": "LOCAL_SHARED_WEIGHT_INFERENCE",
            "provider_class": "EXTERNAL_PROVIDER",
            "runtime_identity": "runtime-x",
            "checkpoint_sha256": CHECKPOINT_A,
        }
        with self.assertRaisesRegex(RouteBindingError, "PROVIDER_CLASS_NOT_POSITIVELY_ADMITTED"):
            admit_engine_binding(raw)

    def test_same_event_distinct_admitted_engines_do_not_alias(self):
        a = bind_route_decision(packet(), ROUTING, model_activation=True, engine=engine("hcu-local-a", CHECKPOINT_A))
        b = bind_route_decision(packet(), ROUTING, model_activation=True, engine=engine("hcu-local-b", CHECKPOINT_B))
        self.assertNotEqual(a.route_decision_sha256, b.route_decision_sha256)

    def test_same_engine_distinct_events_same_route_shape_do_not_alias(self):
        a = bind_route_decision(packet(PAYLOAD_A), ROUTING, model_activation=True, engine=engine())
        b = bind_route_decision(packet(PAYLOAD_B), ROUTING, model_activation=True, engine=engine())
        self.assertNotEqual(a.ingress_id, b.ingress_id)
        self.assertNotEqual(a.route_decision_sha256, b.route_decision_sha256)

    def test_exact_replay_is_deterministic(self):
        a = bind_route_decision(packet(), ROUTING, model_activation=True, engine=engine())
        b = bind_route_decision(packet(), ROUTING, model_activation=True, engine=engine())
        self.assertEqual(a, b)

    def test_script_only_route_rejects_model_engine_binding(self):
        with self.assertRaisesRegex(RouteBindingError, "MUST_NOT_BIND_MODEL_ENGINE"):
            bind_route_decision(packet(), {"model_lanes": []}, model_activation=False, engine=engine())


if __name__ == "__main__":
    unittest.main()
