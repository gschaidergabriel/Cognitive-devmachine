from __future__ import annotations

import unittest
from pathlib import Path

CURRENT_AUTHORITY = "research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json"
CURRENT_PROGRAM = "ENTITYOS_HCU"
CURRENT_STAGE = "ENTITYOS_HCU_COMPUTATIONAL_BOOTSTRAP"
BLOGPOST = "research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md"
LOCAL_INFERENCE = "research_entity/global/LOCAL_INFERENCE_REQUIREMENT.md"
BLOGPOST_ORIGINAL_BLOB = "eeb9945e4c1d01a32e13bf6cb74db0c0c49d2767"
LOCAL_INFERENCE_ORIGINAL_BLOB = "57de4d4f460c0755d3be21cb9ce00369104dbf60"
STALE_OWNER = "research_entity/global/CLAYVERSE_SINGLE_CONTAINER_PRODUCT_DIRECTIVE.md"


def validate_redirect(text: str, *, original_blob: str) -> list[str]:
    errors: list[str] = []
    head = text[:2200]
    if "SUPERSEDED" not in head.upper():
        errors.append("NOT_SUPERSEDED")
    if CURRENT_AUTHORITY not in head:
        errors.append("CURRENT_AUTHORITY_REDIRECT_MISSING")
    if CURRENT_PROGRAM not in head:
        errors.append("CURRENT_PROGRAM_MISSING")
    if CURRENT_STAGE not in head:
        errors.append("CURRENT_STAGE_MISSING")
    if "EntityOS" not in head or "HCU" not in head:
        errors.append("ENTITYOS_HCU_MISSING")
    if STALE_OWNER in head:
        errors.append("STALE_CLAYVERSE_OWNER_REDIRECT_ACTIVE")
    if original_blob not in text:
        errors.append("HISTORICAL_BLOB_ANCHOR_MISSING")
    return errors


class EntityOSHcuLegacyRedirectTests(unittest.TestCase):
    def test_current_repository_redirects_are_fail_closed(self):
        root = Path(__file__).resolve().parents[1]
        cases = (
            (BLOGPOST, BLOGPOST_ORIGINAL_BLOB),
            (LOCAL_INFERENCE, LOCAL_INFERENCE_ORIGINAL_BLOB),
        )
        for rel, blob in cases:
            with self.subTest(path=rel):
                text = (root / rel).read_text(encoding="utf-8")
                self.assertEqual([], validate_redirect(text, original_blob=blob))

    def test_stale_clayverse_owner_pointer_is_rejected(self):
        text = (
            "Status: SUPERSEDED\n"
            f"Current owner/product authority: `{STALE_OWNER}`\n"
            f"program: {CURRENT_PROGRAM}\n"
            f"stage: {CURRENT_STAGE}\n"
            "EntityOS HCU\n"
            f"historical blob: {BLOGPOST_ORIGINAL_BLOB}\n"
        )
        self.assertIn(
            "STALE_CLAYVERSE_OWNER_REDIRECT_ACTIVE",
            validate_redirect(text, original_blob=BLOGPOST_ORIGINAL_BLOB),
        )

    def test_historical_blob_anchor_remains_required(self):
        text = (
            "Status: SUPERSEDED\n"
            f"Current owner/product authority: `{CURRENT_AUTHORITY}`\n"
            f"program: {CURRENT_PROGRAM}\n"
            f"stage: {CURRENT_STAGE}\n"
            "EntityOS HCU\n"
        )
        self.assertIn(
            "HISTORICAL_BLOB_ANCHOR_MISSING",
            validate_redirect(text, original_blob=LOCAL_INFERENCE_ORIGINAL_BLOB),
        )


if __name__ == "__main__":
    unittest.main()
