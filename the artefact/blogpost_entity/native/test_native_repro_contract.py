from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
assert SPEC is not None and SPEC.loader is not None
build = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(build)


class SourceBundleIdentityTests(unittest.TestCase):
    def test_included_source_mutation_changes_bundle_without_changing_entry_hash(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text('#include "part.inc"\nint main(void){return VALUE;}\n', encoding="utf-8")
            part.write_text("#define VALUE 0\n", encoding="utf-8")
            entry_hash = build.sha256_file(entry)
            before = build.source_bundle_identity(entry)
            part.write_text("#define VALUE 1\n", encoding="utf-8")
            after = build.source_bundle_identity(entry)
            self.assertEqual(entry_hash, build.sha256_file(entry))
            self.assertNotEqual(before["sha256"], after["sha256"])

    def test_recursive_local_include_is_bound(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "mini_entity.c").write_text('#include "a.inc"\n', encoding="utf-8")
            (root / "a.inc").write_text('#include "b.inc"\n', encoding="utf-8")
            (root / "b.inc").write_text("#define B 1\n", encoding="utf-8")
            bundle = build.source_bundle_identity(root / "mini_entity.c")
            self.assertEqual(
                [item["path"] for item in bundle["inputs"]],
                ["a.inc", "b.inc", "mini_entity.c"],
            )

    def test_missing_local_include_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            entry = root / "mini_entity.c"
            entry.write_text('#include "missing.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_MISSING"):
                build.source_bundle_identity(entry)

    def test_local_include_escape_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            parent = Path(td)
            root = parent / "native"
            root.mkdir()
            (parent / "outside.inc").write_text("#define X 1\n", encoding="utf-8")
            entry = root / "mini_entity.c"
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "LOCAL_INCLUDE_ESCAPES_SOURCE_ROOT"):
                build.source_bundle_identity(entry)

    def test_current_native_bundle_contains_all_split_units(self) -> None:
        bundle = build.source_bundle_identity(HERE / "mini_entity.c")
        self.assertEqual(
            [item["path"] for item in bundle["inputs"]],
            [
                "mini_entity.c",
                "mini_entity_part00.inc",
                "mini_entity_part01.inc",
                "mini_entity_part02.inc",
                "mini_entity_part03.inc",
                "mini_entity_part04.inc",
            ],
        )


class QuietContractSourceTests(unittest.TestCase):
    def test_verified_empty_short_circuits_before_inference(self) -> None:
        text = (HERE / "mini_entity_part04.inc").read_text(encoding="utf-8")
        quiet = text.index("if(packet.n==0)")
        inference = text.index("model_output(profile,db")
        self.assertLess(quiet, inference)
        self.assertIn('json_object_object_add(r,"quiet",json_object_new_boolean(1))', text)
        self.assertIn('json_object_object_add(r,"generation",json_object_new_int64(observed))', text)


if __name__ == "__main__":
    unittest.main()
