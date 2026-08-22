#!/usr/bin/env python3
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))

from claycode_syntax_v1 import extract_calls, fn_counts
from eval_outputs_v1 import marker_present
from validate_sft_v1 import validate_code


def head():
    return (
        'module clay.cog.turn\n'
        'fn think(i:Map)->Map {\n'
        '  let c = cog_new()\n'
        '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
        '  role_bind(c,cfg("application.role"))\n'
        '  goal_bind(c,cfg("application.goal"))\n'
        '  personality_bind(c,cfg("application.personality"))\n'
    )


def wrap(extra):
    return head()+extra+'  return c\n}'


def valid_omega(grammar='  omega_validate(w,"grammar")\n',commit='  omega_commit_candidate(c,w)\n'):
    return (
        '  let w = omega_new(c,"w0")\n'
        '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        '  omega_generation(w,cfg("state.generation"))\n'
        + grammar +
        '  omega_validate(w,"types")\n'
        '  omega_validate(w,"schema")\n'
        '  omega_validate(w,"authority")\n'
        '  omega_validate(w,"generation")\n'
        + commit
    )


class SharedSyntaxTests(unittest.TestCase):
    def test_quoted_call_is_not_counted(self):
        code='state_note(c,"spoof","hyper_alt(hp,\\"x\\")","REPORTED")'
        self.assertEqual(fn_counts(code).get('hyper_alt',0),0)

    def test_line_comment_call_is_not_counted(self):
        self.assertEqual(fn_counts('// hyper_alt(hp,"x")').get('hyper_alt',0),0)

    def test_block_comment_call_is_not_counted(self):
        self.assertEqual(fn_counts('/* hyper_alt(hp,"x") */').get('hyper_alt',0),0)

    def test_depth_distinguishes_dead_branch_from_turn_body(self):
        code='fn think(i:Map)->Map {\n if false {\n  hyper_alt(hp,"x")\n }\n hyper_alt(hp,"y")\n}'
        rows=[x for x in extract_calls(code) if x['fn']=='hyper_alt']
        self.assertEqual([x['depth'] for x in rows],[2,1])


class PromotionMarkerTests(unittest.TestCase):
    def test_top_level_hyper_marker_passes(self):
        self.assertTrue(marker_present(wrap('  hyper_alt(hp,"x")\n'),'hyper_alt(hp,'))

    def test_string_hyper_marker_fails(self):
        code=wrap('  state_note(c,"spoof","hyper_alt(hp,","REPORTED")\n')
        self.assertFalse(marker_present(code,'hyper_alt(hp,'))

    def test_comment_hyper_marker_fails(self):
        code=wrap('  // hyper_alt(hp,"x")\n')
        self.assertFalse(marker_present(code,'hyper_alt(hp,'))

    def test_nested_dead_hyper_marker_fails(self):
        code=wrap('  if false {\n    hyper_alt(hp,"x")\n  }\n')
        self.assertFalse(marker_present(code,'hyper_alt(hp,'))

    def test_nested_cfg_expression_remains_visible(self):
        self.assertTrue(marker_present(wrap(''),'cfg("entity.id")'))


class CanonicalAdmissionTests(unittest.TestCase):
    def test_comment_syntax_fails_closed(self):
        errors=validate_code(wrap('  // omega_validate(w,"grammar")\n'))
        self.assertIn('comment_syntax_forbidden',errors)

    def test_nested_runtime_binding_fails(self):
        code=(
            'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  if false {\n    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  }\n'
            '  role_bind(c,cfg("application.role"))\n'
            '  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n'
            '  return c\n}'
        )
        errors=validate_code(code)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_valid_top_level_omega_passes(self):
        self.assertEqual(validate_code(wrap(valid_omega())),[])

    def test_nested_omega_gate_fails(self):
        errors=validate_code(wrap(valid_omega('  if false {\n    omega_validate(w,"grammar")\n  }\n')))
        self.assertIn('omega_gate_not_exact_top_level:grammar',errors)

    def test_duplicate_omega_gate_fails(self):
        errors=validate_code(wrap(valid_omega('  omega_validate(w,"grammar")\n  omega_validate(w,"grammar")\n')))
        self.assertIn('omega_validate_call_count:6',errors)

    def test_nested_commit_fails(self):
        errors=validate_code(wrap(valid_omega(commit='  if false {\n    omega_commit_candidate(c,w)\n  }\n')))
        self.assertIn('omega_commit_not_exact_top_level',errors)

    def test_quoted_fake_duplicate_does_not_poison_real_gate(self):
        code=wrap(valid_omega()+'  state_note(c,"x","omega_validate(w,\\"grammar\\")","REPORTED")\n')
        self.assertEqual(validate_code(code),[])


if __name__=='__main__':
    unittest.main()
