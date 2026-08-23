import unittest

from reactive_event_router_v1 import ReactiveRoutingError, assert_inference_echo, route_event
from typed_canonical_v1 import SCHEMA as CANONICALIZATION_SCHEMA


ENGINE_A_SHA256 = "a" * 64
ENGINE_B_SHA256 = "b" * 64


def base_event():
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": 7,
        "novelty": 0.05,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False,
    }


def bind_local_engine(event, *, artifact_sha256=ENGINE_A_SHA256):
    event.update(
        requested_internal_provider="hcu",
        resolved_internal_engine="hcu_local_08b",
        resolved_internal_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_internal_engine_artifact_sha256=artifact_sha256,
    )
    return event


def route(event, *, current_generation=7, admitted_artifact=ENGINE_A_SHA256):
    registry = None
    if event.get("resolved_internal_engine") is not None:
        registry = {"hcu_local_08b": admitted_artifact}
    return route_event(
        event,
        current_generation=current_generation,
        admitted_engine_artifacts=registry,
    )


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route(base_event())
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.canonicalization_schema, CANONICALIZATION_SCHEMA)
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)
        self.assertEqual(len(decision.event_sha256), 64)
        self.assertEqual(len(decision.router_policy_sha256), 64)
        self.assertIsNone(decision.resolved_engine_identity)
        self.assertIsNone(decision.engine_identity_sha256)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = bind_local_engine(base_event()); e.update(contradiction=0.8, uncertainty=0.7)
        decision = route(e)
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(decision.resolved_engine_artifact_sha256, ENGINE_A_SHA256)

    def test_effect_pressure_adds_simulation_zero_model_and_projection(self):
        e = bind_local_engine(base_event()); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route(e)
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_unknown_or_external_provider_fails_closed(self):
        for provider in ("NVIDIA", "mistral", "future-free-cloud"):
            e = base_event(); e["requested_internal_provider"] = provider
            with self.subTest(provider=provider):
                with self.assertRaisesRegex(ReactiveRoutingError, "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN"):
                    route(e)

    def test_model_activation_without_bound_engine_fails_closed(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE"):
            route(e)

    def test_engine_artifact_must_match_external_admission_lock(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ARTIFACT_SHA256_MISMATCH"):
            route(e, admitted_artifact=ENGINE_B_SHA256)

    def test_engine_artifact_registry_is_required_for_model_binding(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ARTIFACT_REGISTRY_REQUIRED"):
            route_event(e, current_generation=7, admitted_engine_artifacts=None)

    def test_unknown_engine_identity_fails_closed(self):
        e = base_event(); e.update(
            requested_internal_provider="hcu",
            resolved_internal_engine="hcu_local_future",
            resolved_internal_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_internal_engine_artifact_sha256=ENGINE_A_SHA256,
        )
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_NOT_ADMITTED"):
            route_event(e, current_generation=7, admitted_engine_artifacts={"hcu_local_future": ENGINE_A_SHA256})

    def test_engine_class_mismatch_fails_closed(self):
        e = base_event(); e.update(
            requested_internal_provider="hcu",
            resolved_internal_engine="hcu_local_08b",
            resolved_internal_engine_class="EXTERNAL_API",
            resolved_internal_engine_artifact_sha256=ENGINE_A_SHA256,
        )
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_CLASS_MISMATCH"):
            route(e)

    def test_canonicalization_version_mismatch_or_downgrade_fails_closed(self):
        for value in (None, "PYTHON_JSON_SORT_KEYS_COMPACT_UTF8/v1", "HCU_TYPED_CANONICAL/v0"):
            e = base_event()
            if value is None:
                del e["canonicalization_schema"]
            else:
                e["canonicalization_schema"] = value
            with self.subTest(value=value):
                with self.assertRaisesRegex(ReactiveRoutingError, "CANONICALIZATION_SCHEMA_MISMATCH_OR_DOWNGRADE"):
                    route(e)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route(base_event(), current_generation=8)

    def test_same_input_is_deterministic_despite_mapping_order(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        a = route(e)
        b = route(dict(reversed(list(e.items()))))
        self.assertEqual(a, b)

    def test_negative_zero_and_positive_zero_share_causal_identity(self):
        a_event = base_event(); a_event["novelty"] = -0.0
        b_event = base_event(); b_event["novelty"] = 0.0
        a = route(a_event)
        b = route(b_event)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.decision_sha256, b.decision_sha256)

    def test_distinct_events_with_same_route_do_not_alias_decision_identity(self):
        a_event = bind_local_engine(base_event()); a_event.update(novelty=0.80, zero_relevance=0.80)
        b_event = bind_local_engine(base_event()); b_event.update(novelty=0.81, zero_relevance=0.80)
        a = route(a_event)
        b = route(b_event)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_engine_binding_is_part_of_route_identity(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        decision = route(e)
        self.assertEqual(len(decision.engine_identity_sha256), 64)
        self.assertEqual(len(decision.decision_sha256), 64)

    def test_same_causal_event_engine_artifact_flip_changes_route_identity_only(self):
        # Regression-only. The shared GO unusual discriminator was already consumed upstream.
        a_event = bind_local_engine(base_event(), artifact_sha256=ENGINE_A_SHA256); a_event.update(novelty=0.8)
        b_event = bind_local_engine(base_event(), artifact_sha256=ENGINE_B_SHA256); b_event.update(novelty=0.8)
        a = route(a_event, admitted_artifact=ENGINE_A_SHA256)
        b = route(b_event, admitted_artifact=ENGINE_B_SHA256)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.engine_identity_sha256, b.engine_identity_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_inference_receipt_must_echo_canonical_event_route_and_engine(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        decision = route(e)
        receipt = {
            "canonicalization_schema": decision.canonicalization_schema,
            "event_sha256": decision.event_sha256,
            "decision_sha256": decision.decision_sha256,
            "engine_identity_sha256": decision.engine_identity_sha256,
            "resolved_engine_identity": decision.resolved_engine_identity,
            "resolved_engine_class": decision.resolved_engine_class,
            "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
        }
        assert_inference_echo(decision, receipt)
        poisoned = dict(receipt); poisoned["canonicalization_schema"] = "HCU_TYPED_CANONICAL/v0"
        with self.assertRaisesRegex(ReactiveRoutingError, "CANONICALIZATION_SCHEMA_MISMATCH"):
            assert_inference_echo(decision, poisoned)


if __name__ == "__main__":
    unittest.main()
