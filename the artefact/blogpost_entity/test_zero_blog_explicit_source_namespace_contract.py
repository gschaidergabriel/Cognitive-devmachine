from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRESET = HERE / "presets" / "zero_blog.json"
DURABLE_IDENTITY_ADAPTERS = {"sqlite_query", "jsonl_cursor"}


def test_zero_blog_durable_sources_declare_explicit_unique_source_namespaces() -> None:
    """The shipped preset must own its logical source identity explicitly.

    Exactly-once consumption, JSONL cursor continuity and persisted evidence provenance
    are all being converged onto one logical source identity.  The runtime must not invent
    that identity from profile_id, kind, query text or a path, because those are replaceable
    addressing/configuration details rather than historical provenance.
    """
    profile = json.loads(PRESET.read_text(encoding="utf-8"))
    durable = [
        source
        for source in profile.get("sources", [])
        if source.get("adapter") in DURABLE_IDENTITY_ADAPTERS
    ]
    assert durable, "shipped preset unexpectedly has no durable sources"

    namespaces: list[str] = []
    for source in durable:
        namespace = str(source.get("source_namespace") or "").strip()
        assert namespace, (
            f"durable source {source.get('kind')!r} has no explicit source_namespace; "
            "runtime derivation would invent provenance"
        )
        namespaces.append(namespace)

    assert len(namespaces) == len(set(namespaces)), (
        "distinct durable shipped sources reuse the same logical source_namespace"
    )
