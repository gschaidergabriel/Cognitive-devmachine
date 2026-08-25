from __future__ import annotations

import hashlib
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import trigger1_native_single_token_scope_gate_v1 as gate


def row(case_id: str, control: str) -> dict:
    return {
        "schema": gate.OBS_SCHEMA,
        "case_id": case_id,
        "control": control,
        "prefill_cvec_applied": False,
        "cvec_active_decode_n_tokens": 1,
        "probe_is_original_last_prompt_token": True,
        "full_prompt_tokens": 12,
        "prefill_tokens": 11,
        "intervention_position_scope": gate.SCOPE,
        "il_start": gate.INJECTION_LAYER,
        "il_end": gate.INJECTION_LAYER,
        "primary_layer_inp": gate.PRIMARY_LAYER,
        "downstream_layer_inp": gate.DOWNSTREAM_LAYER,
        "harness_source_sha256": "a" * 64,
        "runtime_receipt_sha256": hashlib.sha256(f"{case_id}:{control}".encode()).hexdigest(),
        "cvec_applied": control != "BASELINE",
        "cvec_rc": 0,
        "prompt_sha256": "b" * 64,
        "probe_token_id": 123,
    }


def candidate() -> dict:
    return {
        "native_single_token_scope_evidence": {
            "schema": gate.EVIDENCE_SCHEMA,
            "llama_cpp_commit": gate.PINNED_LLAMA_CPP,
            "gguf_sha256": gate.PINNED_GGUF_SHA256,
            "harness_source_sha256": "a" * 64,
            "rows": [row("case-1", c) for c in gate.CONTROLS],
        }
    }


class Trigger1NativeSingleTokenScopeGateTests(unittest.TestCase):
    def test_exact_single_token_post_prefill_scope_passes(self):
        verdict = gate.validate(candidate())
        self.assertTrue(verdict["pass"], verdict["failures"])
        self.assertTrue(verdict["native_single_token_position_scope_candidate"])
        self.assertFalse(verdict["legacy_multitoken_prefill_cvec_causally_identical_to_last_token_witness"])
        self.assertFalse(verdict["cross_runtime_mechanistic_identity_claimed"])

    def test_cvec_during_prefill_is_rejected(self):
        c = candidate()
        c["native_single_token_scope_evidence"]["rows"][1]["prefill_cvec_applied"] = True
        verdict = gate.validate(c)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("PREFILL_MUST_BE_UNSTEERED" in x for x in verdict["failures"]))

    def test_multi_token_active_decode_is_rejected(self):
        c = candidate()
        c["native_single_token_scope_evidence"]["rows"][1]["cvec_active_decode_n_tokens"] = 7
        verdict = gate.validate(c)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("CVEC_ACTIVE_DECODE_MUST_HAVE_ONE_TOKEN" in x for x in verdict["failures"]))

    def test_probe_must_be_original_last_prompt_token(self):
        c = candidate()
        c["native_single_token_scope_evidence"]["rows"][1]["probe_is_original_last_prompt_token"] = False
        verdict = gate.validate(c)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("PROBE_MUST_BE_ORIGINAL_LAST_PROMPT_TOKEN" in x for x in verdict["failures"]))

    def test_missing_control_is_rejected(self):
        c = candidate()
        c["native_single_token_scope_evidence"]["rows"].pop()
        verdict = gate.validate(c)
        self.assertFalse(verdict["pass"])
        self.assertTrue(any("CASE_CONTROL_UNIVERSE_INVALID" in x for x in verdict["failures"]))

    def test_harness_source_orders_prefill_before_cvec_before_probe(self):
        source = (TOOLS / "trigger1_native_llamacpp_single_token_cvec.cpp").read_text(encoding="utf-8")
        prefill = source.index("llama_decode(ctx, prefill_batch)")
        cvec = source.index("llama_set_adapter_cvec")
        probe = source.index("llama_decode(ctx, probe_batch)")
        self.assertLess(prefill, cvec)
        self.assertLess(cvec, probe)
        self.assertIn("llama_batch probe_batch = llama_batch_get_one(&probe, 1)", source)


if __name__ == "__main__":
    unittest.main()
