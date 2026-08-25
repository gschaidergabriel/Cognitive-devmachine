from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ABI_PATH = ROOT / "research_entity/global/COGNITIVE_PROCESS_ABI_v1.json"
VALIDATOR_PATH = ROOT / "tools/validate_cognitive_process_abi_v1.py"
spec = importlib.util.spec_from_file_location("abi_validator", VALIDATOR_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def load():
    return json.loads(ABI_PATH.read_text())


def test_current_contract_passes():
    assert mod.validate(load()) == []


def test_fixed_grid_regression_fails():
    doc = load()
    doc["authority"]["grid_law"] = "GRID10_FIXED"
    assert any("grid law" in e for e in mod.validate(doc))


def test_generic_causal_identity_alias_is_rejected():
    doc = load()
    req = doc["packet_types"]["CognitiveWorkUnit"]["required"]
    req[req.index("entry_event_sha256")] = "causal_event_id"
    assert any("entry_event_sha256" in e or "generic identity alias" in e for e in mod.validate(doc))


def test_claude_bridge_cannot_be_acceptance_only():
    doc = load()
    for pid in ("AZP06", "AZP08", "AZP13"):
        doc["process_binding"][pid] = [x for x in doc["process_binding"][pid] if x != "ClaudeCodeBridgePacket"]
    assert any("Claude bridge missing semantic bindings" in e for e in mod.validate(doc))


def test_state_placement_boundary_is_required():
    doc = load()
    del doc["packet_types"]["StatePlacementDecision"]
    assert any("packet set mismatch" in e for e in mod.validate(doc))


def test_effect_boundary_cannot_be_recast_as_cognitive_result():
    doc = load()
    doc["process_binding"]["AZP12"] = ["EffectProposal", "CognitiveResult"]
    assert any("AZP12 must remain deterministic effect boundary" in e for e in mod.validate(doc))


def test_credit_inflation_fails():
    doc = load()
    doc["credit"]["jspace_model_runtime"] = 1
    assert any("inflated credit" in e for e in mod.validate(doc))


def test_discriminator_must_check_deeper_interface_evidence():
    doc = load()
    doc["first_executable_discriminator"]["steps"] = [
        s for s in doc["first_executable_discriminator"]["steps"]
        if "deeper-interface-without-evidence" not in s
    ]
    assert any("deeper-interface-without-evidence" in e for e in mod.validate(doc))
