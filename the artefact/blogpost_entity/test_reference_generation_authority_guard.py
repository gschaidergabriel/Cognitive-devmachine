from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


def _max_calls_pairing_canonical_and_mirror_generation(source: str) -> list[str]:
    """Find max(...) reconciliation that lets a legacy mirror raise canonical generation."""
    tree = ast.parse(source)
    bad: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Name) or node.func.id != "max":
            continue
        text = ast.get_source_segment(source, node) or ""
        lowered = text.lower()
        has_canonical = "native_generation" in lowered or "entity_generation" in lowered
        has_mirror = "mirror_generation" in lowered or "eos_generation" in lowered
        if has_canonical and has_mirror:
            bad.append(text)
    return bad


def test_legacy_generation_mirror_cannot_promote_canonical_generation_by_max_merge():
    source = RUNTIME.read_text(encoding="utf-8")
    bad = _max_calls_pairing_canonical_and_mirror_generation(source)
    assert bad == [], (
        "LEGACY_GENERATION_MIRROR_AUTHORITY_REGRESSION: once entity_state exists as the "
        "canonical generation/CAS authority, eos_pipeline_state is compatibility state and "
        "must never raise entity_state.generation. If legacy-only migration is required, "
        "seed canonical generation exactly once under an explicit migration/preexistence "
        f"fence, then synchronize mirror from canonical state. Found: {bad}"
    )
