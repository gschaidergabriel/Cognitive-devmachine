import hashlib
import unittest
from dataclasses import asdict, replace

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from grid10_jspace_runtime_binding_v1 import (
    Grid10JSpaceRuntimeBindingError,
    bind_single_lane_inference,
    validate_runtime_binding,
)
from grid10_scheduler_v1 import (
    ENTRY_BINDING_SCHEMA,
    PLAN_SCHEMA,
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
)
from inference_receipt_v1 import (
    SCHEMA as INFERENCE_RECEIPT_SCHEMA,
    STATUS as INFERENCE_RECEIPT_STATUS,
    InferenceReceipt,
)


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


EVENT_SHA256 = digest("event")
ADMISSION_SHA256 = digest("admission")
ROUTE_SHA256 = digest("route")
POLICY_SHA256 = digest("policy")
ENGINE_IDENTITY_SHA256 = digest("engine-identity")
ENGINE_ARTIFACT_SHA256 = digest("engine-artifact")
CAPACITY_SHA256 = digest("capacity")
ENGINE_ADMISSION_RECEIPT_SHA256 = digest("engine-admission-receipt")
LOADER_BINDING_SHA256 = digest("loader-binding")
LOAD_LEASE_SHA256 = digest("load-lease")
LOAD_CONSUMPTION_SHA256 = digest("load-consumption")
OUTPUT_SHA256 = digest("output")


def canonical_sha256(value) -> str:
    return hashlib.sha256(canonicalize(value)).hexdigest()


