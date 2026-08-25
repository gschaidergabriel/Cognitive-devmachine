from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from tools.validate_agent_zero_cognitive_process_abi_v1 import (
    AbiValidationError,
    validate_contract,
    validate_packet,
)

ROOT = Path(__file__).resolve().parents[1]
ABI_PATH = ROOT / "research_entity/global/AGENT_ZERO_COGNITIVE_PROCESS_ABI_v1.json"


def base_packet(kind: str, process_id: str = "AZP04") -> dict:
    payloads = {
        "COGNITIVE_WORK": {"work_id": "w1", "objective": "x", "inputs": [], "completion_test": "done", "resource_budget": {}},
        "COGNITIVE_RESULT": {"work_id": "w1", "result_class": "candidate", "candidate": {}, "evidence_refs": [], "uncertainty": "unknown"},
        "DB_READ_REQUEST": {"query_id": "q1", "query_type": "by_id", "query": {"id": "x"}, "projection_limit": 8},
        "DB_WRITE_PROPOSAL": {"proposal_id": "p1", "record_class": "memory", "candidate_delta": {}, "evidence_refs": [], "expected_state_version": "s1"},
        "WORKSPACE_BROADCAST": {"workspace_id": "ws1", "selection_id": "sel1", "content_refs": [], "salience_basis": {}},
        "WORKSPACE_REENTRY": {"workspace_id": "ws1", "source_result_refs": [], "reentry_target": "planner", "causal_change_test": "must_change"},
        "CLAUDE_CODE_HANDOFF": {"handoff_id": "h1", "interface_mode": "TEXT_TOOL_SESSION", "bounded_context_refs": [], "task": "inspect", "expected_return_schema": "candidate/v1"},
        "CLAUDE_CODE_RETURN": {"handoff_id": "h1", "interface_mode": "TEXT_TOOL_SESSION", "return_class": "candidate", "candidate": {}, "tool_receipt_refs": []},
        "JSPACE_MEASUREMENT": {"measurement_id": "m1", "model_identity": "model", "interface_or_hook_identity": "hook", "measurement_class": "probe", "result": {}},
        "EFFECT_PROPOSAL": {"effect_proposal_id": "e1", "effect_type": "tool", "arguments": {}, "capability_ref": "cap1", "idempotency_key": "idem1"},
        "RECOVERY_REJOIN": {"rejoin_id": "r1", "prior_runtime_id": "rt0", "new_runtime_id": "rt1", "open_work_refs": [], "unknown_effect_refs": []},
    }
    return {
        "abi": "AGENT_ZERO_COGNITIVE_PROCESS_ABI/v1",
        "packet_kind": kind,
        "packet_id": "pkt1",
        "causal_event_id": "ce1",
        "admission_id": "ad1",
        "generation": 7,
        "workspace_epoch": 3,
        "process_id": process_id,
        "source_runtime_id": "runtime-a",
        "target_selector": {"mode": "capability", "value": "cognitive"},
        "state_basis": {"canonical_state_version": "s1", "db_snapshot_ref": "db:1", "workspace_state_ref": "ws:3"},
        "authority_refs": ["authority:canonical"],
        "provenance_refs": ["source:test"],
        "payload": payloads[kind],
    }


