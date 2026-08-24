#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class FreeOnlyProviderRevocation1463(unittest.TestCase):
    def test_running_swarm_is_bound_to_spawn_admission_digest(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn('SWARM_ADMISSION_DIGEST_FILE="$STATE_DIR/swarm.provider-admission.sha256"', text)
        self.assertIn("provider_admission_digest(){", text)
        self.assertIn("from free_provider_admission import admission_snapshot", text)
        self.assertIn("CLAY_SWARM_PROVIDER_ADMISSION_SHA256=\"$admission_digest\"", text)

        start = text.split("start_go_swarm_if_admitted(){", 1)[1].split("\n}\n\nterminate_go_swarm_processes", 1)[0]
        self.assertIn('admission_digest="$(provider_admission_digest)"', start)
        self.assertIn('mv "$SWARM_ADMISSION_DIGEST_FILE.tmp" "$SWARM_ADMISSION_DIGEST_FILE"', start)
        self.assertLess(start.index("provider_admission_digest"), start.index("nohup python3"))

    def test_admission_change_revokes_even_when_another_provider_remains_admitted(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("stop_unadmitted_go_swarm(){", 1)[1].split(
            "\n}\n\nwhile (( $(date +%s) < DEADLINE )); do", 1
        )[0]

        # The digest mismatch is an independent revoke condition. It must not be
        # nested underneath `! has_admitted_provider_key`, because provider B may
        # remain admitted while provider A is revoked.
        self.assertIn('spawn_digest="$(cat "$SWARM_ADMISSION_DIGEST_FILE" 2>/dev/null || true)"', body)
        self.assertIn('[[ -z "$spawn_digest" || "$spawn_digest" != "$current_digest" ]]', body)
        self.assertIn("|| ! has_admitted_provider_key", body)
        self.assertIn("terminate_go_swarm_processes", body)
        self.assertLess(body.index('"$spawn_digest" != "$current_digest"'), body.index("has_admitted_provider_key"))

    def test_missing_spawn_provenance_fails_closed_and_termination_waits_for_death(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("stop_unadmitted_go_swarm(){", 1)[1].split(
            "\n}\n\nwhile (( $(date +%s) < DEADLINE )); do", 1
        )[0]
        terminate = text.split("terminate_go_swarm_processes(){", 1)[1].split(
            "\n}\n\nstop_unadmitted_go_swarm", 1
        )[0]

        self.assertIn('-z "$spawn_digest"', body)
        self.assertIn("kill -TERM", terminate)
        self.assertIn("kill -KILL", terminate)
        self.assertIn("wait \"$pid\"", terminate)
        self.assertIn("return 1", terminate)

    def test_shell_syntax_remains_valid(self):
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
