import importlib.util
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MOD_PATH = ROOT / "tools" / "durable_work_cursor_v1.py"
spec = importlib.util.spec_from_file_location("dwc", MOD_PATH)
dwc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dwc)


def cursor():
    return dwc.new_cursor(
        "run-1",
        "deep research",
        "g1",
        [
            {"node_id": "A", "status": "PENDING"},
            {"node_id": "B", "status": "PENDING"},
            {"node_id": "C", "status": "PENDING"},
        ],
        source_generation="s1",
    )


class DurableWorkCursorTests(unittest.TestCase):
    def test_completed_nodes_survive_and_resume_at_first_incomplete(self):
        c = cursor()
        c = dwc.transition(c, "A", "COMPLETED", evidence_refs=["e:A"])
        c = dwc.transition(c, "B", "COMPLETED", evidence_refs=["e:B"])
        plan = dwc.reentry_plan(c, "g1")
        self.assertEqual(plan["classification"], dwc.REENTER_RESUME)
        self.assertEqual(plan["next_node_id"], "C")
        self.assertEqual(plan["completed_node_ids"], ["A", "B"])

    def test_unconfirmed_node_requires_external_verification_before_retry(self):
        c = cursor()
        c = dwc.transition(c, "A", "RUNNING_UNCONFIRMED", external_identity="workflow:123")
        plan = dwc.reentry_plan(c, "g1")
        self.assertEqual(plan["classification"], dwc.REENTER_VERIFY)
        self.assertEqual(plan["verify_node_ids"], ["A"])
        self.assertEqual(c["nodes"][0]["attempts"], 1)

    def test_completed_requires_evidence(self):
        with self.assertRaisesRegex(ValueError, "evidence"):
            dwc.transition(cursor(), "A", "COMPLETED")

    def test_completed_cannot_be_blindly_retried(self):
        c = dwc.transition(cursor(), "A", "COMPLETED", evidence_refs=["e:A"])
        with self.assertRaisesRegex(ValueError, "illegal transition"):
            dwc.transition(c, "A", "RUNNING_UNCONFIRMED")

    def test_authority_change_preserves_completed_work_but_requires_reresolution(self):
        c = dwc.transition(cursor(), "A", "COMPLETED", evidence_refs=["e:A"])
        plan = dwc.reentry_plan(c, "g2")
        self.assertFalse(plan["authority_current"])
        self.assertTrue(plan["requires_execution_surface_reresolution"])
        self.assertIn("A", plan["completed_node_ids"])
        self.assertEqual(plan["next_node_id"], "B")

    def test_retryable_failure_remains_resumable(self):
        c = dwc.transition(cursor(), "A", "FAILED_RETRYABLE", next_discriminator="retry route")
        plan = dwc.reentry_plan(c, "g1")
        self.assertEqual(plan["classification"], dwc.REENTER_RESUME)
        self.assertEqual(plan["next_node_id"], "A")

    def test_parallel_success_is_not_erased_by_sibling_failure(self):
        c = cursor()
        c = dwc.transition(c, "A", "COMPLETED", evidence_refs=["e:A"])
        c = dwc.transition(c, "B", "FAILED_RETRYABLE", next_discriminator="repair")
        plan = dwc.reentry_plan(c, "g1")
        self.assertIn("A", plan["completed_node_ids"])
        self.assertEqual(plan["next_node_id"], "B")

    def test_terminal_run_when_every_node_is_terminal(self):
        c = cursor()
        c = dwc.transition(c, "A", "COMPLETED", evidence_refs=["e:A"])
        c = dwc.transition(c, "B", "COMPLETED", evidence_refs=["e:B"])
        c = dwc.transition(c, "C", "FAILED_TERMINAL")
        plan = dwc.reentry_plan(c, "g1")
        self.assertEqual(plan["classification"], dwc.REENTER_DONE)
        self.assertIsNone(plan["next_node_id"])


if __name__ == "__main__":
    unittest.main()
