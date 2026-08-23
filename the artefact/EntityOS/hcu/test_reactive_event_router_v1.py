import unittest

from reactive_event_router_v1 import (
    ADMITTED_ENGINE_CLASS,
    ReactiveRoutingError,
    route_event,
)

ENGINE_A = "11" * 32
ENGINE_B = "22" * 32


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
        "due_recheck": False,
    }


def active_event():
    event = base_event()
    event.update(
        contradiction=0.8,
        uncertainty=0.7,
        resolved_engine_class=ADMITTED_ENGINE_CLASS,
        resolved_engine_sha256=ENGINE_A,
    )
    return event


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only_without_engine(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertEqual(decision.engine_class, "DETERMINISTIC_SCRIPT")
        self.assertIsNone(decision.engine_sha256)
        self.assertFalse(decision.external_provider_dependency)

    def test_active_event_requires_positive_engine_identity(self):
        event = base_event()
        event.update(contradiction=0.8, uncertainty=0.7)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_CLASS_NOT_ADMITTED"):
            route_event(event, current_generation=7)

    def test_unknown_engine_class_fails_closed(self):
        event = active_event()
        event["resolved_engine_class"] = "FUTURE_PROVIDER_ALIAS"
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_CLASS_NOT_ADMITTED"):
            route_event(event, current_generation=7)

    def test_invalid_engine_digest_fails_closed(self):
        event = active_event()
        event["resolved_engine_sha256"] = "not-a-digest"
        with self.assertRaisesRegex(ReactiveRoutingError, "SHA256_REQUIRED"):
            route_event(event, current_generation=7)

    def test_any_provider_alias_field_fails_closed(self):
        event = base_event()
        event["requested_internal_provider"] = "unknown-future-provider"
        with self.assertRaisesRegex(ReactiveRoutingError, "PROVIDER_UNSUPPORTED"):
            route_event(event, current_generation=7)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_same_route_different_causal_events_have_distinct_identity(self):
        a = active_event()
        b = active_event()
        a.update(contradiction=0.40, uncertainty=0.60)
        b.update(contradiction=0.95, uncertainty=0.99)
        da = route_event(a, current_generation=7)
        db = route_event(b, current_generation=7)
        self.assertEqual(da.model_lanes, db.model_lanes)
        self.assertNotEqual(da.event_sha256, db.event_sha256)
        self.assertNotEqual(da.decision_sha256, db.decision_sha256)

    def test_same_event_different_admitted_engine_digest_changes_route_identity(self):
        a = active_event()
        b = active_event()
        b["resolved_engine_sha256"] = ENGINE_B
        da = route_event(a, current_generation=7)
        db = route_event(b, current_generation=7)
        self.assertEqual(da.event_sha256, db.event_sha256)
        self.assertNotEqual(da.engine_sha256, db.engine_sha256)
        self.assertNotEqual(da.decision_sha256, db.decision_sha256)

    def test_same_exact_event_replay_is_deterministic(self):
        event = active_event()
        a = route_event(event, current_generation=7)
        b = route_event(event, current_generation=7)
        self.assertEqual(a, b)

    def test_script_only_event_rejects_model_engine_binding(self):
        event = base_event()
        event.update(
            resolved_engine_class=ADMITTED_ENGINE_CLASS,
            resolved_engine_sha256=ENGINE_A,
        )
        with self.assertRaisesRegex(ReactiveRoutingError, "SCRIPT_ONLY_EVENT_MUST_NOT_BIND_MODEL_ENGINE"):
            route_event(event, current_generation=7)


if __name__ == "__main__":
    unittest.main()
