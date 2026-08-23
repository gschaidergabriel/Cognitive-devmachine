import hashlib
import unittest

from global_jspace_gwt_v1 import CellContribution, step
from compile_jspace_bootstrap_dataset_v1 import (
    DatasetError,
    compile_traces,
    derive_bootstrap_examples,
)


class CompilerTests(unittest.TestCase):
    def trace(self, gen=1):
        cells = [
            CellContribution("a", "world", (0.8, 0.1), 0.8, 0.1, 0.2, 0.1, 0.1),
            CellContribution("b", "critic", (-0.4, 0.8), 0.2, 0.9, 0.7, 0.1, 0.1),
        ]
        basis_id = f"B{gen}"
        basis_sha256 = hashlib.sha256(basis_id.encode("utf-8")).hexdigest()
        return step(
            cells,
            generation=gen,
            basis_id=basis_id,
            basis_sha256=basis_sha256,
        ).trace

    def test_each_trace_derives_four_machine_checkable_rows(self):
        rows = derive_bootstrap_examples(self.trace())
        self.assertEqual(len(rows), 4)
        self.assertEqual(rows[0]["metadata"]["family"], "VECTOR_CONTROL_VALIDATE")
        self.assertIn('"decision":"REJECT"', rows[1]["messages"][2]["content"])
        self.assertIn("STALE_VECTOR_CONTROL_GENERATION", rows[1]["messages"][2]["content"])
        self.assertIn("JSPACE_BASIS_ID_MISMATCH", rows[2]["messages"][2]["content"])
        self.assertEqual(rows[3]["metadata"]["family"], "GWT_BROADCAST_FROM_TRACE")

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

    def test_packet_text_transport_drift_fails_closed(self):
        trace = self.trace(7)
        trace["control_packet_text"] = trace["control_packet_text"] + " "
        with self.assertRaisesRegex(DatasetError, "TRACE_CONTROL_PACKET_INVALID"):
            derive_bootstrap_examples(trace)


if __name__ == "__main__":
    unittest.main()
