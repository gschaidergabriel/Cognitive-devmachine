from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
VALIDATOR_PATH = ROOT / "tools/validate_cognitive_process_abi_v1.py"
spec = importlib.util.spec_from_file_location("abi_validator", VALIDATOR_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def load():
    return json.loads(ABI_PATH.read_text(encoding="utf-8"))


def test_current_contract_passes():
    assert mod.validate(load()) == []


def test_typed_entry_event_digest_is_required():
    doc = load()
    doc["packet_types"]["COGNITIVE_WORK_PACKET/v1"]["required"].remove("entry_event_sha256")
    assert any("missing entry_event_sha256" in e for e in mod.validate(doc))


def test_parallel_identity_law_is_required():
    doc = load()
    doc["authority"]["identity_binding_law"] = "GENERIC_IDS_OK"
    assert any("parallel causal identity" in e for e in mod.validate(doc))


def test_state_placement_boundary_is_required():
    doc = load()
    del doc["packet_types"]["STATE_PLACEMENT_DECISION/v1"]
    assert any("packet set mismatch" in e for e in mod.validate(doc))


def test_claude_bridge_must_bind_handoff_and_reconciliation():
    doc = load()
    doc["process_bindings"]["ZECP14"].remove("CLAUDE_CODE_BRIDGE_PACKET/v1")
    assert any("ZECP14 missing Claude bridge" in e for e in mod.validate(doc))


def test_effect_boundary_cannot_be_recast_as_cognitive_result():
    doc = load()
    doc["process_bindings"]["ZECP17"] = ["EFFECT_PROPOSAL/v1", "COGNITIVE_RESULT_PACKET/v1"]
    assert any("ZECP17 must remain deterministic effect boundary" in e for e in mod.validate(doc))


def test_unknown_effect_outcome_status_must_survive():
    doc = load()
    doc["packet_types"]["EFFECT_JOURNAL_RECEIPT/v1"]["allowed_outcome_status"] = ["VERIFIED_SUCCESS", "VERIFIED_FAILURE"]
    assert any("effect outcome status mismatch" in e for e in mod.validate(doc))


def test_runtime_credit_inflation_fails():
    doc = load()
    doc["credit_boundary"]["global_jspace_causal_runtime"] = 1
    assert any("inflated credit" in e for e in mod.validate(doc))


def test_discriminator_requires_deeper_interface_negative():
    doc = load()
    doc["first_executable_discriminator"]["steps"] = [
        s for s in doc["first_executable_discriminator"]["steps"]
        if "deeper-interface-without-evidence" not in s
    ]
    assert any("deeper-interface-without-evidence" in e for e in mod.validate(doc))