class CognitiveProcessAbiV1Tests(unittest.TestCase):
    def setUp(self):
        self.abi = json.loads(ABI_PATH.read_text(encoding="utf-8"))

    def test_exact_contract_passes_and_advances_gate(self):
        result = validate_contract(self.abi)
        self.assertTrue(result["ok"])
        self.assertEqual(result["process_count"], 20)
        self.assertEqual(result["packet_kind_count"], 11)
        self.assertEqual(result["next_owner_gate"], "DB_VS_SIMULATION_BOUNDARY")

    def test_fixed_grid_architecture_is_rejected(self):
        bad = copy.deepcopy(self.abi)
        bad["authority"]["grid_size_law"] = "GRID10_REQUIRED"
        with self.assertRaisesRegex(AbiValidationError, "VARIABLE_N_GRID_LAW_REQUIRED"):
            validate_contract(bad)

    def test_current_owner_target_path_is_required(self):
        bad = copy.deepcopy(self.abi)
        bad["authority"]["owner_target_path"] = "research_entity/global/OWNER_CORRECTION_UNBOUNDED_AGENT_ZERO_COGNITIVE_GRID_2026-08-25.md"
        with self.assertRaisesRegex(AbiValidationError, "CURRENT_OWNER_TARGET_PATH_REQUIRED"):
            validate_contract(bad)

    def test_valid_work_packet_is_grid_size_independent(self):
        packet = base_packet("COGNITIVE_WORK")
        packet["observed_grid_size"] = 17
        result = validate_packet(packet, self.abi)
        self.assertTrue(result["ok"])

    def test_self_granted_capability_is_rejected(self):
        packet = base_packet("COGNITIVE_WORK")
        packet["self_granted_capability"] = True
        with self.assertRaisesRegex(AbiValidationError, "SELF_GRANTED_CAPABILITY"):
            validate_packet(packet, self.abi)

    def test_direct_db_commit_is_rejected(self):
        packet = base_packet("DB_WRITE_PROPOSAL", "AZP14")
        packet["payload"]["commit"] = True
        with self.assertRaisesRegex(AbiValidationError, "CANNOT_COMMIT_CANONICAL_STATE"):
            validate_packet(packet, self.abi)

    def test_direct_effect_execution_is_rejected(self):
        packet = base_packet("EFFECT_PROPOSAL", "AZP11")
        packet["payload"]["execute"] = True
        with self.assertRaisesRegex(AbiValidationError, "EFFECT_PROPOSAL_CANNOT_EXECUTE"):
            validate_packet(packet, self.abi)

    def test_cognitive_result_cannot_mint_fact(self):
        packet = base_packet("COGNITIVE_RESULT", "AZP06")
        packet["payload"]["truth_status"] = "CANONICAL"
        with self.assertRaisesRegex(AbiValidationError, "CANNOT_MINT_CANONICAL_FACT"):
            validate_packet(packet, self.abi)

    def test_claude_activation_claim_needs_exposed_interface_and_reentry(self):
        packet = base_packet("CLAUDE_CODE_RETURN", "AZP13")
        packet["payload"]["activation_level_claim"] = True
        with self.assertRaisesRegex(AbiValidationError, "EXPOSED_INTERFACE_EVIDENCE"):
            validate_packet(packet, self.abi)

    def test_jspace_causal_claim_needs_fresh_bound_evidence(self):
        packet = base_packet("JSPACE_MEASUREMENT", "AZP09")
        packet["payload"]["causal_claim"] = True
        with self.assertRaisesRegex(AbiValidationError, "JSPACE_CAUSAL_CLAIM_REQUIRES"):
            validate_packet(packet, self.abi)

    def test_frozen_v1_cannot_be_repromoted(self):
        packet = base_packet("JSPACE_MEASUREMENT", "AZP09")
        packet["payload"].update({
            "causal_claim": True,
            "exact_model_artifact_ref": "sha256:model",
            "intervention_receipt_ref": "receipt:1",
            "fresh_holdout_id": "holdout:new",
            "model_family_provenance_ref": "family:qwen",
            "controller_version": "frozen_structural_native_v1",
        })
        with self.assertRaisesRegex(AbiValidationError, "FROZEN_V1_CANNOT_BE_PROMOTED"):
            validate_packet(packet, self.abi)

    def test_unknown_effect_is_not_blindly_replayed_on_rejoin(self):
        packet = base_packet("RECOVERY_REJOIN", "AZP16")
        packet["payload"]["replay_unknown_effect"] = True
        with self.assertRaisesRegex(AbiValidationError, "MUST_NOT_BE_BLINDLY_REPLAYED"):
            validate_packet(packet, self.abi)


if __name__ == "__main__":
    unittest.main()
