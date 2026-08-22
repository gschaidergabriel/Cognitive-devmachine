#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from claycode_calls_v2 import extract_calls, fn_counts
from eval_outputs_v1 import marker_present
from validate_sft_v1 import validate_code

def head():
    return ('module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
            '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
            '  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n')
def wrap(extra): return head()+extra+'  return c\n}'
def valid_omega(grammar='  omega_validate(w,"grammar")\n',commit='  omega_commit_candidate(c,w)\n'):
    return ('  let w = omega_new(c,"w0")\n  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'+grammar+
            '  omega_validate(w,"types")\n  omega_validate(w,"schema")\n  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'+commit)

class TopLevelSemanticTests(unittest.TestCase):
    def test_comment_calls_are_not_counted(self):
        self.assertEqual(fn_counts('// hyper_alt(hp,"x")').get('hyper_alt',0),0)
        self.assertEqual(fn_counts('/* hyper_alt(hp,"x") */').get('hyper_alt',0),0)
    def test_depth_distinguishes_nested_from_turn_body(self):
        code='fn think(i:Map)->Map {\n if false {\n  hyper_alt(hp,"x")\n }\n hyper_alt(hp,"y")\n}'
        self.assertEqual([x['depth'] for x in extract_calls(code) if x['fn']=='hyper_alt'],[2,1])
    def test_nested_dead_marker_gets_no_ood_credit(self):
        self.assertFalse(marker_present(wrap('  if false {\n    hyper_alt(hp,"x")\n  }\n'),'hyper_alt(hp,'))
    def test_top_level_marker_gets_credit(self):
        self.assertTrue(marker_present(wrap('  hyper_alt(hp,"x")\n'),'hyper_alt(hp,'))
    def test_nested_cfg_expression_remains_visible(self):
        self.assertTrue(marker_present(wrap(''),'cfg("entity.id")'))
    def test_comment_syntax_fails_admission_closed(self):
        self.assertIn('comment_syntax_forbidden',validate_code(wrap('  // harmless\n')))
    def test_nested_runtime_binding_fails(self):
        code=('module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
              '  if false {\n    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  }\n'
              '  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n'
              '  personality_bind(c,cfg("application.personality"))\n  return c\n}')
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',validate_code(code))
    def test_valid_top_level_omega_passes(self):
        self.assertEqual(validate_code(wrap(valid_omega())),[])
    def test_nested_omega_gate_fails(self):
        self.assertIn('omega_gate_not_exact_top_level:grammar',validate_code(wrap(valid_omega('  if false {\n    omega_validate(w,"grammar")\n  }\n'))))
    def test_duplicate_omega_gate_fails(self):
        self.assertIn('omega_validate_call_count:6',validate_code(wrap(valid_omega('  omega_validate(w,"grammar")\n  omega_validate(w,"grammar")\n'))))
    def test_nested_commit_fails(self):
        self.assertIn('omega_commit_not_exact_top_level',validate_code(wrap(valid_omega(commit='  if false {\n    omega_commit_candidate(c,w)\n  }\n'))))
    def test_quoted_fake_duplicate_does_not_poison_gate(self):
        self.assertEqual(validate_code(wrap(valid_omega()+'  state_note(c,"x","omega_validate(w,\\"grammar\\")","REPORTED")\n')),[])

if __name__=='__main__': unittest.main()
