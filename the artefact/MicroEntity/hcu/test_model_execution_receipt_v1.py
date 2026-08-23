import hashlib
import unittest
from dataclasses import replace

from engine_load_lease_v1 import VERIFIED_LOAD_SCHEMA, LoaderConsumedArtifact, VerifiedEngineLoad
from entry_canonicalization_v1 import CANONICALIZATION_SCHEMA, canonicalize
from grid10_scheduler_v1 import (
    CellLease,
    ExecutionClass,
    GridPlan,
    HCUMode,
    PLAN_SCHEMA,
    grid_plan_material,
    validate_grid_plan_identity,
)
from reactive_event_router_v1 import ENTRY_BINDING_SCHEMA
from model_execution_receipt_v1 import (
    ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
    OBSERVATION_SCHEMA,
    ModelExecutionObservation,
    ModelExecutionReceiptError,
    model_execution_invocation_binding_key,
    model_execution_observation_record,
    model_execution_observation_sha256,
    validate_verified_model_execution,
    verify_model_execution,
)


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def grid_plan() -> GridPlan:
    cells = (
        CellLease("cell-00", "SCRIPT:INGRESS", ExecutionClass.SCRIPT, 0, None),
        CellLease("cell-02", "MODEL:ANALYZE", ExecutionClass.MODEL, 256, 0),
    )
    provisional = GridPlan(
        schema=PLAN_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entry_binding_schema=ENTRY_BINDING_SCHEMA,
        plan_sha256=digest("provisional-plan"),
        ingress_id="ingress:model-exec:1",
        causal_id="causal:model-exec:1",
        entity_generation=7,
        entry_event_sha256=digest("entry-event"),
        entry_admission_sha256=digest("entry-admission"),
        route_event_sha256=digest("route-event"),
        route_decision_sha256=digest("route-decision"),
        router_policy_sha256=digest("router-policy"),
        engine_identity_sha256=digest("engine-identity"),
        resolved_engine_identity="hcu_local_08b",
        resolved_engine_class="LOCAL_SHARED_WEIGHT_08B",
        resolved_engine_artifact_sha256=digest("engine-artifact"),
        capacity_receipt_sha256=digest("capacity"),
        runtime_profile_id="runtime:test",
        mode=HCUMode.GRID10,
        logical_cell_count=len(cells),
        model_call_count=1,
        physical_decoder_limit=1,
        max_wall_ms=2500,
        cells=cells,
    )
    plan_sha256 = hashlib.sha256(canonicalize(grid_plan_material(provisional))).hexdigest()
    plan = replace(provisional, plan_sha256=plan_sha256)
    validate_grid_plan_identity(plan)
    return plan


def artifact(kind: str, seed: str) -> LoaderConsumedArtifact:
    return LoaderConsumedArtifact(kind, digest(seed), 1, 10)


def verified_load(plan: GridPlan) -> VerifiedEngineLoad:
    return VerifiedEngineLoad(
        schema=VERIFIED_LOAD_SCHEMA,
        canonicalization_schema=CANONICALIZATION_SCHEMA,
        entity_generation=plan.entity_generation,
        loader_id="loader:1",
        loader_binding_sha256=digest("loader-binding"),
        engine_admission_receipt_sha256=digest("engine-admission"),
        engine_load_lease_sha256=digest("engine-load-lease"),
        engine_identity=plan.resolved_engine_identity,
        engine_class=plan.resolved_engine_class,
        engine_artifact_sha256=plan.resolved_engine_artifact_sha256,
        checkpoint=artifact("FILE_SHA256", "checkpoint"),
        tokenizer=artifact("FILE_SHA256", "tokenizer"),
        runtime=artifact("FILE_SHA256", "runtime"),
        build=artifact("FILE_SHA256", "build"),
        consumption_receipt_sha256=digest("load-consumption"),
    )


def observation(plan: GridPlan, load: VerifiedEngineLoad) -> ModelExecutionObservation:
    return ModelExecutionObservation(
        schema=OBSERVATION_SCHEMA,
        evidence_source=ACTUAL_MODEL_EXECUTOR_EVIDENCE_SOURCE,
        entity_generation=plan.entity_generation,
        executor_id="entityos:hcu:model-executor:1",
        invocation_id="invocation:1",
        engine_load_consumption_receipt_sha256=load.consumption_receipt_sha256,
        grid_plan_sha256=plan.plan_sha256,
        output_producing_cell_id="cell-02",
        role="ANALYZE",
        input_sha256=digest("input"),
        input_size=64,
        output_ref="unifieddb:candidate-output:1",
        output_sha256=digest("output"),
        output_size=128,
    )


def admission_registries(obs: ModelExecutionObservation):
    record = model_execution_observation_record(obs)
    observation_sha256 = model_execution_observation_sha256(obs)
    return (
        {observation_sha256: record},
        {model_execution_invocation_binding_key(obs): observation_sha256},
    )


