#!/usr/bin/env python3
from __future__ import annotations

import unittest

import free_provider_admission as admission


class FreeProviderAdmission868Tests(unittest.TestCase):
    def test_canonical_868_admission_parses_with_openrouter_fail_closed(self):
        snapshot = admission.admission_snapshot()
        self.assertTrue(snapshot.get("ok"), snapshot)
        self.assertEqual(snapshot.get("authority_epoch"), "8.68")
        self.assertEqual(snapshot.get("admitted_free_providers"), [])
        self.assertIn("openrouter", snapshot.get("providers", {}))
        self.assertFalse(snapshot["providers"]["openrouter"]["admitted"])
        self.assertEqual(snapshot["providers"]["openrouter"]["cost_class"], "UNKNOWN")

    def test_openrouter_is_known_but_not_admitted_free(self):
        payload = admission.load_provider_admission()
        self.assertIn("openrouter", admission.ALLOWED_PROVIDERS)
        self.assertFalse(admission.provider_is_admitted_free("openrouter", payload))

    def test_unlisted_provider_remains_fail_closed(self):
        payload = admission.load_provider_admission()
        self.assertFalse(admission.provider_is_admitted_free("unlisted-provider", payload))


if __name__ == "__main__":
    unittest.main()
