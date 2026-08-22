from __future__ import annotations

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
BLOGPOST = Path(__file__).resolve().parent
DOC = BLOGPOST / "native" / "MINI_ENTITY_0_6_SANDBOX.md"
RECEIPT = BLOGPOST / "receipts" / "2026-08-22_NATIVE_MINI_ENTITY_V0_6_LOCAL_LLM.json"
PROGRAM_STATE = ROOT / "research_entity" / "rooms" / "PROGRAM_STATE.json"


def _doc_hash() -> str:
    text = DOC.read_text(encoding="utf-8")
    match = re.search(r"Sandbox SHA-256:\s*\n\s*`([0-9a-f]{64})`", text)
    assert match is not None, "sandbox reference must expose one explicit binary SHA-256"
    return match.group(1)


def test_native_v06_binary_identity_is_coherent_across_durable_evidence():
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    state = json.loads(PROGRAM_STATE.read_text(encoding="utf-8"))

    doc_hash = _doc_hash()
    receipt_hash = receipt["binary_sha256"]
    state_hash = state["sandbox_evidence"]["native_pipeline"]["binary_sha256"]

    assert doc_hash == receipt_hash == state_hash
    assert receipt["version"] == state["sandbox_evidence"]["native_pipeline"]["version"] == "mini-entity/0.6.0"
    assert receipt["program"] == "MINI_ENTITY_PIPELINE_ALL_IN_ONE"
