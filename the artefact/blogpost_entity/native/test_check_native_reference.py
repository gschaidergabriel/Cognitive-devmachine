import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CHECKER = HERE / "check_native_reference.py"
RECEIPT = HERE.parent / "receipts" / "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"

sys.path.insert(0, str(HERE))
import check_native_reference as checker  # noqa: E402
from build_native_bound import source_closure  # noqa: E402


class NativeReferenceCheckerTests(unittest.TestCase):
    def test_current_source_is_not_mislabeled_as_credited_0_6_rebuild(self):
        identity = source_closure(HERE / "mini_entity.c")
        current_version = checker.source_version(HERE, identity)
        credited_version = json.loads(RECEIPT.read_text(encoding="utf-8"))["version"]

        self.assertIsNotNone(current_version)
        self.assertNotEqual(current_version, credited_version)

        proc = subprocess.run(
            [sys.executable, str(CHECKER)],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        report = json.loads(proc.stdout)
        self.assertEqual(proc.returncode, 2)
        self.assertFalse(report["pass"])
        self.assertEqual(
            report["reproducibility"],
            "CURRENT_SOURCE_IS_DIFFERENT_VERSION_NOT_CREDITED_REBUILD",
        )
        self.assertEqual(report["source_build_binding"], "NOT_PROVEN_BY_THIS_CHECKER")
        self.assertTrue(
            any(
                item.startswith("CANONICAL_SOURCE_VERSION_DIFFERS_FROM_CREDITED_ARTIFACT")
                for item in report["errors"]
            )
        )

    def test_multiple_source_version_labels_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "a.inc").write_text(
                '#define MINI_VERSION "mini-entity/a"\n', encoding="utf-8"
            )
            (root / "b.inc").write_text(
                '#define MINI_VERSION "mini-entity/b"\n', encoding="utf-8"
            )
            identity = {"files": [{"path": "a.inc"}, {"path": "b.inc"}]}

            with self.assertRaisesRegex(RuntimeError, "MULTIPLE_MINI_VERSION_LABELS"):
                checker.source_version(root, identity)


if __name__ == "__main__":
    unittest.main()
