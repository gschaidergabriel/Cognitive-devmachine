import unittest

from reactive_event_router_v1 import (
    HASH_SERIALIZATION_SCHEMA,
    ReactiveRoutingError,
    assert_inference_echo,
    route_event,
)


ENGINE_A_SHA256 = "a" * 64
ENGINE_B_SHA256 = "b" * 64


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


def local_engine_binding(*, artifact_sha256=ENGINE_A_SHA256):
    return {
        "resolved_internal_engine": "hcu_local_08b",
        "resolved_internal_engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "resolved_internal_engine_artifact_sha256": artifact_sha256,
    }


def admitted_registry(*, artifact_sha256=ENGINE_A_SHA256):
    return {"hcu_local_08b": artifact_sha256}


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)
        self.assertEqual(decision.hash_serialization_schema, HASH_SERIALIZATION_SCHEMA)
        self.assertEqual(len(decision.event_sha256), 64)
        self.assertEqual(len(decision.router_policy_sha256), 64)
        self.assertIsNone(decision.resolved_engine_identity)
        self.assertIsNone(decision.resolved_engine_class)
        self.assertIsNone(decision.resolved_engine_artifact_sha256)
        self.assertIsNone(decision.engine_identity_sha256)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        decision = route_event(e, current_generation=7, resolved_engine=local_engine_binding(), admitted_engine_artifacts=admitted_registry())
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(decision.resolved_engine_artifact_sha256, ENGINE_A_SHA256)
        self.assertEqual(len(decision.engine_identity_sha256), 64)

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = base_event(); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_event(e, current_generation=7, resolved_engine=local_engine_binding(), admitted_engine_artifacts=admitted_registry())
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_provider_label_cannot_be_internal_cognitive_authority(self):
        e = base_event(); e["requested_internal_provider"] = "hcu"
        with self.assertRaisesRegex(ReactiveRoutingError, "ADMISSION_FIELDS_FORBIDDEN_IN_EVENT_PAYLOAD"):
            route_event(e, current_generation=7)

    def test_event_cannot_self_assert_resolved_engine(self):
        e = base_event(); e.update(
            novelty=0.8,
            resolved_internal_engine="hcu_local_08b",
            resolved_internal_engine_class="LOCAL_SHARED_WEIGHT_08B",
            resolved_internal_engine_artifact_sha256=ENGINE_A_SHA256,
        )
        with self.assertRaisesRegex(ReactiveRoutingError, "ADMISSION_FIELDS_FORBIDDEN_IN_EVENT_PAYLOAD"):
            route_event(e, current_generation=7, resolved_engine=local_engine_binding(), admitted_engine_artifacts=admitted_registry())

    def test_model_activation_without_bound_engine_fails_closed(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE"):
            route_event(e, current_generation=7)

    def test_missing_engine_artifact_digest_fails_closed(self):
        binding = local_engine_binding(); binding.pop("resolved_internal_engine_artifact_sha256")
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256"):
            route_event(e, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())

    def test_unknown_engine_identity_fails_closed(self):
        binding = local_engine_binding(); binding["resolved_internal_engine"] = "hcu_local_future"
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_NOT_ADMITTED"):
            route_event(e, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())

    def test_engine_class_mismatch_fails_closed(self):
        binding = local_engine_binding(); binding["resolved_internal_engine_class"] = "EXTERNAL_API"
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_CLASS_MISMATCH"):
            route_event(e, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())

    def test_extra_engine_binding_semantics_fail_closed(self):
        binding = local_engine_binding(); binding["provider"] = "hidden"
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_BINDING_SCHEMA_INVALID"):
            route_event(e, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())

    def test_script_only_event_must_not_select_engine(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE"):
            route_event(base_event(), current_generation=7, resolved_engine=local_engine_binding(), admitted_engine_artifacts=admitted_registry())

    def test_missing_artifact_registry_fails_closed(self):
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ADMITTED_INTERNAL_ENGINE_ARTIFACT_REGISTRY_REQUIRED"):
            route_event(e, current_generation=7, resolved_engine=local_engine_binding())

    def test_artifact_registry_mismatch_fails_closed(self):
        e = base_event(); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "RESOLVED_INTERNAL_ENGINE_ARTIFACT_SHA256_MISMATCH"):
            route_event(
                e,
                current_generation=7,
                resolved_engine=local_engine_binding(artifact_sha256=ENGINE_A_SHA256),
                admitted_engine_artifacts=admitted_registry(artifact_sha256=ENGINE_B_SHA256),
            )

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_same_input_is_deterministic(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        binding = local_engine_binding()
        a = route_event(e, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())
        b = route_event(
            dict(reversed(list(e.items()))),
            current_generation=7,
            resolved_engine=dict(reversed(list(binding.items()))),
            admitted_engine_artifacts=dict(reversed(list(admitted_registry().items()))),
        )
        self.assertEqual(a, b)

    def test_distinct_events_with_same_route_do_not_alias_decision_identity(self):
        a_event = base_event(); a_event.update(novelty=0.80, zero_relevance=0.80)
        b_event = base_event(); b_event.update(novelty=0.81, zero_relevance=0.80)
        binding = local_engine_binding()
        a = route_event(a_event, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())
        b = route_event(b_event, current_generation=7, resolved_engine=binding, admitted_engine_artifacts=admitted_registry())
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_same_causal_event_engine_artifact_flip_changes_route_identity_only(self):
        # Regression-only follow-up. The shared GO unusual experiment was already consumed
        # by same-route causal-alias stress; this byte-flip check must not count again.
        event = base_event(); event.update(novelty=0.8)
        a = route_event(event, current_generation=7, resolved_engine=local_engine_binding(artifact_sha256=ENGINE_A_SHA256), admitted_engine_artifacts=admitted_registry(artifact_sha256=ENGINE_A_SHA256))
        b = route_event(event, current_generation=7, resolved_engine=local_engine_binding(artifact_sha256=ENGINE_B_SHA256), admitted_engine_artifacts=admitted_registry(artifact_sha256=ENGINE_B_SHA256))
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.engine_identity_sha256, b.engine_identity_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_inference_receipt_must_echo_event_route_and_engine(self):
        e = base_event(); e.update(novelty=0.8)
        decision = route_event(e, current_generation=7, resolved_engine=local_engine_binding(), admitted_engine_artifacts=admitted_registry())
        receipt = {
            "hash_serialization_schema": decision.hash_serialization_schema,
            "event_sha256": decision.event_sha256,
            "decision_sha256": decision.decision_sha256,
            "engine_identity_sha256": decision.engine_identity_sha256,
            "resolved_engine_identity": decision.resolved_engine_identity,
            "resolved_engine_class": decision.resolved_engine_class,
            "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
        }
        assert_inference_echo(decision, receipt)
        poisoned = dict(receipt); poisoned["event_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_EVENT_SHA256_MISMATCH"):
            assert_inference_echo(decision, poisoned)
        poisoned = dict(receipt); poisoned["hash_serialization_schema"] = "HCU_OTHER_SERIALIZER/v1"
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_HASH_SERIALIZATION_SCHEMA_MISMATCH"):
            assert_inference_echo(decision, poisoned)


if __name__ == "__main__":
    unittest.main()
