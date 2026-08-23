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
        prototype = {
            "schema": "ENTITYOS_HCU_GLOBAL_JSPACE_GWT_TRACE/v3",
            "generation": 7,
            "winner_cell_id": "cell-02",
            "winner_role": "world",
            "basis_id": "basis:7",
            "basis_sha256": h("d"),
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
            "jspace_vector_control_abi": "JSPACE_VECTOR_CONTROL_ABI/v1",
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

    def test_unknown_credit_outcome_still_requires_exact_causal_binding(self):
        _, transition, training, regs = self.fixtures()
        unknown = deepcopy(training)
        unknown["outcome_receipt_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][unknown["trace_sha256"]] = unknown

        unrelated = self.bound_outcome(
            unknown,
            transition,
            credit="UNKNOWN",
            entry_event_sha256=h("9"),
        )
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_CAUSAL_BINDING_MISMATCH:entry_event_sha256"):
            self.admit(
                transition=transition,
                training=unknown,
                regs=regs,
                outcomes={h("6"): unrelated},
            )

        admission = self.admit(
            transition=transition,
            training=unknown,
            regs=regs,
            outcomes={h("6"): self.bound_outcome(unknown, transition, credit="UNKNOWN")},
        )
        self.assertEqual(admission.credit_label, "UNKNOWN")
        self.assertEqual(admission.outcome_receipt_sha256, h("6"))

    def test_nonunknown_credit_requires_exact_causal_outcome_binding(self):
        _, transition, training, regs = self.fixtures()
        credited = deepcopy(training)
        credited["credit_label"] = "POSITIVE"
        credited["outcome_receipt_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited

        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_RECEIPT_NOT_ADMITTED"):
            self.admit(transition=transition, training=credited, regs=regs, outcomes={})

        unrelated = self.bound_outcome(
            credited,
            transition,
            entry_event_sha256=h("9"),
        )
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_CAUSAL_BINDING_MISMATCH:entry_event_sha256"):
            self.admit(
                transition=transition,
                training=credited,
                regs=regs,
                outcomes={h("6"): unrelated},
            )

        admission = self.admit(
            transition=transition,
            training=credited,
            regs=regs,
            outcomes={h("6"): self.bound_outcome(credited, transition)},
        )
        self.assertEqual(admission.credit_label, "POSITIVE")


if __name__ == "__main__":
    unittest.main()
