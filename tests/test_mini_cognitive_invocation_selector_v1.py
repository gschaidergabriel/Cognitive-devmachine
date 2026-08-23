from __future__ import annotations

import hashlib
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import mini_cognitive_invocation_selector_v1 as selector


def digest(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def valid_selector() -> dict:
    return {
        "expected_generation": 7,
        "causal_turn_id": "turn-7",
        "task_text": "inspect exact bounded task",
        "turn_binding_digest": digest("turn-binding"),
    }


def resolved() -> dict:
    return {
        "ok": True,
        "schema": "MINIUNIFIEDDB_COGNITION_STORE/v1",
        "entity_generation": 7,
        "causal_turn_id": "turn-7",
        "turn_binding_digest": digest("turn-binding"),
        "boot_binding_digest": digest("boot-binding"),
        "task_sha256": digest("task"),
        "workspace_digest": digest("workspace"),
        "selected_workspace_slots": ["slot:a"],
        "contradiction_state": "NONE",
        "turn_provenance_refs": ["test:turn"],
        "required_zero_mode": "COGNITIVE",
    }


class MiniCognitiveInvocationSelectorTests(unittest.TestCase):
    def test_exact_selector_resolves_only_through_miniunifieddb(self) -> None:
        with patch.object(selector.cognition_store, "resolve_prepare_binding", return_value=resolved()) as resolver:
            result = selector.resolve_selector(object(), valid_selector())
        resolver.assert_called_once_with(
            unittest.mock.ANY,
            entity_generation=7,
            causal_turn_id="turn-7",
            task_text="inspect exact bounded task",
        )
        self.assertEqual(result["invocation_selector_schema"], selector.SCHEMA)
        self.assertEqual(result["invocation_selector_authority"], "NONE_ROUTING_ONLY")

    def test_extra_cognition_authority_field_fails_before_store_lookup(self) -> None:
        poisoned = valid_selector()
        poisoned["zero_identity_digest"] = digest("caller-zero")
        with patch.object(selector.cognition_store, "resolve_prepare_binding") as resolver:
            with self.assertRaisesRegex(selector.InvocationSelectorError, "INVOCATION_SELECTOR_UNKNOWN_FIELDS"):
                selector.resolve_selector(object(), poisoned)
        resolver.assert_not_called()

    def test_store_generation_or_task_rejection_is_preserved(self) -> None:
        with patch.object(
            selector.cognition_store,
            "resolve_prepare_binding",
            side_effect=selector.cognition_store.CognitionStoreError("STALE_GENERATION"),
        ):
            with self.assertRaisesRegex(selector.InvocationSelectorError, "STALE_GENERATION"):
                selector.resolve_selector(object(), valid_selector())

    def test_turn_binding_digest_mismatch_fails_closed(self) -> None:
        wrong = resolved()
        wrong["turn_binding_digest"] = digest("other-turn")
        with patch.object(selector.cognition_store, "resolve_prepare_binding", return_value=wrong):
            with self.assertRaisesRegex(selector.InvocationSelectorError, "TURN_BINDING_DIGEST_MISMATCH"):
                selector.resolve_selector(object(), valid_selector())

    def test_bool_generation_is_not_integer_generation(self) -> None:
        bad = valid_selector()
        bad["expected_generation"] = True
        with patch.object(selector.cognition_store, "resolve_prepare_binding") as resolver:
            with self.assertRaisesRegex(selector.InvocationSelectorError, "EXPECTED_GENERATION_INVALID"):
                selector.resolve_selector(object(), bad)
        resolver.assert_not_called()


if __name__ == "__main__":
    unittest.main()
