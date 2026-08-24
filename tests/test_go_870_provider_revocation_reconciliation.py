#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


class Go870ProviderRevocationReconciliation(unittest.TestCase):
    def test_running_swarm_is_bound_to_spawn_admission_digest(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("SWARM_ADMISSION_DIGEST_FILE", text)
        self.assertIn("current_provider_admission_digest", text)
        self.assertIn('python3 "$ADMISSION_TOOL" --json', text)
        self.assertIn("sha256sum", text)
        self.assertIn('printf \'%s\\n\' "$admission_digest" >"$SWARM_ADMISSION_DIGEST_FILE"', text)

        reconcile = text.split("stop_unadmitted_go_swarm(){", 1)[1].split("\n}\n\nstart_go_swarm_if_admitted", 1)[0]
        self.assertIn('[[ "$previous_digest" != "$current_digest" ]]', reconcile)
        self.assertIn("PROVIDER_ADMISSION_CHANGED_OR_SPAWN_PROVENANCE_UNKNOWN", reconcile)
        self.assertIn("CURRENT_PROVIDER_ADMISSION_UNAVAILABLE", reconcile)
        self.assertIn("NO_CURRENT_ADMITTED_PROVIDER_CREDENTIAL", reconcile)

    def test_partial_revocation_cannot_be_masked_by_another_provider(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        reconcile = text.split("stop_unadmitted_go_swarm(){", 1)[1].split("\n}\nstart_go_swarm_if_admitted", 1)[0]
        no_key_check = reconcile.index("if ! has_admitted_provider_key; then")
        digest_drift_check = reconcile.index('[[ "$previous_digest" != "$current_digest" ]]')
        self.assertLess(no_key_check, digest_drift_check)
        # The digest drift branch is independent of has_admitted_provider_key being false,
        # so A revoked + B still admitted/credentialed still terminates the stale process.
        self.assertIn("terminate_go_swarm", reconcile[digest_drift_check:])

    def test_reconciliation_precedes_secret_reload_and_child_start(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        loop = text[text.index("while (( $(date +%s) < DEADLINE )); do"):]
        clear = loop.index("clear_unadmitted_provider_secret_env")
        reconcile = loop.index("stop_unadmitted_go_swarm")
        load = loop.index("load_admitted_secret_sources")
        start = loop.index("start_go_swarm_if_admitted")
        self.assertLess(clear, reconcile)
        self.assertLess(reconcile, load)
        self.assertLess(load, start)

    def test_termination_is_bounded_fail_closed_and_receipted(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        terminate = text.split("terminate_go_swarm(){", 1)[1].split("\n}\n\n# Reconcile", 1)[0]
        self.assertIn('kill -TERM "$pid"', terminate)
        self.assertIn('kill -KILL "$pid"', terminate)
        self.assertIn("write_provider_revocation_receipt", terminate)
        self.assertIn("FREE_ONLY_PROVIDER_REVOCATION_RECEIPT/v1", text)
        self.assertIn("credential_values_observed':False", text)
        self.assertIn("SOURCE_GATE_ONLY_NOT_RUNTIME_MEASURED", text)

    def test_spawn_race_rechecks_admission_and_shell_is_valid(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        start = text.split("start_go_swarm_if_admitted(){", 1)[1].split("\n}\n\nwhile ((", 1)[0]
        self.assertIn("post_spawn_digest", start)
        self.assertIn("PROVIDER_ADMISSION_CHANGED_DURING_SPAWN", start)
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
