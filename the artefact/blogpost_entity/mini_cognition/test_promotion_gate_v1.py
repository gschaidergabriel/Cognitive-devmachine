#!/usr/bin/env python3
import importlib.util, json, sys, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load_module(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name]=mod
    spec.loader.exec_module(mod)
    return mod

validator=load_module("validate_sft_v1",HERE/"validate_sft_v1.py")
generator=load_module("generate_eval_ood_v1",HERE/"generate_eval_ood_v1.py")
evaluator=load_module("eval_outputs_v1",HERE/"eval_outputs_v1.py")
sft_generator=load_module("generate_sft_v1",HERE/"generate_sft_v1.py")

def base_lines():
    return [
      "module clay.cog.turn","fn think(i:Map)->Map {","  let c = cog_new()",
      '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
      '  role_bind(c,cfg("application.role"))','  goal_bind(c,cfg("application.goal"))',
      '  personality_bind(c,cfg("application.personality"))',
    ]

def render_expected(expected):
    lines=base_lines()+['  let w = omega_new(c,"w0")',f'  omega_bind(w,"operation",{json.dumps(expected["operation"],separators=(",",":"))})']
    for a in expected["args"]:
        val=json.dumps(a["value"],ensure_ascii=False,separators=(",",":")) if isinstance(a["value"],str) else str(a["value"])
        lines.append(f'  omega_arg(w,{json.dumps(a["name"])},{val},{json.dumps(a["type"])})')
    lines.extend([f'  omega_schema(w,{json.dumps(expected["schema"])})','  omega_authority(w,cfg("architecture.effect_authority"))','  omega_generation(w,cfg("state.generation"))'])
    for gate in expected["validators"]: lines.append(f'  omega_validate(w,{json.dumps(gate)})')
    lines.extend(["  omega_commit_candidate(c,w)","  return c","}"])
    return "\n".join(lines)

class PromotionGateTests(unittest.TestCase):
    def setUp(self):
        self.spec=next(x for x in generator.CASES if "expected_omega" in x)
        self.good=render_expected(self.spec["expected_omega"])

    def test_all_1650_sft_targets_pass_strict_parser(self):
        failures=[]
        rows=sft_generator.build()
        self.assertEqual(1650,len(rows))
        for i,row in enumerate(rows):
            errors=validator.validate_code(row["messages"][-1]["content"])
            if errors: failures.append((i,row["family"],errors))
        self.assertEqual([],failures[:20],f"{len(failures)} generated targets failed")

    def test_exact_valid_vector_passes(self):
        self.assertEqual([],validator.validate_code(self.good))
        self.assertTrue(evaluator.semantic_match(self.spec,self.good))

    def test_old_boilerplate_spoof_is_rejected(self):
        s="\n".join(base_lines()+[
          '  let w = omega_new(c,"w0")',f'  omega_bind(w,"operation",{json.dumps(self.spec["expected_omega"]["operation"])})',
          '  omega_authority(w,cfg("architecture.effect_authority"))','  omega_generation(w,cfg("state.generation"))',
          '  omega_validate(w,"grammar")','  omega_validate(w,"types")','  omega_validate(w,"schema")',
          '  omega_validate(w,"authority")','  omega_validate(w,"generation")','  omega_commit_candidate(c,w)','  return c','}'
        ])
        self.assertIn("omega_schema_count:0",validator.validate_code(s))
        self.assertFalse(evaluator.semantic_match(self.spec,s))

    def test_missing_argument_fails_exact_semantics(self):
        lines=self.good.splitlines(); idx=next(i for i,x in enumerate(lines) if x.startswith('  omega_arg(w,'))
        bad="\n".join(lines[:idx]+lines[idx+1:])
        self.assertEqual([],validator.validate_code(bad))
        self.assertFalse(evaluator.semantic_match(self.spec,bad))

    def test_wrong_argument_value_fails_exact_semantics(self):
        first=self.spec["expected_omega"]["args"][0]
        old=json.dumps(first["value"],ensure_ascii=False,separators=(",",":")) if isinstance(first["value"],str) else str(first["value"])
        bad=self.good.replace(f'omega_arg(w,{json.dumps(first["name"])},{old},{json.dumps(first["type"])})',f'omega_arg(w,{json.dumps(first["name"])} ,"__WRONG__",{json.dumps(first["type"])})'.replace(' ,',','),1)
        self.assertEqual([],validator.validate_code(bad))
        self.assertFalse(evaluator.semantic_match(self.spec,bad))

    def test_extra_argument_fails_exact_semantics(self):
        bad=self.good.replace('  omega_schema(w,','  omega_arg(w,"unexpected","x","String")\n  omega_schema(w,',1)
        self.assertEqual([],validator.validate_code(bad))
        self.assertFalse(evaluator.semantic_match(self.spec,bad))

    def test_wrong_schema_fails_semantics(self):
        bad=self.good.replace(self.spec["expected_omega"]["schema"],"tool.wrong/v9",1)
        self.assertEqual([],validator.validate_code(bad))
        self.assertFalse(evaluator.semantic_match(self.spec,bad))

    def test_duplicate_commit_rejected(self):
        bad=self.good.replace("  omega_commit_candidate(c,w)","  omega_commit_candidate(c,w)\n  omega_commit_candidate(c,w)",1)
        self.assertTrue(any(x.startswith("omega_commit_count:2") for x in validator.validate_code(bad)))
        self.assertFalse(evaluator.semantic_match(self.spec,bad))

    def test_unknown_intrinsic_and_free_prose_rejected(self):
        a=self.good.replace("  return c",'  hallucinated_intrinsic(c)\n  return c',1)
        b=self.good.replace("  return c",'  THIS IS FREE PROSE\n  return c',1)
        self.assertTrue(any("unknown_intrinsic" in x for x in validator.validate_code(a)))
        self.assertTrue(any("not_call" in x for x in validator.validate_code(b)))

    def test_exact_case_count_is_stable(self):
        self.assertEqual(200,len(generator.CASES))
        self.assertEqual(80,sum("expected_omega" in x for x in generator.CASES))

if __name__=="__main__": unittest.main()
