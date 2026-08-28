#!/usr/bin/env python3
from __future__ import annotations

import inspect
from pathlib import Path
import sys
import unittest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from trigger1_local_qwen06_intermediate_execute import RuntimeState, _wrong_layer_request


class WrongLayerSelectedVectorBindingTests(unittest.TestCase):
    def test_wrong_layer_request_separates_intervention_and_vector_source_layers(self) -> None:
        payload = _wrong_layer_request(
            prompt="holdout",
            selected_layer=12,
            wrong_layer=6,
            gain=4.0,
            seed=2718,
            positive_label="A",
            negative_label="B",
        )
        self.assertEqual(payload["layer"], 6)
        self.assertEqual(payload["vector_layer"], 12)
        self.assertEqual(payload["control"], "+VECTOR")
        self.assertEqual(payload["positive_label"], "A")
        self.assertEqual(payload["negative_label"], "B")

    def test_wrong_layer_request_rejects_selected_layer_reuse(self) -> None:
        with self.assertRaisesRegex(ValueError, "WRONG_LAYER_MUST_DIFFER_FROM_SELECTED_LAYER"):
            _wrong_layer_request(
                prompt="holdout",
                selected_layer=12,
                wrong_layer=12,
                gain=4.0,
                seed=2718,
                positive_label="A",
                negative_label="B",
            )

    def test_runtime_uses_vector_source_layer_not_intervention_layer_for_direction(self) -> None:
        source = inspect.getsource(RuntimeState.infer)
        self.assertIn('vector_layer = int(payload.get("vector_layer", layer))', source)
        self.assertIn('direction = self.directions[vector_layer]', source)
        self.assertIn('"vector_layer": vector_layer', source)
        self.assertNotIn('direction = self.directions[layer]', source)


if __name__ == "__main__":
    unittest.main()
