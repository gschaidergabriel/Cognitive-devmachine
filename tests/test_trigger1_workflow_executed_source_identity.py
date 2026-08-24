from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "trigger1-v2-local-fastpath-selfhosted.yml"


class Trigger1WorkflowExecutedSourceIdentityTests(unittest.TestCase):
    def test_runtime_receipt_binds_executed_checkout_not_dispatch_sha(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('SOURCE_HEAD="$(git rev-parse HEAD)"', text)
        self.assertIn('SOURCE_TREE="$(git rev-parse \'HEAD^{tree}\')"', text)
        self.assertIn("'head_sha':os.environ['TRIGGER1_SOURCE_HEAD']", text)
        self.assertIn("'executed_tree_sha':os.environ['TRIGGER1_SOURCE_TREE']", text)
        self.assertIn("'dispatch_event_sha':os.environ.get('GITHUB_SHA')", text)
        self.assertNotIn("'head_sha':os.environ.get('GITHUB_SHA')", text)

    def test_receipt_fails_closed_on_source_result_mismatch(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("EXECUTED_SOURCE_HEAD_MISMATCH", text)
        self.assertIn("EXECUTED_SOURCE_TREE_MISMATCH", text)
        self.assertIn("EXECUTED_SOURCE_DIRTY_BEFORE_INTERVENTION", text)


if __name__ == "__main__":
    unittest.main()
