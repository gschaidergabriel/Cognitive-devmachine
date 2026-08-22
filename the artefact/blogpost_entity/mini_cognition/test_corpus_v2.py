#!/usr/bin/env python3
import hashlib, importlib.util, json, unittest
from collections import Counter
from pathlib import Path

HERE=Path(__file__).resolve().parent

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod

gen=load("generate_sft_v2",HERE/"generate_sft_v2.py")
validator=load("validate_sft_v1",HERE/"validate_sft_v1.py")

def fingerprint(messages):
    return hashlib.sha256(json.dumps(messages,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()).hexdigest()

class CorpusV2Tests(unittest.TestCase):
    def test_split_is_unique_balanced_and_disjoint(self):
        train,valid=gen.build()
        self.assertEqual((1620,180),(len(train),len(valid)))
        self.assertEqual({f:180 for f in gen.FAMILIES},dict(Counter(x["family"] for x in train)))
        self.assertEqual({f:20 for f in gen.FAMILIES},dict(Counter(x["family"] for x in valid)))
        tf={fingerprint(x["messages"]) for x in train}; vf={fingerprint(x["messages"]) for x in valid}
        self.assertEqual(1620,len(tf)); self.assertEqual(180,len(vf)); self.assertFalse(tf & vf)
        self.assertFalse({x["messages"][1]["content"] for x in train} & {x["messages"][1]["content"] for x in valid})

    def test_all_assistant_targets_pass_strict_claycode_validator(self):
        train,valid=gen.build()
        bad=[]
        for x in train+valid:
            errors=validator.validate_code(x["messages"][-1]["content"])
            if errors: bad.append((x["family"],errors))
        self.assertEqual([],bad)

    def test_no_fixed_application_identity_literals(self):
        train,valid=gen.build(); outputs="\n".join(x["messages"][-1]["content"] for x in train+valid).lower()
        for forbidden in ('self_bind(c,"zero"','role_bind(c,"blog','goal_bind(c,"write blog','personality_bind(c,"zero"'):
            self.assertNotIn(forbidden,outputs)

if __name__=="__main__": unittest.main(verbosity=2)
