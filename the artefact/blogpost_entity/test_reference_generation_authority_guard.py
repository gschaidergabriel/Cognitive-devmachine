from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RUNTIME = ROOT / "tools" / "clay_profile_pipeline_runtime.py"


def _max_calls_pairing_native_and_mirror(source: str) -> list[str]:
    """Return max(...) expressions that combine canonical/native and mirror generations.

    The reference convergence donor may migrate a legacy-only DB into the canonical
    entity_state row exactly once. After entity_state exists, however, eos_pipeline_state
    is only a compatibility mirror and may never raise canonical generation.

    This source guard deliberately rejects the known unsafe donor shape
    `max(native_generation, mirror_generation)`. It is not runtime parity evidence; the
    executable fault matrix still has to prove one-time migration and post-migration
    authority on exact candidate bytes.
    """
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
    bad = _max_calls_pairing_native_and_mirror(source)
    assert bad == [], (
        "LEGACY_GENERATION_MIRROR_AUTHORITY_REGRESSION: eos_pipeline_state is derived/legacy "
        "state and must never raise entity_state.generation after canonical authority exists. "
        "If legacy migration is needed, seed entity_state only when the canonical row did not "
        f"previously exist, then synchronize the mirror from canonical state. Found: {bad}"
    )
