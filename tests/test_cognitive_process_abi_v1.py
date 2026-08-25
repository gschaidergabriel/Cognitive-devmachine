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


def test_missing_process_binding_fails():
    doc = load()
    del doc["process_binding"]["AZP20"]
    assert any("process binding mismatch" in e for e in mod.validate(doc))


def test_unknown_packet_reference_fails():
    doc = load()
    doc["process_binding"]["AZP06"].append("MagicTruthPacket")
    assert any("unknown packet" in e for e in mod.validate(doc))


def test_credit_inflation_fails():
    doc = load()
    doc["credit"]["jspace_model_runtime"] = 1
    assert any("inflated credit" in e for e in mod.validate(doc))


def test_discriminator_must_keep_fail_closed_negatives():
    doc = load()
    doc["first_executable_discriminator"]["steps"] = [
        s for s in doc["first_executable_discriminator"]["steps"]
        if "stale-generation" not in s
    ]
    assert any("stale-generation" in e for e in mod.validate(doc))
