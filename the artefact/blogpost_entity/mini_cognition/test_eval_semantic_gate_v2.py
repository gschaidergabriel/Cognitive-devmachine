#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location("eval_outputs_v1",HERE/"eval_outputs_v1.py")
ev=importlib.util.module_from_spec(spec); spec.loader.exec_module(ev)

def head():
    return ('module clay.cog.turn\nfn think(i:Map)->Map {\n'
      '  let c = cog_new()\n'
      '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
      '  role_bind(c,cfg("application.role"))\n'
      '  goal_bind(c,cfg("application.goal"))\n'
      '  personality_bind(c,cfg("application.personality"))\n')
def tail(): return '  return c\n}'

class GateV2Tests(unittest.TestCase):
    def test_missing_exact_args_and_schema_no_longer_pass_valid_omega(self):
        case={"required_lines_once":[
          'omega_bind(w,"operation","calendar.create")',
          'omega_arg(w,"title","Review 7","String")',
          'omega_schema(w,"tool.calendar.create/v1")',
          'omega_authority(w,cfg("architecture.effect_authority"))',
          'omega_generation(w,cfg("state.generation"))',
          'omega_validate(w,"grammar")','omega_validate(w,"types")','omega_validate(w,"schema")',
          'omega_validate(w,"authority")','omega_validate(w,"generation")','omega_commit_candidate(c,w)'],
          "forbidden_prefixes":["omega_reject("]}
        bad=head()+('  let w = omega_new(c,"w0")\n'
          '  omega_bind(w,"operation","calendar.create")\n'
          '  omega_authority(w,cfg("architecture.effect_authority"))\n'
          '  omega_generation(w,cfg("state.generation"))\n'
          '  omega_validate(w,"grammar")\n  omega_validate(w,"types")\n  omega_validate(w,"schema")\n'
          '  omega_validate(w,"authority")\n  omega_validate(w,"generation")\n  omega_commit_candidate(c,w)\n')+tail()
        structural,semantic,errors=ev.score_case(case,bad)
        self.assertTrue(structural)
        self.assertFalse(semantic)
        self.assertTrue(any('omega_arg' in x for x in errors))
        self.assertTrue(any('omega_schema' in x for x in errors))

    def test_neutrality_requires_actual_policy_not_common_header(self):
        case={"required_lines_once":[
          'self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
          'role_bind(c,cfg("application.role"))',
          'state_note(c,"identity_source","runtime_cfg","VERIFIED")',
          'state_note(c,"application_source","runtime_cfg","VERIFIED")',
          'policy_select(c,"preserve_checkpoint_neutrality")']}
        generic=head()+'  focus_set(c,"generic")\n'+tail()
        structural,semantic,errors=ev.score_case(case,generic)
        self.assertTrue(structural)
        self.assertFalse(semantic)
        self.assertGreaterEqual(len(errors),3)

    def test_required_line_hidden_as_string_does_not_count(self):
        case={"required_lines_once":['omega_schema(w,"tool.calendar.create/v1")']}
        stuffed=head()+'  grf_observe(c,"R0","omega_schema(w,\\"tool.calendar.create/v1\\")","REPORTED")\n'+tail()
        structural,semantic,errors=ev.score_case(case,stuffed)
        self.assertTrue(structural)
        self.assertFalse(semantic)
        self.assertIn('required_line_count:omega_schema(w,"tool.calendar.create/v1"):0',errors)

    def test_exact_contract_accepts_one_matching_line_each(self):
        case={"required_lines_once":[
          'state_note(c,"identity_source","runtime_cfg","VERIFIED")',
          'policy_select(c,"preserve_checkpoint_neutrality")'],
          "forbidden_prefixes":['self_bind(c,"Zero"']}
        good=head()+('  state_note(c,"identity_source","runtime_cfg","VERIFIED")\n'
                     '  policy_select(c,"preserve_checkpoint_neutrality")\n')+tail()
        structural,semantic,errors=ev.score_case(case,good)
        self.assertTrue(structural); self.assertTrue(semantic); self.assertEqual([],errors)

if __name__=="__main__": unittest.main(verbosity=2)
