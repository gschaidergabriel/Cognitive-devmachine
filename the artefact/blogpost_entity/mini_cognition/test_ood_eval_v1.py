#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from eval_outputs_v1 import score

HEAD=(
    'module clay.cog.turn\n'
    'fn think(i:Map)->Map {\n'
    '  let c = cog_new()\n'
    '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
    '  role_bind(c,cfg("application.role"))\n'
    '  goal_bind(c,cfg("application.goal"))\n'
    '  personality_bind(c,cfg("application.personality"))\n'
)
TAIL='  return c\n}'

def write_jsonl(path, rows):
    Path(path).write_text(''.join(json.dumps(x,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')

class OODEvalTests(unittest.TestCase):
    def spec(self):
        return {
            'id':'x','family':'omega_valid_ood','prompt':'x',
            'expected_omega':{
                'operation':'http.get','schema':'tool.http.get/v1',
                'args':[{'name':'path','value':'/v1/status/9','type':'Path'},{'name':'timeout_ms','value':2500,'type':'Int'}],
            },
            'must_contain':[
                'omega_bind(w,"operation","http.get")',
                'omega_arg(w,"path","/v1/status/9","Path")',
                'omega_arg(w,"timeout_ms",2500,"Int")',
                'omega_schema(w,"tool.http.get/v1")',
                'omega_validate(w,"grammar")','omega_validate(w,"types")','omega_validate(w,"schema")',
                'omega_validate(w,"authority")','omega_validate(w,"generation")','omega_commit_candidate(c,w)',
            ],
            'must_not_contain':['omega_reject('],
        }

    def output(self, include_args):
        body='  let w = omega_new(c,"w0")\n  omega_bind(w,"operation","http.get")\n'
        if include_args:
            body+='  omega_arg(w,"path","/v1/status/9","Path")\n  omega_arg(w,"timeout_ms",2500,"Int")\n'
        body+='  omega_schema(w,"tool.http.get/v1")\n  omega_authority(w,cfg("architecture.effect_authority"))\n  omega_generation(w,cfg("state.generation"))\n'
        for gate in ('grammar','types','schema','authority','generation'):
            body+=f'  omega_validate(w,"{gate}")\n'
        body+='  omega_commit_candidate(c,w)\n'
        return HEAD+body+TAIL

    def run_score(self, outputs):
        with tempfile.TemporaryDirectory() as td:
            spec=Path(td)/'spec.jsonl'; out=Path(td)/'out.jsonl'
            write_jsonl(spec,[self.spec()]); write_jsonl(out,outputs)
            return score(spec,out)

    def test_argument_free_cheater_fails_exact_vector(self):
        report=self.run_score([{'id':'x','output':self.output(False)}])
        self.assertEqual(report['strict_claycode_rate'],1.0)
        self.assertEqual(report['omega_exact_vector_rate'],0.0)
        self.assertEqual(report['semantic_gate_rate'],0.0)

    def test_exact_vector_oracle_passes(self):
        report=self.run_score([{'id':'x','output':self.output(True)}])
        self.assertEqual(report['omega_exact_vector_rate'],1.0)
        self.assertEqual(report['semantic_gate_rate'],1.0)

    def test_duplicate_and_unexpected_ids_are_reported(self):
        good={'id':'x','output':self.output(True)}
        report=self.run_score([good,good,{'id':'extra','output':'x'}])
        self.assertEqual(report['duplicate_output_ids'],['x'])
        self.assertEqual(report['unexpected_output_ids'],['extra'])

if __name__=='__main__': unittest.main()
