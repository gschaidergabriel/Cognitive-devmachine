#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


validator = load_module("validate_sft_v1", HERE / "validate_sft_v1.py")
generator = load_module("generate_sft_v1", HERE / "generate_sft_v1.py")


def valid_base():
    return '''module clay.cog.turn
fn think(i:Map)->Map {
  let c = cog_new()
  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))
  role_bind(c,cfg("application.role"))
  goal_bind(c,cfg("application.goal"))
  personality_bind(c,cfg("application.personality"))
  focus_set(c,"safe")
  return c
}'''


class ClayCodeAdmissionTests(unittest.TestCase):
    def assertRejected(self, code, needle):
        errors = validator.validate_code(code)
        self.assertTrue(errors, "mutation unexpectedly admitted")
        self.assertTrue(any(needle in e for e in errors), errors)

    def test_current_generator_all_1650_targets_pass_strict_admission(self):
        rows = generator.build()
        self.assertEqual(1650, len(rows))
        failures = []
        for i, row in enumerate(rows):
            errors = validator.validate_code(row["messages"][-1]["content"])
            if errors:
                failures.append((i, row["family"], errors))
        self.assertEqual([], failures[:20], f"{len(failures)} generated targets failed")

    def test_rejects_free_prose_outside_string_literals(self):
        self.assertRejected(valid_base().replace("  return c", "  THIS IS FREE PROSE\n  return c"), "not_call")

    def test_rejects_unknown_intrinsic(self):
        self.assertRejected(valid_base().replace("  return c", "  invented_magic(c)\n  return c"), "unknown_intrinsic")

    def test_rejects_bad_arity(self):
        self.assertRejected(valid_base().replace('focus_set(c,"safe")', 'focus_set(c)'), "bad_arity")

    def test_rejects_trailing_garbage_after_call(self):
        self.assertRejected(valid_base().replace('focus_set(c,"safe")', 'focus_set(c,"safe") trailing garbage'), "trailing_after_call")

    def test_rejects_unknown_constructor(self):
        self.assertRejected(valid_base().replace('let c = cog_new()', 'let c = alien_constructor()'), "unknown_intrinsic")

    def test_rejects_commit_when_omega_gates_occur_after_commit(self):
        code = valid_base().replace(
            '  focus_set(c,"safe")',
            '''  let w = omega_new(c,"w0")
  omega_bind(w,"operation","db.lookup")
  omega_arg(w,"table","events","Identifier")
  omega_schema(w,"tool.db.lookup/v1")
  omega_authority(w,cfg("architecture.effect_authority"))
  omega_generation(w,cfg("state.generation"))
  omega_commit_candidate(c,w)
  omega_validate(w,"grammar")
  omega_validate(w,"types")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_validate(w,"generation")''',
        )
        self.assertRejected(code, "omega_missing_gate")

    def test_accepts_valid_omega_candidate_with_precommit_gates(self):
        code = valid_base().replace(
            '  focus_set(c,"safe")',
            '''  let w = omega_new(c,"w0")
  omega_bind(w,"operation","db.lookup")
  omega_arg(w,"table","events","Identifier")
  omega_schema(w,"tool.db.lookup/v1")
  omega_authority(w,cfg("architecture.effect_authority"))
  omega_generation(w,cfg("state.generation"))
  omega_validate(w,"grammar")
  omega_validate(w,"types")
  omega_validate(w,"schema")
  omega_validate(w,"authority")
  omega_validate(w,"generation")
  omega_commit_candidate(c,w)''',
        )
        self.assertEqual([], validator.validate_code(code))


if __name__ == "__main__":
    unittest.main()
