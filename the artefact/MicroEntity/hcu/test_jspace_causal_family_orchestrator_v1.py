from dataclasses import replace
import unittest

from jspace_causal_family_identity_gate_v1 import CausalTrialIdentity, REQUIRED_CONDITIONS
from jspace_causal_family_orchestrator_v1 import (
    CausalFamilyOrchestratorError,
    CausalFamilyPlan,
    CausalTrialSpec,
    EVIDENCE_CLASS,
    PLAN_SCHEMA,
    causal_family_plan_sha256,
    run_causal_family,
    validate_causal_family_plan,
)


def h(char):
    return char * 64


def model_input_for(condition):
    return h("5") if condition == "BASELINE_CLEAN" else h("6")


def plan():
    specs = []
    for index, condition in enumerate(REQUIRED_CONDITIONS):
        specs.append(CausalTrialSpec(
            condition=condition,
            input_variant_id="clean" if condition == "BASELINE_CLEAN" else "corrupted",
            model_input_sha256=model_input_for(condition),
            intervention_sha256=None if condition.startswith("BASELINE_") else f"{index + 70:064x}",
        ))
    return CausalFamilyPlan(
        schema=PLAN_SCHEMA,
        family_id="holdout:family:17",
        generation=7,
        trials=tuple(reversed(specs)),
    )


class FakeExecutor:
    def __init__(self, mutate=None):
        self.calls = []
        self.mutate = mutate

    def run_causal_trial(self, spec, *, family_id, generation):
        index = REQUIRED_CONDITIONS.index(spec.condition)
        trial = CausalTrialIdentity(
            condition=spec.condition,
            family_id=family_id,
            input_variant_id=spec.input_variant_id,
            model_input_sha256=spec.model_input_sha256,
            generation=generation,
            checkpoint_sha256=h("1"),
            tokenizer_sha256=h("2"),
            runtime_build_sha256=h("3"),
            loader_consumption_sha256=h("4"),
            model_execution_sha256=f"{index + 10:064x}",
            inference_receipt_sha256=f"{index + 20:064x}",
            trace_sha256=f"{index + 30:064x}",
            output_sha256=f"{index + 40:064x}",
            activation_site_id="resid_post:layer=12:position=last",
            pre_activation_sha256=f"{index + 50:064x}",
            post_activation_sha256=f"{index + 60:064x}",
            intervention_sha256=spec.intervention_sha256,
        )
        if self.mutate is not None:
            trial = self.mutate(spec, trial)
        self.calls.append((spec.condition, family_id, generation))
        return trial


