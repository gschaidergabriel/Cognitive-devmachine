from __future__ import annotations

from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SUPERVISOR = ROOT / "tools/run_6000_free_swarm_supervisor.sh"
ACTIVATE = ROOT / "tools/activate_6000_free_swarm.sh"


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


class Go871ProviderSecretScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.text = SUPERVISOR.read_text(encoding="utf-8")
        cls.activate = ACTIVATE.read_text(encoding="utf-8")

    def test_shell_syntax(self) -> None:
        for path in (SUPERVISOR, ACTIVATE):
            proc = subprocess.run(["bash", "-n", str(path)], capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr)

    def test_activation_does_not_give_vault_credentials_to_supervisor(self) -> None:
        start_line = next(
            line for line in self.activate.splitlines()
            if "run_6000_free_swarm_supervisor.sh" in line and line.lstrip().startswith("nohup")
        )
        self.assertNotIn("free_swarm_exec_with_vault.py", start_line)
        self.assertIn("nohup bash tools/run_6000_free_swarm_supervisor.sh", start_line)

    def test_control_parent_clears_all_provider_secrets_before_local_children(self) -> None:
        prepare = _function(self.text, "prepare_provider_environment")
        self.assertIn("clear_all_provider_secret_env", prepare)
        self.assertNotIn("load_admitted_secrets", prepare)
        self.assertNotIn("normalize_provider_pool", prepare)
        loop = self.text[self.text.index("while (( $(date +%s) < DEADLINE )); do"):]
        prep = loop.index("prepare_provider_environment")
        for name in ("start_local_model", "start_dashboard", "start_distillery", "start_forge"):
            self.assertLess(prep, loop.index(name), name)

    def test_dedicated_swarm_child_is_the_only_runtime_vault_loader(self) -> None:
        start = _function(self.text, "start_6000")
        self.assertIn("free_swarm_exec_with_vault.py", start)
        self.assertIn("run_6000_free_swarm_fast.py", start)
        for name in ("start_local_model", "start_dashboard", "start_distillery", "start_forge"):
            self.assertNotIn("free_swarm_exec_with_vault.py", _function(self.text, name))

    def test_binding_changes_from_old_broad_parent_contract(self) -> None:
        digest = _function(self.text, "admission_capability_digest")
        self.assertIn('"credential_scope":"SWARM_CHILD_ONLY/v1"', digest)
        self.assertIn("economic_provenance_sha256", digest)
        reconcile = _function(self.text, "reconcile_6000_admission")
        self.assertIn('bound" != "$current', reconcile)
        self.assertIn("stop_6000", reconcile)

    def test_supervisor_status_declares_credential_scope(self) -> None:
        self.assertIn("'provider_credential_scope':'SWARM_CHILD_ONLY'", self.text)
        self.assertIn("CLAY_6000_SWARM_SUPERVISOR/v4", self.text)


if __name__ == "__main__":
    unittest.main()
