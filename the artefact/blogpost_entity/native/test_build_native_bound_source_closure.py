#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).with_name("build_native_bound.py")
SPEC = importlib.util.spec_from_file_location("build_native_bound", MODULE_PATH)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)


class SourceClosureTests(unittest.TestCase):
    def test_include_mutation_changes_closure_while_entry_sha_stays_same(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text('#include "part.inc"\nint main(void){return VALUE;}\n', encoding="utf-8")
            part.write_text("#define VALUE 0\n", encoding="utf-8")

            entry_sha_before = hashlib.sha256(entry.read_bytes()).hexdigest()
            items_before, closure_before = BUILD.local_source_closure(entry)

            part.write_text("#define VALUE 1\n", encoding="utf-8")
            entry_sha_after = hashlib.sha256(entry.read_bytes()).hexdigest()
            items_after, closure_after = BUILD.local_source_closure(entry)

            self.assertEqual(entry_sha_before, entry_sha_after)
            self.assertNotEqual(closure_before, closure_after)
            self.assertEqual([item["path"] for item in items_before], ["mini_entity.c", "part.inc"])
            self.assertEqual([item["path"] for item in items_after], ["mini_entity.c", "part.inc"])

    def test_include_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            outer = Path(tmp_text)
            root = outer / "native"
            root.mkdir()
            entry = root / "mini_entity.c"
            escaped = outer / "escape.inc"
            escaped.write_text("#define VALUE 0\n", encoding="utf-8")
            entry.write_text('#include "../escape.inc"\nint main(void){return VALUE;}\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT"):
                BUILD.local_source_closure(entry)

    def test_missing_local_include_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            entry = Path(tmp_text) / "mini_entity.c"
            entry.write_text('#include "missing.inc"\nint main(void){return 0;}\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_SOURCE_MISSING"):
                BUILD.local_source_closure(entry)


if __name__ == "__main__":
    unittest.main()
