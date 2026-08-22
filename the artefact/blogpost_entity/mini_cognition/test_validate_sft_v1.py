#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
SPEC=importlib.util.spec_from_file_location("claycog_validate",HERE/"validate_sft_v1.py")
V=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(V)
EXPECTED_TRAIN_SHA="3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93"
EXPECTED_VALIDATION_SHA="ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62"


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


class RuntimeBindingGateTests(unittest.TestCase):
    def test_canonical_runtime_bindings_pass(self):
        self.assertEqual(V.validate_code(valid_code()),[])

    def test_second_hardcoded_identity_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  self_bind(c,"other","fork")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:self_bind:2') for x in errors),errors)

    def test_second_hardcoded_role_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  role_bind(c,"blogger")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:role_bind:2') for x in errors),errors)

    def test_second_hardcoded_goal_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  goal_bind(c,"publish posts")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:goal_bind:2') for x in errors),errors)

    def test_second_hardcoded_personality_binding_is_rejected(self):
        errors=V.validate_code(valid_code('  personality_bind(c,"named persona")\n'))
        self.assertTrue(any(x.startswith('binding_call_count:personality_bind:2') for x in errors),errors)

    def test_reserved_name_literal_via_self_state_is_rejected(self):
        errors=V.validate_code(valid_code('  self_state(c,"name","Zero","COMPUTED")\n'))
        self.assertIn('literal_reserved_runtime_key:name',errors)

    def test_reserved_role_literal_via_state_note_is_rejected(self):
        errors=V.validate_code(valid_code('  state_note(c,"role","blogger","REPORTED")\n'))
        self.assertIn('literal_reserved_runtime_key:role',errors)

    def test_escaped_reserved_key_decodes_before_gate(self):
        errors=V.validate_code(valid_code('  self_state(c,"na\\u006de","Zero","COMPUTED")\n'))
        self.assertIn('literal_reserved_runtime_key:name',errors)

    def test_nonidentity_computed_control_state_still_passes(self):
        self.assertEqual(V.validate_code(valid_code('  self_state(c,"control_label","uncertainty","COMPUTED")\n')),[])

    def test_reserved_intrinsic_text_inside_nonreserved_string_is_not_a_false_positive(self):
        code=valid_code('  state_note(c,"diagnostic","self_state(c,\\"name\\",\\"Zero\\",\\"COMPUTED\\")","REPORTED")\n')
        errors=V.validate_code(code)
        self.assertNotIn('literal_reserved_runtime_key:name',errors)

    def test_required_binding_text_inside_string_cannot_spoof_structure(self):
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

    def test_unterminated_string_is_rejected(self):
        code=valid_code('  state_note(c,"x","unterminated)\n')
        errors=V.validate_code(code)
        self.assertIn('unterminated_string',errors)


class CanonicalCorpusV2Tests(unittest.TestCase):
    def test_regenerate_and_validate_exact_corpus_v2(self):
        subprocess.run([sys.executable,str(HERE/"generate_sft_v2.py")],cwd=HERE,check=True)
        proc=subprocess.run(
            [sys.executable,str(HERE/"validate_corpus_v2.py"),str(HERE/"train_v2.jsonl"),str(HERE/"validation_v2.jsonl")],
            cwd=HERE,check=True,text=True,capture_output=True,
        )
        report=json.loads(proc.stdout)
        self.assertTrue(report["ok"],report)
        self.assertEqual(report["train_lines"],1485)
        self.assertEqual(report["validation_lines"],165)
        self.assertEqual(report["train_unique"],1485)
        self.assertEqual(report["validation_unique"],165)
        self.assertEqual(report["exact_cross_split_overlap"],0)
        self.assertEqual(report["prompt_cross_split_overlap"],0)
        self.assertEqual(report["train_sha256"],EXPECTED_TRAIN_SHA)
        self.assertEqual(report["validation_sha256"],EXPECTED_VALIDATION_SHA)

        manifest=json.loads((HERE/"corpus_manifest_v2.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["schema"],"claycog-sft/v2")
        self.assertEqual(manifest["train_sha256"],EXPECTED_TRAIN_SHA)
        self.assertEqual(manifest["validation_sha256"],EXPECTED_VALIDATION_SHA)


if __name__=='__main__':
    unittest.main()
