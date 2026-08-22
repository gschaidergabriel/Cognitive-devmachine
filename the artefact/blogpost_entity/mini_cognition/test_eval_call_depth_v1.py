#!/usr/bin/env python3
import sys, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent; sys.path.insert(0,str(HERE))
from claycode_calls_v2 import extract_calls
from eval_outputs_v1 import marker_present

HEAD='module clay.cog.turn\nfn think(i:Map)->Map {\n  let c = cog_new()\n  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  role_bind(c,cfg("application.role"))\n  goal_bind(c,cfg("application.goal"))\n  personality_bind(c,cfg("application.personality"))\n'
TAIL='  return c\n}'

class OODCallDepthTests(unittest.TestCase):
    def test_depth_observed(self):
        code=HEAD+'  if false {\n    hyper_alt(hp,"nested","PLAUSIBLE")\n  }\n  hyper_alt(hp,"top","PLAUSIBLE")\n'+TAIL
        self.assertEqual([x['depth'] for x in extract_calls(code) if x['fn']=='hyper_alt'],[2,1])
    def test_dead_branch_hyper_gets_no_credit(self):
        code=HEAD+'  if false {\n    hyper_alt(hp,"nested","PLAUSIBLE")\n  }\n'+TAIL
        self.assertFalse(marker_present(code,'hyper_alt(hp,'))
    def test_top_level_hyper_gets_credit(self):
        self.assertTrue(marker_present(HEAD+'  hyper_alt(hp,"top","PLAUSIBLE")\n'+TAIL,'hyper_alt(hp,'))
    def test_dead_branch_reject_gets_no_credit(self):
        code=HEAD+'  if false {\n    omega_reject(w,"fake")\n  }\n'+TAIL
        self.assertFalse(marker_present(code,'omega_reject('))
    def test_nested_cfg_expression_still_gets_credit(self):
        self.assertTrue(marker_present(HEAD+TAIL,'cfg("entity.id")'))
    def test_comment_and_string_remain_non_calls(self):
        code=HEAD+'  // hyper_alt(hp,"comment","PLAUSIBLE")\n  state_note(c,"spoof","hyper_alt(hp,","REPORTED")\n'+TAIL
        self.assertFalse(marker_present(code,'hyper_alt(hp,'))

if __name__=='__main__': unittest.main()
