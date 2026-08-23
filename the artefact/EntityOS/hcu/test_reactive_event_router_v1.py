import unittest

from reactive_event_router_v1 import (
    LOCAL_ENGINE_CLASS,
    ReactiveRoutingError,
    route_event,
)


def base_event(event_id="evt-0001"):
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "event_source": "unifieddb://entityos/hcu",
        "event_id": event_id,
        "entity_generation": 7,
        "novelty": 0.05,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False,
        "provenance_gap": False,
    }


def local_engine(checkpoint="a" * 64):
    return {
        "engine_id": "entityos.hcu.local-qwen-test",
        "engine_class": LOCAL_ENGINE_CLASS,
        "checkpoint_sha256": checkpoint,
        "tokenizer_sha256": "b" * 64,
        "runtime_id": "llama.cpp/test-contract-v1",
    }


class EntityOSHCUReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertEqual(decision.cognition_engine_class, "DETERMINISTIC_SCRIPT")
        self.assertFalse(decision.external_provider_dependency)

    def test_contradiction_selectively_activates_expected_lanes(self):
        event = base_event()
        event.update(contradiction=0.8, uncertainty=0.7)
        decision = route_event(event, current_generation=7, engine=local_engine())
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})

    def test_effect_pressure_adds_simulation_zero_model_and_projection(self):
        event = base_event()
        event.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_event(event, current_generation=7, engine=local_engine())
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_model_activation_requires_positive_local_engine_admission(self):
        event = base_event()
        event["novelty"] = 0.9
        with self.assertRaisesRegex(ReactiveRoutingError, "LOCAL_HCU_ENGINE_REQUIRED"):
            route_event(event, current_generation=7)
        external = local_engine()
        external["engine_class"] = "HOSTED_PROVIDER"
        with self.assertRaisesRegex(ReactiveRoutingError, "UNADMITTED_COGNITION_ENGINE_CLASS"):
            route_event(event, current_generation=7, engine=external)

    def test_legacy_provider_selector_is_not_a_hidden_admission_path(self):
        event = base_event()
        event["requested_internal_provider"] = "some-new-provider"
        with self.assertRaisesRegex(ReactiveRoutingError, "EVENT_FIELD_UNSUPPORTED"):
            route_event(event, current_generation=7)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_unknown_event_field_fails_instead_of_disappearing_from_identity(self):
        event = base_event()
        event["new_material_signal"] = 1
        with self.assertRaisesRegex(ReactiveRoutingError, "EVENT_FIELD_UNSUPPORTED"):
            route_event(event, current_generation=7)

    def test_same_exact_event_engine_and_policy_replay_is_deterministic(self):
        event = base_event()
        event.update(novelty=0.8, zero_relevance=0.8)
        a = route_event(event, current_generation=7, engine=local_engine())
        b = route_event(event, current_generation=7, engine=local_engine())
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.decision_sha256, b.decision_sha256)
        self.assertEqual(a, b)

    def test_engine_identity_change_changes_route_decision_identity(self):
        event = base_event()
        event["novelty"] = 0.8
        a = route_event(event, current_generation=7, engine=local_engine("a" * 64))
        b = route_event(event, current_generation=7, engine=local_engine("c" * 64))
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_causal_event_alias_collision_pair_is_separated(self):
        """GO unusual discriminator: same routing result, distinct causal event identity."""
        event_a = base_event("evt-causal-A")
        event_b = base_event("evt-causal-B")
        event_a.update(novelty=0.8, zero_relevance=0.8)
        event_b.update(novelty=0.8, zero_relevance=0.8)
        a = route_event(event_a, current_generation=7, engine=local_engine())
        b = route_event(event_b, current_generation=7, engine=local_engine())
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)


if __name__ == "__main__":
    unittest.main()
