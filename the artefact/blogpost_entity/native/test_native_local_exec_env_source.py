#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PART02 = HERE / "mini_entity_part02.inc"


class NativeLocalExecEnvironmentSourceTests(unittest.TestCase):
    @classmethod
    def local_exec_source(cls) -> str:
        text = PART02.read_text(encoding="utf-8")
        start = text.index("static char *run_local_exec")
        end = text.index("typedef struct {buf_t b;} curl_buf", start)
        return text[start:end]

    def test_local_exec_starts_from_empty_environment(self) -> None:
        src = self.local_exec_source()
        self.assertIn('child_argv[ci++]="/usr/bin/env"', src)
        self.assertIn('child_argv[ci++]="-i"', src)
        self.assertIn('execv("/usr/bin/env",child_argv)', src)
        self.assertNotIn("execvp(argv[0],argv)", src)
        self.assertNotIn("getenv(", src)

    def test_only_bounded_nonsecret_environment_is_reintroduced(self) -> None:
        src = self.local_exec_source()
        expected = {
            "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
            "HOME=/tmp",
            "TMPDIR=/tmp",
            "LANG=C.UTF-8",
            "TZ=UTC",
        }
        for item in expected:
            self.assertIn(f'child_argv[ci++]="{item}"', src)
        for forbidden in (
            "TOGETHER_API_KEY",
            "OPENAI_API_KEY",
            "MISTRAL_API_KEY",
            "ANTHROPIC_API_KEY",
            "GITHUB_TOKEN",
            "AWS_SECRET_ACCESS_KEY",
        ):
            self.assertNotIn(forbidden, src)

    def test_runner_contract_is_preserved_without_shell(self) -> None:
        src = self.local_exec_source()
        for placeholder in (
            "{{MODEL_PATH}}",
            "{{PROMPT_FILE}}",
            "{{MAX_TOKENS}}",
            "{{TEMPERATURE}}",
        ):
            self.assertIn(placeholder, src)
        self.assertNotIn("system(", src)
        self.assertNotIn("popen(", src)


if __name__ == "__main__":
    unittest.main()
