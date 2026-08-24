from __future__ import annotations

import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CURRENT_SURFACES = (
    ROOT / "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
    ROOT / "research_entity/rooms/PROGRAM_STATE.json",
    ROOT / "the artefact/manifest.json",
)
SHA40 = re.compile(r"\b[0-9a-f]{40}\b")


class SuccessorDynamicCurrentFrontierTests(unittest.TestCase):
    def _load(self, path: Path) -> dict:
        value = json.loads(path.read_text(encoding="utf-8"))
        self.assertIsInstance(value, dict, path.as_posix())
        return value

    @staticmethod
    def _frontier_text(value: object) -> str:
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value or "")

    def test_retained_lanes_are_repository_qualified(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                payload = self._load(path)
                policy = payload.get("execution_policy", {})
                self.assertEqual(
                    payload.get("retained_hcu_donor_qualified") or policy.get("retained_hcu_donor_qualified"),
                    "gschaidergabriel/clay-global-research-entity#1263",
                )
                self.assertEqual(
                    payload.get("retained_execution_controller_qualified") or policy.get("retained_execution_controller_qualified"),
                    "gschaidergabriel/Dr.-Unterweger#810",
                )

    def test_mutable_frontier_never_freezes_retained_lane_heads(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                frontier = self._frontier_text(self._load(path).get("current_frontier"))
                for line in frontier.splitlines():
                    lower = line.lower()
                    if "retained donor" in lower or "retained executor" in lower or "single successor-dynamic hcu donor" in lower:
                        self.assertIsNone(SHA40.search(line), f"mutable frontier froze a concrete retained head: {line}")

    def test_mutable_frontier_requires_live_refresh_semantics(self) -> None:
        for path in CURRENT_SURFACES:
            with self.subTest(path=path.as_posix()):
                frontier = self._frontier_text(self._load(path).get("current_frontier")).lower()
                self.assertIn("refresh", frontier)
                self.assertIn("live head", frontier)


if __name__ == "__main__":
    unittest.main()