def verify(plan=None, load=None, obs=None):
    plan = plan or grid_plan()
    load = load or verified_load(plan)
    obs = obs or observation(plan, load)
    observations, invocations = admission_registries(obs)
    return verify_model_execution(
        plan,
        load,
        obs,
        admitted_model_execution_observations=observations,
        admitted_model_execution_invocations=invocations,
        current_generation=plan.entity_generation,
    )


class ModelExecutionReceiptTests(unittest.TestCase):
    def test_exact_admitted_executor_observation_binds(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        verified = verify(plan, load, obs)
        validate_verified_model_execution(verified)
        self.assertEqual(verified.grid_plan_sha256, plan.plan_sha256)
        self.assertEqual(verified.output_producing_cell_id, "cell-02")
        self.assertEqual(verified.role, "ANALYZE")
        self.assertEqual(verified.output_sha256, obs.output_sha256)
        self.assertEqual(verified.engine_load_consumption_receipt_sha256, load.consumption_receipt_sha256)

    def test_claimed_actual_path_without_registry_admission_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        with self.assertRaisesRegex(ModelExecutionReceiptError, "MODEL_EXECUTION_OBSERVATION_NOT_ADMITTED"):
            verify_model_execution(
                plan,
                load,
                obs,
                admitted_model_execution_observations={},
                admitted_model_execution_invocations={
                    model_execution_invocation_binding_key(obs): model_execution_observation_sha256(obs)
                },
                current_generation=plan.entity_generation,
            )

    def test_claimed_actual_path_without_invocation_admission_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        record = model_execution_observation_record(obs)
        observation_sha256 = model_execution_observation_sha256(obs)
        with self.assertRaisesRegex(ModelExecutionReceiptError, "MODEL_EXECUTION_INVOCATION_NOT_ADMITTED"):
            verify_model_execution(
                plan,
                load,
                obs,
                admitted_model_execution_observations={observation_sha256: record},
                admitted_model_execution_invocations={},
                current_generation=plan.entity_generation,
            )

    def test_post_hoc_evidence_source_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = replace(observation(plan, load), evidence_source="POST_HOC_OUTPUT_REHASH")
        with self.assertRaisesRegex(ModelExecutionReceiptError, "ACTUAL_MODEL_EXECUTOR_IO_EVIDENCE_REQUIRED"):
            model_execution_observation_record(obs)

    def test_output_tamper_after_registry_admission_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = observation(plan, load)
        original_record = model_execution_observation_record(obs)
        original_sha = model_execution_observation_sha256(obs)
        tampered = replace(obs, output_sha256=digest("different-output"))
        with self.assertRaisesRegex(ModelExecutionReceiptError, "MODEL_EXECUTION_OBSERVATION_NOT_ADMITTED"):
            verify_model_execution(
                plan,
                load,
                tampered,
                admitted_model_execution_observations={original_sha: original_record},
                admitted_model_execution_invocations={model_execution_invocation_binding_key(obs): original_sha},
                current_generation=plan.entity_generation,
            )

    def test_same_invocation_with_different_output_fails_closed_even_if_both_observations_are_admitted(self):
        plan = grid_plan()
        load = verified_load(plan)
        original = observation(plan, load)
        tampered = replace(original, output_sha256=digest("different-output"))
        original_sha = model_execution_observation_sha256(original)
        tampered_sha = model_execution_observation_sha256(tampered)
        observations = {
            original_sha: model_execution_observation_record(original),
            tampered_sha: model_execution_observation_record(tampered),
        }
        invocations = {model_execution_invocation_binding_key(original): original_sha}
        with self.assertRaisesRegex(ModelExecutionReceiptError, "MODEL_EXECUTION_INVOCATION_OBSERVATION_MISMATCH"):
            verify_model_execution(
                plan,
                load,
                tampered,
                admitted_model_execution_observations=observations,
                admitted_model_execution_invocations=invocations,
                current_generation=plan.entity_generation,
            )

    def test_cross_cell_rebind_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = replace(observation(plan, load), output_producing_cell_id="cell-00", role="INGRESS")
        record = model_execution_observation_record(obs)
        observation_sha256 = model_execution_observation_sha256(obs)
        with self.assertRaisesRegex(ModelExecutionReceiptError, "MODEL_EXECUTION_OUTPUT_CELL_NOT_MODEL"):
            verify_model_execution(
                plan,
                load,
                obs,
                admitted_model_execution_observations={observation_sha256: record},
                admitted_model_execution_invocations={model_execution_invocation_binding_key(obs): observation_sha256},
                current_generation=plan.entity_generation,
            )

    def test_stale_generation_fails_closed(self):
        plan = grid_plan()
        load = verified_load(plan)
        obs = replace(observation(plan, load), entity_generation=6)
        record = model_execution_observation_record(obs)
        observation_sha256 = model_execution_observation_sha256(obs)
        with self.assertRaisesRegex(ModelExecutionReceiptError, "STALE_MODEL_EXECUTION_OBSERVATION_GENERATION"):
            verify_model_execution(
                plan,
                load,
                obs,
                admitted_model_execution_observations={observation_sha256: record},
                admitted_model_execution_invocations={model_execution_invocation_binding_key(obs): observation_sha256},
                current_generation=7,
            )


if __name__ == "__main__":
    unittest.main()
