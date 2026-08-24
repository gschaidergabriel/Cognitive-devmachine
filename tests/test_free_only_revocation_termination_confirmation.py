#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


def extract_function(text: str, name: str) -> str:
    start = text.index(f"{name}(){{")
    end = text.index("\n}\n", start) + len("\n}\n")
    return text[start:end]


class FreeOnlyRevocationTerminationConfirmation(unittest.TestCase):
    def test_revocation_waits_for_confirmed_termination_before_binding_cleanup(self) -> None:
        text = SUPERVISOR.read_text(encoding="utf-8")
        terminate = extract_function(text, "terminate_go_swarm_processes")
        stop = extract_function(text, "stop_unadmitted_go_swarm")

        self.assertIn("kill -TERM", terminate)
        self.assertIn("command kill -0", terminate)
        self.assertIn("kill -KILL", terminate)
        self.assertIn("return 1", terminate)
        self.assertIn("terminate_go_swarm_processes", stop)
        self.assertLess(stop.index("terminate_go_swarm_processes"), stop.index("rm -f"))

    def test_term_ignoring_stale_child_is_killed_before_helper_returns(self) -> None:
        child = subprocess.Popen(
            [
                sys.executable,
                "-c",
                "import signal,time; signal.signal(signal.SIGTERM, signal.SIG_IGN); time.sleep(60)",
            ]
        )
        try:
            time.sleep(0.1)
            text = SUPERVISOR.read_text(encoding="utf-8")
            terminate = extract_function(text, "terminate_go_swarm_processes")
            with tempfile.TemporaryDirectory() as td:
                script = Path(td) / "fixture.sh"
                script.write_text(
                    textwrap.dedent(
                        f"""
                        #!/usr/bin/env bash
                        set -Eeuo pipefail
                        pgrep(){{ printf '%s\\n' {child.pid}; }}
                        {terminate}
                        terminate_go_swarm_processes
                        command kill -0 {child.pid} 2>/dev/null && exit 91 || exit 0
                        """
                    ).strip()
                    + "\n",
                    encoding="utf-8",
                )
                proc = subprocess.run(["bash", str(script)], capture_output=True, text=True, timeout=5)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            child.wait(timeout=2)
            self.assertEqual(child.returncode, -signal.SIGKILL)
        finally:
            if child.poll() is None:
                child.kill()
            try:
                child.wait(timeout=2)
            except subprocess.TimeoutExpired:
                pass

    def test_shell_syntax(self) -> None:
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
