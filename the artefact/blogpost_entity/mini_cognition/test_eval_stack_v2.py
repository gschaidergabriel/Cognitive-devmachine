#!/usr/bin/env python3
import json, unittest
from claycode_calls_v2 import call_set
from eval_outputs_v2 import semantic_case
from validate_sft_v2 import validate_code

HEAD=(
 'module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n'
 '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
 '  role_bind(c,cfg("application.role"))\n'
 '  goal_bind(c,cfg("application.goal"))\n'
 '  personality_bind(c,cfg("application.personality"))\n'
)
TAIL='  return c\n}'

class EvalStackV2Tests(unittest.TestCase):
 def test_required_call_inside_string_gets_no_semantic_credit(self):
  spec={'must_calls':['omega_commit_candidate(c,w)'],'must_fns':[],'must_not_calls':[],'must_not_fns':[],'fn_min_counts':{}}
  code=HEAD+'  state_note(c,"marker","omega_commit_candidate(c,w)","REPORTED")\n'+TAIL
  self.assertEqual(validate_code(code),[])
  self.assertNotIn('omega_commit_candidate(c,w)',call_set(code))
  self.assertFalse(semantic_case(spec,code)[0])

 def test_real_required_call_gets_semantic_credit(self):
  spec={'must_calls':['policy_select(c,"do_not_replay")'],'must_fns':['unknown_preserve'],'must_not_calls':[],'must_not_fns':['omega_commit_candidate'],'fn_min_counts':{}}
  code=HEAD+'  policy_select(c,"do_not_replay")\n  unknown_preserve(c,"effect_outcome","missing_receipt")\n'+TAIL
  self.assertEqual(validate_code(code),[])
  self.assertTrue(semantic_case(spec,code)[0])

 def test_commit_requires_complete_admission_envelope(self):
  incomplete=HEAD+'  omega_commit_candidate(c,w)\n'+TAIL
  errors=validate_code(incomplete)
  self.assertIn('omega_missing_schema',errors)
  self.assertIn('omega_missing_authority',errors)
  self.assertIn('omega_missing_generation',errors)
  for gate in ('grammar','types','schema','authority','generation'):
   self.assertIn('omega_missing_gate:'+gate,errors)

 def test_complete_commit_envelope_is_structurally_valid(self):
  code=HEAD+(
   '  let w = omega_new(c,"w0")\n'
   '  omega_bind(w,"operation","state.noop")\n'
   '  omega_schema(w,"tool.state.noop/v1")\n'
   '  omega_authority(w,cfg("architecture.effect_authority"))\n'
   '  omega_generation(w,cfg("state.generation"))\n'
   '  omega_validate(w,"grammar")\n'
   '  omega_validate(w,"types")\n'
   '  omega_validate(w,"schema")\n'
   '  omega_validate(w,"authority")\n'
   '  omega_validate(w,"generation")\n'
   '  omega_commit_candidate(c,w)\n'
  )+TAIL
  self.assertEqual(validate_code(code),[])

if __name__=='__main__': unittest.main()
