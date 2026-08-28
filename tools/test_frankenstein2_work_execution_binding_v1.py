#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from frankenstein2_work_execution_binding_v1 import WorkExecutionLedger


class WorkExecutionBindingV1Tests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.db = Path(self.td.name) / "unified.sqlite"
        self.ledger = WorkExecutionLedger(self.db)

    def tearDown(self):
        self.td.cleanup()

    def bind(self, *, binding="b1", package="p1", generation="g1", child="child-1"):
        return self.ledger.bind_child(
            binding_id=binding,
            workpackage_id=package,
            work_generation=generation,
            child_runtime_kind="TEST_NATIVE_ADAPTER",
            child_execution_id=child,
            identity_provenance="TEST_OBSERVED_CHILD_START",
        )

    def success_path(self):
        self.bind()
        self.ledger.record_invocation(
            binding_id="b1",
            invocation_id="i1",
            invocation_kind="NATIVE_TASK",
            request={"task":"bounded scratch action"},
            native_tool_use_id="tool-1",
        )
        self.ledger.record_result(
            result_id="r1",
            binding_id="b1",
            invocation_id="i1",
            outcome="SUCCESS",
            result={"exit_code":0,"artifact_sha256":"abc"},
            result_provenance="TEST_PROCESS_RECEIPT",
        )

    def test_exact_success_lineage_can_complete_with_mechanistic_evidence(self):
        self.success_path()
        digest = self.ledger.verify_completion(
            completion_id="c1",
            binding_id="b1",
            invocation_id="i1",
            result_id="r1",
            expected_work_generation="g1",
            evidence_kind="PROCESS_EXIT_AND_OUTPUT_DIGEST",
            evidence_ref="receipt:test:1",
            evidence_payload={"exit_code":0,"stdout_digest":"def"},
        )
        snap = self.ledger.binding_snapshot("b1")
        self.assertEqual(snap["binding"]["status"], "COMPLETED")
        self.assertEqual(len(snap["invocations"]), 1)
        self.assertEqual(len(snap["results"]), 1)
        self.assertEqual(len(snap["completions"]), 1)
        self.assertEqual(snap["completions"][0]["evidence_digest"], digest)

    def test_durable_package_binding_without_invocation_cannot_complete(self):
        self.bind()
        with self.assertRaisesRegex(ValueError, "missing bound result"):
            self.ledger.verify_completion(
                completion_id="c1", binding_id="b1", invocation_id="i1", result_id="r1",
                expected_work_generation="g1",
                evidence_kind="DETERMINISTIC_TEST_RECEIPT",
                evidence_ref="receipt:test:missing",
                evidence_payload={"pass":True},
            )

    def test_result_cannot_attach_to_other_binding_or_invocation(self):
        self.bind(binding="b1", child="child-1")
        self.bind(binding="b2", child="child-2")
        self.ledger.record_invocation(
            binding_id="b1", invocation_id="i1", invocation_kind="NATIVE_TASK", request={"x":1}
        )
        with self.assertRaisesRegex(ValueError, "does not bind"):
            self.ledger.record_result(
                result_id="r1", binding_id="b2", invocation_id="i1", outcome="SUCCESS",
                result={"ok":True}, result_provenance="TEST",
            )

    def test_stale_generation_cannot_close_completion(self):
        self.success_path()
        with self.assertRaisesRegex(ValueError, "STALE_WORK_GENERATION"):
            self.ledger.verify_completion(
                completion_id="c1", binding_id="b1", invocation_id="i1", result_id="r1",
                expected_work_generation="g2",
                evidence_kind="DETERMINISTIC_TEST_RECEIPT",
                evidence_ref="receipt:test:stale",
                evidence_payload={"pass":True},
            )
        self.assertNotEqual(self.ledger.binding_snapshot("b1")["binding"]["status"], "COMPLETED")

    def test_unknown_outcome_remains_unknown_and_cannot_complete(self):
        self.bind()
        self.ledger.record_invocation(
            binding_id="b1", invocation_id="i1", invocation_kind="EXTERNAL_EFFECT", request={"op":"submit"}
        )
        self.ledger.record_result(
            result_id="r1", binding_id="b1", invocation_id="i1", outcome="UNKNOWN",
            result={"transport":"connection_lost_after_submit"}, result_provenance="TEST_TRANSPORT",
        )
        self.assertEqual(self.ledger.binding_snapshot("b1")["binding"]["status"], "UNKNOWN_OUTCOME")
        with self.assertRaisesRegex(ValueError, "completion forbidden"):
            self.ledger.verify_completion(
                completion_id="c1", binding_id="b1", invocation_id="i1", result_id="r1",
                expected_work_generation="g1",
                evidence_kind="DETERMINISTIC_TEST_RECEIPT",
                evidence_ref="receipt:test:unknown",
                evidence_payload={"text":"looks done"},
            )

    def test_textual_model_claim_is_not_completion_evidence(self):
        self.success_path()
        with self.assertRaisesRegex(ValueError, "mechanistic evidence"):
            self.ledger.verify_completion(
                completion_id="c1", binding_id="b1", invocation_id="i1", result_id="r1",
                expected_work_generation="g1",
                evidence_kind="MODEL_TEXT_CLAIM",
                evidence_ref="model:said-done",
                evidence_payload={"text":"done"},
            )

    def test_parallel_children_cannot_share_same_native_tool_identity_within_binding(self):
        self.bind()
        self.ledger.record_invocation(
            binding_id="b1", invocation_id="i1", invocation_kind="TOOL", request={"n":1}, native_tool_use_id="tool-x"
        )
        with self.assertRaises(Exception):
            self.ledger.record_invocation(
                binding_id="b1", invocation_id="i2", invocation_kind="TOOL", request={"n":2}, native_tool_use_id="tool-x"
            )

    def test_native_agent_and_task_ids_are_optional_until_observed_not_invented(self):
        binding = self.bind()
        self.assertIsNone(binding.native_agent_id)
        self.assertIsNone(binding.native_task_id)
        snap = self.ledger.binding_snapshot("b1")
        self.assertIsNone(snap["binding"]["native_agent_id"])
        self.assertIsNone(snap["binding"]["native_task_id"])


if __name__ == "__main__":
    unittest.main()
