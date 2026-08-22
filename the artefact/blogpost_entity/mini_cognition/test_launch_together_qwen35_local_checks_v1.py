#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "launch08_local_checks", HERE / "launch_together_qwen35_08b_v1.py"
)
LAUNCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCH)


class LocalChecksTests(unittest.TestCase):
    def test_local_checks_use_canonical_v2_corpus_gate(self):
        canonical = HERE / "validate_corpus_v2.py"
        stale = HERE / "validate_sft_v2.py"
        self.assertTrue(canonical.is_file())
        self.assertFalse(stale.exists())

        with mock.patch.object(LAUNCH.subprocess, "run") as run:
            LAUNCH.local_checks()

        self.assertEqual(
            run.call_args_list,
            [
                mock.call(
                    [sys.executable, str(HERE / "generate_sft_v2.py")],
                    check=True,
                ),
                mock.call(
                    [sys.executable, str(canonical), str(LAUNCH.TRAIN), str(LAUNCH.VALID)],
                    check=True,
                ),
            ],
        )


if __name__ == "__main__":
    unittest.main()
