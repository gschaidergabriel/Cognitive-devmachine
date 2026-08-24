from __future__ import annotations

import copy
import sys
from pathlib import Path
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import free_provider_admission as admission
import free_provider_admission_binding as binding


def _payload() -> dict:
    return {
        "schema": admission.SCHEMA,
        "authority_epoch": "8.68",
        "mode": "FREE_ONLY",
        "product": "EntityOS",
        "compute_architecture": "HCU",
        "source": "ENTITYOS_HCU_CONTROL_PLANE",
        "providers": {
            name: {
                "admitted": False,
                "cost_class": "UNKNOWN",
                "evidence_ref": f"test:{name}:unknown",
            }
            for name in admission.ALLOWED_PROVIDERS
        },
    }


class FreeProviderAdmissionBinding868Tests(unittest.TestCase):
    def test_semantic_digest_is_object_key_order_invariant(self) -> None:
        payload = _payload()
        reordered = dict(reversed(list(payload.items())))
        self.assertEqual(
            binding._validated_semantic_sha256(payload),
            binding._validated_semantic_sha256(reordered),
        )

    def test_same_epoch_policy_mutation_changes_digest(self) -> None:
        payload = _payload()
        before = binding._validated_semantic_sha256(payload)
        changed = copy.deepcopy(payload)
        changed["providers"]["groq"]["admitted"] = True
        changed["providers"]["groq"]["cost_class"] = "FREE"
        self.assertNotEqual(before, binding._validated_semantic_sha256(changed))

    def test_live_revalidation_accepts_unchanged_binding(self) -> None:
        payload = _payload()
        with mock.patch.object(admission, "load_provider_admission", return_value=payload) as loader:
            current = binding.current_provider_admission_binding()
            self.assertEqual(binding.require_current_provider_admission_binding(current), current)
        self.assertEqual(loader.call_count, 2)

    def test_live_revalidation_rejects_same_epoch_mutation(self) -> None:
        payload = _payload()
        changed = copy.deepcopy(payload)
        changed["providers"]["groq"]["evidence_ref"] = "test:groq:new-evidence"
        with mock.patch.object(admission, "load_provider_admission", return_value=payload):
            current = binding.current_provider_admission_binding()
        with mock.patch.object(admission, "load_provider_admission", return_value=changed):
            with self.assertRaisesRegex(admission.ProviderAdmissionError, "DIGEST_CHANGED"):
                binding.require_current_provider_admission_binding(current)

    def test_expected_binding_cannot_self_grant_or_override_current_authority(self) -> None:
        payload = _payload()
        with mock.patch.object(admission, "load_provider_admission", return_value=payload):
            forged = binding.current_provider_admission_binding()
            forged["admission_sha256"] = "0" * 64
            with self.assertRaisesRegex(admission.ProviderAdmissionError, "DIGEST_CHANGED"):
                binding.require_current_provider_admission_binding(forged)


if __name__ == "__main__":
    unittest.main()
