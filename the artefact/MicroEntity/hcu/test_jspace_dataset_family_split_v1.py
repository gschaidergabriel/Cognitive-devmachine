import unittest
from copy import deepcopy

from jspace_dataset_admission_gate_v1 import ADMISSION_SCHEMA as GATE_ADMISSION_SCHEMA
from jspace_dataset_family_split_v1 import (
    DATASET_ADMISSION_SCHEMA,
    JSpaceDatasetFamilySplitError,
    partition_admitted_training_traces,
    split_for_family,
)


def h(n: int) -> str:
    return f"{n:064x}"


def training(trace_id: str, family_id: str, n: int) -> dict:
    return {
        "schema_version": "ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1",
        "trace_id": trace_id,
        "trace_family_id": family_id,
        "trace_sha256": h(1000 + n),
        "generation": 7,
        "entry_event_sha256": h(1),
        "entry_admission_sha256": h(2),
        "route_decision_sha256": h(3),
        "grid_plan_sha256": h(4),
        "cell_id": f"cell-{n:02d}",
        "role": "critic",
        "jspace_basis_id": "basis:7",
        "jspace_basis_sha256": h(5),
        "vector_control_packet_sha256": h(8),
        "vector_control_condition": "baseline",
        "credit_label": "UNKNOWN",
        "outcome_receipt_sha256": None,
    }


def admission(trace: dict) -> dict:
    return {
        "schema": GATE_ADMISSION_SCHEMA,
        "training_trace_sha256": trace["trace_sha256"],
        "transition_trace_sha256": h(6),
        "prototype_trace_sha256": h(7),
        "generation": trace["generation"],
        "entry_event_sha256": trace["entry_event_sha256"],
        "entry_admission_sha256": trace["entry_admission_sha256"],
        "route_decision_sha256": trace["route_decision_sha256"],
        "grid_plan_sha256": trace["grid_plan_sha256"],
        "cell_id": trace["cell_id"],
        "role": trace["role"],
        "jspace_basis_id": trace["jspace_basis_id"],
        "jspace_basis_sha256": trace["jspace_basis_sha256"],
        "vector_control_packet_sha256": trace["vector_control_packet_sha256"],
        "vector_control_condition": trace["vector_control_condition"],
        "credit_label": trace["credit_label"],
        "outcome_receipt_sha256": trace["outcome_receipt_sha256"],
    }


class FamilySplitTests(unittest.TestCase):
    def partition(self, traces):
        registry = {trace["trace_sha256"]: deepcopy(trace) for trace in traces}
        records = [(trace, admission(trace)) for trace in traces]
        return partition_admitted_training_traces(records, admitted_training_traces=registry)

    def test_selected_admission_schema_is_gate_authority_and_legacy_v1_rejected(self):
        self.assertEqual(DATASET_ADMISSION_SCHEMA, GATE_ADMISSION_SCHEMA)
        trace = training("trace:a", "episode:A", 1)
        registry = {trace["trace_sha256"]: deepcopy(trace)}
        stale = admission(trace)
        stale["schema"] = "ENTITYOS_HCU_JSPACE_DATASET_ADMISSION/v1"
        with self.assertRaisesRegex(JSpaceDatasetFamilySplitError, "DATASET_ADMISSION_SCHEMA_UNSUPPORTED"):
            partition_admitted_training_traces([(trace, stale)], admitted_training_traces=registry)

    def test_correlated_family_never_crosses_train_validation_holdout(self):
        traces = []
        for family_n in range(80):
            family = f"episode:{family_n}"
            traces.append(training(f"trace:{family_n}:baseline", family, family_n * 2 + 1))
            traces.append(training(f"trace:{family_n}:lesion", family, family_n * 2 + 2))
        result = self.partition(traces)
        owners = {}
        for split, rows in result["splits"].items():
            for row in rows:
                owners.setdefault(row["trace_family_id"], set()).add(split)
        self.assertTrue(owners)
        self.assertTrue(all(len(splits) == 1 for splits in owners.values()))
        self.assertEqual(result["family_count"], 80)
        self.assertEqual(result["trace_count"], 160)

    def test_split_is_deterministic_and_domain_bound_to_family(self):
        self.assertEqual(split_for_family("episode:alpha"), split_for_family("episode:alpha"))
        observed = {split_for_family(f"episode:{n}") for n in range(200)}
        self.assertEqual(observed, {"train", "validation", "holdout"})

    def test_family_relabel_after_admission_fails_exact_registry_rebind(self):
        original = training("trace:a", "episode:A", 1)
        registry = {original["trace_sha256"]: deepcopy(original)}
        relabelled = deepcopy(original)
        relabelled["trace_family_id"] = "episode:B"
        with self.assertRaisesRegex(JSpaceDatasetFamilySplitError, "TRAINING_TRACE_REGISTRY_MISMATCH"):
            partition_admitted_training_traces(
                [(relabelled, admission(relabelled))],
                admitted_training_traces=registry,
            )

    def test_trace_id_collision_with_different_trace_identity_fails_closed(self):
        a = training("trace:same", "episode:A", 1)
        b = training("trace:same", "episode:A", 2)
        registry = {a["trace_sha256"]: deepcopy(a), b["trace_sha256"]: deepcopy(b)}
        with self.assertRaisesRegex(JSpaceDatasetFamilySplitError, "TRACE_ID_COLLISION"):
            partition_admitted_training_traces(
                [(a, admission(a)), (b, admission(b))],
                admitted_training_traces=registry,
            )

    def test_admission_causal_transplant_fails_closed(self):
        trace = training("trace:a", "episode:A", 1)
        registry = {trace["trace_sha256"]: deepcopy(trace)}
        forged = admission(trace)
        forged["grid_plan_sha256"] = h(99)
        with self.assertRaisesRegex(
            JSpaceDatasetFamilySplitError,
            "TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:grid_plan_sha256",
        ):
            partition_admitted_training_traces(
                [(trace, forged)],
                admitted_training_traces=registry,
            )

    def test_v2_vector_control_packet_transplant_fails_closed(self):
        trace = training("trace:a", "episode:A", 1)
        registry = {trace["trace_sha256"]: deepcopy(trace)}
        forged = admission(trace)
        forged["vector_control_packet_sha256"] = h(99)
        with self.assertRaisesRegex(
            JSpaceDatasetFamilySplitError,
            "TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:vector_control_packet_sha256",
        ):
            partition_admitted_training_traces([(trace, forged)], admitted_training_traces=registry)

    def test_v2_vector_control_condition_transplant_fails_closed(self):
        trace = training("trace:a", "episode:A", 1)
        registry = {trace["trace_sha256"]: deepcopy(trace)}
        forged = admission(trace)
        forged["vector_control_condition"] = "lesion"
        with self.assertRaisesRegex(
            JSpaceDatasetFamilySplitError,
            "TRAINING_TRACE_ADMISSION_BINDING_MISMATCH:vector_control_condition",
        ):
            partition_admitted_training_traces([(trace, forged)], admitted_training_traces=registry)

    def test_duplicate_identical_trace_is_idempotent(self):
        trace = training("trace:a", "episode:A", 1)
        registry = {trace["trace_sha256"]: deepcopy(trace)}
        pair = (trace, admission(trace))
        result = partition_admitted_training_traces(
            [pair, pair],
            admitted_training_traces=registry,
        )
        self.assertEqual(result["trace_count"], 1)
        self.assertEqual(result["family_count"], 1)


if __name__ == "__main__":
    unittest.main()
