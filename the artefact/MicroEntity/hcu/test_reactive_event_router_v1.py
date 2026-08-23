import unittest

from reactive_event_router_v1 import (
    HASH_SERIALIZATION_SCHEMA,
    EngineAdmission,
    ReactiveRoutingError,
    assert_inference_echo,
    route_event,
)


ENGINE_A_SHA256 = "a" * 64
ENGINE_B_SHA256 = "b" * 64
ENTRY_EVENT_SHA256 = "e" * 64
ENTRY_ADMISSION_A_SHA256 = "1" * 64
ENTRY_ADMISSION_B_SHA256 = "2" * 64


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


def request_local_engine(event, *, provider="hcu"):
    event["requested_internal_provider"] = provider
    return event


def control_plane_admission(
    *,
    provider="hcu",
    identity="hcu_local_08b",
    engine_class="LOCAL_SHARED_WEIGHT_08B",
    artifact_sha256=ENGINE_A_SHA256,
):
    return EngineAdmission(
        provider_alias=provider,
        engine_identity=identity,
        engine_class=engine_class,
        engine_artifact_sha256=artifact_sha256,
    )


def bind_entry_projection(
    event,
    *,
    ingress_id="ingress:test:a",
    admission_sha256=ENTRY_ADMISSION_A_SHA256,
    event_sha256=ENTRY_EVENT_SHA256,
):
    event.update(
        ingress_id=ingress_id,
        causal_id="causal:test:entry",
        entry_event_sha256=event_sha256,
        entry_admission_sha256=admission_sha256,
        entry_canonicalization_schema=HASH_SERIALIZATION_SCHEMA,
    )
    return event


def engine_registry(*, artifact_sha256=ENGINE_A_SHA256):
    return {"hcu_local_08b": artifact_sha256}


def route_model(event, *, artifact_sha256=ENGINE_A_SHA256, admission=None):
    return route_event(
        event,
        current_generation=7,
        engine_admission=admission or control_plane_admission(artifact_sha256=artifact_sha256),
        admitted_engine_artifacts=engine_registry(artifact_sha256=artifact_sha256),
    )


def route_entry_model(
    event,
    *,
    admission_sha256=ENTRY_ADMISSION_A_SHA256,
    event_sha256=ENTRY_EVENT_SHA256,
    artifact_sha256=ENGINE_A_SHA256,
    admission=None,
):
    return route_event(
        event,
        current_generation=7,
        engine_admission=admission or control_plane_admission(artifact_sha256=artifact_sha256),
        admitted_engine_artifacts=engine_registry(artifact_sha256=artifact_sha256),
        admitted_entry_bindings={admission_sha256: event_sha256},
    )


def inference_receipt(decision):
    return {
        "hash_serialization_schema": decision.hash_serialization_schema,
        "event_sha256": decision.event_sha256,
        "entry_admission_sha256": decision.entry_admission_sha256,
        "decision_sha256": decision.decision_sha256,
        "engine_identity_sha256": decision.engine_identity_sha256,
        "resolved_engine_identity": decision.resolved_engine_identity,
        "resolved_engine_class": decision.resolved_engine_class,
        "resolved_engine_artifact_sha256": decision.resolved_engine_artifact_sha256,
    }


