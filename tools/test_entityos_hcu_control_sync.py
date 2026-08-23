#!/usr/bin/env python3
"""Source regression obligations for EntityOS/HCU control-plane synchronization.

These tests are deterministic source/control-plane checks. They do not establish HCU,
provider, sandbox, model, effect, or whole EntityOS runtime credit.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

HERE = Path(__file__).resolve().parent
SHIM_PATH = HERE / "run_xeno_go_swarm.py"


def load_shim():
    spec = importlib.util.spec_from_file_location("entityos_hcu_admission_under_test", SHIM_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load admission shim")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class EntityOSHCUControlSyncTests(unittest.TestCase):
    def test_current_branch_control_state_is_admitted_sourcewise(self):
        shim = load_shim()
        with mock.patch.dict(os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=False):
            shim.preflight()

    def test_retained_controller_overlay_uses_entityos_hcu_protocol_and_lanes(self):
        shim = load_shim()

        class Base:
            PROTOCOL_BEGIN = "old"
            PROTOCOL_END = "old"
            OWNER_DIRECTIVE_PATH = None

        class Controller:
            BASE = Base()
            LANES = (("OLD", "old"),)

        shim.install_current_overlay(Controller)
        self.assertEqual(Controller.BASE.PROTOCOL_BEGIN, shim.PROTOCOL_BEGIN)
        self.assertEqual(Controller.BASE.PROTOCOL_END, shim.PROTOCOL_END)
        self.assertEqual(Controller.BASE.OWNER_DIRECTIVE_PATH, shim.SUPERVISOR)
        self.assertIs(Controller.LANES, shim.ENTITYOS_HCU_LANES)
        self.assertTrue(all("Mini Entity product" not in task for _, task in Controller.LANES))

    def test_authority_rollback_poison_fails_closed(self):
        """GO unusual discriminator: one active-program rollback must be rejected."""
        shim = load_shim()
        original = json.loads(shim.BOOTSTRAP.read_text(encoding="utf-8"))
        poisoned = dict(original)
        poisoned["active_program"] = "ENTITYOS_HCU_XENO"

        with tempfile.TemporaryDirectory() as td:
            poison_path = Path(td) / "BOOTSTRAP_MINIMAL.json"
            poison_path.write_text(json.dumps(poisoned), encoding="utf-8")
            with mock.patch.object(shim, "BOOTSTRAP", poison_path), mock.patch.dict(
                os.environ, {"CLAY_FREE_ONLY_ATTESTED": "1"}, clear=False
            ):
                with self.assertRaisesRegex(shim.AdmissionError, "BOOTSTRAP_PROGRAM_MISMATCH"):
                    shim.preflight()


if __name__ == "__main__":
    unittest.main()
