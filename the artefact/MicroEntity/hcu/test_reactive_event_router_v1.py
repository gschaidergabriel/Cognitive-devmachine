import unittest

from reactive_event_router_v1 import ReactiveRoutingError, route_event


LOCAL_ENGINE_REGISTRY = {
    "local-08b-a": {
        "engine_id": "local-08b-a",
        "engine_class": "LOCAL_BUNDLED_MODEL",
        "runtime_identity": "test-runtime-a@sha256:1111",
        "checkpoint_identity": "test-checkpoint-a@sha256:2222",
        "tokenizer_identity": "test-tokenizer-a@sha256:3333",
        "network_required": False,
        "secret_lookup_required": False,
    },
    "local-08b-b": {
        "engine_id": "local-08b-b",
        "engine_class": "LOCAL_INPROCESS_MODEL",
        "runtime_identity": "test-runtime-b@sha256:4444",
        "checkpoint_identity": "test-checkpoint-b@sha256:5555",
        "tokenizer_identity": "test-tokenizer-b@sha256:6666",
        "network_required": False,
        "secret_lookup_required": False,
    },
}


def base_event():
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "event_id": "evt-0001",
        "causal_id": "causal-0001",
        "entity_generation": 7,
        "modality": "intrinsic",
        "observed_at": "2026-08-23T23:23:00+07:00",
        "provenance": {"source_type": "test", "source_id": "fixture-1"},
        "permissions": {"cognition": True},
        "budget": {"allow_model_cognition": True, "max_model_lanes": 8},
        "novelty": 0.05,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False,
    }


def routed(event):
    return route_event(
        event,
        current_generation=7,
        requested_engine_id="local-08b-a",
        engine_registry=LOCAL_ENGINE_REGISTRY,
    )


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)
        self.assertEqual(decision.causal_id, "causal-0001")
        self.assertEqual(len(decision.event_sha256), 64)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        decision = routed(e)
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_id, "local-08b-a")

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = base_event(); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = routed(e)
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_nvidia_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "NVIDIA"
        with self.assertRaisesRegex(ReactiveRoutingError, "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_mistral_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "mistral"
        with self.assertRaisesRegex(ReactiveRoutingError, "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_unknown_provider_alias_fails_closed(self):
        e = base_event(); e["requested_internal_provider"] = "future-provider"
        with self.assertRaisesRegex(ReactiveRoutingError, "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_missing_causal_identity_fails_closed_before_routing(self):
        e = base_event(); del e["causal_id"]
        with self.assertRaisesRegex(ReactiveRoutingError, "causal_id"):
            route_event(e, current_generation=7)

    def test_same_input_is_deterministic(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        a = routed(e)
        b = routed(dict(reversed(list(e.items()))))
        self.assertEqual(a, b)

    def test_distinct_events_with_same_route_do_not_alias_decision_identity(self):
        a_event = base_event(); a_event.update(event_id="evt-A", novelty=0.80, zero_relevance=0.80)
        b_event = base_event(); b_event.update(event_id="evt-B", novelty=0.81, zero_relevance=0.80)
        a = routed(a_event)
        b = routed(b_event)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_same_exact_event_under_two_admitted_engines_has_distinct_route_identity(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        a = route_event(e, current_generation=7, requested_engine_id="local-08b-a", engine_registry=LOCAL_ENGINE_REGISTRY)
        b = route_event(e, current_generation=7, requested_engine_id="local-08b-b", engine_registry=LOCAL_ENGINE_REGISTRY)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.resolved_engine_identity_sha256, b.resolved_engine_identity_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_model_activation_without_positive_engine_registry_fails_closed(self):
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_REGISTRY_REQUIRED"):
            route_event(e, current_generation=7, requested_engine_id="local-08b-a")

    def test_unknown_engine_fails_closed(self):
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_NOT_ADMITTED"):
            route_event(e, current_generation=7, requested_engine_id="missing", engine_registry=LOCAL_ENGINE_REGISTRY)

    def test_engine_that_requires_network_is_not_internal(self):
        e = base_event(); e.update(novelty=0.8)
        poisoned = {k: dict(v) for k, v in LOCAL_ENGINE_REGISTRY.items()}
        poisoned["local-08b-a"]["network_required"] = True
        with self.assertRaisesRegex(ReactiveRoutingError, "NETWORK_DEPENDENCY_FORBIDDEN"):
            route_event(e, current_generation=7, requested_engine_id="local-08b-a", engine_registry=poisoned)

    def test_model_cognition_permission_is_enforced(self):
        e = base_event(); e.update(novelty=0.8, permissions={"cognition": False})
        with self.assertRaisesRegex(ReactiveRoutingError, "COGNITION_PERMISSION_DENIED"):
            routed(e)

    def test_model_lane_budget_is_enforced(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.8, budget={"allow_model_cognition": True, "max_model_lanes": 2})
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_LANE_BUDGET_EXCEEDED"):
            routed(e)


if __name__ == "__main__":
    unittest.main()
