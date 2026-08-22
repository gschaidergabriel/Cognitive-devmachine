#!/usr/bin/env python3
import importlib.util, unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("claycog_v2_validate",HERE/"validate_corpus_v2.py")
V=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)


def valid_code(extra=""):
    return (
        'module clay.cog.turn\n'
        'fn think(i:Map)->Map {\n'
        '  let c = cog_new()\n'
        '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n'
        '  role_bind(c,cfg("application.role"))\n'
        '  goal_bind(c,cfg("application.goal"))\n'
        '  personality_bind(c,cfg("application.personality"))\n'
        + extra +
        '  return c\n'
        '}'
    )


def row(system="CLAYCOG/1",user="do the task",assistant=None):
    return {"messages":[
        {"role":"system","content":system},
        {"role":"user","content":user},
        {"role":"assistant","content":assistant or valid_code()},
    ]}


class CorpusV2CoreGateFusionTests(unittest.TestCase):
    def test_v2_exports_the_canonical_core_validator(self):
        self.assertIs(V.validate_code,V.CORE.validate_code)

    def test_canonical_runtime_bindings_still_pass(self):
        self.assertEqual(V.validate_code(valid_code()),[])

    def test_v2_rejects_second_fixed_identity_binding(self):
        errors=V.validate_code(valid_code('  self_bind(c,"other","fork")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:self_bind:2') for x in errors),errors)

    def test_v2_rejects_structural_binding_spoof_inside_string(self):
        code=(
            'module clay.cog.turn\n'
            'fn think(i:Map)->Map {\n'
            '  let c = cog_new()\n'
            '  state_note(c,"spoof","self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))","REPORTED")\n'
            '  role_bind(c,cfg("application.role"))\n'
            '  goal_bind(c,cfg("application.goal"))\n'
            '  personality_bind(c,cfg("application.personality"))\n'
            '  return c\n'
            '}'
        )
        errors=V.validate_code(code)
        self.assertIn('binding_call_count:self_bind:0',errors)
        self.assertIn('binding_not_exact_runtime_cfg:self_bind:0',errors)

    def test_campaign_literal_poison_is_rejected_in_any_message_role(self):
        poisoned=[
            row(system="Train Qwen/Qwen3.5-0.8B as permanent cognition"),
            row(user="Use Together.ai as the fixed provider"),
            row(assistant=valid_code('  state_note(c,"backend","Qwen3.5-0.8B","MEASURED")\n')),
        ]
        leaks=V.campaign_literal_leaks(poisoned)
        self.assertEqual([no for no,_ in leaks],[1,2,3])
        self.assertIn("model:qwen",leaks[0][1])
        self.assertIn("provider:together",leaks[1][1])
        self.assertIn("model:qwen",leaks[2][1])

    def test_generic_runtime_backend_binding_is_not_a_campaign_leak(self):
        clean=row(user="Runtime may change inference.backend; bind current cfg only.")
        self.assertEqual(V.campaign_literal_leaks([clean]),[])


if __name__=='__main__':
    unittest.main()
