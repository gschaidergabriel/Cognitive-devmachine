#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
import profile_runtime_ucf_terminal_closure_v1 as closure


def digest(value):
    return hashlib.sha256(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def valid_payload():
    packet_digest = "1" * 64
    admission_digest = "2" * 64
    generated_payload = {"answer": "candidate"}
    candidate_digest = digest(generated_payload)
    terminal_digest = closure.terminal_result_digest(
        output_id="out-1",
        generation=8,
        inference_packet_digest=packet_digest,
        cognitive_fabric_admission_receipt_digest=admission_digest,
    )
    return {
        "data": {
            "admitted": {
                "ok": True,
                "generation": 7,
                "canonical_state_hash": "3" * 64,
                "packet_hash": "4" * 64,
                "inference_packet_digest": packet_digest,
                "cognitive_fabric_receipt_digest": admission_digest,
            },
            "generated": {
                "ok": True,
                "payload": generated_payload,
                "candidate_result_digest": candidate_digest,
                "inference_packet_digest": packet_digest,
                "cognitive_fabric_admission_receipt_digest": admission_digest,
            },
            "gated": {
                "ok": True,
                "payload": generated_payload,
                "validation_decision": "ACCEPT",
                "inference_packet_digest": packet_digest,
                "cognitive_fabric_admission_receipt_digest": admission_digest,
            },
            "committed": {
                "ok": True,
                "output_id": "out-1",
                "generation": 8,
                "canonical_write_committed": True,
                "effect_committed": False,
                "terminal_result_digest": terminal_digest,
                "inference_packet_digest": packet_digest,
                "cognitive_fabric_admission_receipt_digest": admission_digest,
            },
            "compiled": {
                "canonical_state_hash": "3" * 64,
                "packet_hash": "4" * 64,
            },
            "prompt": {"system": "s", "user": "u"},
        }
    }


class TerminalClosureTests(unittest.TestCase):
    def test_valid_terminal_ancestry_reports_explicit_evidence_debt(self):
        out = closure.evaluate_terminal_closure(valid_payload())
        self.assertFalse(out["ok"])
        self.assertEqual(
            out["error"],
            "UCF_FINAL_RUNTIME_RECEIPT_EVIDENCE_INCOMPLETE",
        )
        self.assertRegex(out["terminal_ancestry_digest"], r"^[0-9a-f]{64}$")
        self.assertNotIn("ucf_runtime_receipt_digest", out)
        self.assertEqual(
            out["authority"],
            "EVIDENCE_DEBT_ONLY_NO_UCF_RUNTIME_RECEIPT",
        )

    def test_rejects_generated_packet_identity_drift(self):
        payload = valid_payload()
        payload["data"]["generated"]["inference_packet_digest"] = "5" * 64
        with self.assertRaisesRegex(
            closure.ProfileRuntimeUCFTerminalClosureError,
            "GENERATED_PACKET_IDENTITY_DRIFT",
        ):
            closure.evaluate_terminal_closure(payload)

    def test_rejects_candidate_result_identity_drift(self):
        payload = valid_payload()
        payload["data"]["generated"]["payload"] = {"answer": "poison"}
        with self.assertRaisesRegex(
            closure.ProfileRuntimeUCFTerminalClosureError,
            "CANDIDATE_RESULT_IDENTITY_DRIFT",
        ):
            closure.evaluate_terminal_closure(payload)

    def test_rejects_commit_generation_drift(self):
        payload = valid_payload()
        payload["data"]["committed"]["generation"] = 9
        with self.assertRaisesRegex(
            closure.ProfileRuntimeUCFTerminalClosureError,
            "COMMIT_GENERATION_DRIFT",
        ):
            closure.evaluate_terminal_closure(payload)

    def test_rejects_unexpected_effect_commit(self):
        payload = valid_payload()
        payload["data"]["committed"]["effect_committed"] = True
        with self.assertRaisesRegex(
            closure.ProfileRuntimeUCFTerminalClosureError,
            "UNEXPECTED_EFFECT_COMMIT",
        ):
            closure.evaluate_terminal_closure(payload)

    def test_rejects_terminal_result_digest_drift(self):
        payload = valid_payload()
        payload["data"]["committed"]["terminal_result_digest"] = "6" * 64
        with self.assertRaisesRegex(
            closure.ProfileRuntimeUCFTerminalClosureError,
            "TERMINAL_RESULT_IDENTITY_DRIFT",
        ):
            closure.evaluate_terminal_closure(payload)


if __name__ == "__main__":
    unittest.main()
