from __future__ import annotations

from dataclasses import replace
import unittest

from entry_fabric_v1 import (
    AdmissionError,
    IngressSource,
    Modality,
    ResourceBudget,
    XenoIngressDraft,
    admit_ingress,
)
from grid10_scheduler_v1 import (
    FunctionRequest,
    ScheduleError,
    SchedulerConfig,
    XenoMode,
    compile_grid_plan,
)


GENERATION = 17


def draft(
    *,
    provenance=("source:human",),
    observed_at="2026-08-23T16:00:00+00:00",
    received_at="2026-08-23T16:00:01+00:00",
    payload_ref="sha256:" + "a" * 64,
    isolation_domain="session:test",
):
    return XenoIngressDraft(
        causal_id="causal:test:1",
        generation=GENERATION,
        source=IngressSource.HUMAN,
        provenance=tuple(provenance),
        modality=Modality.TEXT,
        observed_at=observed_at,
        received_at=received_at,
        isolation_domain=isolation_domain,
        permissions=("context.read",),
        capability_scope=(),
        resource_budget=ResourceBudget(
            max_logical_cells=10,
            max_inference_calls=4,
            max_tokens=2400,
            wall_ms=8000,
            memory_bytes=256 * 1024 * 1024,
        ),
        payload_ref=payload_ref,
    )


def functions(count=10):
    return tuple(
        FunctionRequest(
            name=f"fn-{i:02d}",
            priority=100 - i,
            inference_required=(i % 2 == 0),
            estimated_tokens=100,
        )
        for i in range(count)
    )


