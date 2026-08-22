from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


class LocalExecEnvironmentFenceSourceTests(unittest.TestCase):
    def test_local_exec_starts_from_empty_bounded_environment(self) -> None:
        source = (HERE / "mini_entity_part02.inc").read_text(encoding="utf-8")
        start = source.index("static char *run_local_exec(")
        end = source.index("typedef struct {buf_t b;} curl_buf;", start)
        fn = source[start:end]

        self.assertIn('child_argv[ci++]="/usr/bin/env";', fn)
        self.assertIn('child_argv[ci++]="-i";', fn)
        self.assertIn('PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin', fn)
        self.assertIn('HOME=/tmp', fn)
        self.assertIn('TMPDIR=/tmp', fn)
        self.assertIn('LANG=C.UTF-8', fn)
        self.assertIn('TZ=UTC', fn)
        self.assertIn('execv("/usr/bin/env",child_argv);', fn)
        self.assertNotIn("execvp(", fn)
        self.assertNotIn("environ", fn)


if __name__ == "__main__":
    unittest.main()
