from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CLAY_PATH = ROOT / "the artefact" / "blogpost_entity" / "BLOGPOST_ENTITY.clay"
GUARD_PATH = ROOT / "the artefact" / "blogpost_entity" / "check_structured_contract_sync.py"


def _load_guard():
    spec = importlib.util.spec_from_file_location("clay_contract_sync_guard", GUARD_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cognition_invocation_selector_is_bounded_to_admission():
    guard = _load_guard()
    contract = guard.clay_contract(CLAY_PATH.read_text(encoding="utf-8"))
    assert contract["cognition_invocation_runtime_boundary"] is True
    assert contract["cognition_invocation_passed_only_to_admission"] is True
    assert contract["caller_cognition_authority_absent"] is True


def test_selector_drop_poison_fails_contract():
    guard = _load_guard()
    source = CLAY_PATH.read_text(encoding="utf-8")
    poisoned = source.replace(
        '  map_set(cognition_data,"invocation",cognition_invocation)\n',
        "",
        1,
    )
    contract = guard.clay_contract(poisoned)
    assert contract["cognition_invocation_runtime_boundary"] is True
    assert contract["cognition_invocation_passed_only_to_admission"] is False


def test_caller_authority_smuggle_poison_fails_contract():
    guard = _load_guard()
    source = CLAY_PATH.read_text(encoding="utf-8")
    poisoned = source.replace(
        '  map_set(cognition_data,"invocation",cognition_invocation)\n',
        '  map_set(cognition_data,"invocation",cognition_invocation)\n'
        '  map_set(cognition_data,"zero_identity_digest","caller-controlled")\n',
        1,
    )
    contract = guard.clay_contract(poisoned)
    assert contract["caller_cognition_authority_absent"] is False
