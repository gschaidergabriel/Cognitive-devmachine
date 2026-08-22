#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PART02 = HERE / "mini_entity_part02.inc"


class NativeLocalExecEnvironmentSourceTests(unittest.TestCase):
    def test_local_exec_uses_empty_environment_boundary(self) -> None:
        text = PART02.read_text(encoding="utf-8")
        start = text.index("static char *run_local_exec")
        end = text.index("typedef struct {buf_t b;} curl_buf", start)
        fn = text[start:end]
        self.assertIn('child_argv[ci++]="/usr/bin/env"', fn)
        self.assertIn('child_argv[ci++]="-i"', fn)
        self.assertIn('execv("/usr/bin/env",child_argv)', fn)
        self.assertNotIn('execvp(argv[0],argv)', fn)

    def test_only_bounded_non_secret_environment_is_admitted(self) -> None:
        text = PART02.read_text(encoding="utf-8")
        start = text.index("static char *run_local_exec")
        end = text.index("typedef struct {buf_t b;} curl_buf", start)
        fn = text[start:end]
        expected = (
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME=/tmp",
            "TMPDIR=/tmp",
            "LANG=C.UTF-8",
            "TZ=UTC",
        )
        for value in expected:
            self.assertIn(value, fn)
        for secret_name in ("TOGETHER_API_KEY", "OPENAI_API_KEY", "MISTRAL_API_KEY"):
            self.assertNotIn(secret_name, fn)


if __name__ == "__main__":
    unittest.main()
