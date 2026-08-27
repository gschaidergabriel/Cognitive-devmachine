from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC_DIR = ROOT / "research_entity/continuity/ordinary_dispatch_specs"
CLAIM_DIR = ROOT / "research_entity/continuity/ordinary_dispatch_claims"
RESULT_DIR = ROOT / "research_entity/continuity/ordinary_dispatch_results"

SPEC_SCHEMA = "CLAY_ORDINARY_DISPATCH_SPEC/v1"
CLAIM_SCHEMA = "CLAY_ORDINARY_DISPATCH_CLAIM/v1"


def load_object(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"{path} must contain a JSON object")
    return value


def derived_key(spec: dict) -> str:
    dispatch_class = spec.get("dispatch_class")
    generation = spec.get("retry_generation")
    if not isinstance(dispatch_class, str) or not dispatch_class.strip():
        raise AssertionError("dispatch_class must be a non-empty string")
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise AssertionError("retry_generation must be a non-negative integer")
    return f"{dispatch_class}-g{generation:04d}"


def declared_key(spec: dict) -> str | None:
    values = [spec.get("dispatch_key"), spec.get("current_dispatch_key")]
    values = [value for value in values if isinstance(value, str) and value]
    if len(set(values)) > 1:
        raise AssertionError("spec declares conflicting dispatch keys")
    return values[0] if values else None


def declared_result_path(spec: dict, key: str) -> str | None:
    direct = spec.get("canonical_result_path")
    if isinstance(direct, str) and direct:
        return direct
    template = spec.get("result_path_template")
    if isinstance(template, str) and template:
        return template.format(dispatch_key=key)
    return None


class OrdinaryDispatchSingletonRegression(unittest.TestCase):
    def test_specs_claims_and_results_are_semantically_singleton(self):
        self.assertTrue(SPEC_DIR.is_dir(), "ordinary dispatch spec directory required")
        specs: dict[str, dict] = {}
        for path in sorted(SPEC_DIR.glob("*.json")):
            spec = load_object(path)
            self.assertEqual(spec.get("schema"), SPEC_SCHEMA, path)
            key = derived_key(spec)
            self.assertEqual(declared_key(spec), key, path)
            canonical_result = (
                f"research_entity/continuity/ordinary_dispatch_results/{key}.json"
            )
            self.assertEqual(declared_result_path(spec, key), canonical_result, path)
            self.assertNotIn(key, specs, f"duplicate dispatch key {key}")
            specs[key] = spec

        self.assertTrue(specs, "at least one ordinary dispatch spec required")

        if CLAIM_DIR.exists():
            for path in sorted(CLAIM_DIR.glob("*.json")):
                claim = load_object(path)
                key = path.stem
                self.assertIn(key, specs, f"orphan claim {path}")
                spec = specs[key]
                self.assertEqual(claim.get("schema"), CLAIM_SCHEMA, path)
                self.assertEqual(claim.get("dispatch_key"), key, path)
                self.assertEqual(
                    claim.get("dispatch_class"), spec.get("dispatch_class"), path
                )
                self.assertEqual(
                    claim.get("retry_generation"), spec.get("retry_generation"), path
                )
                for field in (
                    "authorizes_new_trigger",
                    "new_issue_authorized_by_this_claim",
                ):
                    if field in claim:
                        self.assertIs(claim[field], False, f"{path}:{field}")

        if RESULT_DIR.exists():
            for path in sorted(RESULT_DIR.glob("*.json")):
                key = path.stem
                self.assertIn(key, specs, f"orphan result {path}")
                result = load_object(path)
                if "dispatch_key" in result:
                    self.assertEqual(result["dispatch_key"], key, path)


if __name__ == "__main__":
    unittest.main()
