import hashlib
import sqlite3
import tempfile
import unittest
from dataclasses import asdict, replace
from pathlib import Path

from global_jspace_gwt_v1 import CellContribution, step
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
from test_inference_receipt_v1 import fixture


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


def executor_observation_from_fixture(kwargs) -> ModelExecutionObservation:
    template = kwargs["verified_model_execution"]
    return ModelExecutionObservation(
        schema=OBSERVATION_SCHEMA,
        evidence_source=ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
        entity_generation=template.entity_generation,
        executor_id=template.executor_id,
        invocation_id=template.invocation_id,
        engine_load_consumption_receipt_sha256=(
            template.engine_load_consumption_receipt_sha256
        ),
        grid_plan_sha256=template.grid_plan_sha256,
        output_producing_cell_id=template.output_producing_cell_id,
        role=template.role,
        input_sha256=template.input_sha256,
        input_size=template.input_size,
        output_ref=template.output_ref,
        output_sha256=template.output_sha256,
        output_size=template.output_size,
    )


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
        resource_budget={"max_model_calls": 1, "max_tokens": 1024, "max_wall_ms": 2500},
        requested_action_class="CANDIDATE_INFERENCE",
        expected_structured_model_output="schema://hcu/candidate-output/v1",
        observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
        falsifier_lesion_condition="BASELINE",
        credit_label="UNKNOWN",
    )


class ExecutionStoreInferenceJSpaceChainTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tempdir.name) / "miniunified.db"

    def tearDown(self):
        self.tempdir.cleanup()

    def test_atomic_executor_admission_flows_into_inference_v4_and_jspace_v3(self):
        packet, decision, kwargs = fixture()
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        observation = executor_observation_from_fixture(kwargs)
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
        _packet, _decision, kwargs = fixture()
        plan = kwargs["grid_plan"]
        load = kwargs["verified_engine_load"]
        original = executor_observation_from_fixture(kwargs)
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
                db.execute("SELECT COUNT(*) FROM hcu_model_execution_invocations").fetchone()[0],
                1,
            )
            self.assertEqual(
                db.execute("SELECT COUNT(*) FROM hcu_model_execution_observations").fetchone()[0],
                1,
            )
        finally:
            db.close()


if __name__ == "__main__":
    unittest.main()
