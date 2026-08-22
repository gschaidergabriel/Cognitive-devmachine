#!/usr/bin/env python3
import json
import subprocess
import sys
import unittest
from pathlib import Path

from generate_sft_v1 import build as build_v1
from validate_sft_v1 import PREFIX, validate_code

HERE=Path(__file__).resolve().parent
EXPECTED_TRAIN_SHA="3c715588d1b040494be48228f165208e2f10202b3f125616741116b90cd21b93"
EXPECTED_VALIDATION_SHA="ca284585ba66c532e7e19232edd7f6b5dc1c0969d15cbb9d5ce1cbc202e86f62"
BINDINGS=(
    '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n',
    '  role_bind(c,cfg("application.role"))\n',
    '  goal_bind(c,cfg("application.goal"))\n',
    '  personality_bind(c,cfg("application.personality"))\n',
)


def program(extra="",bindings=BINDINGS):
    return PREFIX+'  let c = cog_new()\n'+''.join(bindings)+extra+'  return c\n}'


def valid_omega(grammar='  omega_validate(w,"grammar")\n'):
    return (
        '  let w = omega_new(c,"w0")\n'
        '  omega_bind(w,"operation","db.lookup")\n'
        '  omega_arg(w,"table","events","Identifier")\n'
        '  omega_schema(w,"tool.db.lookup/v1")\n'
        '  omega_authority(w,cfg("architecture.effect_authority"))\n'
        '  omega_generation(w,cfg("state.generation"))\n'
        +grammar+
        '  omega_validate(w,"types")\n'
        '  omega_validate(w,"schema")\n'
        '  omega_validate(w,"authority")\n'
        '  omega_validate(w,"generation")\n'
        '  omega_commit_candidate(c,w)\n'
    )


class StrictClayCodeAdmissionTests(unittest.TestCase):
    def assertHas(self,errors,needle):
        self.assertTrue(any(needle in x for x in errors),errors)

    def test_canonical_runtime_bindings_pass(self):
        self.assertEqual([],validate_code(program()))

    def test_second_hardcoded_identity_binding_is_rejected(self):
        self.assertHas(validate_code(program('  self_bind(c,"other","fork")\n')),'binding_call_count:self_bind:2')

    def test_second_hardcoded_role_binding_is_rejected(self):
        self.assertHas(validate_code(program('  role_bind(c,"blogger")\n')),'binding_call_count:role_bind:2')

    def test_second_hardcoded_goal_binding_is_rejected(self):
        self.assertHas(validate_code(program('  goal_bind(c,"publish posts")\n')),'binding_call_count:goal_bind:2')

    def test_second_hardcoded_personality_binding_is_rejected(self):
        self.assertHas(validate_code(program('  personality_bind(c,"named persona")\n')),'binding_call_count:personality_bind:2')

    def test_required_binding_text_inside_string_cannot_spoof_structure(self):
        spoof='  state_note(c,"spoof","self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))","REPORTED")\n'
        errors=validate_code(program(spoof,bindings=BINDINGS[1:]))
        self.assertHas(errors,'binding_call_count:self_bind:0')
        self.assertHas(errors,'binding_not_exact_runtime_cfg:self_bind:0')

    def test_unterminated_string_is_rejected(self):
        self.assertHas(validate_code(program('  state_note(c,"x","unterminated)\n')),'unterminated_string')

    def test_free_prose_statement_is_rejected(self):
        self.assertHas(validate_code(program('  THIS IS FREE PROSE\n')),'not_call')

    def test_unknown_intrinsic_fails_closed(self):
        self.assertHas(validate_code(program('  mystery_focus(c,"x")\n')),'unknown_intrinsic:mystery_focus')

    def test_wrong_intrinsic_arity_fails_closed(self):
        self.assertHas(validate_code(program('  focus_set(c,"x","y")\n')),'bad_arity:focus_set:3!=2')

    def test_trailing_garbage_after_call_fails_closed(self):
        self.assertHas(validate_code(program('  focus_set(c,"x") trailing garbage\n')),'trailing_after_call')

    def test_literal_punctuation_does_not_change_arity(self):
        self.assertEqual([],validate_code(program('  focus_set(c,"literal,(with),commas")\n')))

    def test_comment_syntax_outside_strings_fails_closed(self):
        self.assertHas(validate_code(program('  focus_set(c,"x") // bait\n')),'comment_syntax_forbidden')

    def test_valid_omega_commit_passes_when_all_gates_precede_commit(self):
        self.assertEqual([],validate_code(program(valid_omega())))

    def test_gate_after_commit_does_not_receive_precommit_credit(self):
        body=valid_omega('').replace('  omega_commit_candidate(c,w)\n','  omega_commit_candidate(c,w)\n  omega_validate(w,"grammar")\n')
        self.assertHas(validate_code(program(body)),'omega_missing_precommit_gate:grammar')

    def test_reject_and_commit_same_candidate_is_invalid(self):
        body=valid_omega().replace('  omega_commit_candidate(c,w)\n','  omega_reject(w,"bad")\n  omega_commit_candidate(c,w)\n')
        self.assertHas(validate_code(program(body)),'reject_and_commit:w')

    def test_historical_v1_generator_remains_language_closed(self):
        rows=build_v1(); self.assertEqual(1650,len(rows))
        bad=[]
        for i,row in enumerate(rows):
            errors=validate_code(row['messages'][-1]['content'])
            if errors: bad.append((i,row['family'],errors))
        self.assertEqual([],bad[:20],f'{len(bad)} V1 targets failed')


class CanonicalCorpusV2Tests(unittest.TestCase):
    def test_regenerate_and_validate_exact_corpus_v2(self):
        subprocess.run([sys.executable,str(HERE/'generate_sft_v2.py')],cwd=HERE,check=True)
        proc=subprocess.run(
            [sys.executable,str(HERE/'validate_corpus_v2.py'),str(HERE/'train_v2.jsonl'),str(HERE/'validation_v2.jsonl')],
            cwd=HERE,check=True,text=True,capture_output=True,
        )
        report=json.loads(proc.stdout)
        self.assertTrue(report['ok'],report)
        self.assertEqual(report['canonical_code_validator'],'validate_sft_v1.py')
        self.assertEqual(report['train_lines'],1485)
        self.assertEqual(report['validation_lines'],165)
        self.assertEqual(report['train_structural_invalid'],0)
        self.assertEqual(report['validation_structural_invalid'],0)
        self.assertEqual(report['train_unique'],1485)
        self.assertEqual(report['validation_unique'],165)
        self.assertEqual(report['exact_cross_split_overlap'],0)
        self.assertEqual(report['prompt_cross_split_overlap'],0)
        self.assertEqual(report['train_sha256'],EXPECTED_TRAIN_SHA)
        self.assertEqual(report['validation_sha256'],EXPECTED_VALIDATION_SHA)

        manifest=json.loads((HERE/'corpus_manifest_v2.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['schema'],'claycog-sft/v2')
        self.assertEqual(manifest['train_sha256'],EXPECTED_TRAIN_SHA)
        self.assertEqual(manifest['validation_sha256'],EXPECTED_VALIDATION_SHA)


if __name__=='__main__': unittest.main()
