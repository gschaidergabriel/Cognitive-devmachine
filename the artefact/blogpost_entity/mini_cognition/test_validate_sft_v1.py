#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path

from generate_sft_v2 import build as build_v2

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


def valid_omega(grammar='  omega_validate(w,"grammar")\n'):
    return (
        '  let w = omega_new(c,"w0")\n'
        '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        '  omega_generation(w,cfg("state.generation"))\n'+grammar+
        '  omega_validate(w,"types")\n'
        '  omega_validate(w,"schema")\n'
        '  omega_validate(w,"authority")\n'
        '  omega_validate(w,"generation")\n'
        '  omega_commit_candidate(c,w)\n'
    )


class CanonicalClayCodeAdmissionTests(unittest.TestCase):
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
            'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  state_note(c,"spoof","self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))","REPORTED")\n'
            '  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n  return c\n}'
        )
        errors=V.validate_code(code)
        self.assertIn('binding_call_count:self_bind:0',errors)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_nested_binding_cannot_satisfy_runtime_binding(self):
        code=(
            'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  if false {\n    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  }\n'
            '  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n  return c\n}'
        )
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',V.validate_code(code))

    def test_unterminated_string_is_rejected(self):
        errors=V.validate_code(valid_code('  state_note(c,"x","unterminated)\n'))
        self.assertTrue('unterminated_string' in errors or 'multiline_or_unclosed_string' in errors,errors)

    def test_comment_syntax_fails_closed(self):
        self.assertIn('comment_syntax_forbidden',V.validate_code(valid_code('  /* omega_validate(w,"grammar") */\n')))

    def test_valid_omega_sequence_passes(self):
        self.assertEqual(V.validate_code(valid_code(valid_omega())),[])

    def test_omega_gate_inside_string_does_not_count(self):
        bait='  let bait = "omega_validate(w,\\"grammar\\")"\n'
        self.assertIn('omega_missing_gate:grammar',V.validate_code(valid_code(valid_omega(bait))))

    def test_omega_gate_nested_under_control_flow_does_not_count(self):
        nested='  if false {\n    omega_validate(w,"grammar")\n  }\n'
        self.assertIn('omega_missing_gate:grammar',V.validate_code(valid_code(valid_omega(nested))))

    def test_unknown_intrinsic_fails_closed(self):
        self.assertIn('unknown_intrinsic:mystery_focus',V.validate_code(valid_code('  mystery_focus(c,"x")\n')))

    def test_wrong_intrinsic_arity_fails_closed(self):
        self.assertIn('arity:focus_set:3!=2',V.validate_code(valid_code('  focus_set(c,"x","y")\n')))

    def test_literal_punctuation_does_not_change_arity(self):
        self.assertEqual(V.validate_code(valid_code('  focus_set(c,"literal,(with),commas")\n')),[])

    def test_all_sft_v2_paid_training_targets_use_same_admission_language(self):
        train,valid=build_v2()
        self.assertEqual((len(train),len(valid)),(1485,165))
        bad=[]
        for split,rows in (("train",train),("validation",valid)):
            for i,row in enumerate(rows):
                errors=V.validate_code(row["messages"][-1]["content"])
                if errors: bad.append((split,i,row["family"],errors))
        self.assertEqual(bad,[],bad[:20])


if __name__=='__main__':
    unittest.main()
