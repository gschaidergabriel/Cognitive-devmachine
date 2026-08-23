from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from clay_profile_pipeline_runtime import ProfilePipelineRuntime


PRESET = Path(__file__).resolve().parent / "presets" / "zero_blog.json"


def test_shipped_zero_preset_binds_every_source_to_stable_logical_identity() -> None:
    """The default application preset must remain admissible after source-identity hardening.

    This is an integration regression, not a provider/runtime experiment: the preset is only
    parsed and normalized. Requiring explicit identity even for the snapshot source keeps the
    shipped evidence namespace stable if that source later participates in persisted refs.
    """
    raw = json.loads(PRESET.read_text(encoding="utf-8"))
    normalized = ProfilePipelineRuntime._normalize_profile(raw)

    sources = normalized["sources"]
    namespaces = [source.get("source_namespace") for source in sources]

    assert len(sources) == 4
    assert all(isinstance(namespace, str) and namespace.strip() for namespace in namespaces)
    assert len(set(namespaces)) == len(namespaces)
    assert {source["kind"] for source in sources} == {
        "architect_receipt",
        "bug",
        "architect_log",
        "intentions",
    }
