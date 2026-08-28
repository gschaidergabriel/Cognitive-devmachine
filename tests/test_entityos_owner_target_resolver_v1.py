import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "tools" / "entityos_owner_target_resolver_v1.py"
spec = importlib.util.spec_from_file_location("resolver", MODULE)
resolver = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(resolver)

OWNER_TEXT = """# Owner correction — Zero/EntityOS cognition simulated on variable HCU grid
Status: **CURRENT OWNER TARGET / HIGHEST PRECEDENCE WHERE CONFLICTING**
`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`
The cognitive grid is not fixed to GRID10.
`N` is a runtime parameter, not the definition of the architecture.
`SIMULATE COGNITION; STORE DURABLE DATA.`
No unproven activation-level access to Claude Code may be claimed.
GRID10 may be used as one benchmark configuration, but has no special final authority.
"""


def write_fixture(root: Path, *, owner_text: str = OWNER_TEXT, stale_secondary: bool = True):
    owner_rel = Path("research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md")
    owner_path = root / owner_rel
    owner_path.parent.mkdir(parents=True, exist_ok=True)
    owner_path.write_text(owner_text, encoding="utf-8")

    idx_rel = Path("research_entity/continuity/CURRENT_OWNER_PRODUCT_TARGET.json")
    idx_path = root / idx_rel
    idx_path.parent.mkdir(parents=True, exist_ok=True)
    idx = {
        "schema": "CLAY_CURRENT_OWNER_PRODUCT_TARGET/v1",
        "status": "NON_AUTHORITATIVE_RESOLUTION_INDEX_NEWEST_EXPLICIT_OWNER_STILL_WINS",
        "persistent_entity": "Clay",
        "product": "EntityOS",
        "architecture": "HCU",
        "owner_directive_path": str(owner_rel),
        "owner_directive_git_blob_sha1": resolver.git_blob_sha1(owner_text.encode()),
        "grid_size_policy": "RUNTIME_VARIABLE_N",
        "grid10_status": "BENCHMARK_FIXTURE_ONLY_NO_SPECIAL_FINAL_AUTHORITY",
        "finished_runtime": ["VARIABLE_COGNITIVE_GRID", "PERSISTENT_DATABASE", "CLAUDE_CODE"],
        "durable_state_rule": "SIMULATE_COGNITION_STORE_DURABLE_DATA",
        "claude_code_role": "STRONG_MODEL_TOOL_CODE_PARTNER_NOT_REPLACED_BY_08B_GRID",
        "global_jspace_bridge": "STRONGEST_EXPOSED_INTERFACE_ONLY_NO_UNPROVEN_CLAUDE_CODE_ACTIVATION_ACCESS",
        "small_model_target": "QWEN3_5_08B_CLASS_LOW_REFUSAL_WITH_REQUIRED_COGNITIVE_CAPABILITY_RETENTION",
        "go_priority_chain": ["ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS", "COGNITIVE_PROCESS_ABI"],
        "credit_boundary": {"entityos_whole_runtime_credit": 0, "hcu_full_runtime_credit": 0, "jspace_model_runtime_credit": 0, "training_credit": 0},
    }
    idx_path.write_text(json.dumps(idx), encoding="utf-8")

    if stale_secondary:
        b = root / "research_entity/continuity/BOOTSTRAP_MINIMAL.json"
        b.write_text(json.dumps({"scale_target": {"baseline_logical_cells": 10}}), encoding="utf-8")
        p = root / "research_entity/rooms/PROGRAM_STATE.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"mode_policy": {"baseline": "GRID10"}, "scale_policy": {"baseline_logical_cells": 10}}), encoding="utf-8")


class ResolverTests(unittest.TestCase):
    def test_owner_wins_and_reports_stale_secondary_surfaces(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, stale_secondary=True)
            out = resolver.resolve_owner_target(root)
            self.assertEqual(out["status"], "PASS_OWNER_AUTHORITY_WITH_SECONDARY_SURFACE_DRIFT")
            self.assertEqual(out["grid_size_policy"], "RUNTIME_VARIABLE_N")
            self.assertEqual(out["grid10_status"], "BENCHMARK_FIXTURE_ONLY_NO_SPECIAL_FINAL_AUTHORITY")
            self.assertEqual(len(out["secondary_surface_drift"]), 3)

    def test_strict_secondary_alignment_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, stale_secondary=True)
            with self.assertRaisesRegex(ValueError, "secondary authority surfaces lag"):
                resolver.resolve_owner_target(root, require_secondary_alignment=True)

    def test_owner_blob_identity_mismatch_fails_closed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, stale_secondary=False)
            owner = root / "research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md"
            owner.write_text(OWNER_TEXT + "tamper\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                resolver.resolve_owner_target(root)

    def test_fixed_grid_owner_rewrite_cannot_sneak_past_marker_guard(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            fixed = OWNER_TEXT.replace("The cognitive grid is not fixed to GRID10.\n", "The cognitive grid is fixed to GRID10.\n")
            write_fixture(root, owner_text=fixed, stale_secondary=False)
            with self.assertRaisesRegex(ValueError, "missing required invariants"):
                resolver.resolve_owner_target(root)

    def test_jspace_claim_ceiling_is_explicit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            write_fixture(root, stale_secondary=False)
            out = resolver.resolve_owner_target(root)
            self.assertIn("NO_UNPROVEN_CLAUDE_CODE_ACTIVATION_ACCESS", out["global_jspace_bridge"])
            self.assertEqual(out["credit_boundary"]["jspace_model_runtime_credit"], 0)


if __name__ == "__main__":
    unittest.main()
