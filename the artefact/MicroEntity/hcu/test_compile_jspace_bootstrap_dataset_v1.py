import hashlib
import unittest

from compile_jspace_bootstrap_dataset_v1 import DatasetError, compile_traces, derive_bootstrap_examples
from global_jspace_gwt_v1 import CellContribution, step
from jspace_training_trace_v1 import build_training_trace, trace_dict


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


class CompilerTests(unittest.TestCase):
    def trace(self, gen=1, *, family=None, trace_id=None):
        cells = [
            CellContribution("a", "world", (0.8, 0.1), 0.8, 0.1, 0.2, 0.1, 0.1),
            CellContribution("b", "critic", (-0.4, 0.8), 0.2, 0.9, 0.7, 0.1, 0.1),
        ]
        basis_id = f"B{gen}"
        proto = step(
            cells,
            generation=gen,
            basis_id=basis_id,
            basis_sha256=digest(f"basis:{basis_id}"),
        )
        training = build_training_trace(
            proto,
            proto.control_packet,
            trace_id=trace_id or f"trace:{gen}",
            trace_family_id=family or f"episode:{gen}",
            entry_event_sha256=digest(f"entry-event:{gen}"),
            entry_admission_sha256=digest(f"entry-admission:{gen}"),
            route_decision_sha256=digest(f"route:{gen}"),
            grid_plan_sha256=digest(f"grid:{gen}"),
            jspace_input_vector_ref=f"unifieddb:jspace-input:{gen}",
            local_workspace_state_ref=f"unifieddb:workspace:{gen}",
            global_jspace_slice_ref=f"unifieddb:jspace-slice:{gen}",
            hyperposition_branch_ids=("branch:a", "branch:b"),
            provenance_evidence_class="EXACT_PROTOTYPE_TRACE",
            resource_budget={"max_model_calls": 1, "max_tokens": 256, "max_wall_ms": 1000},
            requested_action_class="CANDIDATE_INFERENCE",
            expected_structured_model_output="schema://hcu/candidate-output/v1",
            observed_downstream_outcome="UNKNOWN_NOT_YET_VERIFIED",
            falsifier_lesion_condition="BASELINE",
            credit_label="UNKNOWN",
        )
        return trace_dict(training)

    def test_each_trace_derives_six_machine_checkable_rows(self):
        rows = derive_bootstrap_examples(self.trace())
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["metadata"]["family"], "VECTOR_CONTROL_VALIDATE")
        self.assertIn('"decision":"REJECT"', rows[1]["messages"][2]["content"])
        self.assertIn("STALE_VECTOR_CONTROL_GENERATION", rows[1]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_ID_MISMATCH", rows[2]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_SHA256_MISMATCH", rows[3]["messages"][2]["content"])
        self.assertIn("JSPACE_ROLE_MISMATCH", rows[4]["messages"][2]["content"])
        self.assertEqual(rows[5]["metadata"]["family"], "GWT_BROADCAST_FROM_TRAINING_TRACE")

    def test_trace_family_never_leaks_across_splits(self):
        traces = [self.trace(i) for i in range(1, 40)]
        traces.extend([
            self.trace(40, family="episode:shared", trace_id="trace:shared:a"),
            self.trace(41, family="episode:shared", trace_id="trace:shared:b"),
        ])
        compiled = compile_traces(traces)
        family_owners = {}
        trace_owners = {}
        for split, rows in compiled.items():
            for row in rows:
                family_owners.setdefault(row["metadata"]["trace_family_id"], set()).add(split)
                trace_owners.setdefault(row["metadata"]["trace_sha256"], set()).add(split)
        self.assertTrue(all(len(v) == 1 for v in family_owners.values()))
        self.assertTrue(all(len(v) == 1 for v in trace_owners.values()))
        self.assertEqual(len(family_owners["episode:shared"]), 1)

    def test_duplicate_trace_is_deduplicated(self):
        trace = self.trace(5)
        compiled = compile_traces([trace, trace])
        self.assertEqual(sum(len(rows) for rows in compiled.values()), 6)

    def test_compiler_rejects_training_trace_digest_tamper(self):
        trace = dict(self.trace(7))
        trace["role"] = "tampered"
        with self.assertRaisesRegex(DatasetError, "TRAINING_TRACE_DIGEST_MISMATCH"):
            compile_traces([trace])

    def test_compiler_rejects_vector_basis_digest_substitution_even_after_rehash(self):
        trace = dict(self.trace(8))
        trace["jspace_basis_sha256"] = digest("wrong-basis")
        material = dict(trace)
        material.pop("trace_sha256")
        from entry_canonicalization_v1 import canonicalize
        trace["trace_sha256"] = hashlib.sha256(canonicalize(material)).hexdigest()
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_INVALID:JSPACE_BASIS_SHA256_MISMATCH"):
            compile_traces([trace])


if __name__ == "__main__":
    unittest.main()
