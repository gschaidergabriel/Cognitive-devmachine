import importlib.util
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("build_native_bound.py")
spec = importlib.util.spec_from_file_location("build_native_bound", MODULE_PATH)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


class SourceClosureIdentityTests(unittest.TestCase):
    def test_transitive_include_mutation_changes_closure_hash_without_root_change(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "mini_entity.c"
            part = root / "part.inc"
            source.write_text(
                '#include "part.inc"\nint main(void){return answer();}\n',
                encoding="utf-8",
            )
            part.write_text('static int answer(void){return 1;}\n', encoding="utf-8")
            before = mod.source_closure_identity(source)
            root_hash_before = mod.sha256_file(source)

            part.write_text('static int answer(void){return 2;}\n', encoding="utf-8")
            after = mod.source_closure_identity(source)

            self.assertEqual(root_hash_before, mod.sha256_file(source))
            self.assertEqual(before["root_sha256"], after["root_sha256"])
            self.assertNotEqual(before["closure_sha256"], after["closure_sha256"])

    def test_nested_local_include_is_bound(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / "mini_entity.c"
            a = root / "a.inc"
            b = root / "b.inc"
            source.write_text('#include "a.inc"\n', encoding="utf-8")
            a.write_text('#include "b.inc"\n', encoding="utf-8")
            b.write_text('int x;\n', encoding="utf-8")

            identity = mod.source_closure_identity(source)

            self.assertEqual(
                [entry["path"] for entry in identity["files"]],
                ["a.inc", "b.inc", "mini_entity.c"],
            )

    def test_local_include_escape_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            root = base / "native"
            root.mkdir()
            outside = base / "outside.inc"
            source = root / "mini_entity.c"
            outside.write_text('int x;\n', encoding="utf-8")
            source.write_text('#include "../outside.inc"\n', encoding="utf-8")

            with self.assertRaisesRegex(
                RuntimeError, "LOCAL_INCLUDE_OUTSIDE_SOURCE_ROOT"
            ):
                mod.source_closure_identity(source)


if __name__ == "__main__":
    unittest.main()
