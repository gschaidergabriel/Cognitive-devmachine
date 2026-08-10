#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "research_entity/claycode/base/OWNER_AGENCY_WEB_FIDELITY_LEDGER_V2.json"
CORE = ROOT / "research_entity/claycode/base/SELF_ROOT_AGENCY_WEB_CORE_V18_CANDIDATE.clay"
EXPECTED_OWNER_BLOB = "b48b8720b04012e9c0a2223405b2b513976fb103"
ALLOWED_PHASES = {"WP03_TYPED_CORE","WP04_SEMANTICS","WP05_RUNTIME","EFFECT_BOUNDARY","FORBIDDEN_GUARD","MEASUREMENT","ACCEPTANCE"}


def main() -> int:
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    core = CORE.read_text(encoding="utf-8")
    assert ledger["schema_version"] == "2.0"
    assert ledger["owner_source_git_blob"] == EXPECTED_OWNER_BLOB
    policy = ledger["policy"]
    assert policy["owner_semantics_may_disappear"] is False
    assert policy["surface_syntax_equals_core_language"] is False
    assert policy["untrusted_web_mints_instruction_authority"] is False
    assert policy["untrusted_web_mints_effect_authority"] is False
    assert policy["self_root_mints_harness_authority"] is False
    assert policy["unknown_mapping"] == "FAIL_CLOSED"

    rows = ledger["requirements"]
    assert len(rows) == 40, len(rows)
    ids = [row[0] for row in rows]
    assert len(ids) == len(set(ids)) == 40
    assert ids == [f"F{i:02d}_" + ids[i-1].split("_",1)[1] for i in range(1,41)], ids

    counts = Counter()
    wp03_targets = []
    for row in rows:
        assert isinstance(row, list) and len(row) == 5, row
        req_id, phase, owner_marker, target_marker, disposition = row
        assert phase in ALLOWED_PHASES, row
        assert isinstance(owner_marker, str) and owner_marker.strip(), row
        assert isinstance(disposition, str) and disposition.strip() and "UNMAPPED" not in disposition, row
        counts[phase] += 1
        if phase == "WP03_TYPED_CORE":
            assert isinstance(target_marker, str) and target_marker.strip(), row
            assert target_marker in core, (req_id, target_marker)
            wp03_targets.append(target_marker)
        else:
            assert target_marker is None, row

    # Required typed frontier is now ten records + explicit authority/symbol anchors.
    required_records = ["InterestTrace","AutotelicGoal","AgencyState","InitiativePulse","ActionReadiness","GoalCheckpoint","UntrustedWebJsonEnvelope","WebEvidenceClay","ResearchQuestion","SelfInitiatedExperiment"]
    for name in required_records:
        assert f"record {name}" in core, name
    assert "type ExperimentRisk" in core
    assert "type IngressAuthority" in core
    assert "invariant UntrustedWebJsonEnvelope.executable = false" in core
    assert "invariant WebEvidenceClay.instruction_authority = NONE" in core
    assert "invariant WebEvidenceClay.effect_authority = NONE" in core

    report = {
        "status": "PASS",
        "scope": "WP03_OWNER_AGENCY_WEB_FIDELITY_LEDGER_V2",
        "owner_source_git_blob": ledger["owner_source_git_blob"],
        "requirements": len(rows),
        "unique_requirements": len(set(ids)),
        "phase_counts": dict(sorted(counts.items())),
        "wp03_target_markers_checked": len(wp03_targets),
        "unknown_mappings": 0,
        "required_typed_records": len(required_records),
        "authority_guard_markers": 3,
        "owner_semantics_may_disappear": False,
        "effect_authority": "NONE",
        "truth_authority": "NONE",
        "promotion": "NONE",
        "next": "EXECUTE_PHASE_SPECIFIC_FIDELITY_GATES_FOR_WP04_WP05_EFFECT_AND_ACCEPTANCE",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
