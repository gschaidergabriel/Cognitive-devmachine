from __future__ import annotations

import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET = ROOT / "tools" / "run_6000_free_swarm_v3.py"


class V3AcceleratorImportOrder871Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = TARGET.read_text(encoding="utf-8")

    def test_source_compiles(self) -> None:
        ast.parse(self.source, filename=str(TARGET))

    def test_accelerator_is_installed_before_fabric_import(self) -> None:
        install = self.source.index("_install_accelerator(_base, _opt)")
        fabric_import = self.source.index("import run_6000_free_swarm as fabric")
        self.assertLess(install, fabric_import)
        self.assertIn(
            'ACCELERATOR_BINDING = "FREE_SWARM_ACCELERATOR_V2_PRE_FABRIC"',
            self.source,
        )

    def test_network_free_catalog_override_is_preserved(self) -> None:
        fabric_import = self.source.index("import run_6000_free_swarm as fabric")
        override = self.source.index(
            "fabric.opt.discover_and_export = route_safe_discover_and_export"
        )
        self.assertLess(fabric_import, override)
        self.assertIn('"catalog_network_attempted": False', self.source)

    def test_exact_free_lane_boundary_is_preserved(self) -> None:
        self.assertIn("current_lane_binding(", self.source)
        self.assertIn("binding_still_current(binding)", self.source)
        self.assertIn("emit_execution_receipt(", self.source)
        self.assertNotIn("FREE_LANE_CURRENT_BINDING_REQUIRED\"\n            )\n        )", self.source)


if __name__ == "__main__":
    unittest.main()
