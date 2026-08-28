import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FAIL_OPEN_TYPES = {"command", "http", "mcp_tool"}


def _load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _version_tuple(value: str):
    parts = value.split(".")
    if len(parts) != 3 or any(not p.isdigit() for p in parts):
        raise AssertionError(f"unexpected Claude Code version: {value!r}")
    return tuple(int(p) for p in parts)


class ClaudeTurnAdmissionTimeoutFenceTests(unittest.TestCase):
    def test_current_command_user_prompt_timeout_is_machine_blocked(self):
        settings = _load_json(ROOT / "policy" / "managed-settings.json")
        source_lock = _load_json(ROOT / "SOURCE_LOCK.json")
        gate = _load_json(ROOT / "acceptance" / "CLAUDE_TURN_ADMISSION_TIMEOUT_GATE.json")

        groups = settings["hooks"]["UserPromptSubmit"]
        handlers = [handler for group in groups for handler in group.get("hooks", [])]
        canonical = [
            handler
            for handler in handlers
            if handler.get("command")
            == "/usr/local/bin/python -m clayverse.terminal_hooks user_prompt"
        ]
        self.assertEqual(len(canonical), 1, "canonical UserPromptSubmit handler must be unique")
        handler = canonical[0]

        self.assertEqual(handler.get("type"), "command")
        self.assertEqual(handler.get("timeout"), 10)
        self.assertGreaterEqual(_version_tuple(source_lock["claude_code"]["version"]), (2, 1, 208))

        if handler.get("type") in FAIL_OPEN_TYPES and isinstance(handler.get("timeout"), (int, float)):
            self.assertEqual(gate["status"], "BLOCKED_UPSTREAM_USERPROMPT_TIMEOUT_FAIL_OPEN")
            self.assertEqual(
                gate["upstream_evidence"]["timeout_semantics"],
                "PROMPT_CONTINUES_ON_TIMEOUT_WITH_HOOK_OUTPUT_DISCARDED",
            )
            self.assertFalse(gate["current_consequence"]["fail_closed_turn_admission_proven"])
            self.assertFalse(gate["current_consequence"]["whole_product_acceptance_allowed"])
            self.assertFalse(gate["current_consequence"]["whole_product_runtime_credit"])
            self.assertEqual(gate["runtime_credit"], 0)

    def test_blocker_cannot_claim_runtime_failure_or_runtime_credit(self):
        gate = _load_json(ROOT / "acceptance" / "CLAUDE_TURN_ADMISSION_TIMEOUT_GATE.json")
        note = gate["current_consequence"]["note"].lower()
        self.assertIn("not a claim", note)
        self.assertIn("runtime", note)
        self.assertEqual(gate["evidence_class"], "SOURCE_PLUS_CURRENT_UPSTREAM_SEMANTICS")
        self.assertEqual(gate["runtime_credit"], 0)

    def test_pseudo_fixes_remain_explicitly_rejected(self):
        gate = _load_json(ROOT / "acceptance" / "CLAUDE_TURN_ADMISSION_TIMEOUT_GATE.json")
        rejected = set(gate["rejected_pseudo_fixes"])
        self.assertIn("increase_command_hook_timeout_only", rejected)
        self.assertIn("rely_on_hook_exit_code_2_after_timeout", rejected)
        self.assertIn("rely_on_stop_or_stopfailure_to_retroactively_admit_missing_prompt", rejected)


if __name__ == "__main__":
    unittest.main()
