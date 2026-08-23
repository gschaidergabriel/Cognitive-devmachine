import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_clayverse_authority_consistency.py"

spec = importlib.util.spec_from_file_location("authority_validator_current", VALIDATOR)
mod = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(mod)


def _json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_current_authority_successor_is_one_fail_closed_chain():
    """Newest versioned steering must close through every current authority surface."""
    bootstrap = _json("research_entity/continuity/BOOTSTRAP_MINIMAL.json")
    program = _json("research_entity/rooms/PROGRAM_STATE.json")
    manifest = _json("the artefact/manifest.json")
    inbox = _json("research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")

    expected, version, discovery_errors = mod.discover_current_authority(ROOT)
    assert discovery_errors == [], discovery_errors
    assert expected is not None and version is not None

    expected_file = ROOT / expected
    assert expected_file.is_file(), ("CURRENT_AUTHORITY_TARGET_MISSING", expected)
    steering = json.loads(expected_file.read_text(encoding="utf-8"))

    assert steering["mode"] == "FREE_ONLY"
    assert steering["product"] == "EntityOS"
    assert steering["integrated_cognition_compute_architecture"] == "HCU"

    observed = {
        "bootstrap": bootstrap["authority_correction"],
        "program": program["authority_correction"],
        "manifest": manifest["authority_correction"],
        "inbox": inbox["steering"],
    }
    assert set(observed.values()) == {expected}, (
        "CURRENT_AUTHORITY_SUCCESSOR_SPLIT",
        observed,
    )

    result = mod.validate(ROOT)
    assert result["pass"], result["errors"]
    assert result["current_authority"] == expected
