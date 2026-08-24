from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "trigger1-v2-local-fastpath-selfhosted.yml"


class Trigger1WorkflowGitSourceIdentityTests(unittest.TestCase):
    def test_pre_intervention_uses_canonical_git_source_identity_v1(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("tools/git_source_identity_v1.py --repo . --require-clean", text)
        self.assertIn("TRIGGER1_SOURCE_IDENTITY_SHA256", text)
        self.assertIn("TRIGGER1_DIRTY_STATE_SHA256", text)

    def test_runtime_receipt_separates_executed_checkout_from_dispatch_event(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("'head_sha':executed_head", text)
        self.assertIn("'executed_tree_sha':executed_tree", text)
        self.assertIn("'git_source_identity_sha256':source_identity_sha", text)
        self.assertIn("'dirty_state_sha256':dirty_state_sha", text)
        self.assertIn("'dispatch_event_sha':os.environ.get('GITHUB_SHA')", text)
        self.assertNotIn("'head_sha':os.environ.get('GITHUB_SHA')", text)

    def test_source_result_mismatch_fails_closed(self):
        text = WORKFLOW.read_text(encoding="utf-8")
        self.assertIn("EXECUTED_SOURCE_HEAD_MISMATCH", text)
        self.assertIn("EXECUTED_SOURCE_TREE_MISMATCH", text)
        self.assertIn("EXECUTED_SOURCE_IDENTITY_REQUIRED", text)


if __name__ == "__main__":
    unittest.main()
