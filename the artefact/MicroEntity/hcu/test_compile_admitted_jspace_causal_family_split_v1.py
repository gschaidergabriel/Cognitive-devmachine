import unittest

from compile_admitted_jspace_training_dataset_v1 import (
    CAUSAL_FAMILY_SCHEMA,
    PIPELINE_SCHEMA,
    AdmittedTrainingDatasetError,
    PipelineEvidence,
    _annotate_rows,
    _derive_causal_family_sha256,
)
from jspace_dataset_family_split_v1 import split_for_family


def h(ch: str) -> str:
    return ch * 64


CAUSAL = {
    "entry_event_sha256": h("1"),
    "entry_admission_sha256": h("2"),
    "route_decision_sha256": h("3"),
    "grid_plan_sha256": h("4"),
}


def evidence(label: str, *, causal=None) -> PipelineEvidence:
    causal = dict(CAUSAL if causal is None else causal)
    causal_family_sha256 = _derive_causal_family_sha256(generation=7, causal=causal)
    return PipelineEvidence(
        schema=PIPELINE_SCHEMA,
        training_trace_sha256=h("5"),
        transition_trace_sha256=h("6"),
        prototype_trace_sha256=h("7"),
        inference_binding_sha256=h("8"),
        inference_receipt_sha256=h("9"),
        engine_load_consumption_receipt_sha256=h("a"),
        output_sha256=h("b"),
        generation=7,
        entry_event_sha256=causal["entry_event_sha256"],
        entry_admission_sha256=causal["entry_admission_sha256"],
        route_decision_sha256=causal["route_decision_sha256"],
        grid_plan_sha256=causal["grid_plan_sha256"],
        cell_id="cell:critic:0",
        role="critic",
        declared_trace_family_id=label,
        causal_family_sha256=causal_family_sha256,
        credit_label="UNKNOWN",
        outcome_receipt_sha256=None,
    )


def lower(split: str, label: str):
    value = {"train": [], "validation": [], "holdout": []}
    value[split] = [
        {
            "messages": [],
            "metadata": {
                "trace_sha256": h("5"),
                "trace_family_id": label,
            },
        }
    ]
    return value


class CausalFamilySplitTests(unittest.TestCase):
    def test_same_admitted_causal_ancestry_different_labels_one_split(self):
        left = evidence("same-causal-origin-alias-0")
        right = evidence("same-causal-origin-alias-12")
        self.assertEqual(left.causal_family_sha256, right.causal_family_sha256)

        expected = split_for_family(left.causal_family_sha256)
        left_rows = _annotate_rows(lower("train", left.declared_trace_family_id), left)
        right_rows = _annotate_rows(lower("holdout", right.declared_trace_family_id), right)

        self.assertEqual(sum(len(rows) for rows in left_rows.values()), 1)
        self.assertEqual(sum(len(rows) for rows in right_rows.values()), 1)
        self.assertEqual(len(left_rows[expected]), 1)
        self.assertEqual(len(right_rows[expected]), 1)
        self.assertEqual(left_rows[expected][0]["metadata"]["causal_family_schema"], CAUSAL_FAMILY_SCHEMA)
        self.assertEqual(right_rows[expected][0]["metadata"]["causal_family_sha256"], left.causal_family_sha256)
        self.assertEqual(left_rows[expected][0]["metadata"]["declared_family_split"], "train")
        self.assertEqual(right_rows[expected][0]["metadata"]["declared_family_split"], "holdout")

    def test_causal_family_excludes_downstream_declared_label(self):
        labels = ["BASELINE-family", "LESION-family", "ROLE_SWAP-family", "RESCUE-family"]
        observed = {evidence(label).causal_family_sha256 for label in labels}
        self.assertEqual(len(observed), 1)

    def test_changed_upstream_route_changes_causal_family_identity(self):
        changed = dict(CAUSAL)
        changed["route_decision_sha256"] = h("c")
        self.assertNotEqual(
            evidence("alias:A").causal_family_sha256,
            evidence("alias:A", causal=changed).causal_family_sha256,
        )

    def test_lower_level_family_label_mismatch_fails_closed(self):
        bound = evidence("declared:A")
        with self.assertRaisesRegex(
            AdmittedTrainingDatasetError,
            "LOWER_LEVEL_COMPILER_TRACE_FAMILY_MISMATCH",
        ):
            _annotate_rows(lower("train", "declared:B"), bound)


if __name__ == "__main__":
    unittest.main()
