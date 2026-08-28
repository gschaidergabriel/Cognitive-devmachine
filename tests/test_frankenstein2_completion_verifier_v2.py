from dataclasses import replace
import unittest

from tools.frankenstein2_completion_verifier_v2 import (
    ADMISSION_SCHEMA,
    ENFORCEMENT_SCHEMA,
    EXECUTION_SCHEMA,
    REENTRY_SCHEMA,
    TEST_SCHEMA,
    WORLD_SCHEMA,
    AdmissionReceipt,
    EnforcementReceipt,
    ExecutionReceipt,
    ExpectedInvocation,
    ResultReentryReceipt,
    TestReceipt,
    WorldVerificationReceipt,
    verify_completion,
)


class CompletionVerifierV2Tests(unittest.TestCase):
    def setUp(self):
        self.expected = ExpectedInvocation(
            invocation_id="call-A",
            request_digest="req-A",
            task_id="task-1",
            turn_id="turn-1",
            causal_id="cause-1",
            generation=7,
            source_digest="src-abc",
        )
        self.admission = AdmissionReceipt(ADMISSION_SCHEMA, "call-A", "req-A", 7, "ALLOW")
        self.enforcement = EnforcementReceipt(
            ENFORCEMENT_SCHEMA, "call-A", "req-A", 7, "ALLOW", True, "boundary-1"
        )
        self.execution = ExecutionReceipt(
            EXECUTION_SCHEMA, "call-A", "req-A", 7, "src-abc", "tool-v1",
            "sandbox-1", "SUCCEEDED", 0, "result-A", "UNIQUE"
        )
        self.world = WorldVerificationReceipt(
            WORLD_SCHEMA, "call-A", 7, "result-A", "SUCCEEDED", "world-proof-A"
        )
        self.reentry = ResultReentryReceipt(
            REENTRY_SCHEMA, "call-A", 7, "result-A", "task-1", "turn-1", "cause-1"
        )
        self.test_receipt = TestReceipt(
            TEST_SCHEMA, "call-A", 7, "src-abc", "PASS", 4, 4, "tests-A"
        )

    def decide(self, **overrides):
        values = dict(
            expected=self.expected,
            admission=self.admission,
            enforcement=self.enforcement,
            execution=self.execution,
            world=self.world,
            reentry=self.reentry,
            test_receipt=self.test_receipt,
            require_test_receipt=True,
        )
        values.update(overrides)
        return verify_completion(**values)

    def assertBlocked(self, decision, reason_prefix):
        self.assertFalse(decision.closable)
        self.assertIsNone(decision.validation_digest)
        self.assertTrue(
            any(r.startswith(reason_prefix) for r in decision.reasons),
            f"missing {reason_prefix} in {decision.reasons}",
        )

    def test_bound_success_allowlist_closes(self):
        d = self.decide()
        self.assertTrue(d.closable)
        self.assertEqual(d.reasons, ())
        self.assertTrue(d.validation_digest)

    def test_denied_failed_unchecked_unknown_rejected(self):
        self.assertBlocked(self.decide(admission=replace(self.admission, decision="DENY")), "ADMISSION_NOT_SUCCESS")
        self.assertBlocked(self.decide(execution=replace(self.execution, status="FAILED")), "EXECUTION_NOT_SUCCESS")
        self.assertBlocked(self.decide(execution=replace(self.execution, status="UNCHECKED")), "EXECUTION_NOT_SUCCESS")
        self.assertBlocked(self.decide(world=replace(self.world, outcome="UNKNOWN")), "WORLD_NOT_SUCCESS")

    def test_unbound_textual_test_lookalike_rejected_by_schema(self):
        self.assertBlocked(
            self.decide(test_receipt=replace(self.test_receipt, schema="test:0:looks-good")),
            "TEST_SCHEMA_MISMATCH",
        )

    def test_test_zero_rejected_even_when_status_pass(self):
        self.assertBlocked(
            self.decide(test_receipt=replace(self.test_receipt, assertions_total=0, assertions_passed=0)),
            "TEST_ZERO_OR_NEGATIVE_ASSERTIONS",
        )

    def test_source_drift_rejected(self):
        self.assertBlocked(self.decide(execution=replace(self.execution, source_digest="src-other")), "EXECUTION_SOURCE_DRIFT")

    def test_test_source_drift_rejected(self):
        self.assertBlocked(self.decide(test_receipt=replace(self.test_receipt, source_digest="src-other")), "TEST_SOURCE_DRIFT")

    def test_invocation_transplant_rejected(self):
        self.assertBlocked(self.decide(execution=replace(self.execution, invocation_id="call-B")), "EXECUTION_INVOCATION_MISMATCH")

    def test_stale_generation_rejected(self):
        self.assertBlocked(self.decide(world=replace(self.world, generation=6)), "WORLD_GENERATION_MISMATCH")

    def test_result_transplant_rejected(self):
        self.assertBlocked(self.decide(reentry=replace(self.reentry, result_digest="result-B")), "REENTRY_RESULT_MISMATCH")

    def test_unresolved_duplicate_rejected(self):
        self.assertBlocked(
            self.decide(execution=replace(self.execution, duplicate_state="UNRESOLVED_DUPLICATE")),
            "EXECUTION_DUPLICATE_UNRESOLVED",
        )

    def test_missing_execution_provenance_rejected(self):
        self.assertBlocked(self.decide(execution=replace(self.execution, environment_id="")), "MISSING_EXECUTION_PROVENANCE")

    def test_missing_world_evidence_rejected(self):
        self.assertBlocked(self.decide(world=replace(self.world, evidence_digest=None)), "MISSING_WORLD_EVIDENCE")

    def test_reentry_lineage_transplant_rejected(self):
        self.assertBlocked(self.decide(reentry=replace(self.reentry, task_id="task-other")), "REENTRY_CAUSAL_LINEAGE_MISMATCH")

    def test_missing_required_test_receipt_rejected(self):
        self.assertBlocked(self.decide(test_receipt=None), "MISSING_REQUIRED_TEST_RECEIPT")


if __name__ == "__main__":
    unittest.main()
