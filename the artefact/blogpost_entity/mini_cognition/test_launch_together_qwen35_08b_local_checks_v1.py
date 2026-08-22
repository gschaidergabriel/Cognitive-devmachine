#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location(
    "launch08", HERE / "launch_together_qwen35_08b_v1.py"
)
LAUNCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(LAUNCH)


class LocalChecksContract(unittest.TestCase):
    def test_local_checks_reference_existing_canonical_scripts(self):
        generator = HERE / "generate_sft_v2.py"
        validator = HERE / "validate_corpus_v2.py"
        self.assertTrue(generator.is_file())
        self.assertTrue(validator.is_file())

        with mock.patch.object(LAUNCH.subprocess, "run") as run:
            LAUNCH.local_checks()

        self.assertEqual(run.call_count, 2)
        self.assertEqual(
            run.call_args_list[0],
            mock.call([LAUNCH.sys.executable, str(generator)], check=True),
        )
        self.assertEqual(
            run.call_args_list[1],
            mock.call(
                [
                    LAUNCH.sys.executable,
                    str(validator),
                    str(LAUNCH.TRAIN),
                    str(LAUNCH.VALID),
                ],
                check=True,
            ),
        )


if __name__ == "__main__":
    unittest.main()
