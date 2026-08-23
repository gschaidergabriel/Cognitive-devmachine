import unittest
from copy import deepcopy

from jspace_dataset_admission_gate_v1 import (
    JSpaceDatasetAdmissionError,
    admit_for_training_dataset,
)


def h(ch):
    return ch * 64


class GateTests(unittest.TestCase):
    def fixtures(self):
        prototype_sha = h("a")
        training_sha = h("b")
        transition_sha = h("c")
        control_packet_sha = h("5")
        prototype = {
            "schema": "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v3",
            "generation": 7,
            "winner_cell_id": "cell-02",
            "winner_role": "world",
            "basis_id": "basis:7",
            "basis_sha256": h("d"),
            "control_packet_identity_sha256": control_packet_sha,
            "control_condition": "BASELINE",
        }
        transition = {
            "schema_version": "JSPACE_GWT_TRANSITION_TRACE/v1",
            "trace_sha256": transition_sha,
            "generation": 7,
            "entry_event_sha256": h("1"),
            "entry_admission_sha256": h("2"),
            "route_decision_sha256": h("3"),
            "grid_plan_sha256": h("4"),
            "cell_id": "cell-02",
            "role": "world",
            "jspace_basis_id": "basis:7",
            "jspace_basis_sha256": h("d"),
            "jspace_input_vector_ref": f"sha256:{control_packet_sha}",
            "jspace_vector_control_abi": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "falsifier_lesion_condition": "BASELINE",
            "credit_label": "UNKNOWN",
        }
        training = {
            "schema_version": "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1",
            "trace_sha256": training_sha,
            "prototype_trace_sha256": prototype_sha,
            "generation": 7,
            "entry_event_sha256": h("1"),
            "entry_admission_sha256": h("2"),
            "route_decision_sha256": h("3"),
            "grid_plan_sha256": h("4"),
            "cell_id": "cell-02",
            "role": "world",
            "jspace_basis_id": "basis:7",
            "jspace_basis_sha256": h("d"),
            "jspace_input_codec_version": "JSPACE_VECTOR_CONTROL_ABI/v1",
            "vector_control_packet_sha256": control_packet_sha,
            "vector_control_condition": "BASELINE",
            "credit_label": "UNKNOWN",
            "outcome_receipt_sha256": None,
        }
        regs = {
            "admitted_training_traces": {training_sha: training},
            "admitted_transition_traces": {transition_sha: transition},
            "admitted_prototype_traces": {prototype_sha: prototype},
        }
        return prototype, transition, training, regs

    def admit(self, transition=None, training=None, regs=None, outcomes=None):
        prototype, base_transition, base_training, base_regs = self.fixtures()
        transition = base_transition if transition is None else transition
        training = base_training if training is None else training
        regs = base_regs if regs is None else regs
        return admit_for_training_dataset(
            training,
            transition,
            **regs,
            admitted_outcome_receipts=outcomes,
        )

    def bound_outcome(self, training, transition, *, credit="POSITIVE", **overrides):
        receipt = {
            "status": "VERIFIED",
            "credit_label": credit,
            "training_trace_sha256": training["trace_sha256"],
            "transition_trace_sha256": transition["trace_sha256"],
            "generation": training["generation"],
            "entry_event_sha256": training["entry_event_sha256"],
            "entry_admission_sha256": training["entry_admission_sha256"],
            "route_decision_sha256": training["route_decision_sha256"],
            "grid_plan_sha256": training["grid_plan_sha256"],
            "cell_id": training["cell_id"],
            "role": training["role"],
        }
        receipt.update(overrides)
        return receipt

    def test_exact_admitted_binding_passes(self):
        admission = self.admit()
        self.assertEqual(admission.generation, 7)
        self.assertEqual(admission.grid_plan_sha256, h("4"))
        self.assertEqual(admission.vector_control_packet_sha256, h("5"))
        self.assertEqual(admission.vector_control_condition, "BASELINE")
        self.assertEqual(admission.credit_label, "UNKNOWN")

    def test_unadmitted_synthetic_training_trace_fails(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["trace_sha256"] = h("e")
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "TRACE_NOT_ADMITTED"):
            self.admit(transition=transition, training=forged, regs=regs)

    def test_causal_id_transplant_fails_even_when_trace_is_registry_admitted(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["entry_event_sha256"] = h("9")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "CAUSAL_BINDING:entry_event_sha256:MISMATCH"):
            self.admit(transition=transition, training=forged, regs=regs)

    def test_basis_bytes_transplant_fails(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["jspace_basis_sha256"] = h("e")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "BASIS_SHA256_BINDING:MISMATCH"):
            self.admit(transition=transition, training=forged, regs=regs)

    def test_control_packet_transplant_fails_across_dataset_layers(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["vector_control_packet_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "VECTOR_CONTROL_PACKET_BINDING:MISMATCH:training"):
            self.admit(transition=transition, training=forged, regs=regs)

    def test_control_condition_transplant_fails_across_dataset_layers(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["vector_control_condition"] = "LESION"
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "VECTOR_CONTROL_CONDITION_BINDING:MISMATCH:training"):
            self.admit(transition=transition, training=forged, regs=regs)

    def test_credit_label_must_match_live_transition(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["credit_label"] = "POSITIVE"
        forged["outcome_receipt_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "CREDIT_LABEL_BINDING:MISMATCH:training"):
            self.admit(transition=transition, training=forged, regs=regs, outcomes={})

    def test_nonunknown_credit_requires_exact_causal_outcome_binding(self):
        _, transition, training, regs = self.fixtures()
        credited = deepcopy(training)
        credited["credit_label"] = "POSITIVE"
        credited["outcome_receipt_sha256"] = h("6")
        credited_transition = deepcopy(transition)
        credited_transition["credit_label"] = "POSITIVE"
        regs = deepcopy(regs)
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        regs["admitted_transition_traces"][credited_transition["trace_sha256"]] = credited_transition

        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_RECEIPT_NOT_ADMITTED"):
            self.admit(transition=credited_transition, training=credited, regs=regs, outcomes={})

        unrelated = self.bound_outcome(
            credited,
            credited_transition,
            entry_event_sha256=h("9"),
        )
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_CAUSAL_BINDING_MISMATCH:entry_event_sha256"):
            self.admit(
                transition=credited_transition,
                training=credited,
                regs=regs,
                outcomes={h("6"): unrelated},
            )

        admission = self.admit(
            transition=credited_transition,
            training=credited,
            regs=regs,
            outcomes={h("6"): self.bound_outcome(credited, credited_transition)},
        )
        self.assertEqual(admission.credit_label, "POSITIVE")


if __name__ == "__main__":
    unittest.main()
