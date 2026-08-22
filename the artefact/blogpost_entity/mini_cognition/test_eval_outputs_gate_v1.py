#!/usr/bin/env python3
import importlib.util, json, sys, tempfile, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
SPEC=importlib.util.spec_from_file_location("eval_outputs_v1", HERE/"eval_outputs_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)


def amp_spec(cid="amp-0"):
    return {
      "id":cid,"family":mod.AMPUTATION_FAMILY,
      "must_contain":[
        'omega_bind(w,"operation","contacts.resolve")',
        'omega_arg(w,"query","person-9","String")',
        'omega_schema(w,"tool.contacts.resolve/v2")',
        'omega_validate(w,"grammar")','omega_validate(w,"types")','omega_validate(w,"schema")',
        'omega_validate(w,"authority")','omega_validate(w,"generation")','omega_commit_candidate(c,w)'
      ],
      "must_not_contain":["calendar.create"],
    }


def amp_output(var="w7",complete=True):
    lines=[
      f'omega_bind({var},"operation","contacts.resolve")',
      f'omega_arg({var},"query","person-9","String")',
      f'omega_schema({var},"tool.contacts.resolve/v2")',
      f'omega_validate({var},"grammar")',f'omega_validate({var},"types")',f'omega_validate({var},"schema")',
      f'omega_validate({var},"authority")',f'omega_validate({var},"generation")',f'omega_commit_candidate(c,{var})'
    ]
    if not complete:
        lines=[x for x in lines if not x.startswith(f'omega_schema({var},')]
    return "\n".join(lines)


class PromotionGateTests(unittest.TestCase):
    def write_jsonl(self,path,rows):
        path.write_text("".join(json.dumps(x,separators=(",",":"))+"\n" for x in rows),encoding="utf-8")

    def test_global_95_percent_cannot_mask_unseen_tool_failure(self):
        # 20/21 semantic success = 95.238%, so the aggregate gate alone would pass.
        # The one failed amputation case must veto promotion independently.
        specs=[]; outs=[]
        for i in range(20):
            specs.append({"id":f"normal-{i}","family":"normal","must_contain":["OK"],"must_not_contain":[]})
            outs.append({"id":f"normal-{i}","output":"OK"})
        specs.append(amp_spec())
        outs.append({"id":"amp-0","output":amp_output(complete=False)})
        with tempfile.TemporaryDirectory() as td:
            td=Path(td); sp=td/"spec.jsonl"; op=td/"out.jsonl"
            self.write_jsonl(sp,specs); self.write_jsonl(op,outs)
            old=mod.validate_code; mod.validate_code=lambda _:[]
            try:
                self.assertEqual(1,mod.main(sp,op))
                outs[-1]["output"]=amp_output(); self.write_jsonl(op,outs)
                self.assertEqual(0,mod.main(sp,op))
            finally:
                mod.validate_code=old

    def test_amputation_semantics_do_not_require_literal_w(self):
        s=amp_spec()
        self.assertTrue(mod.semantic_tokens_ok(s,amp_output("candidate_17")))
        self.assertFalse(mod.semantic_tokens_ok(s,amp_output("candidate_17",complete=False)))
        self.assertEqual("candidate_17",mod.committed_omega_var(amp_output("candidate_17")))

    def test_ambiguous_double_commit_rejected(self):
        s=amp_spec()
        out=amp_output("w7")+"\nomega_commit_candidate(c,w8)"
        self.assertIsNone(mod.committed_omega_var(out))
        self.assertFalse(mod.semantic_tokens_ok(s,out))

if __name__=="__main__": unittest.main(verbosity=2)
