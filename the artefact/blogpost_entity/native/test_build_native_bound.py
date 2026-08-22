#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

# Keep the canonical exact-repro workflow entrypoint while reusing the already-admitted
# source-closure falsifiers instead of duplicating their implementation.
from test_build_native_bound_source_closure import SourceClosureTests  # noqa: F401,E402

MODULE_PATH = HERE / "build_native_bound.py"
SPEC = importlib.util.spec_from_file_location("build_native_bound_version", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
subject = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(subject)


class VersionBindingTests(unittest.TestCase):
    def test_canonical_source_declares_0_7_version(self) -> None:
        source = HERE / "mini_entity.c"
        closure = subject.source_closure(source)
        self.assertEqual(len(closure["files"]), 6)
        self.assertEqual(subject.source_version_label(source, closure), "mini-entity/0.7.0-dev1")

    def test_wrong_requested_version_fails_before_build_output(self) -> None:
        source = HERE / "mini_entity.c"
        with tempfile.TemporaryDirectory() as tmp_text:
            tmp = Path(tmp_text)
            output = tmp / "must-not-exist.clay"
            receipt = tmp / "must-not-exist.json"
            proc = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_PATH),
                    "--source",
                    str(source),
                    "--output",
                    str(output),
                    "--receipt",
                    str(receipt),
                    "--version-label",
                    "mini-entity/0.6.0",
                    "--source-date-epoch",
                    "0",
                    "--repeat",
                    "2",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("VERSION_LABEL_SOURCE_MISMATCH", proc.stderr)
            self.assertIn("requested=mini-entity/0.6.0", proc.stderr)
            self.assertIn("source=mini-entity/0.7.0-dev1", proc.stderr)
            self.assertFalse(output.exists())
            self.assertFalse(receipt.exists())

    def test_ambiguous_source_version_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_text:
            root = Path(tmp_text)
            entry = root / "mini_entity.c"
            part = root / "part.inc"
            entry.write_text(
                '#define MINI_VERSION "mini-entity/a"\n#include "part.inc"\n',
                encoding="utf-8",
            )
            part.write_text('#define MINI_VERSION "mini-entity/b"\n', encoding="utf-8")
            closure = subject.source_closure(entry)
            with self.assertRaisesRegex(RuntimeError, "SOURCE_VERSION_AMBIGUOUS"):
                subject.source_version_label(entry, closure)


if __name__ == "__main__":
    unittest.main()
