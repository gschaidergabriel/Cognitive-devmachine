from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SURFACES = (
    ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
    ROOT / "research_entity/rooms/PROGRAM_STATE.json",
)
SHA40 = re.compile(r"\b[0-9a-f]{40}\b")


class SuccessorDynamicCurrentFrontierTests(unittest.TestCase):
    """Keep retained PR lanes successor-dynamic on mutable current-facing state.

    Historical steering/receipts may preserve exact observed heads. Mutable bootstrap and
    program-state frontiers must instead name repository-qualified retained lanes and require
    a live refresh, otherwise a previously correct SHA becomes false current authority as
    soon as another organ advances the retained PR.
    """

    def _load(self, path: Path) -> dict:
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict, path.as_posix())
        return value

    def _frontier_text(self, value: object) -> str:
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value or "")

    def test_retained_lanes_are_repository_qualified(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                payload = self._load(path)
                self.assertEqual(
                    payload.get("retained_hcu_donor_qualified")
                    or payload.get("execution_policy", {}).get("retained_hcu_donor_qualified"),
                    "gschaidergabriel/clay-global-research-entity#1263",
                )
                self.assertEqual(
                    payload.get("retained_execution_controller_qualified")
                    or payload.get("execution_policy", {}).get("retained_execution_controller_qualified"),
                    "gschaidergabriel/Dr.-Unterweger#810",
                )

    def test_current_frontier_does_not_freeze_retained_lane_heads(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                payload = self._load(path)
                frontier = self._frontier_text(payload.get("current_frontier"))
                for line in frontier.splitlines():
                    lower = line.lower()
                    if "retained donor" in lower or "retained executor" in lower:
                        self.assertIsNone(
                            SHA40.search(line),
                            f"current-facing retained lane froze a concrete head: {line}",
                        )

    def test_current_frontier_requires_live_head_refresh(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                payload = self._load(path)
                frontier = self._frontier_text(payload.get("current_frontier")).lower()
                self.assertIn("refresh", frontier)
                self.assertIn("live head", frontier)


if __name__ == "__main__":
    unittest.main()
