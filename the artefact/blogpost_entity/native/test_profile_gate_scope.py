#!/usr/bin/env python3
from __future__ import annotations

import unittest
from pathlib import Path


HERE = Path(__file__).resolve().parent
ENTRY = (HERE / "mini_entity.c").read_text(encoding="utf-8")
CLI = (HERE / "mini_entity_part04.inc").read_text(encoding="utf-8")


class ProfileGateScopeTests(unittest.TestCase):
    def test_generic_json_parser_is_not_globally_macro_replaced(self) -> None:
        self.assertNotIn("#define parse_json parse_json_profile_guarded", ENTRY)

    def test_preset_boundary_uses_profile_guard(self) -> None:
        preset = CLI.split("static void cmd_state_box", 1)[0]
        self.assertIn("parse_json_profile_guarded(text)", preset)

    def test_non_profile_json_surfaces_keep_generic_parser(self) -> None:
        state_box = CLI.split("static void cmd_state_box", 1)[1].split("static void cmd_set_local_model", 1)[0]
        runner = CLI.split("static void cmd_set_runner", 1)[1].split("static void cmd_status", 1)[0]
        run = CLI.split("static void cmd_run", 1)[1].split("static void usage", 1)[0]
        self.assertIn("parse_json(text)", state_box)
        self.assertIn("parse_json(json)", runner)
        self.assertIn("parse_json(profile_text)", run)

    def test_db_profile_reader_revalidates_contract_after_hash_check(self) -> None:
        self.assertIn("json_object *checked=parse_json_profile_guarded(raw)", ENTRY)
        self.assertIn('die("PROFILE_CONTRACT_REJECTED")', ENTRY)


if __name__ == "__main__":
    unittest.main()
