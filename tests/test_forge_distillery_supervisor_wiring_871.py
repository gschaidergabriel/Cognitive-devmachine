from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools" / "run_24h_entityos_swarm_supervisor.sh"


class ForgeDistillerySupervisorWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SUPERVISOR.read_text(encoding="utf-8")

    def test_bridge_uses_exact_existing_artifact_paths(self):
        self.assertIn('local evaluations="$STATE_DIR/forge/architecture_delta_evaluations.jsonl"', self.text)
        self.assertIn('local db="$STATE_DIR/distillery/distillery.sqlite3"', self.text)
        self.assertIn('ingest_forge_accepts_into_distillery.py', self.text)

    def test_bridge_runs_after_both_producers_are_started(self):
        loop = self.text.index('while (( $(date +%s) < DEADLINE )); do')
        tail = self.text[loop:]
        dist = tail.index('  start_distillery\n')
        forge = tail.index('  start_forge\n')
        bridge = tail.index('  run_forge_distillery_bridge\n')
        self.assertLess(dist, bridge)
        self.assertLess(forge, bridge)

    def test_bridge_failure_cannot_abort_supervisor_loop(self):
        self.assertIn('if python3 "$x" --forge-evaluations "$evaluations" --distillery-db "$db"', self.text)
        self.assertIn('else\n    rm -f "$tmp"\n  fi', self.text)

    def test_status_surfaces_latest_bridge_result(self):
        self.assertIn("'forge_distillery_bridge':load_json('$FORGE_DISTILLERY_STATUS')", self.text)

    def test_no_new_provider_or_paid_route_is_introduced(self):
        fn_start = self.text.index('run_forge_distillery_bridge(){')
        fn_end = self.text.index('\n}\n\nstart_go_swarm_if_admitted', fn_start)
        fn = self.text[fn_start:fn_end]
        for forbidden in ('curl ', 'wget ', 'http://', 'https://', 'sudo ', 'docker ', 'podman '):
            self.assertNotIn(forbidden, fn)


if __name__ == "__main__":
    unittest.main()
