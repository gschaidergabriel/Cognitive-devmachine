import json
import unittest

from compile_jspace_training_dataset_v1 import (
    TrainingDatasetError,
    compile_traces,
    derive_training_examples,
)
from global_jspace_gwt_v1 import CellContribution, step
from jspace_training_trace_v1 import build_training_trace, trace_dict


BASIS_SHA256 = "1" * 64


class CausalTrainingDatasetCompilerTests(unittest.TestCase):
    def training_trace(self, *, trace_id="trace:1", family="episode:A", generation=7, salt="2"):
        cells = [
            CellContribution("world.0", "world", (0.8, 0.1, -0.2), 0.8, 0.1, 0.2, 0.2, 0.1),
            CellContribution("critic.0", "critic", (-0.3, 0.9, 0.4), 0.2, 0.95, 0.7, 0.1, 0.1),
        ]
        proto = step(
            cells,
            generation=generation,
            basis_id="basis:training",
            basis_sha256=BASIS_SHA256,
        )
        trace = build_training_trace(
            proto,
            proto.control_packet,
            trace_id=trace_id,
            trace_family_id=family,
            entry_event_sha256=salt * 64,
            entry_admission_sha256="3" * 64,
            route_decision_sha256="4" * 64,
            grid_plan_sha256="5" * 64,
            jspace_input_vector_ref="unifieddb:jspace-input:1",
            local_workspace_state_ref="unifieddb:workspace:1",
            global_jspace_slice_ref="unifieddb:jspace-slice:1",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        return trace_dict(trace)

    def test_training_trace_derives_machine_checkable_causal_and_control_rows(self):
        rows = derive_training_examples(self.training_trace())
        self.assertEqual(len(rows), 8)
        families = [row["metadata"]["family"] for row in rows]
        self.assertEqual(families.count("VECTOR_CONTROL_VALIDATE"), 4)
        self.assertIn("GWT_BROADCAST_FROM_CAUSAL_TRACE", families)
        self.assertEqual(families.count("CAUSAL_TRACE_BINDING_VALIDATE"), 3)
        assistant_payloads = [json.loads(row["messages"][2]["content"]) for row in rows]
        self.assertIn({"decision": "REJECT", "reason": "STALE_VECTOR_CONTROL_GENERATION"}, assistant_payloads)
        self.assertIn({"decision": "REJECT", "reason": "ENTRY_EVENT_MISMATCH"}, assistant_payloads)
        self.assertIn({"decision": "REJECT", "reason": "ROUTE_DECISION_MISMATCH"}, assistant_payloads)

    def test_same_trace_family_never_leaks_across_splits(self):
        traces = [
            self.training_trace(trace_id="trace:A1", family="episode:A", generation=7, salt="2"),
            self.training_trace(trace_id="trace:A2", family="episode:A", generation=8, salt="6"),
            self.training_trace(trace_id="trace:B1", family="episode:B", generation=9, salt="7"),
        ]
        compiled = compile_traces(traces)
        owners = {}
        for split, rows in compiled.items():
            for row in rows:
                family = row["metadata"]["trace_family_id"]
                owners.setdefault(family, set()).add(split)
        self.assertEqual(owners["episode:A"].__len__(), 1)
        self.assertTrue(all(len(splits) == 1 for splits in owners.values()))

    def test_duplicate_training_trace_is_deduplicated(self):
        trace = self.training_trace()
        compiled = compile_traces([trace, trace])
        self.assertEqual(sum(len(rows) for rows in compiled.values()), 8)

    def test_raw_prototype_trace_is_not_silently_promoted(self):
        cells = [CellContribution("a", "world", (0.1, 0.2), 0.1, 0.1, 0.1, 0.1, 0.1)]
        raw = step(cells, generation=1, basis_id="basis:raw", basis_sha256=BASIS_SHA256).trace
        with self.assertRaisesRegex(TrainingDatasetError, "TRACE_SCHEMA_UNSUPPORTED"):
            compile_traces([raw])

    def test_tampered_causal_identity_fails_trace_digest_before_compilation(self):
        trace = self.training_trace()
        trace["route_decision_sha256"] = "8" * 64
        with self.assertRaisesRegex(TrainingDatasetError, "TRAINING_TRACE_DIGEST_MISMATCH"):
            compile_traces([trace])

    def test_tampered_vector_packet_identity_fails_closed(self):
        trace = self.training_trace()
        trace["vector_control_packet_sha256"] = "9" * 64
        material = dict(trace)
        material.pop("trace_sha256")
        from entry_canonicalization_v1 import canonicalize
        import hashlib
        trace["trace_sha256"] = hashlib.sha256(canonicalize(material)).hexdigest()
        with self.assertRaisesRegex(TrainingDatasetError, "TRACE_VECTOR_CONTROL_PACKET_IDENTITY_MISMATCH"):
            compile_traces([trace])


if __name__ == "__main__":
    unittest.main()
