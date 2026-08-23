from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT / "tools"
RUNTIME_PATH = TOOLS / "clay_profile_pipeline_runtime.py"


def _reference_convergence_active() -> bool:
    if not RUNTIME_PATH.is_file():
        return False
    source = RUNTIME_PATH.read_text(encoding="utf-8")
    return "def _pipeline_profile_read" in source and "source_namespace" in source


def _runtime_module():
    sys.path.insert(0, str(TOOLS))
    try:
        return importlib.import_module("clay_profile_pipeline_runtime")
    finally:
        if sys.path and sys.path[0] == str(TOOLS):
            sys.path.pop(0)


def _profile(source_a: Path, source_b: Path) -> dict:
    return {
        "schema": "clay-pipeline-profile/v2",
        "profile_id": "same-kind-shadow-probe",
        "inference": {"kind": "mock"},
        "personality": {
            "output_contract": {
                "title_field": "heading",
                "intro_field": "lead",
                "sections_field": "blocks",
                "section_evidence_field": "refs",
                "section_claims_field": "state",
                "continuity_field": "carry",
                "autobiographical_hypotheses_field": "open_questions",
            }
        },
        "sources": [
            {
                "kind": "events",
                "source_namespace": "logical-A",
                "adapter": "json_snapshot",
                "path": str(source_a),
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            },
            {
                "kind": "events",
                "source_namespace": "logical-B",
                "adapter": "json_snapshot",
                "path": str(source_b),
                "required_for_quiet": True,
                "evidence_prefix": "event:",
            },
        ],
        "canonical_probes": [],
        "state_metrics": [],
        "gate": {},
    }


def _visible_labels(collected: dict) -> list[str]:
    labels: list[str] = []
    sources = collected.get("sources", {})
    values = sources.values() if isinstance(sources, dict) else sources
    for source in values:
        if not isinstance(source, dict):
            continue
        value = source.get("value")
        if isinstance(value, dict) and isinstance(value.get("label"), str):
            labels.append(value["label"])
    return labels


@pytest.mark.skipif(
    not _reference_convergence_active(),
    reason="activates only when DB-profile reference convergence owns source_namespace identity",
)
def test_two_logical_sources_with_same_kind_never_silently_shadow_each_other(tmp_path: Path) -> None:
    """Logical source identity must not be destroyed by a presentation/routing key collision.

    A runtime may choose either of two safe semantics:
    1. fail closed when one profile declares duplicate `kind` values; or
    2. represent both logical sources independently (for example by namespace-qualified keys).

    It may not count/admit both inputs while exposing only the last source through the
    canonical packet/workspace. That would make Exactly-Once identity more precise than the
    reasoning/evidence surface and silently discard causal evidence.
    """
    runtime_module = _runtime_module()
    runtime = runtime_module.ProfilePipelineRuntime(root=tmp_path)

    source_a = tmp_path / "a.json"
    source_b = tmp_path / "b.json"
    source_a.write_text(json.dumps({"label": "A"}), encoding="utf-8")
    source_b.write_text(json.dumps({"label": "B"}), encoding="utf-8")

    raw_profile = _profile(source_a, source_b)
    try:
        profile = runtime._normalize_profile(raw_profile)
    except runtime_module.PipelineFault as exc:
        error = str(exc).upper()
        assert "SOURCE" in error and ("DUPLICATE" in error or "KIND" in error), error
        return

    collected = runtime._pipeline_collect(
        {
            "entity_db": str(tmp_path / "entity.db"),
            "source_db": str(tmp_path / "entity.db"),
            "profile": profile,
            "previous": {"cursors": {}},
        }
    )

    if collected.get("ok") is False:
        error = str(collected.get("error", "")).upper()
        assert "SOURCE" in error and ("DUPLICATE" in error or "KIND" in error), error
        return

    assert sorted(_visible_labels(collected)) == ["A", "B"], (
        "two distinct source_namespace values sharing one kind were both admitted, but "
        "the canonical source workspace exposed fewer than both logical sources"
    )
