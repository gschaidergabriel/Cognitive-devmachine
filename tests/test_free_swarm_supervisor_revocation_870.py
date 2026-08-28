from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

ROOT = Path(os.environ.get("CLAY_TEST_REPO_ROOT", str(Path(__file__).resolve().parents[1])))
SUPERVISOR = ROOT / "tools/run_6000_free_swarm_supervisor.sh"
REQUEST_PATH = ROOT / "tools/run_free_go_swarm.py"


def _function(text: str, name: str) -> str:
    marker = f"{name}(){{"
    start = text.find(marker)
    if start < 0:
        raise AssertionError(f"function not found: {name}")
    rest_start = start + len(marker)
    next_func = re.search(r"(?m)^[_A-Za-z][_A-Za-z0-9]*\(\)\{", text[rest_start:])
    boundaries = []
    if next_func:
        boundaries.append(rest_start + next_func.start())
    loop = text.find("\nwhile (( ", rest_start)
    if loop >= 0:
        boundaries.append(loop)
    boundary = min(boundaries) if boundaries else len(text)
    close = text.rfind("\n}", start, boundary)
    if close < 0:
        raise AssertionError(f"function terminator not found: {name}")
    return text[start:close + 2].rstrip() + "\n"


class FreeSwarmSupervisorRevocation870Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SUPERVISOR.read_text(encoding="utf-8")

    def test_supervisor_sanitizes_revoked_provider_and_does_not_reopen_mixed_bundle(self) -> None:
        shell = "\n".join([
            "set -Eeuo pipefail",
            "TEST_ADMITTED='mistral,nvidia,openrouter'",
            "provider_admitted(){ [[ ,$TEST_ADMITTED, == *,$1,* ]]; }",
            "load_secret_file(){ echo \"$1\" >>\"$CALLS\"; export GROQ_API_KEY=REINTRODUCED_G; export MISTRAL_API_KEY=REINTRODUCED_M; }",
            _function(self.text, "all_llm_providers_admitted"),
            _function(self.text, "clear_unadmitted_provider_secret_env"),
            _function(self.text, "load_admitted_secrets"),
            "export GROQ_API_KEY=STALE_G GROQ_API_KEYS=STALE_G_POOL MISTRAL_API_KEY=LIVE_M NVIDIA_API_KEY=LIVE_N OPENROUTER_API_KEY=LIVE_O",
            "clear_unadmitted_provider_secret_env",
            "load_admitted_secrets",
            "clear_unadmitted_provider_secret_env",
            "[[ -z ${GROQ_API_KEY+x} ]]",
            "[[ -z ${GROQ_API_KEYS+x} ]]",
            "[[ ${MISTRAL_API_KEY:-} == LIVE_M ]]",
            "[[ ${NVIDIA_API_KEY:-} == LIVE_N ]]",
            "[[ ${OPENROUTER_API_KEY:-} == LIVE_O ]]",
            "[[ ! -s $CALLS ]]",
        ])
        with tempfile.TemporaryDirectory() as td:
            calls = Path(td) / "calls"
            env = dict(os.environ)
            env["CALLS"] = str(calls)
            proc = subprocess.run(["bash", "-c", shell], cwd=ROOT, env=env, text=True, capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)

    def test_child_is_bound_to_exact_validated_admission_and_replaced_on_change(self) -> None:
        digest = _function(self.text, "admission_capability_digest")
        reconcile = _function(self.text, "reconcile_6000_admission")
        start = _function(self.text, "start_6000")
        self.assertIn("load_provider_admission", digest)
        self.assertIn('bound" != "$current', reconcile)
        self.assertIn("stop_6000", reconcile)
        self.assertIn("prepare_provider_environment", start)
        self.assertIn('after" == "$before', start)
        self.assertIn('post" != "$after', start)
        self.assertIn('mv "$tmp" "$ADMISSION_BINDING_FILE"', start)

    def _run_child_binding_fixture(self, changed: bool) -> subprocess.CompletedProcess[str]:
        reconcile = _function(self.text, "reconcile_6000_admission")
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            binding = root / "binding"
            digest = root / "digest"
            stops = root / "stops"
            binding.write_text("OK:before\n", encoding="utf-8")
            digest.write_text("OK:after\n" if changed else "OK:before\n", encoding="utf-8")
            shell = "\n".join([
                "set -Eeuo pipefail",
                f"ADMISSION_BINDING_FILE={binding}",
                f"DIGEST_FILE={digest}",
                f"STOP_LOG={stops}",
                "admission_capability_digest(){ cat \"$DIGEST_FILE\"; }",
                "pgrep(){ printf '4242\\n'; }",
                "stop_6000(){ printf 'stop\\n' >>\"$STOP_LOG\"; }",
                reconcile,
                "reconcile_6000_admission",
                "[[ -f \"$STOP_LOG\" ]] && cat \"$STOP_LOG\" || true",
                "[[ -r \"$ADMISSION_BINDING_FILE\" ]] && printf 'BINDING_PRESENT\\n' || printf 'BINDING_REMOVED\\n'",
            ])
            return subprocess.run(["bash", "-c", shell], cwd=ROOT, text=True, capture_output=True)

    def test_partial_revocation_replaces_bound_6000_child(self) -> None:
        proc = self._run_child_binding_fixture(changed=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("stop", proc.stdout)
        self.assertIn("BINDING_REMOVED", proc.stdout)

    def test_unchanged_admission_keeps_bound_6000_child(self) -> None:
        proc = self._run_child_binding_fixture(changed=False)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertNotIn("stop", proc.stdout)
        self.assertIn("BINDING_PRESENT", proc.stdout)

    def test_loop_sanitizes_before_reconcile_and_spawn(self) -> None:
        loop = self.text.index("while (( $(date +%s) < DEADLINE )); do")
        prepare = self.text.index("  prepare_provider_environment", loop)
        reconcile = self.text.index("  reconcile_6000_admission", loop)
        start = self.text.index("  start_6000", loop)
        self.assertLess(prepare, reconcile)
        self.assertLess(reconcile, start)
        self.assertIn("CLAY_6000_SWARM_SUPERVISOR/v3", self.text)

    def test_existing_request_path_revalidates_before_network(self) -> None:
        text = REQUEST_PATH.read_text(encoding="utf-8")
        start = text.index("def request_chat(")
        end = text.index("\ndef extract_text", start)
        fn = text[start:end]
        gate = fn.index("if not provider_execution_admitted(spec):")
        request = fn.index("urllib.request.Request")
        socket = fn.index("urllib.request.urlopen")
        self.assertLess(gate, request)
        self.assertLess(gate, socket)


if __name__ == "__main__":
    unittest.main()
