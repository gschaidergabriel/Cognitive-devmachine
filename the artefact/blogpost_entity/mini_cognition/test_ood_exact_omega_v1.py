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


def render(expected):
    w=expected.get("variable","w")
    lines=[
      "module clay.cog.turn","fn think(i:Map)->Map {","  let c = cog_new()",
      '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))',
      '  role_bind(c,cfg("application.role"))','  goal_bind(c,cfg("application.goal"))',
      '  personality_bind(c,cfg("application.personality"))',
      f'  let {w} = omega_new(c,"ood")',
    ]
    lines.extend(evaluator.expected_lines(expected))
    lines.extend(["  return c","}"])
    return "\n".join(lines)


class ExactOmegaOODTests(unittest.TestCase):
    def setUp(self):
        self.standard=next(x for x in generator.CASES if x["family"]=="omega_valid_ood")
        self.amputation=next(x for x in generator.CASES if x["family"]==evaluator.AMPUTATION_FAMILY)

    def test_suite_cardinality_and_exact_surface(self):
        self.assertEqual(240,len(generator.CASES))
        self.assertEqual(120,sum("expected_omega" in x for x in generator.CASES))
        self.assertEqual(80,sum(x["family"]=="omega_valid_ood" for x in generator.CASES))
        self.assertEqual(40,sum(x["family"]==evaluator.AMPUTATION_FAMILY for x in generator.CASES))
        self.assertEqual(set(),{op for op,_,_ in generator.NOVEL_VALID} & generator.TRAIN_SEEN_OPS)

    def test_exact_standard_vector_passes(self):
        out=render(self.standard["expected_omega"])
        self.assertEqual([],validator.validate_code(out))
        self.assertTrue(evaluator.semantic_match(self.standard,out))

    def test_exact_unseen_tool_vector_passes(self):
        out=render(self.amputation["expected_omega"])
        self.assertEqual([],validator.validate_code(out))
        self.assertTrue(evaluator.semantic_match(self.amputation,out))

    def test_reproduced_old_boilerplate_spoof_is_semantically_rejected(self):
        e=self.standard["expected_omega"]
        out=render(e)
        for a in e["args"]:
            out=out.replace(f'  omega_arg(w,{evaluator.lit(a["name"])},{evaluator.lit(a["value"])},{evaluator.lit(a["type"])})\n','')
        out=out.replace(f'  omega_schema(w,{evaluator.lit(e["schema"])})\n','')
        # This is the exact defect class observed on current main: structural admission can
        # still be green, but promotion semantics must now reject the empty action vector.
        self.assertEqual([],validator.validate_code(out))
        self.assertFalse(evaluator.semantic_match(self.standard,out))

    def test_missing_argument_fails(self):
        e=self.standard["expected_omega"]
        out=render(e)
        a=e["args"][0]
        line=f'  omega_arg(w,{evaluator.lit(a["name"])},{evaluator.lit(a["value"])},{evaluator.lit(a["type"])})\n'
        self.assertFalse(evaluator.semantic_match(self.standard,out.replace(line,"",1)))

    def test_wrong_argument_value_fails(self):
        e=self.standard["expected_omega"]
        out=render(e); a=e["args"][0]
        old=f'  omega_arg(w,{evaluator.lit(a["name"])},{evaluator.lit(a["value"])},{evaluator.lit(a["type"])})'
        new=f'  omega_arg(w,{evaluator.lit(a["name"])},"__WRONG__",{evaluator.lit(a["type"])})'
        self.assertFalse(evaluator.semantic_match(self.standard,out.replace(old,new,1)))

    def test_extra_argument_fails(self):
        out=render(self.standard["expected_omega"])
        out=out.replace("  omega_schema(w,",'  omega_arg(w,"unexpected","x","String")\n  omega_schema(w,',1)
        self.assertFalse(evaluator.semantic_match(self.standard,out))

    def test_wrong_schema_fails(self):
        e=self.standard["expected_omega"]
        out=render(e).replace(f'  omega_schema(w,{evaluator.lit(e["schema"])})','  omega_schema(w,"tool.wrong/v9")',1)
        self.assertFalse(evaluator.semantic_match(self.standard,out))

    def test_nested_or_string_smuggling_does_not_satisfy_exact_line(self):
        e=self.standard["expected_omega"]; out=render(e); a=e["args"][0]
        line=f'  omega_arg(w,{evaluator.lit(a["name"])},{evaluator.lit(a["value"])},{evaluator.lit(a["type"])})'
        nested="    "+line.strip()
        self.assertFalse(evaluator.exact_omega_ok(e,out.replace(line,nested,1)))
        quoted='  state_note(c,"x",'+json.dumps(line.strip())+',"REPORTED")'
        self.assertFalse(evaluator.exact_omega_ok(e,out.replace(line,quoted,1)))

    def test_duplicate_commit_fails_exact_vector(self):
        out=render(self.standard["expected_omega"])
        out=out.replace("  omega_commit_candidate(c,w)","  omega_commit_candidate(c,w)\n  omega_commit_candidate(c,w)",1)
        self.assertFalse(evaluator.exact_omega_ok(self.standard["expected_omega"],out))

    def test_duplicate_and_unknown_output_ids_are_reported(self):
        spec=[self.standard]
        good=render(self.standard["expected_omega"])
        report=evaluator.score_rows(spec,[{"id":self.standard["id"],"output":good},{"id":self.standard["id"],"output":good},{"id":"unknown","output":good}])
        self.assertEqual([self.standard["id"]],report["duplicate_output_ids"])
        self.assertEqual(["unknown"],report["unknown_output_ids"])
        self.assertFalse(report["promotion_gate_pass"])


if __name__=="__main__": unittest.main()
