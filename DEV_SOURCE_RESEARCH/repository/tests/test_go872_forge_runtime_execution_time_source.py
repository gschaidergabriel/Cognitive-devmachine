from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/go871-forge-distillery-runtime-gate.yml"


class Go872ForgeRuntimeExecutionTimeSource(unittest.TestCase):
    def setUp(self) -> None:
        self.text = WORKFLOW.read_text(encoding="utf-8")

    def test_checkout_resolves_main_when_runner_starts(self):
        self.assertIn("ref: main", self.text)
        self.assertIn('SOURCE_SHA="$(git rev-parse HEAD)"', self.text)
        self.assertIn('SOURCE_TREE="$(git rev-parse \'HEAD^{tree}\')"', self.text)
        self.assertIn('test -z "$DIRTY"', self.text)

    def test_gate_uses_bound_execution_source_not_trigger_base(self):
        self.assertIn("SOURCE_SHA: ${{ steps.source.outputs.source_sha }}", self.text)
        self.assertNotIn("SOURCE_SHA: ${{ github.event.pull_request.base.sha || github.sha }}", self.text)

    def test_pr_runtime_result_is_repository_bound(self):
        self.assertIn("- name: Publish sanitized runtime result to main", self.text)
        self.assertNotIn("if: always() && github.event_name != 'pull_request'", self.text)
        self.assertIn("source_selection:'CANONICAL_MAIN_AT_RUNNER_CHECKOUT_TIME'", self.text)
        self.assertIn("branch: 'main'", self.text)


if __name__ == "__main__":
    unittest.main()
