#!/usr/bin/env python3
import importlib.util, json, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("hf_arch",HERE/"hf_architecture_attestation_v1.py")
mod=importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(mod)

def att(model,revision,model_type,architecture,auto_map=False):
    raw=json.dumps({"model_type":model_type,"architectures":[architecture],**({"auto_map":{"AutoModelForCausalLM":"x.y"}} if auto_map else {})},sort_keys=True).encode()
    return mod.attest_config_bytes(model,revision,raw)

class HfArchitectureAttestationTests(unittest.TestCase):
    def test_exact_revision_required(self):
        with self.assertRaises(SystemExit): mod.exact_revision("main")
    def test_qwen2_family_match(self):
        target=att(mod.PRIMARY_HF_MODEL,mod.PRIMARY_HF_REVISION,"qwen2","Qwen2ForCausalLM")
        template=att("Qwen/Qwen2.5-14B","1"*40,"qwen2","Qwen2ForCausalLM")
        out=mod.compare_attestations(target,template)
        self.assertEqual("ARCHITECTURE_MATCH_LOCAL_ONLY",out["status"])
        self.assertEqual("UNPROVEN_UNTIL_TOGETHER_ACCEPTS_EXACT_TUPLE",out["provider_admission"])
    def test_unusual_family_substitution_attack_rejects_qwen35(self):
        target=att(mod.PRIMARY_HF_MODEL,mod.PRIMARY_HF_REVISION,"qwen2","Qwen2ForCausalLM")
        substitute=att("Qwen/Qwen3.5-0.8B","2"*40,"qwen3_5","Qwen3_5ForConditionalGeneration")
        with self.assertRaises(SystemExit) as ctx: mod.compare_attestations(target,substitute)
        self.assertIn("HF_ARCHITECTURE_MISMATCH",str(ctx.exception))
    def test_target_revision_cannot_drift(self):
        target=att(mod.PRIMARY_HF_MODEL,"3"*40,"qwen2","Qwen2ForCausalLM")
        template=att("Qwen/Qwen2.5-14B","4"*40,"qwen2","Qwen2ForCausalLM")
        with self.assertRaises(SystemExit) as ctx: mod.compare_attestations(target,template)
        self.assertIn("HF_ARCH_TARGET_IDENTITY_MISMATCH",str(ctx.exception))
    def test_custom_code_is_not_admitted(self):
        target=att(mod.PRIMARY_HF_MODEL,mod.PRIMARY_HF_REVISION,"qwen2","Qwen2ForCausalLM",auto_map=True)
        template=att("Qwen/Qwen2.5-14B","5"*40,"qwen2","Qwen2ForCausalLM")
        with self.assertRaises(SystemExit) as ctx: mod.compare_attestations(target,template)
        self.assertIn("HF_ARCH_ATTESTATION_CUSTOM_CODE_REJECTED",str(ctx.exception))

if __name__=="__main__": unittest.main(verbosity=2)
