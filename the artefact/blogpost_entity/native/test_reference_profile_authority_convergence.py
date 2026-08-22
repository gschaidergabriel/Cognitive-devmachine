from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
NATIVE_PART00 = Path(__file__).with_name("mini_entity_part00.inc")
NATIVE_PART01 = Path(__file__).with_name("mini_entity_part01.inc")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_reference_profile_authority_converges_on_native_miniunifieddb_contract() -> None:
    """The Python reference may not invent a second active-profile authority.

    Native MiniUnifiedDB already owns profile selection and profile-byte integrity through
    entity_state.active_profile -> profiles(profile_json, profile_sha256). The reference
    runtime must reuse that contract instead of creating eos_pipeline_profile(s).
    """

    runtime = _text(RUNTIME_PATH)
    native00 = _text(NATIVE_PART00)
    native01 = _text(NATIVE_PART01)

    assert "CREATE TABLE IF NOT EXISTS entity_state" in native00
    assert "active_profile" in native00
    assert "CREATE TABLE IF NOT EXISTS profiles" in native00
    assert "profile_sha256" in native00
    assert "JOIN profiles p ON p.profile_id=e.active_profile" in native01

    for required in ("entity_state", "active_profile", "profiles", "profile_sha256"):
        assert required in runtime, f"reference runtime has not adopted native profile authority: {required}"

    for forbidden in ("eos_pipeline_profiles", "eos_pipeline_profile"):
        assert forbidden not in runtime, f"competing profile authority reintroduced: {forbidden}"


def test_local_exec_subprocesses_use_an_explicit_child_environment() -> None:
    """Any direct local inference subprocess must not inherit provider secrets implicitly."""

    source = _text(RUNTIME_PATH)
    tree = ast.parse(source)
    calls: list[ast.Call] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if (
            isinstance(func, ast.Attribute)
            and isinstance(func.value, ast.Name)
            and func.value.id == "subprocess"
            and func.attr == "run"
        ):
            calls.append(node)

    for call in calls:
        assert any(keyword.arg == "env" for keyword in call.keywords), (
            "local inference subprocess inherits the full parent environment; "
            "pass an explicit allowlisted child env"
        )
