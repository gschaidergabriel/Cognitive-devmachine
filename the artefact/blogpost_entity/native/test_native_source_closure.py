from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC is not None and SPEC.loader is not None
build_native_bound = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_native_bound)


def test_include_mutation_changes_source_identity_without_changing_entry_bytes(tmp_path: Path):
    entry = tmp_path / "mini_entity.c"
    part = tmp_path / "mini_entity_part00.inc"
    entry.write_text('#include "mini_entity_part00.inc"\n', encoding="utf-8")
    part.write_text("int answer(void) { return 1; }\n", encoding="utf-8")

    entry_sha_before = build_native_bound.sha256_file(entry)
    first = build_native_bound.source_closure(entry)

    part.write_text("int answer(void) { return 2; }\n", encoding="utf-8")
    entry_sha_after = build_native_bound.sha256_file(entry)
    second = build_native_bound.source_closure(entry)

    assert entry_sha_before == entry_sha_after
    assert first["sha256"] != second["sha256"]
    assert [item["path"] for item in first["files"]] == ["mini_entity.c", "mini_entity_part00.inc"]


def test_transitive_local_includes_are_bound_once(tmp_path: Path):
    entry = tmp_path / "mini_entity.c"
    a = tmp_path / "a.inc"
    b = tmp_path / "b.inc"
    entry.write_text('#include "a.inc"\n#include "b.inc"\n', encoding="utf-8")
    a.write_text('#include "b.inc"\nint a(void) { return 1; }\n', encoding="utf-8")
    b.write_text("int b(void) { return 2; }\n", encoding="utf-8")

    closure = build_native_bound.source_closure(entry)

    assert [item["path"] for item in closure["files"]] == ["a.inc", "b.inc", "mini_entity.c"]
    assert len(closure["files"]) == 3


def test_missing_local_include_fails_closed(tmp_path: Path):
    entry = tmp_path / "mini_entity.c"
    entry.write_text('#include "missing.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="LOCAL_INCLUDE_MISSING"):
        build_native_bound.source_closure(entry)


def test_local_include_cannot_escape_source_root(tmp_path: Path):
    root = tmp_path / "native"
    root.mkdir()
    outside = tmp_path / "outside.inc"
    outside.write_text("int x;\n", encoding="utf-8")
    entry = root / "mini_entity.c"
    entry.write_text('#include "../outside.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="LOCAL_INCLUDE_ESCAPES_ROOT"):
        build_native_bound.source_closure(entry)


def test_symlinked_local_source_fails_closed(tmp_path: Path):
    entry = tmp_path / "mini_entity.c"
    target = tmp_path / "target.inc"
    link = tmp_path / "part.inc"
    target.write_text("int x;\n", encoding="utf-8")
    try:
        link.symlink_to(target.name)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks unavailable")
    entry.write_text('#include "part.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="LOCAL_SOURCE_SYMLINK_FORBIDDEN"):
        build_native_bound.source_closure(entry)
