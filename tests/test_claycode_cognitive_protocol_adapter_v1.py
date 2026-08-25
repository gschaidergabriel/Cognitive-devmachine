from dataclasses import replace
import tempfile
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from claycode_cognitive_protocol_adapter_v1 import (
    ClayCodeCognitiveProtocolError,
    compile_protocol_contract,
    encode_packet,
    roundtrip,
)
from zero_entityos_restart_resize_db_smoke_v1 import (
    CanonicalStateAuthority,
    CognitiveGridRuntime,
    GridConfig,
)


def work_packet():
    return {
        "schema": "COGNITIVE_WORK_PACKET/v1",
        "causal_event_id": "event-001",
        "admission_id": "admission-001",
        "generation": 3,
        "work_id": "work-001",
        "process_id": "ZECP03",
        "parent_work_ids": [],
        "workspace_epoch": 7,
        "state_snapshot_ref": {
            "schema": "DB_STATE_REF/v1",
            "ref_id": "db-state-001",
            "store": "sqlite",
            "snapshot_or_epoch": "epoch-7",
            "object_key": "goal",
            "digest": "a" * 64,
            "provenance": "fixture",
            "mutability": "IMMUTABLE_SNAPSHOT",
        },
        "input_refs": ["db://goal"],
        "epistemic_inputs": [{"class": "OBSERVED", "ref": "db://goal"}],
        "capability_scope_ref": "cap://cognitive-only",
        "resource_budget": {"tokens_max": 0},
        "grid_runtime": {"requested_N": 1, "observed_available_N": 1},
        "route_policy_ref": "route://fixture",
        "completion_contract": {"kind": "deterministic-fixture"},
    }


def result_packet(process_id="ZECP08", result_class="CANDIDATE"):
    return {
        "schema": "COGNITIVE_RESULT_PACKET/v1",
        "causal_event_id": "event-001",
        "admission_id": "admission-001",
        "generation": 3,
        "work_id": "work-001",
        "process_id": process_id,
        "executor_binding": {"executor_id": "fixture"},
        "result_id": "result-001",
        "result_class": result_class,
        "result_payload_ref": "mem://candidate",
        "result_digest": "b" * 64,
        "evidence_refs": [],
        "unknowns": [],
        "db_write_proposals": [],
        "effect_request_candidates": [],
        "workspace_reentry": "NONE",
        "runtime_receipt": {"runtime": "deterministic-fixture"},
    }


class ClayCodeCognitiveProtocolAdapterTests(unittest.TestCase):
    def test_checked_in_protocol_compiles_on_current_claycode_frontend(self):
        result = compile_protocol_contract()
        self.assertEqual("ClayCodeBaseFrontendAST/v1", result["frontend_schema"])
        self.assertEqual("BASE_D_V18_REWARD_RELATIONS", result["surface"])
        self.assertTrue(result["semantic_hash"])
        self.assertTrue(result["grammar_sha256"])

    def test_work_packet_roundtrip_is_claycode_and_digest_bound(self):
        envelope, decoded = roundtrip("COGNITIVE_WORK_PACKET/v1", work_packet())
        self.assertEqual(work_packet(), decoded)
        self.assertIn("module entityos.hcu.cognitive_packet", envelope.clay_source)
        self.assertIn("never_confers canonical_truth", envelope.clay_source)
        self.assertTrue(envelope.clay_semantic_hash)
        self.assertTrue(envelope.clay_grammar_sha256)

    def test_payload_tamper_fails_closed(self):
        envelope = encode_packet("COGNITIVE_WORK_PACKET/v1", work_packet())
        tampered = replace(envelope, payload_json=envelope.payload_json + " ")
        from claycode_cognitive_protocol_adapter_v1 import decode_packet
        with self.assertRaisesRegex(ClayCodeCognitiveProtocolError, "PAYLOAD_DIGEST_MISMATCH"):
            decode_packet(tampered)

    def test_nested_authority_smuggling_fails_closed(self):
        packet = work_packet()
        packet["completion_contract"] = {"nested": {"canonical_truth": True}}
        with self.assertRaisesRegex(ClayCodeCognitiveProtocolError, "AUTHORITY_SMUGGLING"):
            encode_packet("COGNITIVE_WORK_PACKET/v1", packet)

    def test_non_effectgate_process_cannot_emit_effect_receipt(self):
        with self.assertRaisesRegex(ClayCodeCognitiveProtocolError, "NON_ZECP17_EFFECT_RECEIPT"):
            encode_packet("COGNITIVE_RESULT_PACKET/v1", result_packet("ZECP16", "EFFECT_RECEIPT"))
        envelope, decoded = roundtrip(
            "COGNITIVE_RESULT_PACKET/v1", result_packet("ZECP17", "EFFECT_RECEIPT")
        )
        self.assertEqual("ZECP17", decoded["process_id"])
        self.assertTrue(envelope.clay_semantic_hash)

    def test_same_claycode_work_survives_runtime_n_change_without_semantic_identity_change(self):
        _, decoded = roundtrip("COGNITIVE_WORK_PACKET/v1", work_packet())
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "canonical.sqlite3"
            authority = CanonicalStateAuthority(path)
            authority.seed("goal", {"goal": "claycode-restart"}, provenance="test", generation=3, epoch=1)
            first = CognitiveGridRuntime(path, GridConfig(n=1, generation=3))
            try:
                a = first.enqueue(decoded["process_id"], decoded)
                ra = first.execute(a)
            finally:
                first.close()
            second = CognitiveGridRuntime(path, GridConfig(n=20, generation=3))
            try:
                b = second.enqueue(decoded["process_id"], decoded)
                rb = second.execute(b)
                self.assertEqual(ra["semantic_identity"], rb["semantic_identity"])
                self.assertEqual({"goal": "claycode-restart"}, second.read_s0("goal"))
                self.assertTrue(second.attempt_direct_s0_write("illegal", {"x": 1}))
            finally:
                second.close()
                authority.close()


if __name__ == "__main__":
    unittest.main()
