#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

from check_native_reference import classify_source
from native_source_closure import (
    declared_mini_version,
    describe_source_closure,
    source_closure_sha256,
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class NativeSourceClosureTests(unittest.TestCase):
    def test_included_byte_change_changes_closure_not_entry_hash(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text('#include "part.inc"\n', encoding="utf-8")
            part.write_text('#define MINI_VERSION "mini-entity/test"\nint x=1;\n', encoding="utf-8")

            entry_before = sha256(entry)
            closure_before = source_closure_sha256(describe_source_closure(entry))
            part.write_text('#define MINI_VERSION "mini-entity/test"\nint x=2;\n', encoding="utf-8")
            entry_after = sha256(entry)
            closure_after = source_closure_sha256(describe_source_closure(entry))

            self.assertEqual(entry_before, entry_after)
            self.assertNotEqual(closure_before, closure_after)

    def test_local_include_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            base = Path(tmp_text)
            root = base / "native"
            root.mkdir()
            outside = base / "outside.inc"
            outside.write_text("int x;\n", encoding="utf-8")
            entry = root / "mini_entity.c"
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT"):
                describe_source_closure(entry)

    def test_declared_version_can_live_in_split_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text('#include "part.inc"\n', encoding="utf-8")
            part.write_text('#define MINI_VERSION "mini-entity/0.7.0-dev1"\n', encoding="utf-8")
            self.assertEqual(declared_mini_version(entry), "mini-entity/0.7.0-dev1")

    def test_historical_version_cannot_alias_newer_source(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text('#include "part.inc"\n', encoding="utf-8")
            part.write_text('#define MINI_VERSION "mini-entity/0.7.0-dev1"\n', encoding="utf-8")
            result = classify_source("mini-entity/0.6.0", {}, entry)
            self.assertEqual(result["reproducibility"], "BLOCKED_SOURCE_VERSION_MISMATCH")
            self.assertIn("expected=mini-entity/0.6.0", result["error"])

    def test_matching_version_without_credited_closure_still_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            entry.write_text('#define MINI_VERSION "mini-entity/0.6.0"\n', encoding="utf-8")
            result = classify_source("mini-entity/0.6.0", {}, entry)
            self.assertEqual(
                result["reproducibility"],
                "BLOCKED_CREDITED_SOURCE_CLOSURE_UNRECORDED",
            )

    def test_matching_credited_closure_is_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            entry.write_text('#define MINI_VERSION "mini-entity/0.7.0"\n', encoding="utf-8")
            closure_sha = source_closure_sha256(describe_source_closure(entry))
            receipt = {"build_definition": {"source_closure": {"sha256": closure_sha}}}
            result = classify_source("mini-entity/0.7.0", receipt, entry)
            self.assertEqual(result["reproducibility"], "SOURCE_CLOSURE_BOUND")
            self.assertIsNone(result["error"])


if __name__ == "__main__":
    unittest.main()
