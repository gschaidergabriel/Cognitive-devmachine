#!/usr/bin/env python3
import importlib.util, json, sys, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
SPEC=importlib.util.spec_from_file_location("eval_outputs_v1", HERE/"eval_outputs_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

class PromotionGateTests(unittest.TestCase):
    def write_jsonl(self,path,rows):
        path.write_text("".join(json.dumps(x,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")

    def test_global_95_percent_cannot_mask_unseen_tool_failure(self):
        # 20/21 semantic success = 95.238%, so the old aggregate gate would pass.
        # The one failed amputation case must now veto promotion independently.
        specs=[]; outs=[]
        for i in range(20):
            specs.append({"id":f"normal-{i}","family":"normal","must_contain":["OK"],"must_not_contain":[]})
            outs.append({"id":f"normal-{i}","output":"OK"})
        specs.append({"id":"amp-0","family":mod.AMPUTATION_FAMILY,"must_contain":["AMP"],"must_not_contain":[]})
        outs.append({"id":"amp-0","output":"WRONG"})
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); sp=td/"spec.jsonl"; op=td/"out.jsonl"
            self.write_jsonl(sp,specs); self.write_jsonl(op,outs)
            old=mod.validate_code; mod.validate_code=lambda _:[]
            try:
                self.assertEqual(1,mod.main(sp,op))
                outs[-1]["output"]="AMP"; self.write_jsonl(op,outs)
                self.assertEqual(0,mod.main(sp,op))
            finally:
                mod.validate_code=old

if __name__=="__main__": unittest.main(verbosity=2)