class CausalFamilyOrchestratorTests(unittest.TestCase):
    def test_complete_family_runs_in_canonical_order_without_causal_credit(self):
        executor = FakeExecutor()
        result = run_causal_family(executor, plan())
        self.assertEqual([call[0] for call in executor.calls], list(REQUIRED_CONDITIONS))
        self.assertEqual(result.evidence_class, EVIDENCE_CLASS)
        self.assertFalse(result.jspace_causal_credit)
        self.assertFalse(result.identity_result.jspace_causal_credit)
        self.assertEqual(result.invocation_count, 5)
        self.assertEqual(len(result.plan_sha256), 64)
        self.assertEqual(result.family_identity_sha256, result.identity_result.family_identity_sha256)
        self.assertEqual(result.identity_result.clean_model_input_sha256, h("5"))
        self.assertEqual(result.identity_result.corrupted_model_input_sha256, h("6"))
        self.assertEqual(len(result.trial_identity_sha256), 5)

    def test_plan_digest_is_canonical_across_input_order(self):
        original = plan()
        canonical_trials = validate_causal_family_plan(original)
        reordered = replace(original, trials=canonical_trials)
        self.assertEqual(causal_family_plan_sha256(original), causal_family_plan_sha256(reordered))

    def test_duplicate_intervention_fails_before_executor_invocation(self):
        current = plan()
        trials = list(current.trials)
        target = next(spec for spec in trials if spec.condition == "INTERVENTION_TARGET")
        sham_index = next(i for i, spec in enumerate(trials) if spec.condition == "SHAM_CONTROL")
        trials[sham_index] = replace(trials[sham_index], intervention_sha256=target.intervention_sha256)
        executor = FakeExecutor()
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "CROSS_CONTROL_REUSE_FORBIDDEN"):
            run_causal_family(executor, replace(current, trials=tuple(trials)))
        self.assertEqual(executor.calls, [])

    def test_plan_rejects_input_content_drift_before_executor_invocation(self):
        current = plan()
        trials = list(current.trials)
        target_index = next(i for i, spec in enumerate(trials) if spec.condition == "INTERVENTION_TARGET")
        trials[target_index] = replace(trials[target_index], model_input_sha256=h("7"))
        executor = FakeExecutor()
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "CORRUPTED_BASE_MODEL_INPUT_REQUIRED"):
            run_causal_family(executor, replace(current, trials=tuple(trials)))
        self.assertEqual(executor.calls, [])

        trials = list(current.trials)
        corrupted_index = next(i for i, spec in enumerate(trials) if spec.condition == "BASELINE_CORRUPTED")
        trials[corrupted_index] = replace(trials[corrupted_index], model_input_sha256=h("5"))
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "BASELINE_CONTENT_COLLISION_FORBIDDEN"):
            validate_causal_family_plan(replace(current, trials=tuple(trials)))

    def test_executor_cannot_relabel_condition_or_input(self):
        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, condition="SHAM_CONTROL")
            if spec.condition == "INTERVENTION_TARGET" else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "EXECUTOR_CONDITION_RELABEL_FORBIDDEN"):
            run_causal_family(executor, plan())

        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, input_variant_id="other")
            if spec.condition == "BASELINE_CORRUPTED" else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "EXECUTOR_INPUT_VARIANT_MISMATCH"):
            run_causal_family(executor, plan())

        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, model_input_sha256=h("7"))
            if spec.condition == "INTERVENTION_TARGET" else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "EXECUTOR_MODEL_INPUT_IDENTITY_MISMATCH"):
            run_causal_family(executor, plan())

    def test_executor_cannot_substitute_intervention_or_generation(self):
        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, intervention_sha256=h("a"))
            if spec.condition == "INTERVENTION_TARGET" else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "EXECUTOR_INTERVENTION_IDENTITY_MISMATCH"):
            run_causal_family(executor, plan())

        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, generation=8)
            if spec.condition == "SHAM_CONTROL" else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "EXECUTOR_GENERATION_MISMATCH"):
            run_causal_family(executor, plan())

    def test_downstream_identity_reuse_is_rejected_by_existing_gate(self):
        shared = f"{999:064x}"
        executor = FakeExecutor(
            mutate=lambda spec, trial: replace(trial, trace_sha256=shared)
            if spec.condition in {"SHAM_CONTROL", "OFF_TARGET_CONTROL"} else trial
        )
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "IDENTITY_GATE_REJECTED:trace_sha256:CROSS_CONTROL_REUSE_FORBIDDEN"):
            run_causal_family(executor, plan())

    def test_baseline_intervention_and_noncanonical_family_id_fail_closed(self):
        current = plan()
        trials = list(current.trials)
        clean_index = next(i for i, spec in enumerate(trials) if spec.condition == "BASELINE_CLEAN")
        trials[clean_index] = replace(trials[clean_index], intervention_sha256=h("a"))
        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "BASELINE_INTERVENTION_MUST_BE_NONE"):
            validate_causal_family_plan(replace(current, trials=tuple(trials)))

        with self.assertRaisesRegex(CausalFamilyOrchestratorError, "NONCANONICAL_WHITESPACE_FORBIDDEN"):
            validate_causal_family_plan(replace(current, family_id=" holdout:family:17 "))


if __name__ == "__main__":
    unittest.main()
