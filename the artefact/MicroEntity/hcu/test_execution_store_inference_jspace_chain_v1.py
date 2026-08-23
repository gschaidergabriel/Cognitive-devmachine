import hashlib
import sqlite3
import tempfile
import threading
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from engine_admission_v1 import (
    LOCK_SCHEMA,
    EngineArtifactLock,
    EngineArtifactPaths,
    derive_engine_artifact_sha256,
    verify_and_construct_engine_admission,
)
from engine_load_lease_v1 import (
    ACTUAL_LOADER_EVIDENCE_SOURCE,
    CONSUMPTION_SCHEMA,
    VERIFIED_LOAD_SCHEMA,
    LoaderConsumedArtifact,
    LoaderConsumption,
    issue_engine_load_lease,
    loader_consumption_record,
    loader_consumption_record_sha256,
    verify_loader_consumption,
)
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA
from global_jspace_gwt_v1 import CellContribution, step
from grid10_scheduler_v1 import (
    ExecutionClass,
    HCUMode,
    RuntimeCapacity,
    compile_plan,
    validate_grid_plan_identity,
)
from inference_receipt_v1 import make_inference_receipt
from jspace_inference_binding_v1 import (
    SCHEMA as JSPACE_BINDING_SCHEMA,
    bind_training_trace_to_inference,
    validate_binding,
)
from jspace_training_trace_v1 import build_training_trace
from model_execution_admission_store_v1 import (
    ModelExecutionAdmissionStoreError,
    admit_and_verify_model_execution,
)
from model_execution_receipt_v1 import (
    ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
    OBSERVATION_SCHEMA,
    ModelExecutionObservation,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA, route_event
from xeno_entry_fabric_v1 import admit_entry, to_hcu_reactive_event


GENERATION = 7
CAPABILITY_BINDING_SHA256 = hashlib.sha256(b"capability-binding:producer-chain:v1").hexdigest()
ADMITTED_BUDGET = {
    "max_model_calls": 3,
    "max_tokens": 2048,
    "max_wall_ms": 5000,
}


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def open_db(path: Path, generation: int) -> sqlite3.Connection:
    db = sqlite3.connect(path, timeout=5.0, check_same_thread=False)
    db.execute("PRAGMA foreign_keys=ON")
    db.execute(
        "CREATE TABLE IF NOT EXISTS entity_state(id INTEGER PRIMARY KEY, generation INTEGER NOT NULL)"
    )
    row = db.execute("SELECT generation FROM entity_state WHERE id=1").fetchone()
    if row is None:
        db.execute("INSERT INTO entity_state(id,generation) VALUES(1,?)", (generation,))
    db.commit()
    return db


def base_entry() -> dict:
    return {
        "schema": "XENO_ENTRY_PACKET/v1",
        "ingress_id": "ingress:execution-store-chain:v1",
        "causal_id": "causal:execution-store-chain:v1",
        "entity_generation": GENERATION,
        "source_kind": "HUMAN_PROMPT",
        "source_id": "user:test",
        "modality": "TEXT",
        "observed_time": "2026-08-24T02:16:00+07:00",
        "received_time": "2026-08-24T02:16:01+07:00",
        "provenance_ref": "unifieddb:source:execution-store-chain:v1",
        "provenance_sha256": digest("provenance:execution-store-chain:v1"),
        "capabilities": ["memory.read", "hcu.route"],
        "capability_binding_sha256": CAPABILITY_BINDING_SHA256,
        "parent_id": None,
        "stream_id": "stream:execution-store-chain:v1",
        "budget": dict(ADMITTED_BUDGET),
        "payload_ref": "unifieddb:payload:execution-store-chain:v1",
        "payload_sha256": digest("payload:execution-store-chain:v1"),
    }


def entry_binding(packet) -> dict:
    return {
        "schema": ENTRY_BINDING_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "event_sha256": packet.event_sha256,
    }


def write_artifact(path: Path, payload: bytes) -> str:
    path.write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def producer_verified_engine_admission(root: Path):
    checkpoint = root / "checkpoint.bin"
    tokenizer = root / "tokenizer.json"
    runtime = root / "runtime.bin"
    build = root / "build.txt"

    checkpoint_sha256 = write_artifact(checkpoint, b"checkpoint:execution-store-chain:v1")
    tokenizer_sha256 = write_artifact(tokenizer, b'{"tokenizer":"execution-store-chain:v1"}')
    runtime_sha256 = write_artifact(runtime, b"runtime:execution-store-chain:v1")
    build_sha256 = write_artifact(build, b"build:execution-store-chain:v1")

    provisional = EngineArtifactLock(
        schema=LOCK_SCHEMA,
        provider_alias="hcu",
        engine_identity="hcu_local_08b",
        engine_class="LOCAL_SHARED_WEIGHT_08B",
        checkpoint_sha256=checkpoint_sha256,
        tokenizer_sha256=tokenizer_sha256,
        runtime_sha256=runtime_sha256,
        build_sha256=build_sha256,
        engine_artifact_sha256=digest("provisional-engine-bundle"),
    )
    lock = replace(
        provisional,
        engine_artifact_sha256=derive_engine_artifact_sha256(provisional),
    )
    return verify_and_construct_engine_admission(
        lock,
        EngineArtifactPaths(
            checkpoint=checkpoint,
            tokenizer=tokenizer,
            runtime=runtime,
            build=build,
        ),
        entity_generation=GENERATION,
        current_generation=GENERATION,
    )


def loader_artifact(artifact) -> LoaderConsumedArtifact:
    return LoaderConsumedArtifact(
        kind=artifact.kind,
        sha256=artifact.sha256,
        file_count=artifact.file_count,
        byte_count=artifact.byte_count,
        evidence_source=ACTUAL_LOADER_EVIDENCE_SOURCE,
    )


def producer_verified_engine_load(verified):
    lease = issue_engine_load_lease(
        verified,
        loader_id="entityos:hcu:loader:execution-store-chain:v1",
        loader_binding_sha256=digest("loader-binding:execution-store-chain:v1"),
        current_generation=GENERATION,
    )
    consumption = LoaderConsumption(
        schema=CONSUMPTION_SCHEMA,
        entity_generation=GENERATION,
        loader_id=lease.loader_id,
        loader_binding_sha256=lease.loader_binding_sha256,
        engine_identity=lease.engine_identity,
        engine_artifact_sha256=lease.engine_artifact_sha256,
        checkpoint=loader_artifact(verified.checkpoint),
        tokenizer=loader_artifact(verified.tokenizer),
        runtime=loader_artifact(verified.runtime),
        build=loader_artifact(verified.build),
    )
    admitted = {
        loader_consumption_record_sha256(consumption): loader_consumption_record(consumption)
    }
    return verify_loader_consumption(
        lease,
        verified,
        consumption,
        admitted_loader_consumptions=admitted,
        current_generation=GENERATION,
    )


def verified_load_receipt(load) -> dict:
    def artifact(value):
        return {
            "kind": value.kind,
            "sha256": value.sha256,
            "file_count": value.file_count,
            "byte_count": value.byte_count,
            "evidence_source": value.evidence_source,
        }

    return {
        "schema": VERIFIED_LOAD_SCHEMA,
        "canonicalization_schema": CANONICALIZATION_SCHEMA,
        "entity_generation": load.entity_generation,
        "loader_id": load.loader_id,
        "loader_binding_sha256": load.loader_binding_sha256,
        "engine_admission_receipt_sha256": load.engine_admission_receipt_sha256,
        "engine_load_lease_sha256": load.engine_load_lease_sha256,
        "engine_identity": load.engine_identity,
        "engine_class": load.engine_class,
        "engine_artifact_sha256": load.engine_artifact_sha256,
        "checkpoint": artifact(load.checkpoint),
        "tokenizer": artifact(load.tokenizer),
        "runtime": artifact(load.runtime),
        "build": artifact(load.build),
        "consumption_receipt_sha256": load.consumption_receipt_sha256,
    }


def producer_fixture(root: Path):
    packet = admit_entry(
        base_entry(),
        current_generation=GENERATION,
        expected_capability_binding_sha256=CAPABILITY_BINDING_SHA256,
        admitted_capabilities=("memory.read", "hcu.route"),
        admitted_budget=ADMITTED_BUDGET,
    )
    event = to_hcu_reactive_event(packet, novelty=0.8, zero_relevance=0.8)
    event["requested_internal_provider"] = "hcu"
    entry_bindings = {packet.admission_sha256: entry_binding(packet)}

    verified = producer_verified_engine_admission(root)
    engine_artifacts = verified.admitted_engine_artifacts()
    decision = route_event(
        event,
        current_generation=GENERATION,
        engine_admission=verified.admission,
        admitted_engine_artifacts=engine_artifacts,
        admitted_entry_bindings=entry_bindings,
    )

    capacity = RuntimeCapacity(
        profile_id="runtime:execution-store-chain:v1",
        capacity_receipt_sha256=digest("capacity:execution-store-chain:v1"),
        max_logical_cells=10,
        physical_decoder_limit=1,
    )
    admitted_capacity_receipts = {
        capacity.capacity_receipt_sha256: {
            "profile_id": capacity.profile_id,
            "max_logical_cells": capacity.max_logical_cells,
            "physical_decoder_limit": capacity.physical_decoder_limit,
        }
    }
    plan = compile_plan(
        packet,
        decision=decision,
        mode=HCUMode.GRID10,
        capacity=capacity,
        current_generation=GENERATION,
        admitted_entry_bindings=entry_bindings,
        admitted_capacity_receipts=admitted_capacity_receipts,
    )
    validate_grid_plan_identity(plan)

    load = producer_verified_engine_load(verified)
    model_cells = [cell for cell in plan.cells if cell.execution_class is ExecutionClass.MODEL]
    if not model_cells:
        raise AssertionError("PRODUCER_GRID10_MODEL_CELL_REQUIRED")
    output_cell = model_cells[0]
    if not output_cell.function.startswith("MODEL:"):
        raise AssertionError("PRODUCER_GRID10_MODEL_ROLE_REQUIRED")
    role = output_cell.function.removeprefix("MODEL:")

    observation = ModelExecutionObservation(
        schema=OBSERVATION_SCHEMA,
        evidence_source=ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
        entity_generation=GENERATION,
        executor_id="entityos:hcu:model-executor:execution-store-chain:v1",
        invocation_id="invocation:execution-store-chain:v1",
        engine_load_consumption_receipt_sha256=load.consumption_receipt_sha256,
        grid_plan_sha256=plan.plan_sha256,
        output_producing_cell_id=output_cell.cell_id,
        role=role,
        input_sha256=digest("input:execution-store-chain:v1"),
        input_size=64,
        output_ref="unifieddb:candidate-output:execution-store-chain:v1",
        output_sha256=digest("output:execution-store-chain:v1"),
        output_size=128,
    )
    kwargs = {
        "current_generation": GENERATION,
        "admitted_route_generations": {decision.decision_sha256: GENERATION},
        "entry_admission_sha256": packet.admission_sha256,
        "admitted_entry_bindings": entry_bindings,
        "admitted_engine_artifacts": engine_artifacts,
        "verified_engine_admission": verified,
        "admitted_engine_admission_receipts": {
            verified.receipt_sha256: verified.receipt()
        },
        "verified_engine_load": load,
        "admitted_verified_engine_loads": {
            load.consumption_receipt_sha256: verified_load_receipt(load)
        },
        "grid_plan": plan,
    }
    return packet, decision, kwargs, observation


def training_trace_for(packet, decision, kwargs, execution):
    cells = [
        CellContribution(
            "cell-00",
            "retrieval",
            (0.2, 0.1, -0.1),
            0.1,
            0.1,
            0.1,
            0.1,
            0.1,
        ),
        CellContribution(
            execution.output_producing_cell_id,
            execution.role,
            (-0.3, 0.9, 0.4),
            0.8,
            0.95,
            0.7,
            0.4,
            0.2,
        ),
    ]
    proto = step(
        cells,
        generation=execution.entity_generation,
        basis_id="basis:execution-store-chain:v1",
        basis_sha256=digest("basis:execution-store-chain:v1"),
    )
    plan = kwargs["grid_plan"]
    return build_training_trace(
        proto,
        proto.control_packet,
        trace_id="trace:execution-store-chain:v1",
        trace_family_id="episode:execution-store-chain:v1",
        entry_event_sha256=packet.event_sha256,
        entry_admission_sha256=packet.admission_sha256,
        route_decision_sha256=decision.decision_sha256,
        grid_plan_sha256=plan.plan_sha256,
        jspace_input_vector_ref="unifieddb:jspace-input:execution-store-chain:v1",
        local_workspace_state_ref="unifieddb:workspace:execution-store-chain:v1",
        global_jspace_slice_ref="unifieddb:jspace-slice:execution-store-chain:v1",
        hyperposition_branch_ids=("branch:execution-store:a", "branch:execution-store:b"),
        provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
        resource_budget=dict(ADMITTED_BUDGET),
        requested_action_class="CANDIDATE_INFERENCE",
        expected_structured_model_output="schema://hcu/candidate-output/v1",
        observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
        falsifier_lesion_condition="BASELINE",
        credit_label="UNKNOWN",
    )


class ExecutionStoreInferenceJSpaceChainTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.db_path = self.root / "miniunified.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def admit_execution(self):
        packet, decision, kwargs, observation = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        db = open_db(self.db_path, plan.entity_generation)
        try:
            execution = admit_and_verify_model_execution(
                db,
                plan,
                load,
                observation,
                current_generation=plan.entity_generation,
            )
        finally:
            db.close()
        return packet, decision, kwargs, observation, execution

    def test_upstream_trust_objects_are_canonical_producer_outputs(self):
        packet, decision, kwargs, _observation = producer_fixture(self.root)
        verified = kwargs["verified_engine_admission"]
        plan = kwargs["grid_plan"]
        self.assertEqual(verified.admission.engine_identity, decision.resolved_engine_identity)
        self.assertEqual(verified.admission.engine_class, decision.resolved_engine_class)
        self.assertEqual(verified.engine_artifact_sha256, decision.resolved_engine_artifact_sha256)
        self.assertEqual(verified.admitted_engine_artifacts(), kwargs["admitted_engine_artifacts"])
        self.assertEqual(plan.entry_admission_sha256, packet.admission_sha256)
        self.assertEqual(plan.route_decision_sha256, decision.decision_sha256)
        self.assertEqual(plan.resolved_engine_artifact_sha256, verified.engine_artifact_sha256)
        self.assertEqual(plan.logical_cell_count, 10)
        self.assertEqual(validate_grid_plan_identity(plan), plan.plan_sha256)

    def test_atomic_executor_admission_flows_into_inference_v4_and_jspace_v3(self):
        packet, decision, kwargs, _observation, execution = self.admit_execution()
        plan = kwargs["grid_plan"]

        kwargs["verified_model_execution"] = execution
        kwargs["admitted_verified_model_executions"] = {
            execution.receipt_sha256: asdict(execution)
        }
        inference = make_inference_receipt(decision, **kwargs)
        trace = training_trace_for(packet, decision, kwargs, execution)
        binding = bind_training_trace_to_inference(trace, inference, plan)
        validate_binding(binding)

        self.assertEqual(inference.schema, "HCU_INFERENCE_RECEIPT/v4")
        self.assertEqual(binding.schema, JSPACE_BINDING_SCHEMA)
        self.assertEqual(binding.model_execution_receipt_sha256, execution.receipt_sha256)
        self.assertEqual(binding.inference_receipt_sha256, inference.receipt_sha256)
        self.assertEqual(binding.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(binding.cell_id, execution.output_producing_cell_id)
        self.assertEqual(binding.role, execution.role)
        self.assertEqual(binding.output_sha256, execution.output_sha256)
        self.assertEqual(inference.model_execution_invocation_id, execution.invocation_id)
        self.assertEqual(inference.model_call_id, execution.invocation_id)

    def test_divergent_same_invocation_is_rejected_before_second_inference_or_jspace_binding(self):
        _packet, _decision, kwargs, original = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        divergent = replace(original, output_sha256=digest("divergent-chain-output"))
        db = open_db(self.db_path, plan.entity_generation)
        try:
            admit_and_verify_model_execution(
                db,
                plan,
                load,
                original,
                current_generation=plan.entity_generation,
            )
            with self.assertRaisesRegex(
                ModelExecutionAdmissionStoreError,
                "MODEL_EXECUTION_INVOCATION_REPLAY_DIVERGENCE",
            ):
                admit_and_verify_model_execution(
                    db,
                    plan,
                    load,
                    divergent,
                    current_generation=plan.entity_generation,
                )
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM hcu_model_execution_invocations"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM hcu_model_execution_observations"
                ).fetchone()[0],
                1,
            )
        finally:
            db.close()

    def test_concurrent_divergent_invocation_yields_one_downstream_jspace_binding(self):
        packet, decision, kwargs, original = producer_fixture(self.root)
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        divergent = replace(
            original,
            output_sha256=digest("concurrent-divergent-chain-output"),
        )

        bootstrap = open_db(self.db_path, plan.entity_generation)
        bootstrap.close()
        barrier = threading.Barrier(2)
        outcomes = []
        outcome_lock = threading.Lock()

        def worker(candidate):
            db = open_db(self.db_path, plan.entity_generation)
            barrier.wait()
            try:
                execution = admit_and_verify_model_execution(
                    db,
                    plan,
                    load,
                    candidate,
                    current_generation=plan.entity_generation,
                )
                local_kwargs = dict(kwargs)
                local_kwargs["verified_model_execution"] = execution
                local_kwargs["admitted_verified_model_executions"] = {
                    execution.receipt_sha256: asdict(execution)
                }
                inference = make_inference_receipt(decision, **local_kwargs)
                trace = training_trace_for(
                    packet,
                    decision,
                    local_kwargs,
                    execution,
                )
                binding = bind_training_trace_to_inference(
                    trace,
                    inference,
                    plan,
                )
                validate_binding(binding)
                result = ("PASS", binding)
            except ModelExecutionAdmissionStoreError as exc:
                result = ("REJECT", str(exc))
            finally:
                db.close()
            with outcome_lock:
                outcomes.append(result)

        threads = [
            threading.Thread(target=worker, args=(original,)),
            threading.Thread(target=worker, args=(divergent,)),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=10)

        self.assertFalse(any(thread.is_alive() for thread in threads))
        winners = [detail for status, detail in outcomes if status == "PASS"]
        rejects = [detail for status, detail in outcomes if status == "REJECT"]
        self.assertEqual(len(winners), 1)
        self.assertEqual(len(rejects), 1)
        self.assertIn("MODEL_EXECUTION_INVOCATION_REPLAY_DIVERGENCE", rejects[0])

        binding = winners[0]
        self.assertEqual(binding.model_execution_invocation_id, original.invocation_id)
        self.assertEqual(binding.model_call_id, original.invocation_id)
        self.assertIn(
            binding.output_sha256,
            {original.output_sha256, divergent.output_sha256},
        )

        db = open_db(self.db_path, plan.entity_generation)
        try:
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM hcu_model_execution_invocations"
                ).fetchone()[0],
                1,
            )
            self.assertEqual(
                db.execute(
                    "SELECT COUNT(*) FROM hcu_model_execution_observations"
                ).fetchone()[0],
                1,
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
