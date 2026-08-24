from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

import audit_current_authority_surfaces as audit_mod


EPOCH = "9.01"
STEERING_REL = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_9_01.json"
DIRECTIVE_REL = "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_9_01.md"
OWNER_REL = "governance/OWNER_CURRENT.md"


def write_json(root: Path, rel: str, value: dict) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def make_fixture(root: Path, *, stale_program: bool = False, stale_readme: bool = False) -> None:
    write_json(
        root,
        "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json",
        {
            "schema_version": EPOCH,
            "steering": STEERING_REL,
            "execution_authority": {"active_owner_authority": OWNER_REL},
        },
    )
    write_json(
        root,
        STEERING_REL,
        {
            "schema_version": EPOCH,
            "active_program": "ENTITYOS_HCU",
            "product": "EntityOS",
            "integrated_cognition_compute_architecture": "HCU",
        },
    )
    write_json(
        root,
        "research_entity/continuity/BOOTSTRAP_MINIMAL.json",
        {
            "schema_version": EPOCH,
            "authority_correction": STEERING_REL,
            "all_worker_protocol": DIRECTIVE_REL,
            "active_owner_authority": OWNER_REL,
        },
    )
    program_epoch = "8.99" if stale_program else EPOCH
    write_json(
        root,
        "research_entity/rooms/PROGRAM_STATE.json",
        {
            "schema_version": program_epoch,
            "authority_correction": (
                "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_99.json"
                if stale_program
                else STEERING_REL
            ),
            "all_worker_protocol": (
                "research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE_8_99.md"
                if stale_program
                else DIRECTIVE_REL
            ),
            "active_owner_authority": OWNER_REL,
        },
    )
    write_json(
        root,
        "the artefact/manifest.json",
        {
            "authority_correction": STEERING_REL,
            "execution_policy": {"active_supervisor_epoch": EPOCH},
            "coordination_authority": {"supervisor": EPOCH},
        },
    )
    readme = (
        "# current\n"
        f"{Path(STEERING_REL).name}\n"
        f"{Path(DIRECTIVE_REL).name}\n"
        f"Current supervisor epoch: **{EPOCH}**\n"
        f"{OWNER_REL}\n"
    )
    if stale_readme:
        readme = readme.replace(EPOCH, "8.99").replace("9_01", "8_99")
    readme_path = root / "the artefact/README.md"
    readme_path.parent.mkdir(parents=True, exist_ok=True)
    readme_path.write_text(readme, encoding="utf-8")


class AuthoritySurfaceAuditTests(unittest.TestCase):
    def test_aligned_fixture_passes_from_inbox_to_steering_authority(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_fixture(root)
            report = audit_mod.audit(root)
        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["expected"]["epoch"], EPOCH)
        self.assertEqual(report["mismatch_count"], 0)
        self.assertEqual(report["error_count"], 0)

    def test_stale_program_and_readme_are_detected_without_self_seeding(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            make_fixture(root, stale_program=True, stale_readme=True)
            report = audit_mod.audit(root)
        self.assertEqual(report["status"], "DRIFT")
        fields = {(item["surface"], item["field"]) for item in report["mismatches"]}
        self.assertIn(("PROGRAM_STATE", "schema_version"), fields)
        self.assertIn(("PROGRAM_STATE", "authority_correction"), fields)
        self.assertIn(("ARTIFACT_README", "steering_pointer"), fields)
        self.assertEqual(report["expected"]["epoch"], EPOCH)

    def test_missing_inbox_fails_as_authority_resolution_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with self.assertRaisesRegex(audit_mod.AuthorityAuditError, "MISSING_FILE"):
                audit_mod.resolve_current_authority(root)


if __name__ == "__main__":
    unittest.main()
