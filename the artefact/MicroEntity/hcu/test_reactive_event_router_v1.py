import unittest

from reactive_event_router_v1 import ReactiveRoutingError, route_event


CHECKPOINT_A = "a" * 64
CHECKPOINT_B = "b" * 64


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


def local_engine(
    engine_identity="hcu.local.08b.primary",
    checkpoint_sha256=CHECKPOINT_A,
    requested_provider_identity=None,
):
    return {
        "engine_identity": engine_identity,
        "engine_class": "BUNDLED_LOCAL_MODEL",
        "provider_identity": "local",
        "requested_provider_identity": requested_provider_identity,
        "checkpoint_sha256": checkpoint_sha256,
    }


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only_with_internal_script_identity(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)
        self.assertEqual(decision.engine_identity, "hcu.script-plane.v1")
        self.assertEqual(decision.engine_class, "DETERMINISTIC_SCRIPT")
        self.assertEqual(len(decision.event_sha256), 64)

    def test_contradiction_requires_and_binds_local_model_engine(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        decision = route_event(e, current_generation=7, resolved_engine=local_engine())
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.engine_identity, "hcu.local.08b.primary")
        self.assertEqual(decision.engine_checkpoint_sha256, CHECKPOINT_A)

    def test_model_activation_without_positive_engine_binding_fails_closed(self):
        e = base_event(); e.update(contradiction=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_MODEL_ENGINE_BINDING_REQUIRED"):
            route_event(e, current_generation=7)

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = base_event(); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_event(e, current_generation=7, resolved_engine=local_engine())
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_known_external_provider_cannot_be_internal_cognitive_dependency(self):
        for provider in ("NVIDIA", "mistral", "Groq", "openrouter", "Together", "claude_code"):
            with self.subTest(provider=provider):
                e = base_event(); e["requested_internal_provider"] = provider
                with self.assertRaisesRegex(ReactiveRoutingError, "EXTERNAL_PROVIDER_FORBIDDEN"):
                    route_event(e, current_generation=7, resolved_engine=local_engine())

    def test_arbitrary_unknown_provider_without_positive_resolution_fails_closed(self):
        e = base_event(); e["requested_internal_provider"] = "future-cloud-xyz"
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_INTERNAL_PROVIDER_UNRESOLVED"):
            route_event(e, current_generation=7)

    def test_unknown_alias_can_only_pass_when_resolver_binds_same_alias_to_local_engine(self):
        e = base_event(); e.update(requested_internal_provider=" local-alias ", contradiction=0.8)
        decision = route_event(
            e,
            current_generation=7,
            resolved_engine=local_engine(requested_provider_identity="local-alias"),
        )
        self.assertEqual(decision.requested_provider_identity, "local-alias")
        self.assertEqual(decision.engine_provider_identity, "local")

    def test_requested_provider_and_resolved_engine_alias_must_match(self):
        e = base_event(); e.update(requested_internal_provider="local-a", contradiction=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_PROVIDER_ENGINE_RESOLUTION_MISMATCH"):
            route_event(
                e,
                current_generation=7,
                resolved_engine=local_engine(requested_provider_identity="local-b"),
            )

    def test_external_engine_class_is_rejected_even_without_provider_label(self):
        e = base_event(); e.update(contradiction=0.8)
        binding = local_engine()
        binding["engine_class"] = "REMOTE_API_MODEL"
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_CLASS_NOT_ADMITTED"):
            route_event(e, current_generation=7, resolved_engine=binding)

    def test_external_engine_provider_identity_is_rejected(self):
        e = base_event(); e.update(contradiction=0.8)
        binding = local_engine()
        binding["provider_identity"] = "remote"
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_PROVIDER_NOT_ADMITTED"):
            route_event(e, current_generation=7, resolved_engine=binding)

    def test_bundled_local_model_requires_exact_checkpoint_digest(self):
        e = base_event(); e.update(contradiction=0.8)
        for bad in (None, "", "xyz", "a" * 63, "g" * 64):
            with self.subTest(checkpoint=bad):
                binding = local_engine(checkpoint_sha256=bad)
                with self.assertRaises(ReactiveRoutingError):
                    route_event(e, current_generation=7, resolved_engine=binding)

    def test_uppercase_checkpoint_digest_is_canonicalized(self):
        e = base_event(); e.update(contradiction=0.8)
        decision = route_event(
            e,
            current_generation=7,
            resolved_engine=local_engine(checkpoint_sha256="A" * 64),
        )
        self.assertEqual(decision.engine_checkpoint_sha256, CHECKPOINT_A)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_same_exact_event_engine_and_policy_replay_is_deterministic(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        binding = local_engine()
        a = route_event(e, current_generation=7, resolved_engine=binding)
        b = route_event(dict(e), current_generation=7, resolved_engine=dict(binding))
        self.assertEqual(a, b)

    def test_materially_different_events_with_same_route_result_do_not_alias(self):
        a_event = base_event(); a_event.update(contradiction=0.80, uncertainty=0.70)
        b_event = base_event(); b_event.update(contradiction=0.81, uncertainty=0.70)
        a = route_event(a_event, current_generation=7, resolved_engine=local_engine())
        b = route_event(b_event, current_generation=7, resolved_engine=local_engine())
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_same_event_with_distinct_local_engines_does_not_alias(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        a = route_event(
            e,
            current_generation=7,
            resolved_engine=local_engine(engine_identity="hcu.local.08b.a", checkpoint_sha256=CHECKPOINT_A),
        )
        b = route_event(
            e,
            current_generation=7,
            resolved_engine=local_engine(engine_identity="hcu.local.08b.b", checkpoint_sha256=CHECKPOINT_B),
        )
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_mapping_order_does_not_change_event_or_decision_identity(self):
        e = base_event(); e.update(contradiction=0.8)
        reversed_event = dict(reversed(list(e.items())))
        a = route_event(e, current_generation=7, resolved_engine=local_engine())
        b = route_event(reversed_event, current_generation=7, resolved_engine=local_engine())
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.decision_sha256, b.decision_sha256)


if __name__ == "__main__":
    unittest.main()
