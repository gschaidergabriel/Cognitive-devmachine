#!/usr/bin/env python3
"""Idempotently migrate the existing structured regression adapter to the current 3-arg run.

The profile preset remains an import/configuration surface, but the actual Clay run reads
its active profile from MiniUnifiedDB. This patches only the existing canonical test file.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST = ROOT / "the artefact" / "blogpost_entity" / "test_blogpost_entity.py"


def replace_exact(text: str, old: str, new: str, expected: int, label: str) -> str:
    count = text.count(old)
    if count == 0 and new in text:
        return text
    if count != expected:
        raise SystemExit(f"{label}: expected {expected} source anchors, found {count}")
    return text.replace(old, new)


def main() -> None:
    text = TEST.read_text(encoding="utf-8")
    original = text

    old_execute = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    result, runtime = execute_source(
        SRC,
        "run",
        [str(entity_db), str(source_db), str(profile_path), ""],
        runtime,
    )
'''
    new_execute = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=provider)
    imported = runtime.import_profile(str(entity_db), str(profile_path))
    assert imported["ok"] is True
    result, runtime = execute_source(
        SRC,
        "run",
        [str(entity_db), str(source_db), ""],
        runtime,
    )
'''
    text = replace_exact(text, old_execute, new_execute, 1, "execute helper")

    old_bad = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=bad_provider)
    with pytest.raises(clay.StructuredFault):
        execute_source(SRC, "run", [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), str(profile_path), ""], runtime)
'''
    new_bad = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=bad_provider)
    imported = runtime.import_profile(str(tmp_path / "entity.db"), str(profile_path))
    assert imported["ok"] is True
    with pytest.raises(clay.StructuredFault):
        execute_source(SRC, "run", [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), ""], runtime)
'''
    text = replace_exact(text, old_bad, new_bad, 1, "immutable-gate adapter")

    old_missing = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=inspect)
    execute_source(SRC, "run", [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), str(profile_path), ""], runtime)
'''
    new_missing = '''    runtime = ProfilePipelineRuntime(root=tmp_path, provider_override=inspect)
    imported = runtime.import_profile(str(tmp_path / "entity.db"), str(profile_path))
    assert imported["ok"] is True
    execute_source(SRC, "run", [str(tmp_path / "entity.db"), str(tmp_path / "source.db"), ""], runtime)
'''
    text = replace_exact(text, old_missing, new_missing, 1, "missing-source adapter")

    if 'str(profile_path), ""' in text:
        raise SystemExit("legacy fourth profile_path run argument remains")
    if text.count("runtime.import_profile(") < 3:
        raise SystemExit("DB-resident profile setup is not bound at all migrated call sites")

    changed = text != original
    if changed:
        TEST.write_text(text, encoding="utf-8")
    print(json.dumps({
        "changed": changed,
        "test": str(TEST.relative_to(ROOT)),
        "legacy_fourth_arg_remaining": 'str(profile_path), ""' in text,
        "db_profile_import_sites": text.count("runtime.import_profile("),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
