from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC and SPEC.loader
build_native_bound = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build_native_bound)


def test_source_closure_binds_quoted_includes_not_only_entry_unit(tmp_path: Path) -> None:
    entry = tmp_path / "mini_entity.c"
    part = tmp_path / "part.inc"
    entry.write_text('#include "part.inc"\nint main(void){return value();}\n', encoding="utf-8")
    part.write_text("static int value(void){return 1;}\n", encoding="utf-8")

    entry_sha_before = build_native_bound.sha256_file(entry)
    files_before, closure_before = build_native_bound.source_closure(entry)

    part.write_text("static int value(void){return 2;}\n", encoding="utf-8")

    entry_sha_after = build_native_bound.sha256_file(entry)
    files_after, closure_after = build_native_bound.source_closure(entry)

    assert entry_sha_before == entry_sha_after
    assert closure_before != closure_after
    assert [item["path"] for item in files_before] == ["mini_entity.c", "part.inc"]
    assert [item["path"] for item in files_after] == ["mini_entity.c", "part.inc"]
    assert files_before[1]["sha256"] != files_after[1]["sha256"]


def test_source_closure_rejects_include_escape(tmp_path: Path) -> None:
    root = tmp_path / "native"
    root.mkdir()
    outside = tmp_path / "outside.inc"
    outside.write_text("static int x;\n", encoding="utf-8")
    entry = root / "mini_entity.c"
    entry.write_text('#include "../outside.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="SOURCE_INCLUDE_ESCAPES_ROOT"):
        build_native_bound.source_closure(entry)


def test_source_closure_rejects_symlinked_local_source(tmp_path: Path) -> None:
    target = tmp_path / "real.inc"
    target.write_text("static int x;\n", encoding="utf-8")
    link = tmp_path / "part.inc"
    link.symlink_to(target.name)
    entry = tmp_path / "mini_entity.c"
    entry.write_text('#include "part.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="SOURCE_SYMLINK_FORBIDDEN"):
        build_native_bound.source_closure(entry)


def test_source_closure_rejects_symlinked_directory_escape(tmp_path: Path) -> None:
    root = tmp_path / "native"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "part.inc").write_text("static int x;\n", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)
    entry = root / "mini_entity.c"
    entry.write_text('#include "linked/part.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="SOURCE_SYMLINK_FORBIDDEN"):
        build_native_bound.source_closure(entry)
