from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from validate_claycode_cognitive_authority_kernel_v1 import KernelValidationError, validate

KERNEL = ROOT / "research_entity/global/CLAYCODE_COGNITIVE_AUTHORITY_KERNEL_v1.clay"
GRAMMAR = ROOT / "research_entity/claycode/base/D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
CENSUS = ROOT / "research_entity/global/ZERO_ENTITYOS_COGNITIVE_PROCESS_CENSUS_v1.json"
BOUNDARY = ROOT / "research_entity/global/DB_VS_SIMULATION_BOUNDARY_v1.json"


class ClayCodeCognitiveAuthorityKernelV1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = KERNEL.read_text(encoding="utf-8")
        cls.grammar = GRAMMAR.read_text(encoding="utf-8")
        cls.census = json.loads(CENSUS.read_text(encoding="utf-8"))
        cls.boundary = json.loads(BOUNDARY.read_text(encoding="utf-8"))

    def test_exact_kernel_compiles_executes_and_lowers(self):
        result = validate(self.source, self.grammar, self.census, self.boundary)
        self.assertTrue(result["ok"])
        self.assertEqual("claycode.typed-ir.v0", result["compiler_ir_schema"])
        self.assertEqual(18, result["function_count"])
        self.assertEqual("PASS", result["c11_lowering"])
        self.assertEqual([1, 2, 10, 20, 64, 600], result["n_discriminator_values"])
        self.assertEqual("GLOBAL_WORKSPACE", result["next_gate"])
        for key in (
            "model_runtime_credit", "db_runtime_credit", "claude_runtime_credit",
            "jspace_causal_credit", "full_hcu_credit", "whole_entityos_credit", "training_credit",
        ):
            self.assertEqual(0, result[key])

    def test_n_cannot_enter_semantic_process_identity(self):
        bad = self.source.replace(
            "fn semantic_process_identity(process:Int,n:Int)->Int=process",
            "fn semantic_process_identity(process:Int,n:Int)->Int=process+n",
        )
        with self.assertRaisesRegex(KernelValidationError, "N_CHANGED_PROCESS_SEMANTICS"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_direct_db_commit_cannot_be_enabled(self):
        bad = self.source.replace(
            "fn direct_cognitive_db_commit_allowed(process:Int)->Bool=false",
            "fn direct_cognitive_db_commit_allowed(process:Int)->Bool=process==15",
        )
        with self.assertRaisesRegex(KernelValidationError, "DIRECT_DB_COMMIT_ALLOWED"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_effect_authority_cannot_move_from_zecp17(self):
        bad = self.source.replace(
            "fn real_effect_authority_process(process:Int)->Bool=process==17",
            "fn real_effect_authority_process(process:Int)->Bool=process==16",
        )
        with self.assertRaisesRegex(KernelValidationError, "PROCESS_ROLE_BINDING_DRIFT:real_effect_authority_process"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_unknown_effect_cannot_be_blindly_replayed(self):
        bad = self.source.replace(
            "fn unknown_effect_blind_replay_allowed(outcome_class:Int)->Bool=false",
            "fn unknown_effect_blind_replay_allowed(outcome_class:Int)->Bool=outcome_class==0",
        )
        with self.assertRaisesRegex(KernelValidationError, "UNKNOWN_EFFECT_BLIND_REPLAY_ALLOWED"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_claude_cannot_gain_direct_canonical_write(self):
        bad = self.source.replace(
            "fn claude_direct_canonical_write_allowed(process:Int)->Bool=false",
            "fn claude_direct_canonical_write_allowed(process:Int)->Bool=process==14",
        )
        with self.assertRaisesRegex(KernelValidationError, "CLAUDE_DIRECT_CANONICAL_WRITE_ALLOWED"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_jspace_cannot_gain_direct_truth_authority(self):
        bad = self.source.replace(
            "fn jspace_direct_truth_allowed(process:Int)->Bool=false",
            "fn jspace_direct_truth_allowed(process:Int)->Bool=process==10",
        )
        with self.assertRaisesRegex(KernelValidationError, "JSPACE_DIRECT_TRUTH_ALLOWED"):
            validate(bad, self.grammar, self.census, self.boundary)

    def test_census_role_drift_fails_closed(self):
        bad_census = copy.deepcopy(self.census)
        process = next(item for item in bad_census["processes"] if item["id"] == "ZECP17")
        process["name"] = "MODEL_EFFECT_EXECUTOR"
        with self.assertRaisesRegex(KernelValidationError, "CENSUS_ROLE_DRIFT:ZECP17"):
            validate(self.source, self.grammar, bad_census, self.boundary)

    def test_fixed_grid_boundary_regression_fails_closed(self):
        bad_boundary = copy.deepcopy(self.boundary)
        bad_boundary["authority"]["grid_law"] = "GRID10_FIXED"
        with self.assertRaisesRegex(KernelValidationError, "VARIABLE_N_BOUNDARY_REQUIRED"):
            validate(self.source, self.grammar, self.census, bad_boundary)


if __name__ == "__main__":
    unittest.main()