class ReactiveRouterTests(unittest.TestCase):
    def test_low_change_event_stays_script_only(self):
        decision = route_event(base_event(), current_generation=7)
        self.assertEqual(decision.status, "SCRIPT_ONLY")
        self.assertEqual(decision.model_lanes, ())
        self.assertFalse(decision.zero_projection)
        self.assertFalse(decision.external_provider_dependency)
        self.assertEqual(decision.hash_serialization_schema, HASH_SERIALIZATION_SCHEMA)
        self.assertEqual(len(decision.event_sha256), 64)
        self.assertIsNone(decision.entry_admission_sha256)
        self.assertEqual(len(decision.router_policy_sha256), 64)
        self.assertIsNone(decision.resolved_engine_identity)
        self.assertIsNone(decision.resolved_engine_class)
        self.assertIsNone(decision.resolved_engine_artifact_sha256)
        self.assertIsNone(decision.engine_identity_sha256)

    def test_contradiction_selectively_activates_world_hypothesis_critic(self):
        e = request_local_engine(base_event()); e.update(contradiction=0.8, uncertainty=0.7)
        decision = route_model(e)
        self.assertEqual(set(decision.model_lanes), {"world", "hypothesis", "critic"})
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(decision.resolved_engine_artifact_sha256, ENGINE_A_SHA256)
        self.assertEqual(len(decision.engine_identity_sha256), 64)

    def test_effect_pressure_adds_simulation_zero_model_and_claycode_projection(self):
        e = request_local_engine(base_event()); e.update(effect_pressure=0.9, zero_relevance=0.9)
        decision = route_model(e)
        self.assertIn("simulation", decision.model_lanes)
        self.assertIn("zero_model", decision.model_lanes)
        self.assertTrue(decision.zero_projection)
        self.assertEqual(decision.zero_projection_format, "ClayCode")

    def test_nvidia_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "NVIDIA"
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_INTERNAL_PROVIDER:NOT_ADMITTED"):
            route_event(e, current_generation=7)

    def test_mistral_cannot_be_internal_cognitive_dependency(self):
        e = base_event(); e["requested_internal_provider"] = "mistral"
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_INTERNAL_PROVIDER:NOT_ADMITTED"):
            route_event(e, current_generation=7)

    def test_unknown_future_provider_fails_closed(self):
        e = base_event(); e["requested_internal_provider"] = "future-free-cloud"
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_INTERNAL_PROVIDER:NOT_ADMITTED"):
            route_event(e, current_generation=7)

    def test_event_cannot_self_mint_engine_authority(self):
        for field, value in (
            ("resolved_internal_engine", "hcu_local_08b"),
            ("resolved_internal_engine_class", "LOCAL_SHARED_WEIGHT_08B"),
            ("resolved_internal_engine_artifact_sha256", ENGINE_A_SHA256),
            ("engine_identity_sha256", "f" * 64),
        ):
            with self.subTest(field=field):
                e = base_event(); e[field] = value
                with self.assertRaisesRegex(ReactiveRoutingError, "EVENT_MUST_NOT_MINT_ENGINE_AUTHORITY"):
                    route_event(e, current_generation=7)

    def test_model_activation_without_control_plane_engine_admission_fails_closed(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "MODEL_ACTIVATION_REQUIRES_CONTROL_PLANE_ENGINE_ADMISSION"):
            route_event(e, current_generation=7)

    def test_missing_engine_artifact_digest_fails_closed(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        admission = control_plane_admission(artifact_sha256="")
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_ADMISSION_ARTIFACT_SHA256"):
            route_event(e, current_generation=7, engine_admission=admission, admitted_engine_artifacts=engine_registry())

    def test_unknown_engine_identity_fails_closed(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        admission = control_plane_admission(identity="hcu_local_future")
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_ADMISSION_IDENTITY_NOT_ADMITTED"):
            route_event(e, current_generation=7, engine_admission=admission, admitted_engine_artifacts=engine_registry())

    def test_engine_class_mismatch_fails_closed(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        admission = control_plane_admission(engine_class="EXTERNAL_API")
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_ADMISSION_CLASS_MISMATCH"):
            route_event(e, current_generation=7, engine_admission=admission, admitted_engine_artifacts=engine_registry())

    def test_requested_provider_must_match_engine_admission(self):
        e = request_local_engine(base_event(), provider="local"); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "REQUESTED_PROVIDER_ENGINE_ADMISSION_MISMATCH"):
            route_model(e, admission=control_plane_admission(provider="hcu"))

    def test_provider_absent_can_use_positive_control_plane_admission(self):
        e = base_event(); e.update(novelty=0.8)
        decision = route_model(e)
        self.assertEqual(decision.status, "SELECTIVE_MODEL_ACTIVATION")
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")

    def test_script_only_event_rejects_engine_admission(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "SCRIPT_ONLY_EVENT_MUST_NOT_SELECT_INTERNAL_ENGINE"):
            route_model(base_event())

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(ReactiveRoutingError, "STALE_ENTITY_GENERATION"):
            route_event(base_event(), current_generation=8)

    def test_current_generation_bool_fails_closed(self):
        e = dict(base_event()); e["entity_generation"] = 1
        with self.assertRaisesRegex(ReactiveRoutingError, "CURRENT_GENERATION_INVALID"):
            route_event(e, current_generation=True)

    def test_same_input_is_deterministic(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        a = route_model(e)
        b = route_model(dict(reversed(list(e.items()))))
        self.assertEqual(a, b)

    def test_distinct_events_with_same_route_do_not_alias_decision_identity(self):
        a_event = request_local_engine(base_event()); a_event.update(novelty=0.80, zero_relevance=0.80)
        b_event = request_local_engine(base_event()); b_event.update(novelty=0.81, zero_relevance=0.80)
        a = route_model(a_event)
        b = route_model(b_event)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.zero_projection, b.zero_projection)
        self.assertNotEqual(a.event_sha256, b.event_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_engine_binding_is_part_of_route_identity(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8, zero_relevance=0.8)
        decision = route_model(e)
        self.assertEqual(decision.resolved_engine_identity, "hcu_local_08b")
        self.assertEqual(decision.resolved_engine_class, "LOCAL_SHARED_WEIGHT_08B")
        self.assertEqual(len(decision.engine_identity_sha256), 64)
        self.assertEqual(len(decision.decision_sha256), 64)

    def test_engine_admission_artifact_requires_independent_registry(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        admission = control_plane_admission(artifact_sha256=ENGINE_B_SHA256)
        with self.assertRaisesRegex(ReactiveRoutingError, "ENGINE_ADMISSION_ARTIFACT_SHA256_MISMATCH"):
            route_event(e, current_generation=7, engine_admission=admission, admitted_engine_artifacts=engine_registry())

    def test_model_activation_without_independent_artifact_registry_fails_closed(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ADMITTED_INTERNAL_ENGINE_ARTIFACT_REGISTRY_REQUIRED"):
            route_event(e, current_generation=7, engine_admission=control_plane_admission())

    def test_admitted_engine_artifact_rotation_changes_route_identity_only(self):
        # Regression-only follow-up; no additional unusual experiment.
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        a = route_model(e, artifact_sha256=ENGINE_A_SHA256)
        b = route_model(e, artifact_sha256=ENGINE_B_SHA256)
        self.assertEqual(a.event_sha256, b.event_sha256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertNotEqual(a.engine_identity_sha256, b.engine_identity_sha256)
        self.assertNotEqual(a.decision_sha256, b.decision_sha256)

    def test_typed_entry_projection_requires_matching_canonicalization_schema(self):
        for value in (None, "ENTITYOS_HCU_ENTRY_CBOR_RFC8949_SUBSET/v1", "UNKNOWN/v999"):
            with self.subTest(value=value):
                e = request_local_engine(bind_entry_projection(base_event())); e.update(novelty=0.8)
                if value is None:
                    e.pop("entry_canonicalization_schema")
                else:
                    e["entry_canonicalization_schema"] = value
                with self.assertRaisesRegex(ReactiveRoutingError, "ENTRY_CANONICALIZATION_SCHEMA_MISMATCH"):
                    route_entry_model(e)

    def test_typed_entry_projection_requires_independent_admission_binding(self):
        e = request_local_engine(bind_entry_projection(base_event())); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ADMITTED_ENTRY_BINDING_REGISTRY_REQUIRED"):
            route_event(
                e,
                current_generation=7,
                engine_admission=control_plane_admission(),
                admitted_engine_artifacts=engine_registry(),
            )

    def test_typed_entry_projection_rejects_event_identity_not_bound_to_admission(self):
        e = request_local_engine(bind_entry_projection(base_event())); e.update(novelty=0.8)
        with self.assertRaisesRegex(ReactiveRoutingError, "ENTRY_EVENT_SHA256_MISMATCH"):
            route_event(
                e,
                current_generation=7,
                engine_admission=control_plane_admission(),
                admitted_engine_artifacts=engine_registry(),
                admitted_entry_bindings={ENTRY_ADMISSION_A_SHA256: "f" * 64},
            )

    def test_transport_replay_keeps_causal_route_identity_but_changes_admission_binding(self):
        a_event = request_local_engine(bind_entry_projection(base_event())); a_event.update(novelty=0.8)
        b_event = request_local_engine(bind_entry_projection(
            base_event(),
            ingress_id="ingress:test:b",
            admission_sha256=ENTRY_ADMISSION_B_SHA256,
        )); b_event.update(novelty=0.8)
        a = route_entry_model(a_event)
        b = route_entry_model(b_event, admission_sha256=ENTRY_ADMISSION_B_SHA256)
        self.assertEqual(a.event_sha256, ENTRY_EVENT_SHA256)
        self.assertEqual(b.event_sha256, ENTRY_EVENT_SHA256)
        self.assertEqual(a.model_lanes, b.model_lanes)
        self.assertEqual(a.decision_sha256, b.decision_sha256)
        self.assertEqual(a.entry_admission_sha256, ENTRY_ADMISSION_A_SHA256)
        self.assertEqual(b.entry_admission_sha256, ENTRY_ADMISSION_B_SHA256)
        self.assertNotEqual(a.entry_admission_sha256, b.entry_admission_sha256)

    def test_typed_entry_inference_receipt_must_echo_concrete_admission(self):
        e = request_local_engine(bind_entry_projection(base_event())); e.update(novelty=0.8)
        decision = route_entry_model(e)
        receipt = inference_receipt(decision)
        assert_inference_echo(decision, receipt)
        poisoned = dict(receipt); poisoned["entry_admission_sha256"] = ENTRY_ADMISSION_B_SHA256
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_ENTRY_ADMISSION_SHA256_MISMATCH"):
            assert_inference_echo(decision, poisoned)
        missing = dict(receipt); missing.pop("entry_admission_sha256")
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_ENTRY_ADMISSION_SHA256_MISMATCH"):
            assert_inference_echo(decision, missing)

    def test_inference_receipt_must_echo_event_route_exact_engine_and_serializer(self):
        e = request_local_engine(base_event()); e.update(novelty=0.8)
        decision = route_model(e)
        receipt = inference_receipt(decision)
        assert_inference_echo(decision, receipt)
        poisoned = dict(receipt); poisoned["event_sha256"] = "0" * 64
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_EVENT_SHA256_MISMATCH"):
            assert_inference_echo(decision, poisoned)
        poisoned = dict(receipt); poisoned["resolved_engine_artifact_sha256"] = ENGINE_B_SHA256
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_RESOLVED_ENGINE_ARTIFACT_SHA256_MISMATCH"):
            assert_inference_echo(decision, poisoned)
        poisoned = dict(receipt); poisoned["hash_serialization_schema"] = "HCU_OTHER_SERIALIZER/v1"
        with self.assertRaisesRegex(ReactiveRoutingError, "INFERENCE_RECEIPT_HASH_SERIALIZATION_SCHEMA_MISMATCH"):
            assert_inference_echo(decision, poisoned)


if __name__ == "__main__":
    unittest.main()
