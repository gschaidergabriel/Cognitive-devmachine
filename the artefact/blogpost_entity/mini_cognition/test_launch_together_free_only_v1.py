#!/usr/bin/env python3
import importlib.util
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
spec = importlib.util.spec_from_file_location("launch08_free_only", HERE / "launch_together_qwen35_08b_v1.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ProbeEnv(dict):
    def __init__(self, values=None):
        super().__init__(values or {})
        self.lookups = []

    def get(self, key, default=None):
        self.lookups.append(key)
        if key == "TOGETHER_API_KEY":
            raise AssertionError("TOGETHER_API_KEY_LOOKUP_FORBIDDEN_BEFORE_ADMISSION")
        return super().get(key, default)


class Tests(unittest.TestCase):
    def _run_main_until_provider_gate(self, env):
        old_env = os.environ
        old_argv = sys.argv
        old_local_checks = m.local_checks
        local_checks_called = []
        try:
            os.environ = env
            sys.argv = [str(m.__file__)]
            m.local_checks = lambda: local_checks_called.append(True)
            with self.assertRaises(SystemExit) as cm:
                m.main()
            return str(cm.exception), local_checks_called
        finally:
            m.local_checks = old_local_checks
            sys.argv = old_argv
            os.environ = old_env

    def test_free_only_launcher_blocks_before_local_checks_secret_and_together_import(self):
        sys.modules.pop("together", None)
        env = ProbeEnv({
            "CLAY_EXECUTION_MODE": "FREE_ONLY",
            "TOGETHER_API_KEY": "poison",
        })
        error, local_checks_called = self._run_main_until_provider_gate(env)
        self.assertIn("FREE_ONLY_PROVIDER_BLOCK", error)
        self.assertEqual(local_checks_called, [])
        self.assertNotIn("TOGETHER_API_KEY", env.lookups)
        self.assertNotIn("together", sys.modules)

    def test_unknown_mode_launcher_fails_closed_before_local_checks_and_secret(self):
        env = ProbeEnv({
            "CLAY_EXECUTION_MODE": "UNKNOWN",
            "TOGETHER_API_KEY": "poison",
        })
        error, local_checks_called = self._run_main_until_provider_gate(env)
        self.assertIn("PROVIDER_MODE_REJECTED", error)
        self.assertEqual(local_checks_called, [])
        self.assertNotIn("TOGETHER_API_KEY", env.lookups)


if __name__ == "__main__":
    unittest.main()
