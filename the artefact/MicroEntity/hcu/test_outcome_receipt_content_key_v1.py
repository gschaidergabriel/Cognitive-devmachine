import hashlib
import unittest

from entry_canonicalization_v1 import canonicalize
from outcome_receipt_content_key_v1 import (
    OutcomeReceiptContentKeyError,
    finalize_outcome_receipt,
    outcome_receipt_content_key,
    verify_outcome_receipt_content_key,
)


def h(ch):
    return ch * 64


def provisional(**overrides):
    value = {
        "status": "VERIFIED",
        "credit_label": "POSITIVE",
        "transition_trace_sha256": h("a"),
        "generation": 7,
        "entry_event_sha256": h("1"),
        "entry_admission_sha256": h("2"),
        "route_decision_sha256": h("3"),
        "grid_plan_sha256": h("4"),
        "cell_id": "cell-02",
        "role": "world",
    }
    value.update(overrides)
    return value


class OutcomeReceiptContentKeyTests(unittest.TestCase):
    def test_constructive_dag_has_no_hash_cycle(self):
        before = provisional()
        key = outcome_receipt_content_key(before)
        training_material = {
            "schema_version": "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1",
            "outcome_receipt_sha256": key,
            "transition_trace_sha256": before["transition_trace_sha256"],
        }
        training_sha = hashlib.sha256(canonicalize(training_material)).hexdigest()
        final = finalize_outcome_receipt(before, training_sha)
        self.assertEqual(outcome_receipt_content_key(final), key)
        verify_outcome_receipt_content_key(
            final,
            key,
            expected_training_trace_sha256=training_sha,
        )

    def test_only_late_training_backreference_is_excluded_from_key(self):
        base = provisional()
        first = finalize_outcome_receipt(base, h("b"))
        second = finalize_outcome_receipt(base, h("c"))
        self.assertEqual(outcome_receipt_content_key(first), outcome_receipt_content_key(second))
        with self.assertRaisesRegex(OutcomeReceiptContentKeyError, "OUTCOME_TRAINING_TRACE_MISMATCH"):
            verify_outcome_receipt_content_key(
                second,
                outcome_receipt_content_key(first),
                expected_training_trace_sha256=h("b"),
            )

    def test_every_causal_or_credit_field_changes_content_key(self):
        base = provisional()
        base_key = outcome_receipt_content_key(base)
        changes = {
            "credit_label": "NEGATIVE",
            "transition_trace_sha256": h("b"),
            "generation": 8,
            "entry_event_sha256": h("5"),
            "entry_admission_sha256": h("6"),
            "route_decision_sha256": h("7"),
            "grid_plan_sha256": h("8"),
            "cell_id": "cell-03",
            "role": "critic",
        }
        for field, value in changes.items():
            with self.subTest(field=field):
                self.assertNotEqual(
                    outcome_receipt_content_key(provisional(**{field: value})),
                    base_key,
                )

    def test_unbound_extra_field_fails_closed(self):
        value = provisional()
        value["evidence_note"] = "unhashed metadata must not ride along"
        with self.assertRaisesRegex(OutcomeReceiptContentKeyError, "FIELD_SET_MISMATCH"):
            outcome_receipt_content_key(value)

    def test_missing_content_field_fails_closed(self):
        value = provisional()
        del value["route_decision_sha256"]
        with self.assertRaisesRegex(OutcomeReceiptContentKeyError, "FIELD_SET_MISMATCH"):
            outcome_receipt_content_key(value)

    def test_noncanonical_text_and_invalid_credit_fail_closed(self):
        with self.assertRaisesRegex(OutcomeReceiptContentKeyError, "NONCANONICAL_TEXT"):
            outcome_receipt_content_key(provisional(role=" world"))
        with self.assertRaisesRegex(OutcomeReceiptContentKeyError, "OUTCOME_CREDIT_LABEL_UNSUPPORTED"):
            outcome_receipt_content_key(provisional(credit_label="MAYBE"))

    def test_content_key_is_not_full_receipt_byte_digest(self):
        final = finalize_outcome_receipt(provisional(), h("b"))
        content_key = outcome_receipt_content_key(final)
        full_digest = hashlib.sha256(canonicalize(final)).hexdigest()
        self.assertNotEqual(content_key, full_digest)


if __name__ == "__main__":
    unittest.main()
