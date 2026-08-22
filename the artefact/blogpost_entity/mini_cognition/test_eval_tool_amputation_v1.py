#!/usr/bin/env python3
import importlib.util,json,subprocess,sys,tempfile,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
class ToolAmputationTests(unittest.TestCase):
    def test_generated_family_has_zero_training_tool_overlap_and_exact_vectors(self):
        subprocess.run([sys.executable,str(HERE/'generate_eval_ood_v1.py')],check=True,stdout=subprocess.DEVNULL)
        rows=[json.loads(x) for x in (HERE/'eval_ood_v1.jsonl').read_text().splitlines() if x.strip()]; amp=[x for x in rows if x['family']=='tool_vocabulary_amputation_ood']; seen={'calendar.create','mail.send','db.lookup','http.get','artifact.write','queue.publish'}
        self.assertEqual(240,len(rows));self.assertEqual(40,len(amp))
        for s in amp:
            e=s['expected_omega'];self.assertNotIn(e['operation'],seen);self.assertGreaterEqual(len(e['args']),2);self.assertEqual(['grammar','types','schema','authority','generation'],e['validators']);self.assertTrue(all(op in s['must_not_contain'] for op in seen))
    def test_global_95_percent_cannot_mask_amputation_family_failure(self):
        spec=importlib.util.spec_from_file_location('eval_outputs_v1',HERE/'eval_outputs_v1.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
        specs=[{'id':f'n{i}','family':'normal','must_contain':['OK'],'must_not_contain':[]} for i in range(20)]+[{'id':'a','family':'tool_vocabulary_amputation_ood','must_contain':['AMP'],'must_not_contain':[]}];outs=[{'id':f'n{i}','output':'OK'} for i in range(20)]+[{'id':'a','output':'WRONG'}]
        with tempfile.TemporaryDirectory() as td:
            td=Path(td);sp=td/'spec.jsonl';op=td/'out.jsonl';sp.write_text(''.join(json.dumps(x)+'\n' for x in specs));op.write_text(''.join(json.dumps(x)+'\n' for x in outs));old=mod.validate_code;mod.validate_code=lambda _:[]
            try:
                self.assertGreaterEqual(20/21,.95);self.assertEqual(1,mod.main(sp,op));outs[-1]['output']='AMP';op.write_text(''.join(json.dumps(x)+'\n' for x in outs));self.assertEqual(0,mod.main(sp,op))
            finally:mod.validate_code=old
if __name__=='__main__':unittest.main(verbosity=2)
