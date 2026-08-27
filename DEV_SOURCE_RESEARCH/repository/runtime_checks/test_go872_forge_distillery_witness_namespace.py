from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "run_go871_forge_distillery_runtime_gate.py"
spec = importlib.util.spec_from_file_location("gate872", MODULE)
gate = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(gate)


class ForgeDistilleryWitnessNamespace872(unittest.TestCase):
    def test_probe_workdir_is_read_only(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(gate.shutil, "which", return_value="/usr/bin/bwrap"):
            cwd = Path(td)
            prefix = gate.bwrap_prefix(cwd)
        self.assertIn(["--ro-bind", str(cwd.resolve()), "/work"], [prefix[i:i+3] for i in range(len(prefix)-2)])
        self.assertNotIn(["--bind", str(cwd.resolve()), "/work"], [prefix[i:i+3] for i in range(len(prefix)-2)])

    def test_witness_clone_workdir_can_be_writable(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(gate.shutil, "which", return_value="/usr/bin/bwrap"):
            cwd = Path(td)
            prefix = gate.bwrap_prefix(cwd, writable_workdir=True)
        self.assertIn(["--bind", str(cwd.resolve()), "/work"], [prefix[i:i+3] for i in range(len(prefix)-2)])
        self.assertNotIn(["--ro-bind", str(cwd.resolve()), "/work"], [prefix[i:i+3] for i in range(len(prefix)-2)])

    def test_run_isolated_requests_writable_workdir(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            with mock.patch.object(gate, "bwrap_prefix", return_value=None) as prefix:
                result = gate.run_isolated(cwd, ["python3", "-m", "py_compile", "x.py"])
            prefix.assert_called_once_with(cwd, writable_workdir=True)
            self.assertEqual(126, result["rc"])

    def test_backend_probe_requests_read_only_workdir(self):
        with tempfile.TemporaryDirectory() as td:
            cwd = Path(td)
            with mock.patch.object(gate, "bwrap_prefix", return_value=None) as prefix:
                result = gate.backend_status(cwd)
            prefix.assert_called_once_with(cwd, writable_workdir=False)
            self.assertFalse(result["admitted"])


if __name__ == "__main__":
    unittest.main()
