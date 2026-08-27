from __future__ import annotations

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import run_xeno_active_build_swarm as xeno


class XenoFreeLaneBinding870Tests(unittest.TestCase):
    def test_exact_v3_request_and_reservation_gates_are_bound(self) -> None:
        self.assertIs(xeno.fabric.base.request_chat, xeno.economic.gated_request_chat)
        self.assertIs(
            xeno.fabric.FastProviderRuntime.next_key_model,
            xeno.economic.gated_next_key_model,
        )
        xeno._require_free_lane_binding()

    def test_request_gate_drift_fails_closed(self) -> None:
        original = xeno.fabric.base.request_chat
        try:
            xeno.fabric.base.request_chat = lambda *args, **kwargs: (599, {}, {})
            with self.assertRaisesRegex(RuntimeError, "XENO_FREE_LANE_REQUEST_GATE_DRIFT"):
                xeno._require_free_lane_binding()
        finally:
            xeno.fabric.base.request_chat = original
        xeno._require_free_lane_binding()

    def test_reservation_gate_drift_fails_closed(self) -> None:
        original = xeno.fabric.FastProviderRuntime.next_key_model
        try:
            xeno.fabric.FastProviderRuntime.next_key_model = lambda self: None
            with self.assertRaisesRegex(RuntimeError, "XENO_FREE_LANE_RESERVATION_GATE_DRIFT"):
                xeno._require_free_lane_binding()
        finally:
            xeno.fabric.FastProviderRuntime.next_key_model = original
        xeno._require_free_lane_binding()


if __name__ == "__main__":
    unittest.main()
