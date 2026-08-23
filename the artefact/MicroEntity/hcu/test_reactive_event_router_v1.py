import unittest

from reactive_event_router_v1 import ReactiveRoutingError, route_event


def base_event():
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "entity_generation": 7,
        "novelty": 0.05,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False
    }


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        decision = route_event(e, current_generation=7)
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = base_event(); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_event(e, current_generation=7)
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_nvidia_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "NVIDIA"
        with self.assertRaisesRegex(ReactiveRoutingError, "EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_mistral_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "mistral"
        with self.assertRaisesRegex(ReactiveRoutingError, "EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_same_input_is_deterministic(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        a = route_event(e, current_generation=7)
        b = route_event(e, current_generation=7)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
