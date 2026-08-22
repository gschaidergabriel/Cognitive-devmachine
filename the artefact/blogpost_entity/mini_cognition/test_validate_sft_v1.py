#!/usr/bin/env python3
import unittest

from validate_sft_v1 import PREFIX, validate_code

BINDINGS = (
    '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n',
    '  role_bind(c,cfg("application.role"))\n',
    '  goal_bind(c,cfg("application.goal"))\n',
    '  personality_bind(c,cfg("application.personality"))\n',
)


def program(extra="", bindings=BINDINGS):
    return PREFIX + "".join(bindings) + extra + '  return c\n}'


class ClayCogValidatorFenceTests(unittest.TestCase):
    def test_minimal_real_bindings_pass(self):
        self.assertEqual(validate_code(program()), [])

    def test_required_binding_inside_string_does_not_count(self):
        spoof = '  let bait = "self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))"\n'
        code = program(spoof, bindings=BINDINGS[1:])
        errors = validate_code(code)
        self.assertTrue(any(x.startswith("missing_statement:self_bind") for x in errors), errors)

    def test_required_binding_inside_comment_fails_closed(self):
        spoof = '  /* self_bind(c,cfg("entity.id"),cfg("entity.continuity")) */\n'
        code = program(spoof, bindings=BINDINGS[1:])
        errors = validate_code(code)
        self.assertIn("comment_syntax_forbidden", errors)
        self.assertTrue(any(x.startswith("missing_statement:self_bind") for x in errors), errors)

    def test_required_binding_nested_under_control_flow_does_not_count(self):
        nested = (
            '  if false {\n'
            '    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
            '  }\n'
        )
        code = program(nested, bindings=BINDINGS[1:])
        errors = validate_code(code)
        self.assertTrue(any(x.startswith("missing_statement:self_bind") for x in errors), errors)

    def test_comment_wrapped_contract_fails_closed(self):
        code = program('  /* omega_validate(w,"grammar") */\n')
        self.assertIn("comment_syntax_forbidden", validate_code(code))

    def test_valid_omega_commit_requires_real_gate_statements(self):
        omega = (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'
            '  omega_validate(w,"grammar")\n'
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_commit_candidate(c,w)\n'
        )
        self.assertEqual(validate_code(program(omega)), [])

    def test_omega_gate_inside_string_does_not_count(self):
        omega = (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'
            '  let bait = "omega_validate(w,\\"grammar\\")"\n'
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_commit_candidate(c,w)\n'
        )
        errors = validate_code(program(omega))
        self.assertIn("omega_missing_gate:grammar", errors)

    def test_omega_gate_inside_comment_fails_closed(self):
        omega = (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'
            '  /* omega_validate(w,"grammar") */\n'
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_commit_candidate(c,w)\n'
        )
        self.assertIn("comment_syntax_forbidden", validate_code(program(omega)))

    def test_omega_gate_nested_under_control_flow_does_not_count(self):
        omega = (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'
            '  if false {\n'
            '    omega_validate(w,"grammar")\n'
            '  }\n'
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_commit_candidate(c,w)\n'
        )
        self.assertIn("omega_missing_gate:grammar", validate_code(program(omega)))

    def test_multiline_or_unclosed_string_fails_closed(self):
        code = program('  let bait = "unterminated\n')
        self.assertIn("multiline_or_unclosed_string", validate_code(code))

    def test_reject_and_commit_remains_invalid(self):
        omega = (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'
            '  omega_validate(w,"grammar")\n'
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_reject(w,"bad")\n'
            '  omega_commit_candidate(c,w)\n'
        )
        self.assertIn("reject_and_commit", validate_code(program(omega)))


if __name__ == "__main__":
    unittest.main()
