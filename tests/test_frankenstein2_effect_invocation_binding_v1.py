import tempfile
from pathlib import Path
import unittest

from tools.frankenstein2_effect_invocation_binding_v1 import (
    EffectInvocationBindingError,
    reenter_bound_result,
    verify_bound_result_identity,
)
from tools.frankenstein2_effect_lifecycle_v1 import (
    AdmissionDecision,
    EffectLifecycleStore,
)


class EffectInvocationBindingTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.store = EffectLifecycleStore(Path(self.td.name) / "effects.sqlite")

    def tearDown(self):
        self.td.cleanup()

    def _prepare_same_digest_execution(self, invocation_id: str, *, task_id: str, turn_id: str, causal_id: str) -> None:
        req = self.store.build_request(
            invocation_id=invocation_id,
            session_id="shared-session",
            agent_id="agent-1",
            task_id=task_id,
            turn_id=turn_id,
            causal_id=causal_id,
            generation=23,
            tool_name="bounded-tool",
            normalized_arguments={"invocation": invocation_id},
            effect_scope="TEST_ONLY",
        )
        self.store.create_request(req)
        self.store.decide(invocation_id, AdmissionDecision.ALLOW, reason="test")
        self.store.record_enforcement(
            invocation_id,
            boundary_id=f"gate-{invocation_id}",
            dispatch_permitted=True,
        )
        self.store.bind_completion_source(invocation_id, source_digest=f"src-{invocation_id}")
        self.store.mark_submitted(invocation_id)
        self.store.record_execution(
            invocation_id,
            executable_id="tool-v1",
            command_digest=f"cmd-{invocation_id}",
            environment_id="sandbox",
            exit_code=0,
            result_digest="same-result-digest",
        )

    def test_same_session_same_digest_cross_invocation_reentry_is_rejected_before_store_mutation(self):
        self._prepare_same_digest_execution("call-A", task_id="task-A", turn_id="turn-A", causal_id="cause-A")
        self._prepare_same_digest_execution("call-B", task_id="task-B", turn_id="turn-B", causal_id="cause-B")

        # Digest-only validation cannot distinguish these calls because both results are equal.
        # The external tool-use id must therefore be checked independently of session/result data.
        with self.assertRaisesRegex(EffectInvocationBindingError, "RESULT_REENTRY_INVOCATION_MISMATCH"):
            reenter_bound_result(
                self.store,
                target_invocation_id="call-A",
                observed_invocation_id="call-B",
                result_digest="same-result-digest",
            )
        self.assertIsNone(self.store.snapshot("call-A")["reentry"])

        reenter_bound_result(
            self.store,
            target_invocation_id="call-B",
            observed_invocation_id="call-B",
            result_digest="same-result-digest",
        )
        reenter_bound_result(
            self.store,
            target_invocation_id="call-A",
            observed_invocation_id="call-A",
            result_digest="same-result-digest",
        )
        self.assertEqual(self.store.snapshot("call-A")["reentry"]["task_id"], "task-A")
        self.assertEqual(self.store.snapshot("call-B")["reentry"]["task_id"], "task-B")

    def test_missing_observed_call_identity_fails_closed(self):
        with self.assertRaisesRegex(EffectInvocationBindingError, "MISSING_OBSERVED_INVOCATION_ID"):
            verify_bound_result_identity(
                target_invocation_id="call-A",
                observed_invocation_id="",
                result_digest="digest",
            )


if __name__ == "__main__":
    unittest.main()
