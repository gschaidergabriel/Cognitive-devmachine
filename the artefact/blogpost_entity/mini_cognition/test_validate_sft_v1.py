#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("claycog_validate",HERE/"validate_sft_v1.py")
V=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def valid_code(extra=""):
    return (
        'module clay.cog.turn\n'
        'fn think(i:Map)->Map {\n'
        '  let c = cog_new()\n'
        '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
        '  role_bind(c,cfg("application.role"))\n'
        '  goal_bind(c,cfg("application.goal"))\n'
        '  personality_bind(c,cfg("application.personality"))\n'
        + extra +
        '  return c\n'
        '}'
    )


def valid_omega(grammar_line='  omega_validate(w,"grammar")\n',commit_line='  omega_commit_candidate(c,w)\n'):
    return (
        '  let w = omega_new(c,"w0")\n'
        '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        '  omega_generation(w,cfg("state.generation"))\n'
        + grammar_line +
        '  omega_validate(w,"types")\n'
        '  omega_validate(w,"schema")\n'
        '  omega_validate(w,"authority")\n'
        '  omega_validate(w,"generation")\n'
        + commit_line
    )


class RuntimeBindingGateTests(unittest.TestCase):
    def test_canonical_runtime_bindings_pass(self):
        self.assertEqual(V.validate_code(valid_code()),[])

    def test_second_hardcoded_identity_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  self_bind(c,"other","fork")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:self_bind:2') for x in errors),errors)

    def test_second_hardcoded_role_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  role_bind(c,"blogger")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:role_bind:2') for x in errors),errors)

    def test_second_hardcoded_goal_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  goal_bind(c,"publish posts")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:goal_bind:2') for x in errors),errors)

    def test_second_hardcoded_personality_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  personality_bind(c,"named persona")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:personality_bind:2') for x in errors),errors)

    def test_required_binding_text_inside_string_cannot_spoof_structure(self):
        code=(
            'module clay.cog.turn\n'
            'fn think(i:Map)->Map {\n'
            '  let c = cog_new()\n'
            '  state_note(c,"spoof","self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))","REPORTED")\n'
            '  role_bind(c,cfg("application.role"))\n'
            '  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n'
            '  return c\n'
            '}'
        )
        errors=V.validate_code(code)
        self.assertIn('binding_call_count:self_bind:0',errors)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_required_binding_inside_comment_fails_closed(self):
        code=(
            'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  /* self_bind(c,cfg("entity.id"),cfg("entity.continuity")) */\n'
            '  role_bind(c,cfg("application.role"))\n'
            '  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n'
            '  return c\n}'
        )
        errors=V.validate_code(code)
        self.assertIn('comment_syntax_forbidden',errors)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_required_binding_nested_under_control_flow_is_rejected(self):
        code=(
            'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  if false {\n'
            '    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
            '  }\n'
            '  role_bind(c,cfg("application.role"))\n'
            '  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n'
            '  return c\n}'
        )
        errors=V.validate_code(code)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_unterminated_string_is_rejected(self):
        code=valid_code('  state_note(c,"x","unterminated)\n')
        errors=V.validate_code(code)
        self.assertIn('unterminated_string',errors)


class OmegaAdmissionGateTests(unittest.TestCase):
    def test_valid_omega_commit_passes(self):
        self.assertEqual(V.validate_code(valid_code(valid_omega())),[])

    def test_omega_gate_inside_comment_fails_closed(self):
        code=valid_code(valid_omega('  /* omega_validate(w,"grammar") */\n'))
        self.assertIn('comment_syntax_forbidden',V.validate_code(code))

    def test_omega_gate_nested_under_control_flow_is_rejected(self):
        code=valid_code(valid_omega('  if false {\n    omega_validate(w,"grammar")\n  }\n'))
        errors=V.validate_code(code)
        self.assertIn('omega_gate_not_exact_top_level:grammar:0',errors)

    def test_omega_commit_nested_under_control_flow_is_rejected(self):
        code=valid_code(valid_omega(commit_line='  if false {\n    omega_commit_candidate(c,w)\n  }\n'))
        errors=V.validate_code(code)
        self.assertIn('omega_commit_not_exact_top_level:0',errors)

    def test_duplicate_omega_gate_is_rejected(self):
        code=valid_code(valid_omega('  omega_validate(w,"grammar")\n  omega_validate(w,"grammar")\n'))
        errors=V.validate_code(code)
        self.assertIn('omega_validate_call_count:6',errors)
        self.assertIn('omega_gate_not_exact_top_level:grammar:2',errors)

    def test_duplicate_commit_is_rejected(self):
        code=valid_code(valid_omega(commit_line='  omega_commit_candidate(c,w)\n  omega_commit_candidate(c,w)\n'))
        errors=V.validate_code(code)
        self.assertIn('omega_commit_call_count:2',errors)
        self.assertIn('omega_commit_not_exact_top_level:2',errors)

    def test_reject_and_commit_is_rejected(self):
        code=valid_code(valid_omega()+'  omega_reject(w,"bad")\n')
        self.assertIn('reject_and_commit',V.validate_code(code))


if __name__=='__main__':
    unittest.main()
