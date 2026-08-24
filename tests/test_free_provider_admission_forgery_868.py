#!/usr/bin/env python3
from __future__ import annotations

import unittest
from unittest import mock

import tools.free_provider_admission as admission


class FreeProviderAdmissionForgery868Tests(unittest.TestCase):
    def test_caller_forged_free_payload_cannot_self_grant(self) -> None:
        canonical_blocked = {
            "providers": {
                "groq": {"admitted": False, "cost_class": "UNKNOWN"},
            },
        }
        caller_forged = {
            "providers": {
                "groq": {"admitted": True, "cost_class": "FREE"},
            },
        }
        with mock.patch.object(admission, "load_provider_admission", return_value=canonical_blocked) as loader:
            self.assertFalse(admission.provider_is_admitted_free("groq", caller_forged))
        loader.assert_called_once_with()

    def test_admitted_provider_names_ignores_caller_forged_payload(self) -> None:
        canonical_blocked = {
            "providers": {
                name: {"admitted": False, "cost_class": "UNKNOWN"}
                for name in admission.ALLOWED_PROVIDERS
            },
        }
        caller_forged = {
            "providers": {
                name: {"admitted": True, "cost_class": "FREE"}
                for name in admission.ALLOWED_PROVIDERS
            },
        }
        with mock.patch.object(admission, "load_provider_admission", return_value=canonical_blocked) as loader:
            self.assertEqual(admission.admitted_provider_names(caller_forged), ())
        loader.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