def make_plan(lanes=("ANALYZE",), *, generation: int = 7) -> GridPlan:
    cells = [
        CellLease("cell-00", "RETRIEVE", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-01", "PROVENANCE_BUDGET_CHECK", ExecutionClass.SCRIPT, 0, None),
    ]
    for ordinal, lane in enumerate(lanes):
        cells.append(
            CellLease(
                f"cell-{len(cells):02d}",
                f"MODEL:{lane}",
                ExecutionClass.MODEL,
                512,
                ordinal,
            )
        )
    while len(cells) < 9:
        cells.append(CellLease(f"cell-{len(cells):02d}", "IDLE", ExecutionClass.SCRIPT, 0, None))
    cells.append(CellLease("cell-09", "SYNTHESIZE", ExecutionClass.SCRIPT, 0, None))

    plan = GridPlan(
        schema=PLAN_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entry_binding_schema=ENTRY_BINDING_SCHEMA,
        plan_sha256="1" * 64,
        ingress_id="ingress:jspace-runtime-binding:1",
        causal_id="causal:jspace-runtime-binding:1",
        entity_generation=generation,
        entry_event_sha256=EVENT_SHA256,
        entry_admission_sha256=ADMISSION_SHA256,
        route_event_sha256=EVENT_SHA256,
        route_decision_sha256=ROUTE_SHA256,
        router_policy_sha256=POLICY_SHA256,
        engine_identity_sha256=ENGINE_IDENTITY_SHA256,
        resolved_engine_identity="hcu_local_08b",
        resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_engine_artifact_sha256=ENGINE_ARTIFACT_SHA256,
        capacity_receipt_sha256=CAPACITY_SHA256,
        runtime_profile_id="test:runtime:single-loader",
        mode=HCUMode.GRID10,
        logical_cell_count=10,
        model_call_count=len(lanes),
        physical_decoder_limit=max(1, min(2, len(lanes))),
        max_wall_ms=2500,
        cells=tuple(cells),
    )
    material = {
        "schema": plan.schema,
        "canonicalization_schema": plan.canonicalization_schema,
        "entry_binding_schema": plan.entry_binding_schema,
        "ingress_id": plan.ingress_id,
        "causal_id": plan.causal_id,
        "entity_generation": plan.entity_generation,
        "entry_event_sha256": plan.entry_event_sha256,
        "entry_admission_sha256": plan.entry_admission_sha256,
        "route_event_sha256": plan.route_event_sha256,
        "route_decision_sha256": plan.route_decision_sha256,
        "router_policy_sha256": plan.router_policy_sha256,
        "engine_identity_sha256": plan.engine_identity_sha256,
        "resolved_engine_identity": plan.resolved_engine_identity,
        "resolved_engine_class": plan.resolved_engine_class,
        "resolved_engine_artifact_sha256": plan.resolved_engine_artifact_sha256,
        "capacity_receipt_sha256": plan.capacity_receipt_sha256,
        "runtime_profile_id": plan.runtime_profile_id,
        "mode": plan.mode.value,
        "logical_cell_count": plan.logical_cell_count,
        "model_call_count": plan.model_call_count,
        "physical_decoder_limit": plan.physical_decoder_limit,
        "max_wall_ms": plan.max_wall_ms,
        "cells": [
            {
                "cell_id": cell.cell_id,
                "function": cell.function,
                "execution_class": cell.execution_class.value,
                "model_token_budget": cell.model_token_budget,
                "physical_decoder_lane": cell.physical_decoder_lane,
            }
            for cell in plan.cells
        ],
    }
    return replace(plan, plan_sha256=canonical_sha256(material))


def make_receipt(lanes=("ANALYZE",), *, generation: int = 7) -> InferenceReceipt:
    receipt = InferenceReceipt(
        schema=INFERENCE_RECEIPT_SCHEMA,
        status=INFERENCE_RECEIPT_STATUS,
        hash_serialization_schema=CANONICALIZATION_SCHEMA,
        entry_binding_schema=ENTRY_BINDING_SCHEMA,
        entity_generation=generation,
        entry_admission_sha256=ADMISSION_SHA256,
        event_sha256=EVENT_SHA256,
        decision_sha256=ROUTE_SHA256,
        router_policy_sha256=POLICY_SHA256,
        engine_identity_sha256=ENGINE_IDENTITY_SHA256,
        resolved_engine_identity="hcu_local_08b",
        resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_engine_artifact_sha256=ENGINE_ARTIFACT_SHA256,
        engine_admission_receipt_sha256=ENGINE_ADMISSION_RECEIPT_SHA256,
        engine_load_canonicalization_schema=CANONICALIZATION_SCHEMA,
        engine_load_loader_binding_sha256=LOADER_BINDING_SHA256,
        engine_load_lease_sha256=LOAD_LEASE_SHA256,
        engine_load_consumption_receipt_sha256=LOAD_CONSUMPTION_SHA256,
        engine_load_loader_id="entityos:hcu:loader:1",
        model_call_id="model-call:jspace-runtime-binding:1",
        output_ref="unifieddb:candidate-output:jspace-runtime-binding:1",
        output_sha256=OUTPUT_SHA256,
        output_size=128,
        model_lanes=tuple(lanes),
        receipt_sha256="1" * 64,
    )
    material = asdict(receipt)
    material.pop("receipt_sha256")
    return replace(receipt, receipt_sha256=canonical_sha256(material))


class Grid10JSpaceRuntimeBindingTests(unittest.TestCase):
    def test_single_lane_binding_is_deterministic_and_loader_bound(self):
        plan = make_plan()
        receipt = make_receipt()
        first = bind_single_lane_inference(
            plan,
            receipt,
            current_generation=7,
            cell_id="cell-02",
        )
        second = bind_single_lane_inference(
            plan,
            receipt,
            current_generation=7,
            cell_id="cell-02",
        )
        self.assertEqual(first, second)
        self.assertEqual(first.model_lane, "ANALYZE")
        self.assertEqual(first.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(first.inference_receipt_sha256, receipt.receipt_sha256)
        self.assertEqual(first.output_sha256, OUTPUT_SHA256)
        self.assertEqual(
            first.engine_load_consumption_receipt_sha256,
            LOAD_CONSUMPTION_SHA256,
        )
        validate_runtime_binding(first)

    def test_stale_generation_fails_closed(self):
        with self.assertRaisesRegex(
            Grid10JSpaceRuntimeBindingError,
            "STALE_RUNTIME_BINDING_GENERATION",
        ):
            bind_single_lane_inference(
                make_plan(),
                make_receipt(),
                current_generation=8,
                cell_id="cell-02",
            )

    def test_cross_route_receipt_fails_closed(self):
        plan = make_plan()
        receipt = make_receipt()
        poisoned = replace(receipt, decision_sha256=digest("other-route"))
        material = asdict(poisoned)
        material.pop("receipt_sha256")
        poisoned = replace(poisoned, receipt_sha256=canonical_sha256(material))
        with self.assertRaisesRegex(
            Grid10JSpaceRuntimeBindingError,
            "RUNTIME_CAUSAL_IDENTITY_MISMATCH:route_decision_sha256",
        ):
            bind_single_lane_inference(
                plan,
                poisoned,
                current_generation=7,
                cell_id="cell-02",
            )

    def test_tampered_grid_plan_digest_fails_closed(self):
        plan = replace(make_plan(), runtime_profile_id="tampered-profile")
        with self.assertRaisesRegex(
            Grid10JSpaceRuntimeBindingError,
            "GRID_PLAN_DIGEST_MISMATCH",
        ):
            bind_single_lane_inference(
                plan,
                make_receipt(),
                current_generation=7,
                cell_id="cell-02",
            )

    def test_tampered_inference_receipt_digest_fails_closed(self):
        receipt = replace(make_receipt(), output_ref="tampered-output")
        with self.assertRaisesRegex(
            Grid10JSpaceRuntimeBindingError,
            "INFERENCE_RECEIPT_DIGEST_MISMATCH",
        ):
            bind_single_lane_inference(
                make_plan(),
                receipt,
                current_generation=7,
                cell_id="cell-02",
            )

    def test_unusual_multilane_cross_cell_output_assignment_is_rejected(self):
        """Exactly-one GO unusual experiment: expose v3's cross-cell ambiguity.

        The receipt is internally valid and carries both routed lanes, while GRID10 has two
        distinct MODEL cells.  Because v3 does not say which lane produced this output,
        assigning it to either cell would be an unverifiable guess.  The bridge must refuse
        both rather than minting a causal training trace.
        """
        plan = make_plan(("ANALYZE", "CRITIC"))
        receipt = make_receipt(("ANALYZE", "CRITIC"))
        for cell_id in ("cell-02", "cell-03"):
            with self.assertRaisesRegex(
                Grid10JSpaceRuntimeBindingError,
                "MULTI_LANE_GRID_PLAN_REQUIRES_LANE_BOUND_INFERENCE_RECEIPT",
            ):
                bind_single_lane_inference(
                    plan,
                    receipt,
                    current_generation=7,
                    cell_id=cell_id,
                )


if __name__ == "__main__":
    unittest.main()
