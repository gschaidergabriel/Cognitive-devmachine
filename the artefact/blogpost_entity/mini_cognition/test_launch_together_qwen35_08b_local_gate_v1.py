#!/usr/bin/env python3
import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "launch08_local_gate", HERE / "launch_together_qwen35_08b_v1.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LocalGateTests(unittest.TestCase):
    def test_launcher_uses_existing_canonical_v2_validator(self):
        self.assertTrue((HERE / "validate_corpus_v2.py").is_file())
        self.assertFalse((HERE / "validate_sft_v2.py").exists())
        with patch.object(MODULE.subprocess, "run") as run:
            MODULE.local_checks()
        self.assertEqual(run.call_count, 2)
        self.assertEqual(
            run.call_args_list[0].args[0],
            [sys.executable, str(HERE / "generate_sft_v2.py")],
        )
        self.assertTrue(run.call_args_list[0].kwargs["check"])
        self.assertEqual(
            run.call_args_list[1].args[0],
            [
                sys.executable,
                str(HERE / "validate_corpus_v2.py"),
                str(MODULE.TRAIN),
                str(MODULE.VALID),
            ],
        )
        self.assertTrue(run.call_args_list[1].kwargs["check"])


if __name__ == "__main__":
    unittest.main()
