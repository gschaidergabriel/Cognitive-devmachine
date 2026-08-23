import hashlib
import unittest

from tools.mini_cognitive_invocation_selector_v1 import (
    InvocationSelectorFault,
    OneShotInvocationSelector,
    validate_selector,
    verify_resolved_binding,
)


class MiniCognitiveInvocationSelectorV1Tests(unittest.TestCase):
    def setUp(self):
        self.task = "bound task text"
        self.turn_digest = hashlib.sha256(b"turn-binding").hexdigest()
        self.selector = {
            "schema": "MINI_COGNITIVE_INVOCATION/v1",
            "expected_generation": 7,
            "causal_turn_id": "turn-7-a",
            "task_text": self.task,
            "turn_binding_digest": self.turn_digest,
        }
        self.resolved = {
            "ok": True,
            "entity_generation": 7,
            "causal_turn_id": "turn-7-a",
            "turn_binding_digest": self.turn_digest,
            "task_sha256": hashlib.sha256(self.task.encode("utf-8")).hexdigest(),
            "authority": {
                "durable_state": "MiniUnifiedDB",
                "candidate_only": True,
                "direct_truth_authority": False,
                "direct_effect_authority": False,
            },
        }

    def test_exact_selector_and_resolved_binding_cross_bind(self):
        selected = validate_selector(self.selector)
        self.assertEqual(selected, self.selector)
        verified = verify_resolved_binding(selected, self.resolved)
        self.assertTrue(verified["ok"])
        self.assertEqual(verified["authority"], "ROUTING_ONLY")

    def test_caller_cannot_smuggle_cognition_identity(self):
        poisoned = dict(self.selector)
        poisoned["zero_identity_digest"] = hashlib.sha256(b"caller-zero").hexdigest()
        with self.assertRaisesRegex(InvocationSelectorFault, "SELECTOR_FIELD_SET_MISMATCH"):
            validate_selector(poisoned)

    def test_bool_generation_is_not_integer_authority(self):
        poisoned = dict(self.selector)
        poisoned["expected_generation"] = True
        with self.assertRaisesRegex(InvocationSelectorFault, "EXPECTED_GENERATION_INVALID"):
            validate_selector(poisoned)

    def test_task_text_mutation_fails_cross_binding(self):
        poisoned = dict(self.selector)
        poisoned["task_text"] = self.task + " mutated"
        with self.assertRaisesRegex(InvocationSelectorFault, "RESOLVED_TASK_BINDING_MISMATCH"):
            verify_resolved_binding(poisoned, self.resolved)

    def test_turn_digest_mutation_fails_cross_binding(self):
        poisoned = dict(self.selector)
        poisoned["turn_binding_digest"] = hashlib.sha256(b"other-turn").hexdigest()
        with self.assertRaisesRegex(InvocationSelectorFault, "RESOLVED_TURN_BINDING_DIGEST_MISMATCH"):
            verify_resolved_binding(poisoned, self.resolved)

    def test_resolved_authority_cannot_be_promoted_by_selector(self):
        poisoned = dict(self.resolved)
        poisoned["authority"] = dict(poisoned["authority"])
        poisoned["authority"]["direct_truth_authority"] = True
        with self.assertRaisesRegex(InvocationSelectorFault, "RESOLVED_AUTHORITY_CONTRACT_MISMATCH"):
            verify_resolved_binding(self.selector, poisoned)

    def test_one_shot_selector_replay_fails_closed(self):
        slot = OneShotInvocationSelector(self.selector)
        self.assertEqual(slot.take(), self.selector)
        with self.assertRaisesRegex(InvocationSelectorFault, "INVOCATION_SELECTOR_ALREADY_CONSUMED"):
            slot.take()


if __name__ == "__main__":
    unittest.main()
