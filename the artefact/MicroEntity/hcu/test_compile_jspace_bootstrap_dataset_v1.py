import unittest

from global_jspace_gwt_v1 import CellContribution, step
from compile_jspace_bootstrap_dataset_v1 import DatasetError, compile_traces, derive_bootstrap_examples


class CompilerTests(unittest.TestCase):
    def trace(self, gen=1):
        cells = [
            CellContribution("a", "world", (0.8, 0.1), 0.8, 0.1, 0.2, 0.1, 0.1),
            CellContribution("b", "critic", (-0.4, 0.8), 0.2, 0.9, 0.7, 0.1, 0.1),
        ]
        return step(cells, generation=gen, basis_id=f"B{gen}", basis_sha256=f"{gen:064x}").trace

    def test_each_trace_derives_four_machine_checkable_rows(self):
        trace = self.trace()
        self.assertIn("control_packet_text", trace)
        self.assertIn("control_packet_identity_sha256", trace)
        self.assertEqual(trace["control_packet_sha256"], trace["control_packet_wire_sha256"])
        rows = derive_bootstrap_examples(trace)
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["metadata"]["family"], "VECTOR_CONTROL_VALIDATE")
        self.assertIn('"decision":"REJECT"', rows[1]["messages"][2]["content"])
        self.assertIn("STALE_VECTOR_CONTROL_GENERATION", rows[1]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_ID_MISMATCH", rows[2]["messages"][2]["content"])
        self.assertEqual(rows[3]["metadata"]["family"], "GWT_BROADCAST_FROM_TRACE")
        self.assertIn(trace["basis_sha256"], rows[0]["messages"][1]["content"])

    def test_trace_family_never_leaks_across_splits(self):
        traces = [self.trace(i) for i in range(1, 40)]
        compiled = compile_traces(traces)
        owners = {}
        for split, rows in compiled.items():
            for row in rows:
                sha = row["metadata"]["trace_sha256"]
                owners.setdefault(sha, set()).add(split)
        self.assertTrue(all(len(v) == 1 for v in owners.values()))
        self.assertEqual(sum(len(v) for v in owners.values()), len(traces))

    def test_duplicate_trace_is_deduplicated(self):
        trace = self.trace(5)
        compiled = compile_traces([trace, trace])
        self.assertEqual(sum(len(rows) for rows in compiled.values()), 4)

    def test_basis_digest_cannot_be_relabelled_around_packet(self):
        trace = dict(self.trace(7))
        trace["basis_sha256"] = "b" * 64
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_BASIS_SHA256_MISMATCH"):
            derive_bootstrap_examples(trace)

    def test_wire_digest_alias_cannot_hide_packet_substitution(self):
        trace = dict(self.trace(9))
        trace["control_packet_wire_sha256"] = "c" * 64
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_WIRE_SHA256_MISMATCH"):
            derive_bootstrap_examples(trace)

    def test_control_condition_cannot_be_relabelled_around_packet(self):
        trace = dict(self.trace(11))
        trace["control_condition"] = "LESION"
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_CONDITION_MISMATCH"):
            derive_bootstrap_examples(trace)

    def test_packet_identity_digest_is_bound_independently_of_wire_digest(self):
        trace = dict(self.trace(12))
        trace["control_packet_identity_sha256"] = "d" * 64
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_IDENTITY_MISMATCH"):
            derive_bootstrap_examples(trace)


if __name__ == "__main__":
    unittest.main()
