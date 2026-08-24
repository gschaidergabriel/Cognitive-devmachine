from __future__ import annotations

from pathlib import Path
import importlib.util
import unittest

ROOT=Path(__file__).resolve().parents[1]
PATH=ROOT/"tools/validate_clayverse_authority_consistency.py"
spec=importlib.util.spec_from_file_location("authority_guard_v6",PATH)
assert spec and spec.loader
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)


class SuccessorAuthorityResolutionV6Tests(unittest.TestCase):
    def test_guard_has_no_fixed_current_authority_minor(self):
        self.assertFalse(hasattr(mod,"CURRENT_AUTHORITY"))

    def test_historical_869_path_resolves(self):
        path="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_69.json"
        self.assertEqual(mod._safe_authority_path(path),path)
        self.assertEqual(mod._authority_version(path),"8.69")

    def test_current_870_path_requires_no_fixed_minor(self):
        path="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_70.json"
        self.assertEqual(mod._safe_authority_path(path),path)
        self.assertEqual(mod._authority_version(path),"8.70")
        self.assertEqual(mod._version_tuple("8.70"),(8,70))

    def test_future_871_path_requires_no_code_change(self):
        path="research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_71.json"
        self.assertEqual(mod._safe_authority_path(path),path)
        self.assertEqual(mod._authority_version(path),"8.71")

    def test_path_traversal_and_noncanonical_names_fail_closed(self):
        bad=("../SUPERVISOR_STEERING_8_70.json","/tmp/SUPERVISOR_STEERING_8_70.json","research_entity/claycode/autonomous/current.json","research_entity/claycode/autonomous/SUPERVISOR_STEERING_8.70.json")
        for value in bad:
            with self.subTest(value=value):self.assertIsNone(mod._safe_authority_path(value))


if __name__=="__main__":unittest.main()
