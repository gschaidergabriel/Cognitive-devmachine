#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "tools/trigger1_openrouter_closed_loop_jspace.py"


def load_module():
    spec = importlib.util.spec_from_file_location("trigger1_openrouter_closed_loop_jspace", MODULE_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClosedLoopJSpaceTests(unittest.TestCase):
    def setUp(self):
        self.m = load_module()
        self.adapter = self.m.build_adapter(
            source_basis_id="global-jspace-test",
            source_basis_sha256="1" * 64,
            model="qwen/qwen3-0.6b-04-28:free",
            tokenizer_id="Qwen/Qwen3-0.6B",
            tokenizer_sha256="2" * 64,
            token_ids=[10, 20, 30],
            projection_rows=[[1,0,0],[0,1,0],[0,0,1]],
            feedback_rows=[[0,1,0],[0,0,1],[1,0,0]],
            decay=0.5,
            feedback_gain=0.25,
        )
        self.state = (2.0, -1.0, 0.5)

    def test_controls(self):
        plus = self.m.control_state(self.state, "+VECTOR")
        sign = self.m.control_state(self.state, "SIGN_FLIP")
        null = self.m.control_state(self.state, "NULL_VECTOR")
        orth = self.m.control_state(self.state, "ORTHOGONAL_SAME_NORM")
        perm = self.m.control_state(self.state, "PERMUTED_SAME_NORM")
        self.assertEqual(tuple(-x for x in plus), sign)
        self.assertTrue(all(x == 0.0 for x in null))
        self.assertAlmostEqual(sum(a*b for a,b in zip(plus, orth)), 0.0, places=10)
        self.assertAlmostEqual(math.sqrt(sum(x*x for x in plus)), math.sqrt(sum(x*x for x in orth)), places=10)
        self.assertAlmostEqual(math.sqrt(sum(x*x for x in plus)), math.sqrt(sum(x*x for x in perm)), places=10)

    def test_one_token_request_and_no_fallback(self):
        r = self.m.build_step_request(
            adapter=self.adapter, source_packet_sha256="3"*64,
            primary_state=self.state, control="+VECTOR", gain=4.0,
            step_index=0, seed=17, messages=[{"role":"user","content":"A B C"}],
        )
        b = r["body"]
        self.assertEqual(1, b["max_tokens"])
        self.assertTrue(b["provider"]["require_parameters"])
        self.assertFalse(b["provider"]["allow_fallbacks"])
        self.assertEqual({"10":8.0,"20":-4.0,"30":2.0}, b["logit_bias"])
        self.assertEqual(self.m.CREDIT_SCOPE, r["identity"]["credit_scope"])

    def test_baseline_vs_null(self):
        kw = dict(adapter=self.adapter, source_packet_sha256="4"*64,
                  primary_state=self.state, gain=2.0, step_index=1, seed=19,
                  messages=[{"role":"user","content":"x"}])
        baseline = self.m.build_step_request(control="BASELINE", **kw)
        null = self.m.build_step_request(control="NULL_VECTOR", **kw)
        self.assertNotIn("logit_bias", baseline["body"])
        self.assertEqual({"10":0.0,"20":0.0,"30":0.0}, null["body"]["logit_bias"])

    def test_feedback_changes_next_bias(self):
        first = self.m.build_step_request(
            adapter=self.adapter, source_packet_sha256="5"*64,
            primary_state=self.state, control="+VECTOR", gain=1.0,
            step_index=0, seed=23, messages=[{"role":"user","content":"x"}],
        )
        nxt = self.m.advance_state(self.adapter, first["state"], observed_token_id=10)
        self.assertEqual((1.0, -0.25, 0.25), nxt)
        second = self.m.build_step_request(
            adapter=self.adapter, source_packet_sha256="5"*64,
            primary_state=nxt, control="+VECTOR", gain=1.0,
            step_index=1, seed=23,
            messages=[{"role":"user","content":"x"},{"role":"assistant","content":"A"}],
        )
        self.assertNotEqual(first["bias"], second["bias"])

    def test_transition_identity_deterministic(self):
        nxt = self.m.advance_state(self.adapter, self.state, observed_token_id=20)
        a = self.m.bind_transition(step_identity_sha256="6"*64, observed_token_id=20,
                                   current_state=self.state, next_state=nxt)
        b = self.m.bind_transition(step_identity_sha256="6"*64, observed_token_id=20,
                                   current_state=self.state, next_state=nxt)
        self.assertEqual(a, b)
        self.assertEqual(64, len(a["transition_sha256"]))

    def test_dimension_mismatch_fails(self):
        with self.assertRaisesRegex(self.m.ClosedLoopJSpaceError, "STATE_DIMENSION_MISMATCH"):
            self.m.project_bias(self.adapter, (1.0, 2.0), 1.0)


if __name__ == "__main__":
    unittest.main()
