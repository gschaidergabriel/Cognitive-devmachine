import importlib.util
import sys
import unittest
from pathlib import Path


PATH = Path(__file__).parents[1] / "research_entity/runtime/free_api_provider_runtime.py"
SPEC = importlib.util.spec_from_file_location("free_api_provider_runtime", PATH)
MOD = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MOD
SPEC.loader.exec_module(MOD)


class FreeApiProviderRuntimeTests(unittest.TestCase):
    def test_nvidia_is_preferred_and_secret_is_not_exposed(self):
        env = {"NVIDIA_API_KEY": "do-not-leak", "GROQ_API_KEY": "also-secret"}
        rows = MOD.inventory(env)
        self.assertEqual(MOD.route(env)["selected"], "nvidia")
        self.assertNotIn("do-not-leak", repr(rows))
        self.assertTrue(all(row["secret_exposed"] is False for row in rows))

    def test_together_is_hard_denied_even_if_key_exists(self):
        env = {"TOGETHER_API_KEY": "must-not-be-touched"}
        self.assertIn("together", MOD.DENIED_PROVIDERS)
        self.assertTrue(all(row["provider_id"] != "together" for row in MOD.inventory(env)))
        self.assertIsNone(MOD.route(env)["selected"])

    def test_no_key_means_no_route(self):
        self.assertIsNone(MOD.route({})["selected"])
        self.assertTrue(MOD.route({})["zero_cost_only"])


if __name__ == "__main__":
    unittest.main()
