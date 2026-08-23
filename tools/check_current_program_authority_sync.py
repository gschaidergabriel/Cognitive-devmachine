#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXPECTED_PROGRAM = "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
EXPECTED_PROGRAM_ID = "mini-entity-pipeline-all-in-one"
EXPECTED_STAGE = "MINI_ENTITY_PIPELINE_CLAY_PLUS_BUNDLED_08B_UNIFIED_JSPACE_GWT"
EXPECTED_OWNER_DIRECTIVE = "research_entity/global/ENTITYOS_FIXED_CLAUDE_ADAPTIVE_INFERENCE_INTEGRATION.md"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()


def validate(root: Path) -> list[str]:
    errors: list[str] = []
    bootstrap = _load(root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json")
    program = _load(root / "research_entity/rooms/PROGRAM_STATE.json")
    inbox = _load(root / "research_entity/claycode/autonomous/SUPERVISOR_INBOX.json")
    control_path = root / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL.json"
    control = _load(control_path)
    addendum = _load(root / "research_entity/claycode/CLAYCODE_AUTONOMOUS_RESEARCH_CONTROL_4_2_EXECUTION_BOUNDARY.json")

    checks = (
        (bootstrap.get("active_program") == EXPECTED_PROGRAM, "BOOTSTRAP_MINIMAL active_program drift"),
        (bootstrap.get("active_stage") == EXPECTED_STAGE, "BOOTSTRAP_MINIMAL active_stage drift"),
        (bootstrap.get("sole_owner_directive") == EXPECTED_OWNER_DIRECTIVE, "BOOTSTRAP_MINIMAL owner directive drift"),
        (program.get("program_id") == EXPECTED_PROGRAM_ID, "PROGRAM_STATE program_id drift"),
        (program.get("stage") == EXPECTED_STAGE, "PROGRAM_STATE stage drift"),
        (program.get("owner_directive") == EXPECTED_OWNER_DIRECTIVE, "PROGRAM_STATE owner directive drift"),
        (program.get("execution_policy", {}).get("control_sync_required_before_research_spend") is False, "PROGRAM_STATE still blocks research spend for control sync"),
        (inbox.get("active_program") == EXPECTED_PROGRAM, "SUPERVISOR_INBOX active_program drift"),
        (inbox.get("control_sync_required_before_research_spend") is False, "SUPERVISOR_INBOX still blocks research spend for control sync"),
        (control.get("active_program") == EXPECTED_PROGRAM, "autonomous control active_program drift"),
        (control.get("target_stage") == EXPECTED_STAGE, "autonomous control target_stage drift"),
        (control.get("mode") == "FREE_ONLY", "autonomous control FREE_ONLY weakened"),
        (control.get("cycle_policy", {}).get("paid_fallback") is False, "autonomous control paid fallback enabled"),
        (control.get("cycle_policy", {}).get("vps_testing") == "FORBIDDEN", "autonomous control VPS testing weakened"),
        (addendum.get("mode") == "FREE_ONLY", "execution addendum FREE_ONLY weakened"),
        (addendum.get("preserved_hard_rules", {}).get("together_forbidden") is True, "Together prohibition weakened"),
        (addendum.get("preserved_hard_rules", {}).get("frank_harness_modification") == "FORBIDDEN", "Frank Harness protection weakened"),
        (addendum.get("base_control_blob_sha") == _git_blob_sha(control_path), "execution addendum base_control_blob_sha drift"),
    )
    for ok, message in checks:
        if not ok:
            errors.append(message)
    return errors


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    errors = validate(root)
    if errors:
        print(json.dumps({"ok": False, "errors": errors}, sort_keys=True))
        return 1
    print(json.dumps({"ok": True, "program": EXPECTED_PROGRAM, "stage": EXPECTED_STAGE}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
