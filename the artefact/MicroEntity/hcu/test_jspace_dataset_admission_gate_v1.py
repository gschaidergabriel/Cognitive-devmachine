import hashlib
import unittest
from copy import deepcopy
from dataclasses import replace

from entry_canonicalization_v1 import canonicalize
from jspace_dataset_admission_gate_v1 import (
    JSpaceDatasetAdmissionError,
    admit_for_training_dataset,
)
from jspace_vector_control_v1 import encode_vector


def h(ch):
    return ch * 64


def receipt_sha(receipt):
    return hashlib.sha256(canonicalize(dict(receipt))).hexdigest()


class GateTests(unittest.TestCase):
    def fixtures(self):
        prototype_sha = h("a")
        training_sha = h("b")
        transition_sha = h("c")
        control_packet = encode_vector(
            (0.25, -0.5, 1.0),
            basis_id="basis:7",
            basis_sha256=h("d"),
            generation=7,
            role="world",
            control_condition="BASELINE",
        )
        control_packet_sha = control_packet.packet_sha256
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
        grid_plan = {
            "schema": "ENTITYOS_HCU_GRID_PLAN/v2",
            "plan_sha256": h("4"),
            "entity_generation": 7,
            "entry_event_sha256": h("1"),
            "entry_admission_sha256": h("2"),
            "route_decision_sha256": h("3"),
        }
        regs = {
            "admitted_training_traces": {training_sha: training},
            "admitted_transition_traces": {transition_sha: transition},
            "admitted_prototype_traces": {prototype_sha: prototype},
            "admitted_grid_plans": {h("4"): grid_plan},
            "admitted_vector_control_packets": {control_packet_sha: control_packet},
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

    def rebind_packet(self, prototype, transition, training, regs, packet):
        prototype = deepcopy(prototype)
        transition = deepcopy(transition)
        training = deepcopy(training)
        regs = deepcopy(regs)
        packet_sha = packet.packet_sha256
        prototype["control_packet_identity_sha256"] = packet_sha
        transition["jspace_input_vector_ref"] = f"sha256:{packet_sha}"
        training["vector_control_packet_sha256"] = packet_sha
        regs["admitted_prototype_traces"][training["prototype_trace_sha256"]] = prototype
        regs["admitted_transition_traces"][transition["trace_sha256"]] = transition
        regs["admitted_training_traces"][training["trace_sha256"]] = training
        regs["admitted_vector_control_packets"] = {packet_sha: packet}
        return prototype, transition, training, regs

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
        _, _, _, regs = self.fixtures()
        expected_packet_sha = next(iter(regs["admitted_vector_control_packets"]))
        admission = self.admit(regs=regs)
        self.assertEqual(admission.schema, "ENTITYOS_HCU_JSPACE_DATASET_ADMISSION/v2")
        self.assertEqual(admission.generation, 7)
        self.assertEqual(admission.grid_plan_sha256, h("4"))
        self.assertEqual(admission.vector_control_packet_sha256, expected_packet_sha)
        self.assertEqual(admission.vector_control_condition, "BASELINE")
        self.assertEqual(admission.credit_label, "UNKNOWN")

    def test_shared_digest_without_packet_preimage_fails(self):
        _, transition, training, regs = self.fixtures()
        regs = deepcopy(regs)
        regs["admitted_vector_control_packets"] = {}
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "VECTOR_CONTROL_PACKET_NOT_ADMITTED"):
            self.admit(transition=transition, training=training, regs=regs)

    def test_packet_registry_value_identity_mismatch_fails(self):
        prototype, transition, training, regs = self.fixtures()
        referenced_sha = training["vector_control_packet_sha256"]
        other = encode_vector(
            (0.5, -0.25, 1.0),
            basis_id="basis:7",
            basis_sha256=h("d"),
            generation=7,
            role="world",
            control_condition="BASELINE",
        )
        regs = deepcopy(regs)
        regs["admitted_vector_control_packets"] = {referenced_sha: other}
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH"):
            self.admit(transition=transition, training=training, regs=regs)

    def test_tampered_packet_preimage_fails_selected_abi_validator(self):
        _, transition, training, regs = self.fixtures()
        packet = next(iter(regs["admitted_vector_control_packets"].values()))
        tampered = replace(packet, q8_values=(126,) + packet.q8_values[1:])
        regs = deepcopy(regs)
        regs["admitted_vector_control_packets"] = {packet.packet_sha256: tampered}
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "VECTOR_CONTROL_PACKET_REJECTED:VECTOR_CONTROL_PACKET_DIGEST_MISMATCH"):
            self.admit(transition=transition, training=training, regs=regs)

    def test_packet_generation_basis_role_and_condition_crossbind(self):
        cases = [
            ({"generation": 8}, "VECTOR_CONTROL_PACKET_GENERATION_MISMATCH"),
            ({"basis_id": "basis:other"}, "VECTOR_CONTROL_PACKET_BASIS_ID_MISMATCH"),
            ({"basis_sha256": h("e")}, "VECTOR_CONTROL_PACKET_BASIS_SHA256_MISMATCH"),
            ({"role": "critic"}, "VECTOR_CONTROL_PACKET_ROLE_MISMATCH"),
            ({"control_condition": "LESION"}, "VECTOR_CONTROL_PACKET_CONDITION_MISMATCH"),
        ]
        for overrides, code in cases:
            with self.subTest(code=code):
                prototype, transition, training, regs = self.fixtures()
                kwargs = {
                    "basis_id": "basis:7",
                    "basis_sha256": h("d"),
                    "generation": 7,
                    "role": "world",
                    "control_condition": "BASELINE",
                }
                kwargs.update(overrides)
                packet = encode_vector((0.25, -0.5, 1.0), **kwargs)
                _, transition, training, regs = self.rebind_packet(
                    prototype, transition, training, regs, packet
                )
                with self.assertRaisesRegex(JSpaceDatasetAdmissionError, code):
                    self.admit(transition=transition, training=training, regs=regs)

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

    def test_shared_but_unadmitted_grid_hash_fails(self):
        _, transition, training, regs = self.fixtures()
        forged_transition = deepcopy(transition)
        forged_training = deepcopy(training)
        forged_transition["grid_plan_sha256"] = h("9")
        forged_training["grid_plan_sha256"] = h("9")
        regs = deepcopy(regs)
        regs["admitted_transition_traces"][forged_transition["trace_sha256"]] = forged_transition
        regs["admitted_training_traces"][forged_training["trace_sha256"]] = forged_training
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "GRID_PLAN_NOT_ADMITTED"):
            self.admit(transition=forged_transition, training=forged_training, regs=regs)

    def test_admitted_grid_plan_crossbinds_generation_entry_and_route(self):
        _, transition, training, regs = self.fixtures()
        cases = [
            ("entity_generation", 8, "GRID_PLAN_GENERATION_MISMATCH"),
            ("entry_event_sha256", h("9"), "GRID_PLAN_CAUSAL_BINDING_MISMATCH:entry_event_sha256"),
            ("entry_admission_sha256", h("9"), "GRID_PLAN_CAUSAL_BINDING_MISMATCH:entry_admission_sha256"),
            ("route_decision_sha256", h("9"), "GRID_PLAN_CAUSAL_BINDING_MISMATCH:route_decision_sha256"),
        ]
        for field, value, code in cases:
            with self.subTest(code=code):
                poisoned = deepcopy(regs)
                poisoned["admitted_grid_plans"][h("4")][field] = value
                with self.assertRaisesRegex(JSpaceDatasetAdmissionError, code):
                    self.admit(transition=transition, training=training, regs=poisoned)

    def test_grid_plan_receipt_schema_is_exact(self):
        _, transition, training, regs = self.fixtures()
        poisoned = deepcopy(regs)
        poisoned["admitted_grid_plans"][h("4")]["extra"] = "untrusted"
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "GRID_PLAN_RECEIPT_SCHEMA_MISMATCH"):
            self.admit(transition=transition, training=training, regs=poisoned)

    def test_credit_label_must_match_live_transition(self):
        _, transition, training, regs = self.fixtures()
        forged = deepcopy(training)
        forged["credit_label"] = "POSITIVE"
        forged["outcome_receipt_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][forged["trace_sha256"]] = forged
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "CREDIT_LABEL_BINDING:MISMATCH:training"):
            self.admit(transition=transition, training=forged, regs=regs, outcomes={})

    def test_outcome_receipt_key_must_match_canonical_bytes(self):
        _, transition, training, regs = self.fixtures()
        credited = deepcopy(training)
        credited["credit_label"] = "POSITIVE"
        credited_transition = deepcopy(transition)
        credited_transition["credit_label"] = "POSITIVE"
        receipt = self.bound_outcome(credited, credited_transition)
        credited["outcome_receipt_sha256"] = h("6")
        regs = deepcopy(regs)
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        regs["admitted_transition_traces"][credited_transition["trace_sha256"]] = credited_transition
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_RECEIPT_IDENTITY_MISMATCH"):
            self.admit(
                transition=credited_transition,
                training=credited,
                regs=regs,
                outcomes={h("6"): receipt},
            )

    def test_byte_distinct_receipt_cannot_reuse_claimed_sha_identity(self):
        _, transition, training, regs = self.fixtures()
        credited = deepcopy(training)
        credited["credit_label"] = "POSITIVE"
        credited_transition = deepcopy(transition)
        credited_transition["credit_label"] = "POSITIVE"
        receipt = self.bound_outcome(credited, credited_transition)
        claimed = receipt_sha(receipt)
        altered = deepcopy(receipt)
        altered["evidence_note"] = "byte-distinct receipt"
        self.assertNotEqual(receipt_sha(altered), claimed)
        credited["outcome_receipt_sha256"] = claimed
        regs = deepcopy(regs)
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        regs["admitted_transition_traces"][credited_transition["trace_sha256"]] = credited_transition
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_RECEIPT_IDENTITY_MISMATCH"):
            self.admit(
                transition=credited_transition,
                training=credited,
                regs=regs,
                outcomes={claimed: altered},
            )

    def test_unknown_credit_outcome_requires_exact_causal_binding(self):
        _, transition, training, regs = self.fixtures()
        unknown = deepcopy(training)
        regs = deepcopy(regs)

        unrelated = self.bound_outcome(
            unknown,
            transition,
            credit="UNKNOWN",
            entry_event_sha256=h("9"),
        )
        unrelated_sha = receipt_sha(unrelated)
        unknown["outcome_receipt_sha256"] = unrelated_sha
        regs["admitted_training_traces"][unknown["trace_sha256"]] = unknown
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_CAUSAL_BINDING_MISMATCH:entry_event_sha256"):
            self.admit(
                transition=transition,
                training=unknown,
                regs=regs,
                outcomes={unrelated_sha: unrelated},
            )

        exact = self.bound_outcome(unknown, transition, credit="UNKNOWN")
        exact_sha = receipt_sha(exact)
        unknown["outcome_receipt_sha256"] = exact_sha
        regs["admitted_training_traces"][unknown["trace_sha256"]] = unknown
        admission = self.admit(
            transition=transition,
            training=unknown,
            regs=regs,
            outcomes={exact_sha: exact},
        )
        self.assertEqual(admission.credit_label, "UNKNOWN")
        self.assertEqual(admission.outcome_receipt_sha256, exact_sha)

    def test_nonunknown_credit_requires_exact_causal_outcome_binding(self):
        _, transition, training, regs = self.fixtures()
        credited = deepcopy(training)
        credited["credit_label"] = "POSITIVE"
        credited_transition = deepcopy(transition)
        credited_transition["credit_label"] = "POSITIVE"
        exact = self.bound_outcome(credited, credited_transition)
        exact_sha = receipt_sha(exact)
        credited["outcome_receipt_sha256"] = exact_sha
        regs = deepcopy(regs)
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        regs["admitted_transition_traces"][credited_transition["trace_sha256"]] = credited_transition

        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_RECEIPT_NOT_ADMITTED"):
            self.admit(transition=credited_transition, training=credited, regs=regs, outcomes={})

        unrelated = self.bound_outcome(credited, credited_transition, entry_event_sha256=h("9"))
        unrelated_sha = receipt_sha(unrelated)
        credited["outcome_receipt_sha256"] = unrelated_sha
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        with self.assertRaisesRegex(JSpaceDatasetAdmissionError, "OUTCOME_CAUSAL_BINDING_MISMATCH:entry_event_sha256"):
            self.admit(
                transition=credited_transition,
                training=credited,
                regs=regs,
                outcomes={unrelated_sha: unrelated},
            )

        exact = self.bound_outcome(credited, credited_transition)
        exact_sha = receipt_sha(exact)
        credited["outcome_receipt_sha256"] = exact_sha
        regs["admitted_training_traces"][credited["trace_sha256"]] = credited
        admission = self.admit(
            transition=credited_transition,
            training=credited,
            regs=regs,
            outcomes={exact_sha: exact},
        )
        self.assertEqual(admission.credit_label, "POSITIVE")
        self.assertEqual(admission.outcome_receipt_sha256, exact_sha)


if __name__ == "__main__":
    unittest.main()
