import hashlib
import unittest

from compile_jspace_bootstrap_dataset_v1 import DatasetError, compile_traces, derive_bootstrap_examples
from global_jspace_gwt_v1 import CellContribution, step
from jspace_dataset_family_split_v1 import causal_family_id_from_event
from jspace_training_trace_v1 import build_training_trace, trace_dict


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def admitted_for(*traces):
    return {trace["jspace_basis_id"]: trace["jspace_basis_sha256"] for trace in traces}


class CompilerTests(unittest.TestCase):
    def trace(self, gen=1, *, family=None, trace_id=None, event_label=None):
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
        event_label = event_label or f"entry-event:{gen}"
        training = build_training_trace(
            proto,
            proto.control_packet,
            trace_id=trace_id or f"trace:{gen}",
            trace_family_id=family or f"episode:{gen}",
            entry_event_sha256=digest(event_label),
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
        trace = self.trace()
        rows = derive_bootstrap_examples(trace, admitted_bases=admitted_for(trace))
        self.assertEqual(len(rows), 6)
        self.assertEqual(rows[0]["metadata"]["family"], "VECTOR_CONTROL_VALIDATE")
        self.assertEqual(
            rows[0]["metadata"]["causal_family_id"],
            causal_family_id_from_event(trace["entry_event_sha256"]),
        )
        self.assertIn('"decision":"REJECT"', rows[1]["messages"][2]["content"])
        self.assertIn("STALE_VECTOR_CONTROL_GENERATION", rows[1]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_ID_MISMATCH", rows[2]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_SHA256_MISMATCH", rows[3]["messages"][2]["content"])
        self.assertIn("JSPACE_ROLE_MISMATCH", rows[4]["messages"][2]["content"])
        self.assertEqual(rows[5]["metadata"]["family"], "GWT_BROADCAST_FROM_TRAINING_TRACE")

    def test_same_causal_event_different_labels_never_leaks_across_splits(self):
        traces = [self.trace(i) for i in range(1, 40)]
        traces.extend([
            self.trace(
                40,
                family="caller-alias:A",
                trace_id="trace:shared:a",
                event_label="shared-causal-event",
            ),
            self.trace(
                41,
                family="caller-alias:B",
                trace_id="trace:shared:b",
                event_label="shared-causal-event",
            ),
        ])
        compiled = compile_traces(traces, admitted_bases=admitted_for(*traces))
        causal_owners = {}
        trace_owners = {}
        alias_owners = {}
        for split, rows in compiled.items():
            for row in rows:
                metadata = row["metadata"]
                causal_owners.setdefault(metadata["causal_family_id"], set()).add(split)
                trace_owners.setdefault(metadata["trace_sha256"], set()).add(split)
                alias_owners.setdefault(metadata["trace_family_id"], set()).add(split)
        self.assertTrue(all(len(v) == 1 for v in causal_owners.values()))
        self.assertTrue(all(len(v) == 1 for v in trace_owners.values()))
        shared_causal = causal_family_id_from_event(digest("shared-causal-event"))
        self.assertEqual(len(causal_owners[shared_causal]), 1)
        self.assertEqual(alias_owners["caller-alias:A"], alias_owners["caller-alias:B"])

    def test_compiler_reuses_selected_family_split_authority(self):
        import compile_jspace_bootstrap_dataset_v1 as compiler
        import jspace_dataset_family_split_v1 as family_split

        self.assertIs(compiler.split_for_family, family_split.split_for_family)
        self.assertIs(compiler.causal_family_id_from_event, family_split.causal_family_id_from_event)
        self.assertEqual(compiler.FAMILY_SPLIT_SCHEMA, family_split.SPLIT_SCHEMA)
        self.assertEqual(compiler.split_for_family("family:1"), family_split.split_for_family("family:1"))
        families = [f"family:{index}" for index in range(256)]
        families.extend(("family:A", "family:B", "unicode:Δ", "nested/a:b"))
        for family_id in families:
            with self.subTest(family_id=family_id):
                self.assertEqual(
                    compiler.split_for_family(family_id),
                    family_split.split_for_family(family_id),
                )

    def test_duplicate_trace_is_deduplicated(self):
        trace = self.trace(5)
        compiled = compile_traces([trace, trace], admitted_bases=admitted_for(trace))
        self.assertEqual(sum(len(rows) for rows in compiled.values()), 6)

    def test_compiler_rejects_training_trace_digest_tamper(self):
        trace = dict(self.trace(7))
        admission = admitted_for(trace)
        trace["role"] = "tampered"
        with self.assertRaisesRegex(DatasetError, "TRAINING_TRACE_DIGEST_MISMATCH"):
            compile_traces([trace], admitted_bases=admission)

    def test_compiler_rejects_vector_basis_digest_substitution_even_after_rehash(self):
        trace = dict(self.trace(8))
        trace["jspace_basis_sha256"] = digest("wrong-basis")
        material = dict(trace)
        material.pop("trace_sha256")
        from entry_canonicalization_v1 import canonicalize
        trace["trace_sha256"] = hashlib.sha256(canonicalize(material)).hexdigest()
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_INVALID:JSPACE_BASIS_SHA256_MISMATCH"):
            compile_traces([trace], admitted_bases=admitted_for(trace))

    def test_missing_external_basis_admission_fails_closed(self):
        trace = self.trace(13)
        with self.assertRaisesRegex(DatasetError, "JSPACE_BASIS_ADMISSION_REQUIRED"):
            compile_traces([trace])

    def test_self_consistent_rogue_basis_cannot_self_admit(self):
        rogue = self.trace(14)
        trusted = {"basis:trusted": digest("basis:trusted")}
        with self.assertRaisesRegex(DatasetError, "JSPACE_BASIS_NOT_ADMITTED"):
            compile_traces([rogue], admitted_bases=trusted)

    def test_basis_id_cannot_rebind_to_unadmitted_digest(self):
        trace = self.trace(15)
        wrong_registry = {trace["jspace_basis_id"]: digest("different-admitted-basis")}
        with self.assertRaisesRegex(DatasetError, "JSPACE_BASIS_ADMISSION_DIGEST_MISMATCH"):
            compile_traces([trace], admitted_bases=wrong_registry)


if __name__ == "__main__":
    unittest.main()