class EntryFabricRegressionTests(unittest.TestCase):
    def test_exact_replay_is_deterministic(self):
        a = admit_ingress(draft(), current_generation=GENERATION)
        b = admit_ingress(draft(), current_generation=GENERATION)
        self.assertEqual(a.ingress_id, b.ingress_id)
        self.assertEqual(a.receipt(), b.receipt())

    def test_equivalent_timestamp_encodings_canonicalize(self):
        a = admit_ingress(
            draft(observed_at="2026-08-23T16:00:00Z", received_at="2026-08-23T16:00:01Z"),
            current_generation=GENERATION,
        )
        b = admit_ingress(
            draft(observed_at="2026-08-23T18:00:00+02:00", received_at="2026-08-23T18:00:01+02:00"),
            current_generation=GENERATION,
        )
        self.assertEqual(a.ingress_id, b.ingress_id)
        self.assertEqual(a.observed_at, "2026-08-23T16:00:00.000000Z")

    def test_stale_generation_fails_closed(self):
        with self.assertRaises(AdmissionError):
            admit_ingress(draft(), current_generation=GENERATION + 1)

    def test_generation_and_budget_reject_bool_or_string_coercion(self):
        with self.assertRaisesRegex(AdmissionError, "generation must be an integer"):
            admit_ingress(replace(draft(), generation=True), current_generation=1)
        with self.assertRaisesRegex(AdmissionError, "current_generation must be an integer"):
            admit_ingress(draft(), current_generation=str(GENERATION))
        bool_budget = ResourceBudget(
            max_logical_cells=True,
            max_inference_calls=4,
            max_tokens=2400,
            wall_ms=8000,
            memory_bytes=256 * 1024 * 1024,
        )
        with self.assertRaisesRegex(AdmissionError, "max_logical_cells must be an integer"):
            admit_ingress(replace(draft(), resource_budget=bool_budget), current_generation=GENERATION)

    def test_security_collections_reject_scalar_or_mapping_coercion(self):
        malformed = (
            ("provenance", "source:human"),
            ("permissions", "context.read"),
            ("capability_scope", "effect.request"),
            ("provenance", {"source": "human"}),
        )
        for field, value in malformed:
            with self.subTest(field=field, value=value):
                with self.assertRaisesRegex(AdmissionError, f"{field} must be a collection of strings"):
                    admit_ingress(replace(draft(), **{field: value}), current_generation=GENERATION)

    def test_raw_payload_is_not_admitted_as_payload_ref(self):
        with self.assertRaises(AdmissionError):
            admit_ingress(draft(payload_ref="this is raw prompt text"), current_generation=GENERATION)

    def test_malformed_sha256_payload_ref_fails_closed(self):
        with self.assertRaises(AdmissionError):
            admit_ingress(draft(payload_ref="sha256:not-a-real-digest"), current_generation=GENERATION)

    def test_isolation_domain_is_bound_into_ingress_identity(self):
        a = admit_ingress(draft(isolation_domain="session:a"), current_generation=GENERATION)
        b = admit_ingress(draft(isolation_domain="session:b"), current_generation=GENERATION)
        self.assertNotEqual(a.ingress_id, b.ingress_id)

    def test_grid10_is_logical_over_shared_workers_and_budget_bounded(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        plan = compile_grid_plan(
            packet,
            functions(12),
            mode=XenoMode.XENO_GRID10,
            current_generation=GENERATION,
            config=SchedulerConfig(max_logical_cells=10, shared_workers=("xcu:worker-b", "xcu:worker-a")),
        )
        self.assertLessEqual(len(plan.leases), 10)
        self.assertLessEqual(plan.inference_lease_count, packet.resource_budget.max_inference_calls)
        self.assertLessEqual(plan.total_estimated_tokens, packet.resource_budget.max_tokens)
        physical = {lease.worker_id for lease in plan.leases if lease.inference_required}
        self.assertLessEqual(len(physical), 2)

    def test_scheduler_rejects_effect_authority_in_cell(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        with self.assertRaises(ScheduleError):
            compile_grid_plan(
                packet,
                (FunctionRequest("candidate-action", 90, authority_class="REAL_EFFECT"),),
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION,
            )

    def test_scheduler_rechecks_generation_fence(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        with self.assertRaises(ScheduleError):
            compile_grid_plan(
                packet,
                functions(2),
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION + 1,
            )

    def test_scheduler_rejects_forged_admitted_packet_identity(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        forged_id = replace(packet, ingress_id="xeno-ingress:" + "0" * 64)
        forged_budget = replace(
            packet,
            resource_budget=ResourceBudget(
                max_logical_cells=10,
                max_inference_calls=10,
                max_tokens=999999,
                wall_ms=packet.resource_budget.wall_ms,
                memory_bytes=packet.resource_budget.memory_bytes,
            ),
        )
        for poisoned in (forged_id, forged_budget):
            with self.subTest(poisoned=poisoned.ingress_id):
                with self.assertRaisesRegex(ScheduleError, "unverified ingress packet"):
                    compile_grid_plan(
                        poisoned,
                        functions(2),
                        mode=XenoMode.XENO_GRID10,
                        current_generation=GENERATION,
                    )

    def test_scheduler_rejects_string_boolean_coercion(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        with self.assertRaisesRegex(ScheduleError, "inference_required must be boolean"):
            compile_grid_plan(
                packet,
                (FunctionRequest("critic", 90, inference_required="false", estimated_tokens=100),),
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION,
            )

    def test_scheduler_rejects_fractional_priority_coercion(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        with self.assertRaisesRegex(ScheduleError, "priority must be an integer"):
            compile_grid_plan(
                packet,
                (FunctionRequest("critic", 90.9, estimated_tokens=100),),
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION,
            )

    def test_scheduler_rejects_scalar_worker_collection(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        with self.assertRaisesRegex(ScheduleError, "shared_workers must be a collection"):
            compile_grid_plan(
                packet,
                functions(2),
                mode=XenoMode.XENO_GRID10,
                current_generation=GENERATION,
                config=SchedulerConfig(shared_workers="xcu:worker-a"),
            )

    def test_scheduler_duplicate_function_names_are_order_independent_or_rejected(self):
        packet = admit_ingress(draft(), current_generation=GENERATION)
        exact = FunctionRequest("critic", 90, inference_required=True, estimated_tokens=100)
        single = compile_grid_plan(
            packet,
            (exact,),
            mode=XenoMode.XENO_GRID10,
            current_generation=GENERATION,
        )
        duplicate = compile_grid_plan(
            packet,
            (exact, exact),
            mode=XenoMode.XENO_GRID10,
            current_generation=GENERATION,
        )
        self.assertEqual(single.plan_id, duplicate.plan_id)

        conflicting = FunctionRequest("critic", 90, inference_required=False, estimated_tokens=100)
        for ordered in ((exact, conflicting), (conflicting, exact)):
            with self.subTest(ordered=ordered):
                with self.assertRaisesRegex(ScheduleError, "conflicting duplicate function request"):
                    compile_grid_plan(
                        packet,
                        ordered,
                        mode=XenoMode.XENO_GRID10,
                        current_generation=GENERATION,
                    )


class GoUnusualExperiment(unittest.TestCase):
    def test_causal_alias_poison_same_routing_different_event_identity(self):
        """Exactly-one GO unusual experiment: CAUSAL_ALIAS_POISON."""
        left = admit_ingress(draft(provenance=("sensor:A",)), current_generation=GENERATION)
        right = admit_ingress(draft(provenance=("sensor:B",)), current_generation=GENERATION)
        left_replay = admit_ingress(draft(provenance=("sensor:A",)), current_generation=GENERATION)

        left_plan = compile_grid_plan(left, functions(4), mode=XenoMode.XENO_GRID10, current_generation=GENERATION)
        right_plan = compile_grid_plan(right, functions(4), mode=XenoMode.XENO_GRID10, current_generation=GENERATION)
        replay_plan = compile_grid_plan(left_replay, functions(4), mode=XenoMode.XENO_GRID10, current_generation=GENERATION)

        self.assertNotEqual(left.ingress_id, right.ingress_id)
        self.assertNotEqual(left_plan.plan_id, right_plan.plan_id)
        self.assertEqual(left.ingress_id, left_replay.ingress_id)
        self.assertEqual(left_plan.plan_id, replay_plan.plan_id)


if __name__ == "__main__":
    unittest.main()
