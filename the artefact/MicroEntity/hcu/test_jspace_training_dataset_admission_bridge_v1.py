import unittest
from copy import deepcopy

from jspace_training_dataset_admission_bridge_v1 import (
    JSpaceTrainingDatasetAdmissionBridgeError,
    compile_admitted_traces,
)
from test_compile_jspace_training_dataset_v1 import CausalTrainingDatasetCompilerTests


def h(ch):
    return ch * 64


class TrainingDatasetAdmissionBridgeTests(unittest.TestCase):
    def fixtures(self):
        training = CausalTrainingDatasetCompilerTests().training_trace()
        prototype_sha = training["prototype_trace_sha256"]
        prototype = {
            "schema": "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v3",
            "generation": training["generation"],
            "winner_cell_id": training["cell_id"],
            "winner_role": training["role"],
            "basis_id": training["jspace_basis_id"],
            "basis_sha256": training["jspace_basis_sha256"],
        }
        transition = {
            "schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1",
            "trace_sha256": h("c"),
            "generation": training["generation"],
            "entry_event_sha256": training["entry_event_sha256"],
            "entry_admission_sha256": training["entry_admission_sha256"],
            "route_decision_sha256": training["route_decision_sha256"],
            "grid_plan_sha256": training["grid_plan_sha256"],
            "cell_id": training["cell_id"],
            "role": training["role"],
            "jspace_basis_id": training["jspace_basis_id"],
            "jspace_basis_sha256": training["jspace_basis_sha256"],
            "jspace_vector_control_abi": "JSPACE_VECTOR_CONTROL_ABI/v1",
        }
        regs = {
            "admitted_training_traces": {training["trace_sha256"]: training},
            "admitted_transition_traces": {transition["trace_sha256"]: transition},
            "admitted_prototype_traces": {prototype_sha: prototype},
        }
        return training, transition, regs

    def compile(self, training=None, transition=None, regs=None):
        base_training, base_transition, base_regs = self.fixtures()
        training = base_training if training is None else training
        transition = base_transition if transition is None else transition
        regs = base_regs if regs is None else regs
        return compile_admitted_traces([(training, transition)], **regs)

    def test_admitted_trace_delegates_to_existing_serializer(self):
        result = self.compile()
        self.assertEqual(result["schema"], "ENTITYOS_HCU_JSPACE_TRAINING_DATASET_ADMISSION_BRIDGE/v1")
        self.assertEqual(len(result["admissions"]), 1)
        self.assertGreater(sum(len(rows) for rows in result["splits"].values()), 0)

    def test_unadmitted_training_trace_cannot_reach_serializer(self):
        training, transition, regs = self.fixtures()
        regs = deepcopy(regs)
        regs["admitted_training_traces"] = {}
        with self.assertRaisesRegex(
            JSpaceTrainingDatasetAdmissionBridgeError,
            "DATASET_ADMISSION_REJECTED:admitted_training_traces:TRACE_NOT_ADMITTED",
        ):
            self.compile(training=training, transition=transition, regs=regs)

    def test_registry_admitted_cross_episode_route_transplant_fails_closed(self):
        # GO unusual discriminator: even a registry-admitted transition cannot be paired
        # with this training trace when its route identity belongs to another episode.
        training, transition, regs = self.fixtures()
        poisoned = deepcopy(transition)
        poisoned["route_decision_sha256"] = h("9")
        poisoned["trace_sha256"] = h("d")
        regs = deepcopy(regs)
        regs["admitted_transition_traces"] = {poisoned["trace_sha256"]: poisoned}
        with self.assertRaisesRegex(
            JSpaceTrainingDatasetAdmissionBridgeError,
            "DATASET_ADMISSION_REJECTED:CAUSAL_BINDING:route_decision_sha256:MISMATCH",
        ):
            self.compile(training=training, transition=poisoned, regs=regs)

    def test_one_training_trace_cannot_alias_two_transition_families(self):
        training, transition, regs = self.fixtures()
        second = deepcopy(transition)
        second["trace_sha256"] = h("e")
        regs = deepcopy(regs)
        regs["admitted_transition_traces"][second["trace_sha256"]] = second
        with self.assertRaisesRegex(
            JSpaceTrainingDatasetAdmissionBridgeError,
            "TRAINING_TRACE_BOUND_TO_MULTIPLE_TRANSITIONS",
        ):
            compile_admitted_traces([(training, transition), (training, second)], **regs)


if __name__ == "__main__":
    unittest.main()
