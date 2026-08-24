#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class Go870ProviderRevocationTerminationRace(unittest.TestCase):
    def test_revocation_escalates_term_to_kill(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("terminate_go_swarm(){", 1)[1].split("\n}\n\nstart_go_swarm_if_admitted", 1)[0]
        self.assertIn('kill -TERM "$pid"', body)
        self.assertIn('kill -0 "$pid"', body)
        self.assertIn('kill -KILL "$pid"', body)
        self.assertLess(body.index('kill -TERM "$pid"'), body.index('kill -KILL "$pid"'))
        self.assertIn('rm -f "$SWARM_ADMISSION_BINDING_FILE"', body)

    def test_spawn_rechecks_admission_before_return(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("start_go_swarm_if_admitted(){", 1)[1].split("\n}\n\nstop_unadmitted_go_swarm", 1)[0]
        first = body.index('admission_binding="$(current_provider_admission_binding)"')
        spawn = body.index('nohup python3 "$ROOT/tools/run_24h_entityos_swarm.py"')
        second = body.index('post_spawn_binding="$(current_provider_admission_binding)"')
        terminate = body.index("terminate_go_swarm")
        self.assertLess(first, spawn)
        self.assertLess(spawn, second)
        self.assertLess(second, terminate)
        self.assertIn('[[ "$post_spawn_binding" != "$admission_binding" ]]', body)

    def test_regular_drift_reconciliation_uses_hard_termination(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        body = text.split("stop_unadmitted_go_swarm(){", 1)[1].split("\n}\n\nwhile ((", 1)[0]
        self.assertIn('[[ -n "$spawned_binding" && "$spawned_binding" == "$current_binding" ]] || must_stop=1', body)
        self.assertIn("terminate_go_swarm", body)
        self.assertNotIn("kill \"$pid\"", body)

    def test_shell_syntax_is_valid(self):
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
