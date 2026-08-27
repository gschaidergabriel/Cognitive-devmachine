#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/run_trigger1_jspace_10x.py"
SHELL_PATH = ROOT / "tools/trigger1_jspace_research.sh"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_jspace_10x", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Trigger1ContractTests(unittest.TestCase):
    def test_exactly_ten_distinct_dynamic_work_slots(self):
        mod = load_module()
        self.assertEqual(10, len(mod.EXPERIMENTS))
        names = [name for name, _ in mod.EXPERIMENTS]
        self.assertEqual(10, len(set(names)))
        self.assertIn("local_runtime_repair", names)
        self.assertIn("holdout_reproduction", names)
        self.assertIn("blocker_killer_and_forge", names)

    def test_parent_secret_scrub_is_provider_scoped(self):
        mod = load_module()
        keys = {
            "GROQ_API_KEY": "secret-a",
            "NVIDIA_NIM_API_KEY": "secret-b",
            "OPENROUTER_API_KEY_2": "secret-c",
            "TOGETHER_API_KEY": "secret-d",
            "CLAY_TRIGGER1_SAFE_MARKER": "keep-me",
        }
        old = {k: os.environ.get(k) for k in keys}
        try:
            os.environ.update(keys)
            mod.scrub_parent_provider_secrets()
            for k in keys:
                if k == "CLAY_TRIGGER1_SAFE_MARKER":
                    self.assertEqual("keep-me", os.environ.get(k))
                else:
                    self.assertNotIn(k, os.environ)
        finally:
            for k, value in old.items():
                if value is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = value

    def test_vault_is_child_side_not_shell_parent(self):
        py = MODULE_PATH.read_text(encoding="utf-8")
        sh = SHELL_PATH.read_text(encoding="utf-8")
        self.assertIn('sys.executable, str(VAULT_EXEC)', py)
        self.assertIn('sys.executable, str(LANE_EXEC)', py)
        self.assertIn('"orchestrator_credential_scope": "BLIND"', py)
        self.assertIn('"provider_lane_credential_scope": "SWARM_CHILD_ONLY/v1"', py)
        self.assertIn('exec python3 tools/run_trigger1_jspace_10x.py "$@"', sh)
        self.assertNotIn('exec python3 tools/free_swarm_exec_with_vault.py \\\n  python3 tools/run_trigger1_jspace_10x.py', sh)

    def test_primary_fastpath_is_strong_intermediate_causal_path(self):
        sh = SHELL_PATH.read_text(encoding="utf-8")
        self.assertIn('bash "$ROOT/tools/trigger1_local_qwen06_midlayer_causal.sh" "$LOCAL_DIR"', sh)
        self.assertNotIn('bash "$ROOT/tools/trigger1_local_qwen06_activation_api.sh" "$LOCAL_DIR"', sh)
        self.assertIn('trigger1_jspace_promotion_gate.py', sh)
        self.assertIn("owner_trigger1_goal_credit_candidate", sh)

    def test_no_together_experiment_lane(self):
        mod = load_module()
        joined = "\n".join(f"{name} {focus}" for name, focus in mod.EXPERIMENTS).lower()
        self.assertNotIn("together", joined)


if __name__ == "__main__":
    unittest.main()
