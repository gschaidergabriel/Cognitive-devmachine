#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC and SPEC.loader
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def test_local_include_mutation_changes_source_closure_identity(tmp_path: Path) -> None:
    entry = tmp_path / "mini_entity.c"
    part = tmp_path / "part.inc"
    entry.write_text('#include "part.inc"\nint main(void){return value();}\n', encoding="utf-8")
    part.write_text("static int value(void){return 1;}\n", encoding="utf-8")

    entry_sha_before = MOD.sha256_file(entry)
    first = MOD.local_source_closure(entry)
    assert [item["path"] for item in first["files"]] == ["mini_entity.c", "part.inc"]

    part.write_text("static int value(void){return 2;}\n", encoding="utf-8")
    entry_sha_after = MOD.sha256_file(entry)
    second = MOD.local_source_closure(entry)

    assert entry_sha_after == entry_sha_before
    assert second["sha256"] != first["sha256"]
    assert next(item for item in second["files"] if item["path"] == "part.inc")["sha256"] != next(
        item for item in first["files"] if item["path"] == "part.inc"
    )["sha256"]


def test_nested_local_include_is_bound_transitively(tmp_path: Path) -> None:
    entry = tmp_path / "mini_entity.c"
    a = tmp_path / "a.inc"
    b = tmp_path / "b.inc"
    entry.write_text('#include "a.inc"\n', encoding="utf-8")
    a.write_text('#include "b.inc"\n', encoding="utf-8")
    b.write_text("static const int k = 1;\n", encoding="utf-8")

    closure = MOD.local_source_closure(entry)
    assert [item["path"] for item in closure["files"]] == ["a.inc", "b.inc", "mini_entity.c"]


def test_local_include_escape_fails_closed(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.inc"
    outside.write_text("static const int x = 1;\n", encoding="utf-8")
    entry = root / "mini_entity.c"
    entry.write_text('#include "../outside.inc"\n', encoding="utf-8")

    try:
        MOD.local_source_closure(entry)
    except RuntimeError as exc:
        assert str(exc).startswith("LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT:")
    else:
        raise AssertionError("source-root escape was not rejected")
