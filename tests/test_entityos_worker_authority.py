#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import types
import unittest

from tools.entityos_worker_authority import (
    WorkerAuthorityError,
    install_worker_authority,
    resolve_worker_authority,
)


class WorkerAuthorityTests(unittest.TestCase):
    def _root(self, *, protocol_path="research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_68.md"):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)
        (root / "research_entity/continuity").mkdir(parents=True)
        (root / "research_entity/claycode/autonomous").mkdir(parents=True)
        (root / "research_entity/claycode").mkdir(parents=True, exist_ok=True)
        (root / "governance").mkdir(parents=True)
        bootstrap = {
            "schema_version": "8.68",
            "active_program": "ENTITYOS_HCU",
            "product_endpoint": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
            "free_only": True,
            "all_worker_protocol": protocol_path,
            "active_owner_authority": "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md",
            "authority_correction": "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json",
        }
        (root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json").write_text(json.dumps(bootstrap), encoding="utf-8")
        p = root / protocol_path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "# CLAYCODE ALL-WORKERS EXECUTION DIRECTIVE 8.68\n"
            "Authority epoch: 8.68\nProgram: ENTITYOS_HCU\nProduct: EntityOS\n"
            "Compute architecture: HCU\nMode: FREE_ONLY\n"
            "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json\n",
            encoding="utf-8",
        )
        (root / "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_68.json").write_text("{}", encoding="utf-8")
        (root / "governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md").write_text("ACTIVE USER AUTHORITY\n", encoding="utf-8")
        return tmp, root

    def test_resolves_versioned_current_protocol_not_legacy(self):
        tmp, root = self._root()
        self.addCleanup(tmp.cleanup)
        a = resolve_worker_authority(root)
        self.assertTrue(a.protocol_path.name.endswith("_8_68.md"))
        self.assertEqual(a.authority_epoch, "8.68")

    def test_rejects_path_escape_and_stale_epoch(self):
        tmp, root = self._root(protocol_path="../outside.md")
        self.addCleanup(tmp.cleanup)
        with self.assertRaises(WorkerAuthorityError):
            resolve_worker_authority(root)

        tmp2, root2 = self._root()
        self.addCleanup(tmp2.cleanup)
        p = root2 / "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_68.md"
        p.write_text(p.read_text().replace("Authority epoch: 8.68", "Authority epoch: 8.63"), encoding="utf-8")
        with self.assertRaises(WorkerAuthorityError):
            resolve_worker_authority(root2)

    def test_install_replaces_historical_prompt_and_refreshes(self):
        tmp, root = self._root()
        self.addCleanup(tmp.cleanup)
        base = types.SimpleNamespace(
            PROTOCOL_PATH=None,
            OWNER_DIRECTIVE_PATH=None,
            PROTOCOL_BEGIN="[MINI ENTITY",
            PROTOCOL_END="[/MINI ENTITY",
            load_protocol=lambda: "legacy",
            worker_prompt=lambda *args: "Mini Entity `go` macrocycle",
        )
        a = install_worker_authority(base, root)
        self.assertEqual(base.load_protocol(), a.protocol_text)
        prompt = base.worker_prompt(a.protocol_text, "TEST", "do work", "{}", 1)
        self.assertIn("EntityOS + HCU `go` macrocycle", prompt)
        self.assertNotIn("Mini Entity `go` macrocycle", prompt)


if __name__ == "__main__":
    unittest.main()
