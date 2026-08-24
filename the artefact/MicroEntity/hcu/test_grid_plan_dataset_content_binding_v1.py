import hashlib
import unittest
from dataclasses import replace

from entry_canonicalization_v1 import canonicalize
from grid10_scheduler_v1 import (
    CANONICALIZATION_SCHEMA,
    ENTRY_BINDING_SCHEMA,
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
)
from grid_plan_dataset_content_binding_v1 import (
    GridPlanDatasetBindingError,
    verify_admitted_grid_plan_binding,
)


def h(ch):
    return ch * 64


def valid_plan():
    cells = (
        CellLease("cell-00", "RETRIEVE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-01", "PROVENANCE_BUDGET_CHECK", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-02", "MODEL:world", ExecutionClass.MODEL, 128, 0),
        CellLease("cell-03", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-04", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-05", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-06", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-07", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-08", "IDLE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-09", "SYNTHESIZE", ExecutionClass.SCRIPT, 0, None),
    )
    plan = GridPlan(
        schema=PLAN_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entry_binding_schema=ENTRY_BINDING_SCHEMA,
        plan_sha256=h("a"),
        ingress_id="ingress-1",
        causal_id="causal-1",
        entity_generation=7,
        entry_event_sha256=h("1"),
        entry_admission_sha256=h("2"),
        route_event_sha256=h("1"),
        route_decision_sha256=h("3"),
        router_policy_sha256=h("4"),
        engine_identity_sha256=h("5"),
        resolved_engine_identity="local:qwen",
        resolved_engine_class="LOCAL_MODEL",
        resolved_engine_artifact_sha256=h("6"),
        capacity_receipt_sha256=h("7"),
        runtime_profile_id="profile:grid10-test",
        mode=HCUMode.GRID10,
        logical_cell_count=10,
        model_call_count=1,
        physical_decoder_limit=1,
        max_wall_ms=1000,
        cells=cells,
    )
    digest = hashlib.sha256(canonicalize(grid_plan_material(plan))).hexdigest()
    return replace(plan, plan_sha256=digest)


class GridPlanDatasetBindingTests(unittest.TestCase):
    def causal(self):
        return {
            "entry_event_sha256": h("1"),
            "entry_admission_sha256": h("2"),
            "route_decision_sha256": h("3"),
        }

    def test_exact_content_bound_plan_passes(self):
        plan = valid_plan()
        observed = verify_admitted_grid_plan_binding(
            {plan.plan_sha256: plan},
            grid_plan_sha256=plan.plan_sha256,
            generation=7,
            causal=self.causal(),
        )
        self.assertEqual(observed, plan)

    def test_registry_alias_key_cannot_launder_valid_plan_preimage(self):
        plan = valid_plan()
        forged = ("0" if plan.plan_sha256[0] != "0" else "1") + plan.plan_sha256[1:]
        with self.assertRaisesRegex(
            GridPlanDatasetBindingError,
            "GRID_PLAN_REGISTRY_KEY_CONTENT_MISMATCH",
        ):
            verify_admitted_grid_plan_binding(
                {forged: plan},
                grid_plan_sha256=forged,
                generation=7,
                causal=self.causal(),
            )

    def test_stale_digest_after_plan_content_mutation_fails(self):
        plan = valid_plan()
        mutated = replace(plan, runtime_profile_id="profile:mutated")
        with self.assertRaisesRegex(
            GridPlanDatasetBindingError,
            "GRID_PLAN_PREIMAGE_REJECTED:GRID10_PLAN_DIGEST_MISMATCH",
        ):
            verify_admitted_grid_plan_binding(
                {plan.plan_sha256: mutated},
                grid_plan_sha256=plan.plan_sha256,
                generation=7,
                causal=self.causal(),
            )

    def test_reduced_receipt_is_not_accepted_as_cryptographic_preimage(self):
        plan = valid_plan()
        reduced = {
            "schema": plan.schema,
            "plan_sha256": plan.plan_sha256,
            "entity_generation": plan.entity_generation,
            "entry_event_sha256": plan.entry_event_sha256,
            "entry_admission_sha256": plan.entry_admission_sha256,
            "route_decision_sha256": plan.route_decision_sha256,
        }
        with self.assertRaisesRegex(
            GridPlanDatasetBindingError,
            "GRID_PLAN_PREIMAGE_TYPE_INVALID",
        ):
            verify_admitted_grid_plan_binding(
                {plan.plan_sha256: reduced},
                grid_plan_sha256=plan.plan_sha256,
                generation=7,
                causal=self.causal(),
            )

    def test_generation_and_causal_transplants_fail(self):
        plan = valid_plan()
        with self.assertRaisesRegex(GridPlanDatasetBindingError, "GRID_PLAN_GENERATION_MISMATCH"):
            verify_admitted_grid_plan_binding(
                {plan.plan_sha256: plan},
                grid_plan_sha256=plan.plan_sha256,
                generation=8,
                causal=self.causal(),
            )

        causal = self.causal()
        causal["route_decision_sha256"] = h("9")
        with self.assertRaisesRegex(
            GridPlanDatasetBindingError,
            "GRID_PLAN_CAUSAL_BINDING_MISMATCH:route_decision_sha256",
        ):
            verify_admitted_grid_plan_binding(
                {plan.plan_sha256: plan},
                grid_plan_sha256=plan.plan_sha256,
                generation=7,
                causal=causal,
            )


if __name__ == "__main__":
    unittest.main()
