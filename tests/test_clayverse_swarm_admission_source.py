from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ASSERTION = ROOT / "tools" / "assert_clayverse_swarm_admission.py"
CURRENT = ROOT / "tools" / "run_go_zero_swarm.py"


def load_assertion():
    spec = importlib.util.spec_from_file_location("clayverse_swarm_admission", ASSERTION)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_controller_is_blocked():
    module = load_assertion()
    classification, markers = module.classify_current_controller(None)
    assert classification == "MISSING_BLOCKED"
    assert markers == ()


def test_existing_unvalidated_controller_is_not_admitted_by_existence():
    module = load_assertion()
    classification, markers = module.classify_current_controller(
        "#!/usr/bin/env python3\n# hypothetical replacement with no validated authority marker\n"
    )
    assert classification == "UNADMITTED_REQUIRES_CLAYVERSE_CONTROLLER_VALIDATION"
    assert markers == ()


def test_known_legacy_mini_entity_controller_is_explicitly_quarantined():
    module = load_assertion()
    source = (
        'OWNER_DIRECTIVE_PATH = "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md"\n'
        'PROTOCOL_BEGIN = "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]"\n'
    )
    classification, markers = module.classify_current_controller(source)
    assert classification == "LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED"
    assert "MINI_ENTITY_CLAYCOG_APPROX1B_TRAINING_DIRECTIVE.md" in markers
    assert "[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]" in markers


def test_repository_current_controller_cannot_be_silently_promoted():
    module = load_assertion()
    source = CURRENT.read_text(encoding="utf-8")
    classification, markers = module.classify_current_controller(source)
    assert classification == "LEGACY_MINI_ENTITY_CONTROLLER_NOT_ADMITTED"
    assert markers
