from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


MODULE_PATH = Path(__file__).with_name("build_native_bound.py")
spec = importlib.util.spec_from_file_location("build_native_bound", MODULE_PATH)
assert spec and spec.loader
build_native_bound = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build_native_bound)


def test_source_bundle_changes_when_included_bytes_change(tmp_path: Path) -> None:
    source = tmp_path / "mini_entity.c"
    part = tmp_path / "mini_entity_part00.inc"
    source.write_text('#include "mini_entity_part00.inc"\n', encoding="utf-8")
    part.write_text("int value(void){return 1;}\n", encoding="utf-8")

    wrapper_before = build_native_bound.sha256_file(source)
    bundle_before, members_before = build_native_bound.source_bundle_identity(source)

    part.write_text("int value(void){return 2;}\n", encoding="utf-8")

    wrapper_after = build_native_bound.sha256_file(source)
    bundle_after, members_after = build_native_bound.source_bundle_identity(source)

    assert wrapper_before == wrapper_after
    assert bundle_before != bundle_after
    assert [item["path"] for item in members_before] == ["mini_entity.c", "mini_entity_part00.inc"]
    assert [item["path"] for item in members_after] == ["mini_entity.c", "mini_entity_part00.inc"]
    assert members_before[1]["sha256"] != members_after[1]["sha256"]


def test_source_bundle_recurses_through_local_include_closure(tmp_path: Path) -> None:
    source = tmp_path / "mini_entity.c"
    first = tmp_path / "first.inc"
    second = tmp_path / "second.inc"
    source.write_text('#include "first.inc"\n', encoding="utf-8")
    first.write_text('#include "second.inc"\n', encoding="utf-8")
    second.write_text("static const int sentinel = 7;\n", encoding="utf-8")

    _, members = build_native_bound.source_bundle_identity(source)

    assert [item["path"] for item in members] == ["first.inc", "mini_entity.c", "second.inc"]


def test_source_bundle_rejects_out_of_root_include(tmp_path: Path) -> None:
    root = tmp_path / "native"
    root.mkdir()
    outside = tmp_path / "outside.inc"
    outside.write_text("int outside;\n", encoding="utf-8")
    source = root / "mini_entity.c"
    source.write_text('#include "../outside.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT"):
        build_native_bound.source_bundle_identity(source)


def test_source_bundle_rejects_symlink_substitution(tmp_path: Path) -> None:
    source = tmp_path / "mini_entity.c"
    real = tmp_path / "real.inc"
    link = tmp_path / "part.inc"
    real.write_text("int real;\n", encoding="utf-8")
    try:
        link.symlink_to(real.name)
    except OSError:
        pytest.skip("symlink creation unavailable")
    source.write_text('#include "part.inc"\n', encoding="utf-8")

    with pytest.raises(RuntimeError, match="LOCAL_SOURCE_SYMLINK_FORBIDDEN"):
        build_native_bound.source_bundle_identity(source)
