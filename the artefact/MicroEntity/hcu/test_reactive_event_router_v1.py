import unittest

from reactive_event_router_v1 import (
    ReactiveRoutingError,
    route_event,
    verify_inference_receipt,
)


RUNTIME_SHA = "a" * 64


def base_event():
    return {
        "schema": "HCU_REACTIVE_EVENT/v1",
        "ingress_id": "ingress-001",
        "causal_id": "causal-001",
        "entity_generation": 7,
        "novelty": 0.05,
        "contradiction": 0.0,
        "uncertainty": 0.10,
        "forecast_need": 0.0,
        "effect_pressure": 0.0,
        "zero_relevance": 0.10,
        "due_recheck": False,
    }


def local_engine(engine_id="local-08b-primary", runtime_sha=RUNTIME_SHA):
    return {
        "schema": "HCU_ENGINE_BINDING/v1",
        "execution_scope": "LOCAL_ONLY",
        "engine_id": engine_id,
        "engine_class": "LOCAL_SHARED_WEIGHT_08B",
        "runtime_identity_sha256": runtime_sha,
    }


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only_and_binds_causal_event(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertEqual(decision.resolved_engine_id, "xpu.script.v1")
        self.assertEqual(decision.ingress_id, "ingress-001")
        self.assertEqual(decision.causal_id, "causal-001")
        self.assertEqual(len(decision.event_sha256), 64)
        self.assertFalse(decision.external_provider_dependency)

    def test_contradiction_requires_positive_local_engine_binding(self):
        e = base_event(); e.update(contradiction=0.8, uncertainty=0.7)
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ENGINE_BINDING_REQUIRED"):
            route_event(e, current_generation=7)
        decision = route_event(e, current_generation=7, engine_binding=local_engine())
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")

    def test_unknown_engine_class_fails_closed_instead_of_denylist_fail_open(self):
        e = base_event(); e.update(contradiction=0.8)
        binding = local_engine(); binding["engine_class"] = "UNRECOGNIZED_LOCAL_OR_EXTERNAL"
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ENGINE_CLASS_NOT_ADMITTED"):
            route_event(e, current_generation=7, engine_binding=binding)

    def test_provider_selector_is_not_internal_authority(self):
        e = base_event(); e["requested_internal_provider"] = "new-provider-never-seen-before"
        with self.assertRaisesRegex(ReactiveRoutingError, "LEGACY_PROVIDER_SELECTOR_NOT_ADMITTED"):
            route_event(e, current_generation=7)

    def test_external_or_unbound_runtime_scope_fails_closed(self):
        e = base_event(); e.update(effect_pressure=0.9)
        binding = local_engine(); binding["execution_scope"] = "REMOTE"
        with self.assertRaisesRegex(ReactiveRoutingError, "EXECUTION_SCOPE_NOT_LOCAL"):
            route_event(e, current_generation=7, engine_binding=binding)

    def test_model_binding_rejects_provider_fields(self):
        e = base_event(); e.update(effect_pressure=0.9)
        binding = local_engine(); binding["provider"] = "anything"
        with self.assertRaisesRegex(ReactiveRoutingError, "PROVIDER_SELECTOR_NOT_ADMITTED"):
            route_event(e, current_generation=7, engine_binding=binding)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_materially_different_events_same_route_do_not_alias_decision_identity(self):
        a = base_event(); a.update(novelty=0.60)
        b = base_event(); b.update(novelty=0.70)
        da = route_event(a, current_generation=7, engine_binding=local_engine())
        db = route_event(b, current_generation=7, engine_binding=local_engine())
        self.assertEqual(da.model_lanes, db.model_lanes)
        self.assertNotEqual(da.event_sha256, db.event_sha256)
        self.assertNotEqual(da.decision_sha256, db.decision_sha256)

    def test_same_exact_event_replay_is_deterministic(self):
        e = base_event(); e.update(novelty=0.8, zero_relevance=0.8)
        binding = local_engine()
        a = route_event(e, current_generation=7, engine_binding=binding)
        b = route_event(e, current_generation=7, engine_binding=binding)
        self.assertEqual(a, b)

    def test_distinct_admitted_engine_identities_change_decision_identity(self):
        e = base_event(); e.update(contradiction=0.8)
        a = route_event(e, current_generation=7, engine_binding=local_engine("local-08b-a", "a" * 64))
        b = route_event(e, current_generation=7, engine_binding=local_engine("local-08b-b", "b" * 64))
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_downstream_receipt_must_echo_event_route_and_engine_identity(self):
        e = base_event(); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_event(e, current_generation=7, engine_binding=local_engine())
        receipt = {
            "schema": "HCU_INFERENCE_RECEIPT/v1",
            "event_sha256": decision.event_sha256,
            "decision_sha256": decision.decision_sha256,
            "entity_generation": decision.entity_generation,
            "resolved_engine_id": decision.resolved_engine_id,
            "resolved_engine_class": decision.resolved_engine_class,
            "resolved_runtime_identity_sha256": decision.resolved_runtime_identity_sha256,
        }
        verify_inference_receipt(decision, receipt)
        poisoned = dict(receipt); poisoned["event_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReactiveRoutingError, "EVENT_SHA256_MISMATCH"):
            verify_inference_receipt(decision, poisoned)


if __name__ == "__main__":
    unittest.main()
