import hashlib
import importlib.util
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("build_native_bound", HERE / "build_native_bound.py")
MOD = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MOD)


class SourceClosureTests(unittest.TestCase):
    def test_recursive_local_include_closure_is_bound(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "mini_entity.c"
            p0 = root / "part0.inc"
            p1 = root / "part1.inc"
            entry.write_text('#include "part0.inc"\nint main(void){return answer();}\n', encoding="utf-8")
            p0.write_text('#include "part1.inc"\nstatic int answer(void){return VALUE;}\n', encoding="utf-8")
            p1.write_text('#define VALUE 0\n', encoding="utf-8")

            closure = MOD.source_closure(entry)
            self.assertEqual(closure["file_count"], 3)
            self.assertEqual(
                [item["path"] for item in closure["files"]],
                ["mini_entity.c", "part0.inc", "part1.inc"],
            )

    def test_include_mutation_changes_closure_identity_while_entry_hash_is_unchanged(self):
        # Go-cycle discriminator: the old wrapper would miss this mutation.
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            entry = root / "mini_entity.c"
            part = root / "mini_entity_part00.inc"
            entry.write_text('#include "mini_entity_part00.inc"\n', encoding="utf-8")
            part.write_text('static int x = 1;\n', encoding="utf-8")

            entry_before = hashlib.sha256(entry.read_bytes()).hexdigest()
            closure_before = MOD.source_closure(entry)["sha256"]
            part.write_text('static int x = 2;\n', encoding="utf-8")
            entry_after = hashlib.sha256(entry.read_bytes()).hexdigest()
            closure_after = MOD.source_closure(entry)["sha256"]

            self.assertEqual(entry_before, entry_after)
            self.assertNotEqual(closure_before, closure_after)

    def test_quoted_include_cannot_escape_source_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            src = root / "src"
            src.mkdir()
            outside = root / "outside.inc"
            outside.write_text("static int x;\n", encoding="utf-8")
            entry = src / "mini_entity.c"
            entry.write_text('#include "../outside.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SOURCE_INCLUDE_OUTSIDE_ROOT"):
                MOD.source_closure(entry)

    def test_missing_quoted_include_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            entry = Path(tmp) / "mini_entity.c"
            entry.write_text('#include "missing.inc"\n', encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "SOURCE_INCLUDE_MISSING"):
                MOD.source_closure(entry)


if __name__ == "__main__":
    unittest.main()
