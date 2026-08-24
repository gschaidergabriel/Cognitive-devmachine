#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import replace
import hashlib
import unittest

from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from executor_sequence_lane_v1 import (
    ExecutorSequenceLaneError,
    derive_executor_sequence_lane,
    validate_executor_sequence_lane_binding,
)
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
from xeno_entry_fabric_v1 import (
    ENTRY_ADMISSION_IDENTITY_SCHEMA,
    ENTRY_EVENT_IDENTITY_SCHEMA,
    ENTRY_SCHEMA,
    EntryPacket,
)


def _sha(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def _entry(
    *,
    ingress_id: str = "ingress-1",
    causal_id: str = "causal-1",
    source_id: str = "source-A",
    stream_id: str | None = "stream-alpha",
    parent_id: str | None = "parent-0",
    received_time: str = "2026-08-24T00:00:01.000000Z",
) -> EntryPacket:
    generation = 7
    source_kind = "HUMAN_PROMPT"
    modality = "TEXT"
    observed_time = "2026-08-24T00:00:00.000000Z"
    provenance_ref = "provenance:fixture"
    provenance_sha256 = _sha("provenance")
    payload_sha256 = _sha(f"payload:{causal_id}")
    event_material = {
        "schema": ENTRY_EVENT_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "causal_id": causal_id,
        "source_kind": source_kind,
        "source_id": source_id,
        "modality": modality,
        "observed_time": observed_time,
        "provenance_ref": provenance_ref,
        "provenance_sha256": provenance_sha256,
        "parent_id": parent_id,
        "stream_id": stream_id,
        "payload_sha256": payload_sha256,
    }
    event_sha256 = hashlib.sha256(canonicalize(event_material)).hexdigest()
    capabilities = ("MODEL_CALL",)
    capability_binding_sha256 = _sha("capability-binding")
    budget = (
        ("max_model_calls", 1),
        ("max_tokens", 512),
        ("max_wall_ms", 1000),
    )
    payload_ref = f"payload:{causal_id}"
    admission_material = {
        "schema": ENTRY_ADMISSION_IDENTITY_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": event_sha256,
        "entity_generation": generation,
        "ingress_id": ingress_id,
        "received_time": received_time,
        "capabilities": list(capabilities),
        "capability_binding_sha256": capability_binding_sha256,
        "budget": dict(budget),
        "payload_ref": payload_ref,
    }
    admission_sha256 = hashlib.sha256(canonicalize(admission_material)).hexdigest()
    return EntryPacket(
        schema=ENTRY_SCHEMA,
        ingress_id=ingress_id,
        causal_id=causal_id,
        entity_generation=generation,
        source_kind=source_kind,
        source_id=source_id,
        modality=modality,
        observed_time=observed_time,
        received_time=received_time,
        provenance_ref=provenance_ref,
        provenance_sha256=provenance_sha256,
        capabilities=capabilities,
        capability_binding_sha256=capability_binding_sha256,
        parent_id=parent_id,
        stream_id=stream_id,
        budget=budget,
        payload_ref=payload_ref,
        payload_sha256=payload_sha256,
        event_sha256=event_sha256,
        admission_sha256=admission_sha256,
    )


def _plan(
    entry: EntryPacket,
    *,
    role: str = "planner",
    cell_id: str = "cell-model",
    execution_class: ExecutionClass = ExecutionClass.MODEL,
) -> GridPlan:
    cell = CellLease(
        cell_id=cell_id,
        function=f"MODEL:{role}" if execution_class is ExecutionClass.MODEL else "SCRIPT:fixture",
        execution_class=execution_class,
        model_token_budget=256 if execution_class is ExecutionClass.MODEL else 0,
        physical_decoder_lane=0 if execution_class is ExecutionClass.MODEL else None,
    )
    material = {
        "schema": PLAN_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entry_binding_schema": ENTRY_BINDING_SCHEMA,
        "plan_sha256": "1" * 64,
        "ingress_id": entry.ingress_id,
        "causal_id": entry.causal_id,
        "entity_generation": entry.entity_generation,
        "entry_event_sha256": entry.event_sha256,
        "entry_admission_sha256": entry.admission_sha256,
        "route_event_sha256": _sha(f"route-event:{entry.causal_id}"),
        "route_decision_sha256": _sha(f"route-decision:{entry.causal_id}"),
        "router_policy_sha256": _sha("router-policy"),
        "engine_identity_sha256": _sha("engine-identity"),
        "resolved_engine_identity": "engine:fixture",
        "resolved_engine_class": "LOCAL_MODEL",
        "resolved_engine_artifact_sha256": _sha("engine-artifact"),
        "capacity_receipt_sha256": _sha("capacity"),
        "runtime_profile_id": "runtime:fixture",
        "mode": HCUMode.GRID10,
        "logical_cell_count": 1,
        "model_call_count": 1 if execution_class is ExecutionClass.MODEL else 0,
        "physical_decoder_limit": 1,
        "max_wall_ms": 1000,
        "cells": (cell,),
    }
    provisional = GridPlan(**material)
    plan_sha256 = hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest()
    return replace(provisional, plan_sha256=plan_sha256)


def _derive(entry: EntryPacket, plan: GridPlan, **overrides):
    args = {
        "executor_id": "executor-A",
        "cell_id": "cell-model",
        "role": "planner",
    }
    args.update(overrides)
    return derive_executor_sequence_lane(entry, plan, **args)


class ExecutorSequenceLaneTests(unittest.TestCase):
    def test_same_admitted_stream_across_distinct_steps_keeps_lane_identity(self):
        first_entry = _entry(ingress_id="ingress-1", causal_id="causal-1", parent_id="root")
        second_entry = _entry(
            ingress_id="ingress-2",
            causal_id="causal-2",
            parent_id="causal-1",
            received_time="2026-08-24T00:00:02.000000Z",
        )
        first = _derive(first_entry, _plan(first_entry))
        second = _derive(second_entry, _plan(second_entry))
        validate_executor_sequence_lane_binding(first)
        validate_executor_sequence_lane_binding(second)
        self.assertEqual(first.sequence_lane_id, second.sequence_lane_id)
        self.assertNotEqual(first.binding_sha256, second.binding_sha256)
        self.assertNotEqual(first.entry_event_sha256, second.entry_event_sha256)

    def test_received_time_does_not_become_lane_authority(self):
        first_entry = _entry(received_time="2026-08-24T00:00:01.000000Z")
        second_entry = _entry(received_time="2026-08-24T09:59:59.000000Z")
        first = _derive(first_entry, _plan(first_entry))
        second = _derive(second_entry, _plan(second_entry))
        self.assertEqual(first.sequence_lane_id, second.sequence_lane_id)
        self.assertNotEqual(first.entry_admission_sha256, second.entry_admission_sha256)

    def test_missing_stream_id_fails_closed_instead_of_inventing_lane(self):
        entry = _entry(stream_id=None)
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE",
        ):
            _derive(entry, _plan(entry))

    def test_stream_identity_changes_lane(self):
        first_entry = _entry(stream_id="stream-alpha")
        second_entry = _entry(stream_id="stream-beta")
        first = _derive(first_entry, _plan(first_entry))
        second = _derive(second_entry, _plan(second_entry))
        self.assertNotEqual(first.sequence_lane_id, second.sequence_lane_id)

    def test_source_identity_namespaces_stream(self):
        first_entry = _entry(source_id="source-A", stream_id="stream-shared")
        second_entry = _entry(source_id="source-B", stream_id="stream-shared")
        first = _derive(first_entry, _plan(first_entry))
        second = _derive(second_entry, _plan(second_entry))
        self.assertNotEqual(first.sequence_lane_id, second.sequence_lane_id)

    def test_executor_identity_namespaces_stream(self):
        entry = _entry()
        plan = _plan(entry)
        first = _derive(entry, plan, executor_id="executor-A")
        second = _derive(entry, plan, executor_id="executor-B")
        self.assertNotEqual(first.sequence_lane_id, second.sequence_lane_id)

    def test_role_identity_namespaces_stream(self):
        entry = _entry()
        planner = _derive(entry, _plan(entry, role="planner"), role="planner")
        critic = _derive(entry, _plan(entry, role="critic"), role="critic")
        self.assertNotEqual(planner.sequence_lane_id, critic.sequence_lane_id)

    def test_tampered_entry_identity_is_rejected_before_lane_derivation(self):
        entry = _entry()
        tampered = replace(entry, event_sha256=_sha("forged-event"))
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "ENTRY_EVENT_IDENTITY_REVALIDATION_MISMATCH",
        ):
            _derive(tampered, _plan(tampered))

    def test_grid_plan_for_different_entry_cannot_supply_lane(self):
        first_entry = _entry(ingress_id="ingress-1", causal_id="causal-1")
        second_entry = _entry(ingress_id="ingress-2", causal_id="causal-2")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_LANE_ENTRY_GRID_MISMATCH",
        ):
            _derive(first_entry, _plan(second_entry))

    def test_non_model_cell_cannot_become_executor_sequence_lane(self):
        entry = _entry()
        plan = _plan(entry, execution_class=ExecutionClass.SCRIPT)
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_LANE_CELL_NOT_MODEL",
        ):
            _derive(entry, plan)

    def test_role_mismatch_is_rejected(self):
        entry = _entry()
        plan = _plan(entry, role="planner")
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "EXECUTOR_SEQUENCE_LANE_CELL_ROLE_MISMATCH",
        ):
            _derive(entry, plan, role="critic")

    def test_tampered_grid_identity_is_rejected(self):
        entry = _entry()
        plan = replace(_plan(entry), plan_sha256=_sha("forged-plan"))
        with self.assertRaisesRegex(
            ExecutorSequenceLaneError,
            "GRID_PLAN_REJECTED|GRID_PLAN_IDENTITY_REVALIDATION_MISMATCH",
        ):
            _derive(entry, plan)


if __name__ == "__main__":
    unittest.main()
