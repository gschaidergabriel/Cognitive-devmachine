import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "research_entity/global/DB_VS_SIMULATION_BOUNDARY_v1.json"
VALIDATOR_PATH = ROOT / "tools/validate_db_vs_simulation_boundary_v1.py"
spec = importlib.util.spec_from_file_location("db_boundary_validator", VALIDATOR_PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def load():
    return json.loads(DOC_PATH.read_text())


def test_current_contract_passes():
    assert mod.validate(load()) == []


def test_fixed_grid_regression_fails():
    doc = load()
    doc["authority"]["grid_law"] = "GRID10_FIXED"
    assert any("variable-N" in e for e in mod.validate(doc))


def test_model_direct_db_write_fails():
    doc = load()
    doc["transition_rules"]["S2_to_S0"] = "MODEL_MAY_WRITE"
    assert any("S2->S0" in e for e in mod.validate(doc))


def test_claude_code_direct_truth_fails():
    doc = load()
    doc["claude_code_boundary"]["direct_S0_write"] = True
    assert any("Claude Code direct S0 write" in e for e in mod.validate(doc))


def test_workspace_truth_minting_fails():
    doc = load()
    doc["state_classes"]["S1"]["may_mint_truth"] = True
    assert any("S1 truth minting" in e for e in mod.validate(doc))


def test_missing_stale_generation_negative_fails():
    doc = load()
    doc["hard_negatives"].remove("STALE_GENERATION_WRITE_PROPOSAL_ACCEPTED")
    assert any("missing hard negatives" in e for e in mod.validate(doc))


def test_jspace_truth_promotion_fails():
    doc = load()
    doc["jspace_boundary"]["can_mint_truth"] = True
    assert any("J-Space cannot mint truth" in e for e in mod.validate(doc))


def test_credit_inflation_fails():
    doc = load()
    doc["credit"]["training"] = 1
    assert any("inflated credit" in e for e in mod.validate(doc))
