#!/usr/bin/env python3
import importlib.util,json,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE));S=importlib.util.spec_from_file_location('eval_outputs_v1',HERE/'eval_outputs_v1.py');mod=importlib.util.module_from_spec(S);S.loader.exec_module(mod)
class T(unittest.TestCase):
 def w(self,p,r):p.write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in r))
 def test_global_95_percent_cannot_mask_unseen_tool_failure(self):
  specs=[{'id':f'n{i}','family':'normal','must_contain':['OK'],'must_not_contain':[]} for i in range(20)]+[{'id':'a','family':mod.AMPUTATION_FAMILY,'must_contain':['AMP'],'must_not_contain':[]}];outs=[{'id':f'n{i}','output':'OK'} for i in range(20)]+[{'id':'a','output':'WRONG'}]
  with tempfile.TemporaryDirectory() as td:
   td=Path(td);sp=td/'s';op=td/'o';self.w(sp,specs);self.w(op,outs);old=mod.validate_code;mod.validate_code=lambda _:[]
   try:self.assertGreaterEqual(20/21,.95);self.assertEqual(1,mod.main(sp,op));outs[-1]['output']='AMP';self.w(op,outs);self.assertEqual(0,mod.main(sp,op))
   finally:mod.validate_code=old
if __name__=='__main__':unittest.main(verbosity=2)
