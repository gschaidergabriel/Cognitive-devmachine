import unittest

from reactive_event_router_v1 import ReactiveRoutingError, assert_inference_echo, route_event


ENGINE_A_SHA256 = "a" * 64
ENGINE_B_SHA256 = "b" * 64


def engine_registry(*, artifact_sha256=ENGINE_A_SHA256, network_required=False):
    return {
        "hcu_local_08b": {
            "engine_id": "hcu_local_08b",
            "engine_class": "LOCAL_SHARED_WEIGHT_08B",
            "artifact_sha256": artifact_sha256,
            "runtime_identity": "test-runtime@sha256:runtime-a",
            "checkpoint_identity": "test-checkpoint@sha256:checkpoint-a",
            "tokenizer_identity": "test-tokenizer@sha256:tokenizer-a",
            "network_required": network_required,
            "secret_lookup_required": False,
        }
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


def bind_local_engine(event, *, artifact_sha256=ENGINE_A_SHA256):
    event.update(
        requested_internal_provider="hcu",
        resolved_internal_engine="hcu_local_08b",
        resolved_internal_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_internal_engine_artifact_sha256=artifact_sha256,
    )
    return event


def routed(event, *, artifact_sha256=ENGINE_A_SHA256):
    return route_event(
        event,
        current_generation=7,
        engine_registry=engine_registry(artifact_sha256=artifact_sha256),
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
        self.assertEqual(len(decision.router_policy_sha256), 64)
        self.assertIsNone(decision.resolved_engine_identity)
        self.assertIsNone(decision.engine_identity_sha256)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = bind_local_engine(base_event()); e.update(contradiction=0.8, uncertainty=0.7)
        decision = routed(e)
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(decision.resolved_engine_artifact_sha256, ENGINE_A_SHA256)
        self.assertEqual(decision.resolved_engine_runtime_identity, "test-runtime@sha256:runtime-a")
        self.assertEqual(decision.resolved_engine_checkpoint_identity, "test-checkpoint@sha256:checkpoint-a")
        self.assertEqual(decision.resolved_engine_tokenizer_identity, "test-tokenizer@sha256:tokenizer-a")
        self.assertEqual(len(decision.engine_identity_sha256), 64)

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = bind_local_engine(base_event()); e.update(effect_pressure=0.9, zero_relevance=0.9)
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

    def test_unknown_future_provider_fails_closed(self):
        e = base_event(); e["requested_internal_provider"] = "future-free-cloud"
        with self.assertRaisesRegex(ReactiveRoutingError, "UNKNOWN_OR_EXTERNAL_PROVIDER_FORBIDDEN"):
            route_event(e, current_generation=7)

    def test_missing_causal_identity_fails_closed_before_routing(self):
        e = base_event(); del e["causal_id"]
        with self.assertRaisesRegex(ReactiveRoutingError, "causal_id"):
            route_event(e, current_generation=7)

    def test_missing_provenance_fails_closed_before_routing(self):
        e = base_event(); del e["provenance"]
        with self.assertRaisesRegex(ReactiveRoutingError, "PROVENANCE_MAPPING_REQUIRED"):
            route_event(e, current_generation=7)

    def test_model_activation_without_bound_engine_fails_closed(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ACTIVATION_REQUIRES_ADMITTED_INTERNAL_ENGINE"):
            route_event(e, current_generation=7)

    def test_missing_engine_registry_fails_closed(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_REGISTRY_REQUIRED"):
            route_event(e, current_generation=7)

    def test_event_cannot_self_assert_alternate_engine_bytes(self):
        e = bind_local_engine(base_event(), artifact_sha256=ENGINE_B_SHA256); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_REGISTRY_ARTIFACT_MISMATCH"):
            route_event(e, current_generation=7, engine_registry=engine_registry(artifact_sha256=ENGINE_A_SHA256))

    def test_engine_registry_cannot_require_network(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "INTERNAL_ENGINE_NETWORK_DEPENDENCY_FORBIDDEN"):
            route_event(e, current_generation=7, engine_registry=engine_registry(network_required=True))

    def test_model_cognition_permission_is_enforced(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8, permissions={"cognition": False})
        with self.assertRaisesRegex(ReactiveRoutingError, "COGNITION_PERMISSION_DENIED"):
            routed(e)

    def test_model_lane_budget_is_enforced(self):
        e = bind_local_engine(base_event()); e.update(
            contradiction=0.8,
            uncertainty=0.8,
            budget={"allow_model_cognition": True, "max_model_lanes": 2},
        )
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_LANE_BUDGET_EXCEEDED"):
            routed(e)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_same_input_is_deterministic(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        a = routed(e)
        b = routed(dict(reversed(list(e.items()))))
        self.assertEqual(a, b)

    def test_distinct_events_with_same_route_do_not_alias_decision_identity(self):
        a_event = bind_local_engine(base_event()); a_event.update(event_id="evt-A", novelty=0.80, zero_relevance=0.80)
        b_event = bind_local_engine(base_event()); b_event.update(event_id="evt-B", novelty=0.81, zero_relevance=0.80)
        a = routed(a_event)
        b = routed(b_event)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_engine_binding_is_part_of_route_identity(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        decision = routed(e)
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(len(decision.engine_identity_sha256), 64)
        self.assertEqual(len(decision.decision_sha256), 64)

    def test_same_causal_event_engine_artifact_flip_changes_route_identity_only(self):
        # Unusual discriminator already selected for this GO: hold event semantics and
        # route topology fixed, perturb only exact admitted engine bytes. Event identity
        # must stay stable while engine and route decision identities change.
        a_event = bind_local_engine(base_event(), artifact_sha256=ENGINE_A_SHA256); a_event.update(novelty=0.8)
        b_event = bind_local_engine(base_event(), artifact_sha256=ENGINE_B_SHA256); b_event.update(novelty=0.8)
        a = routed(a_event, artifact_sha256=ENGINE_A_SHA256)
        b = routed(b_event, artifact_sha256=ENGINE_B_SHA256)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.engine_identity_sha256, b.engine_identity_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_inference_receipt_must_echo_causal_event_route_and_engine(self):
        e = bind_local_engine(base_event()); e.update(novelty=0.8)
        decision = routed(e)
        receipt = {
            "event_sha256": decision.event_sha256,
            "causal_id": decision.causal_id,
            "decision_sha256": decision.decision_sha256,
            "engine_identity_sha256": decision.engine_identity_sha256,
            "resolved_engine_identity": decision.resolved_engine_identity,
        }
        assert_inference_echo(decision, receipt)
        poisoned = dict(receipt); poisoned["causal_id"] = "wrong-causal"
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_CAUSAL_ID_MISMATCH"):
            assert_inference_echo(decision, poisoned)


if __name__ == "__main__":
    unittest.main()
