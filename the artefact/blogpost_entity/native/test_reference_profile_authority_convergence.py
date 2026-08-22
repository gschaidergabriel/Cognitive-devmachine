from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_PATH = ROOT / "tools" / "clay_profile_pipeline_runtime.py"
NATIVE_PART00 = Path(__file__).with_name("mini_entity_part00.inc")
NATIVE_PART01 = Path(__file__).with_name("mini_entity_part01.inc")


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _profile_read_method(source: str) -> ast.FunctionDef | None:
    tree = ast.parse(source)
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != "ProfilePipelineRuntime":
            continue
        for child in node.body:
            if isinstance(child, ast.FunctionDef) and child.name == "_pipeline_profile_read":
                return child
    return None


def test_reference_profile_authority_converges_on_native_miniunifieddb_contract() -> None:
    """A converged reference runtime may not invent a second active-profile authority.

    Current main intentionally still has the legacy reference implementation. This gate is
    dormant until `_pipeline_profile_read` is actually introduced; from that moment onward
    it requires the existing native MiniUnifiedDB profile authority rather than a parallel
    eos_pipeline_profile(s) table.
    """

    runtime = _text(RUNTIME_PATH)
    method = _profile_read_method(runtime)
    if method is None:
        return

    native00 = _text(NATIVE_PART00)
    native01 = _text(NATIVE_PART01)
    assert "CREATE TABLE IF NOT EXISTS entity_state" in native00
    assert "active_profile" in native00
    assert "CREATE TABLE IF NOT EXISTS profiles" in native00
    assert "profile_sha256" in native00
    assert "JOIN profiles p ON p.profile_id=e.active_profile" in native01

    method_source = ast.get_source_segment(runtime, method) or ""
    for required in ("entity_state", "active_profile", "profiles", "profile_sha256"):
        assert required in method_source, (
            "reference profile read has not adopted native profile authority: " + required
        )

    for forbidden in ("eos_pipeline_profiles", "eos_pipeline_profile"):
        assert forbidden not in runtime, f"competing profile authority reintroduced: {forbidden}"
