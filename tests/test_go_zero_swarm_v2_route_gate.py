from __future__ import annotations

import importlib
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

mod = importlib.import_module("run_go_zero_swarm_v2")


class RouteBoundGoZeroTests(unittest.TestCase):
    def setUp(self) -> None:
        self.spec = SimpleNamespace(
            name="openrouter",
            endpoint="https://openrouter.ai/api/v1/chat/completions",
        )

    def test_unbound_lane_never_reaches_original_network_boundary(self) -> None:
        calls = {"network": 0}

        def network(*args, **kwargs):
            calls["network"] += 1
            raise AssertionError("network boundary must not be called")

        with patch.object(mod, "_evidence", return_value={"ok": False, "reason": "NO_ZERO_COST_BINDING"}), \
             patch.object(mod, "_ORIGINAL_REQUEST", side_effect=network):
            status, headers, payload = mod.gated_request_chat(
                self.spec, "secret-key", "paid/model", "prompt", 20, 1.0
            )

        self.assertEqual(status, 460)
        self.assertEqual(headers, {})
        self.assertEqual(payload["error"], "FREE_LANE_ECONOMIC_PROVENANCE_REQUIRED")
        self.assertEqual(calls["network"], 0)

    def test_bound_lane_calls_provider_once_and_emits_receipt(self) -> None:
        calls = {"network": 0, "receipt": 0}
        evidence = {"ok": True, "kind": "EXACT_ROUTE_ZERO_PRICE"}

        def network(*args, **kwargs):
            calls["network"] += 1
            return 200, {"x-request-id": "req-1"}, {
                "id": "req-1",
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5},
            }

        def receipt(**kwargs):
            calls["receipt"] += 1
            self.assertEqual(kwargs["provider"], "openrouter")
            self.assertEqual(kwargs["model_or_route"], "openrouter/free")
            self.assertEqual(kwargs["evidence"], evidence)
            self.assertEqual(kwargs["http_status"], 200)
            self.assertEqual(kwargs["request_id"], "req-1")
            return kwargs

        with patch.object(mod, "_evidence", return_value=evidence), \
             patch.object(mod, "_ORIGINAL_REQUEST", side_effect=network), \
             patch.object(mod, "emit_execution_receipt", side_effect=receipt):
            status, _, _ = mod.gated_request_chat(
                self.spec, "secret-key", "openrouter/free", "prompt", 20, 1.0
            )

        self.assertEqual(status, 200)
        self.assertEqual(calls, {"network": 1, "receipt": 1})

    def test_scheduler_skips_unbound_pairs_before_reservation(self) -> None:
        runtime = SimpleNamespace(
            keys=["k1", "k2"],
            models=["bad", "openrouter/free"],
            spec=self.spec,
        )
        pairs = iter([("k1", "bad"), ("k2", "openrouter/free")])

        def original_next(_runtime):
            try:
                return next(pairs)
            except StopIteration:
                return None

        def evidence(_spec, key, model):
            return {"ok": key == "k2" and model == "openrouter/free"}

        with patch.object(mod, "_ORIGINAL_NEXT_PAIR", side_effect=original_next), \
             patch.object(mod, "_evidence", side_effect=evidence):
            selected = mod.gated_next_key_model(runtime)

        self.assertEqual(selected, ("k2", "openrouter/free"))


if __name__ == "__main__":
    unittest.main()
