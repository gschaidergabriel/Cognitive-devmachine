#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_24h_entityos_swarm_supervisor.sh"


def extract_function(text: str, name: str) -> str:
    start = text.index(f"{name}(){{")
    end = text.index("\n}\n", start) + len("\n}\n")
    return text[start:end]


class Go868DynamicProviderRevocation(unittest.TestCase):
    def test_supervisor_binds_child_to_validated_admission_and_checks_before_restart(self):
        text = SUPERVISOR.read_text(encoding="utf-8")
        self.assertIn("SWARM_ADMISSION_BINDING_FILE", text)
        self.assertIn("current_provider_admission_binding", text)

        start_body = extract_function(text, "start_go_swarm_if_admitted")
        self.assertIn('admission_binding="$(current_provider_admission_binding)"', start_body)
        self.assertIn('mv "${SWARM_ADMISSION_BINDING_FILE}.tmp" "$SWARM_ADMISSION_BINDING_FILE"', start_body)

        stop_body = extract_function(text, "stop_unadmitted_go_swarm")
        self.assertIn('current_binding="$(current_provider_admission_binding)"', stop_body)
        self.assertIn('"$spawned_binding" == "$current_binding"', stop_body)
        self.assertIn('must_stop=1', stop_body)
        self.assertIn('kill "$pid"', stop_body)

        loop = text[text.index("while (( $(date +%s) < DEADLINE )); do"):]
        self.assertLess(loop.index("clear_unadmitted_provider_secret_env"), loop.index("stop_unadmitted_go_swarm"))
        self.assertLess(loop.index("stop_unadmitted_go_swarm"), loop.index("start_go_swarm_if_admitted"))

    def _run_revocation_fixture(self, changed: bool) -> subprocess.CompletedProcess[str]:
        text = SUPERVISOR.read_text(encoding="utf-8")
        binding_fn = extract_function(text, "current_provider_admission_binding")
        stop_fn = extract_function(text, "stop_unadmitted_go_swarm")

        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            snapshot = tmp / "snapshot.json"
            tool = tmp / "admission_tool.py"
            kill_log = tmp / "kills.log"
            state = tmp / "state"
            state.mkdir()

            initial = {
                "schema": "ENTITYOS_HCU_FREE_PROVIDER_ADMISSION_STATUS/v1",
                "ok": True,
                "authority_epoch": "8.68",
                "admitted_free_providers": ["groq", "mistral"],
                "providers": {
                    "groq": {"admitted": True, "cost_class": "FREE", "evidence_ref": "A"},
                    "mistral": {"admitted": True, "cost_class": "FREE", "evidence_ref": "B"},
                },
            }
            revoked = {
                **initial,
                "admitted_free_providers": ["mistral"],
                "providers": {
                    "groq": {"admitted": False, "cost_class": "UNKNOWN", "evidence_ref": "A-revoked"},
                    "mistral": {"admitted": True, "cost_class": "FREE", "evidence_ref": "B"},
                },
            }
            snapshot.write_text(json.dumps(initial, sort_keys=True, separators=(",", ":")), encoding="utf-8")
            tool.write_text(
                "from pathlib import Path\nimport os\nprint(Path(os.environ['SNAPSHOT_PATH']).read_text(encoding='utf-8'), end='')\n",
                encoding="utf-8",
            )

            script = tmp / "fixture.sh"
            script.write_text(
                textwrap.dedent(
                    f"""
                    #!/usr/bin/env bash
                    set -Eeuo pipefail
                    STATE_DIR={state!s}
                    SWARM_ADMISSION_BINDING_FILE="$STATE_DIR/swarm-admission-binding.sha256"
                    ADMISSION_TOOL={tool!s}
                    SNAPSHOT_PATH={snapshot!s}
                    KILL_LOG={kill_log!s}
                    export SNAPSHOT_PATH KILL_LOG
                    {binding_fn}
                    has_admitted_provider_key(){{ return 0; }}
                    pgrep(){{ printf '4242\\n'; }}
                    kill(){{ printf '%s\\n' "$1" >> "$KILL_LOG"; }}
                    {stop_fn}
                    current_provider_admission_binding > "$SWARM_ADMISSION_BINDING_FILE"
                    """
                ).strip()
                + "\n",
                encoding="utf-8",
            )
            if changed:
                with script.open("a", encoding="utf-8") as fh:
                    fh.write(
                        "python3 - <<'PY'\n"
                        "import json, os\n"
                        "from pathlib import Path\n"
                        f"payload={revoked!r}\n"
                        "Path(os.environ['SNAPSHOT_PATH']).write_text(json.dumps(payload, sort_keys=True, separators=(',', ':')), encoding='utf-8')\n"
                        "PY\n"
                    )
            with script.open("a", encoding="utf-8") as fh:
                fh.write("stop_unadmitted_go_swarm\n")
                fh.write("[[ -f \"$KILL_LOG\" ]] && cat \"$KILL_LOG\" || true\n")
                fh.write("[[ -r \"$SWARM_ADMISSION_BINDING_FILE\" ]] && printf 'BINDING_PRESENT\\n' || printf 'BINDING_REMOVED\\n'\n")

            return subprocess.run(["bash", str(script)], capture_output=True, text=True)

    def test_partial_revocation_kills_existing_child_even_when_other_provider_remains_admitted(self):
        proc = self._run_revocation_fixture(changed=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("4242", proc.stdout)
        self.assertIn("BINDING_REMOVED", proc.stdout)

    def test_unchanged_admission_keeps_existing_child(self):
        proc = self._run_revocation_fixture(changed=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("4242", proc.stdout)
        self.assertIn("BINDING_PRESENT", proc.stdout)

    def test_shell_syntax(self):
        proc = subprocess.run(["bash", "-n", str(SUPERVISOR)], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)


if __name__ == "__main__":
    unittest.main()
