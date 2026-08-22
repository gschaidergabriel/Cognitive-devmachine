#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_native_bound.py")
SPEC = importlib.util.spec_from_file_location("build_native_bound", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class SourceClosureTests(unittest.TestCase):
    def test_transitive_local_include_change_changes_source_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part0 = root / "part0.inc"
            part1 = root / "part1.inc"
            entry.write_text('#include "part0.inc"\nint main(void) { return VALUE; }\n', encoding="utf-8")
            part0.write_text('#include "part1.inc"\n', encoding="utf-8")
            part1.write_text('#define VALUE 0\n', encoding="utf-8")

            entry_sha_before = subject.sha256_file(entry)
            closure_before = subject.source_closure(entry)
            self.assertEqual(
                [item["path"] for item in closure_before["files"]],
                ["mini_entity.c", "part0.inc", "part1.inc"],
            )

            part1.write_text('#define VALUE 1\n', encoding="utf-8")
            entry_sha_after = subject.sha256_file(entry)
            closure_after = subject.source_closure(entry)

            self.assertEqual(entry_sha_before, entry_sha_after)
            self.assertNotEqual(closure_before["sha256"], closure_after["sha256"])

    def test_dynamic_include_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            entry = Path(tmp_text) / "mini_entity.c"
            entry.write_text('#define PICK "part.inc"\n#include PICK\n', encoding="utf-8")
            (entry.parent / "part.inc").write_text("/* hidden */\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "DYNAMIC_OR_UNBOUND_INCLUDE"):
                subject.source_closure(entry)

    def test_local_include_cannot_escape_source_root(self) -> None:
        with tempfile.TemporaryDirectory() as parent_text:
            parent = Path(parent_text)
            root = parent / "native"
            root.mkdir()
            entry = root / "mini_entity.c"
            outside = parent / "outside.inc"
            outside.write_text("/* outside */\n", encoding="utf-8")
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT"):
                subject.source_closure(entry)

    def test_local_include_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            target = root / "real.inc"
            alias = root / "alias.inc"
            target.write_text("static int real = 1;\n", encoding="utf-8")
            alias.symlink_to(target.name)
            entry.write_text('#include "alias.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_SOURCE_SYMLINK_FORBIDDEN"):
                subject.source_closure(entry)

    def test_entry_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            target = root / "real.c"
            alias = root / "mini_entity.c"
            target.write_text("int main(void) { return 0; }\n", encoding="utf-8")
            alias.symlink_to(target.name)
            with self.assertRaisesRegex(RuntimeError, "LOCAL_SOURCE_SYMLINK_FORBIDDEN"):
                subject.source_closure(alias)


if __name__ == "__main__":
    unittest.main()
