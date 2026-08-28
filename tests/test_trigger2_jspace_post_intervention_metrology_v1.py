from __future__ import annotations

import unittest

import torch

from tools import trigger2_jspace_post_intervention_metrology_v1 as metrology


class TupleLayer(torch.nn.Module):
    def forward(self, x):
        return (x * 2, {"aux": True})


class Trigger2PostInterventionMetrologyTests(unittest.TestCase):
    def test_tensor_output_captures_exact_returned_post_tensor(self):
        layer = torch.nn.Identity()
        m = metrology.PostInterventionMetrology(lambda h: h + 1, require_change=True)
        handle = layer.register_forward_hook(m.hook)
        try:
            x = torch.tensor([[1.0, 2.0]])
            y = layer(x)
        finally:
            handle.remove()
        self.assertTrue(torch.equal(y, torch.tensor([[2.0, 3.0]])))
        receipt = m.receipt()
        self.assertEqual("PASS_COMPONENT_ONLY", receipt["status"])
        self.assertTrue(receipt["records"][0]["post_equals_returned"])
        self.assertTrue(receipt["records"][0]["changed"])

    def test_tuple_output_preserves_tail_and_replaces_first_tensor(self):
        layer = TupleLayer()
        m = metrology.PostInterventionMetrology(lambda h: h - 0.5, require_change=True)
        handle = layer.register_forward_hook(m.hook)
        try:
            y, aux = layer(torch.tensor([[2.0, 3.0]]))
        finally:
            handle.remove()
        self.assertTrue(torch.equal(y, torch.tensor([[3.5, 5.5]])))
        self.assertEqual({"aux": True}, aux)
        self.assertEqual("tuple_first_tensor", m.records[0].output_form)

    def test_require_change_fails_closed_on_noop(self):
        layer = torch.nn.Identity()
        m = metrology.PostInterventionMetrology(lambda h: h, require_change=True)
        handle = layer.register_forward_hook(m.hook)
        try:
            with self.assertRaisesRegex(metrology.MetrologyError, "INTERVENTION_EXPECTED_CHANGE"):
                layer(torch.ones(1, 2))
        finally:
            handle.remove()

    def test_shape_change_fails_closed(self):
        layer = torch.nn.Identity()
        m = metrology.PostInterventionMetrology(lambda h: h[..., :1])
        handle = layer.register_forward_hook(m.hook)
        try:
            with self.assertRaisesRegex(metrology.MetrologyError, "INTERVENTION_SHAPE_CHANGED"):
                layer(torch.ones(1, 2))
        finally:
            handle.remove()


if __name__ == "__main__":
    unittest.main()
