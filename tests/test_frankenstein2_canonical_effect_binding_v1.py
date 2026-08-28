import sqlite3
import tempfile
from pathlib import Path
import unittest

from tools.frankenstein2_canonical_effect_binding_v1 import (
    CanonicalEffectBindingError,
    CanonicalEffectBindingStore,
)
from tools.frankenstein2_effect_lifecycle_v1 import EffectLifecycleStore


class CanonicalEffectBindingTests(unittest.TestCase):
    AUTHORITY = "ENTITYOS_EFFECT_AUTHORITY_IMPLEMENTATION_BINDING/v2-admitted"

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "effects.sqlite"
        self.lifecycle = EffectLifecycleStore(self.path)
        self.bindings = CanonicalEffectBindingStore(self.path)

    def tearDown(self):
        self.td.cleanup()

    def _request(self, invocation_id: str) -> None:
        req = self.lifecycle.build_request(
            invocation_id=invocation_id,
            session_id="shared-session",
            agent_id="agent-1",
            task_id=f"task-{invocation_id}",
            turn_id=f"turn-{invocation_id}",
            causal_id=f"cause-{invocation_id}",
            generation=23,
            tool_name="bounded-tool",
            normalized_arguments={"same": "shape"},
            effect_scope="TEST_ONLY",
        )
        self.lifecycle.create_request(req)

    def test_overlapping_calls_bind_bijectively_and_crosswire_fails_closed(self):
        self._request("call-A")
        self._request("call-B")

        a = self.bindings.bind(
            "call-A",
            canonical_effect_id="effect-A",
            authority_ref=self.AUTHORITY,
        )
        b = self.bindings.bind(
            "call-B",
            canonical_effect_id="effect-B",
            authority_ref=self.AUTHORITY,
        )
        self.assertEqual((a.invocation_id, a.canonical_effect_id), ("call-A", "effect-A"))
        self.assertEqual((b.invocation_id, b.canonical_effect_id), ("call-B", "effect-B"))

        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "OBSERVED_INVOCATION_ID_MISMATCH"
        ):
            self.bindings.verify_observed_binding(
                target_invocation_id="call-A",
                observed_invocation_id="call-B",
                observed_effect_id="effect-A",
                authority_ref=self.AUTHORITY,
            )

        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "CANONICAL_EFFECT_ID_MISMATCH"
        ):
            self.bindings.verify_observed_binding(
                target_invocation_id="call-A",
                observed_invocation_id="call-A",
                observed_effect_id="effect-B",
                authority_ref=self.AUTHORITY,
            )

        resolved = self.bindings.verify_observed_binding(
            target_invocation_id="call-A",
            observed_invocation_id="call-A",
            observed_effect_id="effect-A",
            authority_ref=self.AUTHORITY,
        )
        self.assertEqual(resolved.canonical_effect_id, "effect-A")

    def test_create_once_binding_rejects_rebind_and_effect_id_reuse(self):
        self._request("call-A")
        self._request("call-B")
        first = self.bindings.bind(
            "call-A",
            canonical_effect_id="effect-A",
            authority_ref=self.AUTHORITY,
        )
        duplicate = self.bindings.bind(
            "call-A",
            canonical_effect_id="effect-A",
            authority_ref=self.AUTHORITY,
        )
        self.assertEqual(first, duplicate)

        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "INVOCATION_CANONICAL_EFFECT_REBIND_DENIED"
        ):
            self.bindings.bind(
                "call-A",
                canonical_effect_id="effect-B",
                authority_ref=self.AUTHORITY,
            )

        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "CANONICAL_EFFECT_ID_ALREADY_BOUND"
        ):
            self.bindings.bind(
                "call-B",
                canonical_effect_id="effect-A",
                authority_ref=self.AUTHORITY,
            )

        con = sqlite3.connect(self.path)
        try:
            self.assertEqual(
                con.execute("SELECT COUNT(*) FROM canonical_effect_bindings").fetchone()[0],
                1,
            )
        finally:
            con.close()

    def test_authority_ref_is_part_of_binding_and_cannot_be_swapped(self):
        self._request("call-A")
        self.bindings.bind(
            "call-A",
            canonical_effect_id="effect-A",
            authority_ref=self.AUTHORITY,
        )
        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "CANONICAL_EFFECT_AUTHORITY_MISMATCH"
        ):
            self.bindings.verify_observed_binding(
                target_invocation_id="call-A",
                observed_invocation_id="call-A",
                observed_effect_id="effect-A",
                authority_ref="stale-or-other-authority",
            )

    def test_unknown_invocation_cannot_mint_binding(self):
        with self.assertRaisesRegex(
            CanonicalEffectBindingError, "UNKNOWN_INVOCATION_ID"
        ):
            self.bindings.bind(
                "call-missing",
                canonical_effect_id="effect-X",
                authority_ref=self.AUTHORITY,
            )


if __name__ == "__main__":
    unittest.main()
