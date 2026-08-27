#!/usr/bin/env python3
from __future__ import annotations

import builtins
import json
import os
import unittest
from unittest.mock import patch

import describe_campaign_offline_v1 as offline


class OfflineCampaignTests(unittest.TestCase):
    def _report(self, secret: str | None) -> dict:
        original_import = builtins.__import__

        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "together" or name.startswith("together."):
                raise AssertionError("offline campaign path attempted to import Together")
            return original_import(name, globals, locals, fromlist, level)

        env = {} if secret is None else {"TOGETHER_API_KEY": secret}
        with patch.object(offline.launch, "run_local_checks", lambda: None), \
             patch.object(offline.launch, "TEMPLATE", None), \
             patch.dict(os.environ, env, clear=False), \
             patch("builtins.__import__", side_effect=guarded_import):
            if secret is None:
                os.environ.pop("TOGETHER_API_KEY", None)
            return offline.build_report(False)

    def test_poisoned_provider_secret_cannot_change_offline_campaign_identity(self) -> None:
        baseline = self._report(None)
        poisoned = self._report("SENTINEL_PROVIDER_SECRET_DO_NOT_READ")
        self.assertEqual(baseline, poisoned)
        rendered = json.dumps(poisoned, sort_keys=True)
        self.assertNotIn("SENTINEL_PROVIDER_SECRET_DO_NOT_READ", rendered)
        self.assertFalse(poisoned["provider_network"])
        self.assertFalse(poisoned["provider_secret_required"])
        self.assertFalse(poisoned["training_started"])


if __name__ == "__main__":
    unittest.main()
