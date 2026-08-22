#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class SourceClosureTests(unittest.TestCase):
    def test_included_part_mutation_changes_source_set_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "mini_entity_part00.inc"
            entry.write_text('#include "mini_entity_part00.inc"\n', encoding="utf-8")
            part.write_text("static int value = 1;\n", encoding="utf-8")

            entry_sha_before = MODULE.sha256_file(entry)
            set_before = MODULE.discover_source_closure(entry)

            part.write_text("static int value = 2;\n", encoding="utf-8")
            entry_sha_after = MODULE.sha256_file(entry)
            set_after = MODULE.discover_source_closure(entry)

            self.assertEqual(entry_sha_before, entry_sha_after)
            self.assertNotEqual(set_before["sha256"], set_after["sha256"])
            self.assertEqual(
                [item["path"] for item in set_after["members"]],
                ["mini_entity.c", "mini_entity_part00.inc"],
            )

    def test_nested_local_include_is_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            first = root / "first.inc"
            second = root / "second.inc"
            entry.write_text('#include "first.inc"\n', encoding="utf-8")
            first.write_text('#include "second.inc"\n', encoding="utf-8")
            second.write_text("static int nested = 1;\n", encoding="utf-8")

            source_set = MODULE.discover_source_closure(entry)
            self.assertEqual(
                [item["path"] for item in source_set["members"]],
                ["first.inc", "mini_entity.c", "second.inc"],
            )

    def test_include_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            parent = Path(tmp_text)
            root = parent / "native"
            root.mkdir()
            entry = root / "mini_entity.c"
            outside = parent / "outside.inc"
            outside.write_text("static int outside = 1;\n", encoding="utf-8")
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT"):
                MODULE.discover_source_closure(entry)

    def test_local_source_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            target = root / "real.inc"
            link = root / "alias.inc"
            target.write_text("static int real = 1;\n", encoding="utf-8")
            link.symlink_to(target.name)
            entry.write_text('#include "alias.inc"\n', encoding="utf-8")

            with self.assertRaisesRegex(RuntimeError, "LOCAL_SOURCE_SYMLINK_FORBIDDEN"):
                MODULE.discover_source_closure(entry)


if __name__ == "__main__":
    unittest.main()
