#!/usr/bin/env python3
import unittest

from generate_sft_v1 import build
from validate_sft_v1 import PREFIX, validate_code

BINDINGS = (
    '  self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n',
    '  role_bind(c,cfg("application.role"))\n',
    '  goal_bind(c,cfg("application.goal"))\n',
    '  personality_bind(c,cfg("application.personality"))\n',
)

def program(extra="", bindings=BINDINGS):
    return PREFIX + "".join(bindings) + extra + '  return c\n}'

class ClayCogValidatorFusionTests(unittest.TestCase):
    def test_minimal_real_bindings_pass(self):
        self.assertEqual(validate_code(program()), [])

    def test_required_binding_inside_string_does_not_count(self):
        spoof='  let bait = "self_bind(c,cfg(\\"entity.id\\"),cfg(\\"entity.continuity\\"))"\n'
        errors=validate_code(program(spoof,bindings=BINDINGS[1:]))
        self.assertTrue(any(x.startswith("missing_statement:self_bind") for x in errors),errors)

    def test_required_binding_nested_under_control_flow_does_not_count(self):
        nested='  if false {\n    self_bind(c,cfg("entity.id"),cfg("entity.continuity"))\n  }\n'
        errors=validate_code(program(nested,bindings=BINDINGS[1:]))
        self.assertTrue(any(x.startswith("missing_statement:self_bind") for x in errors),errors)

    def test_comment_wrapped_contract_fails_closed(self):
        self.assertIn("comment_syntax_forbidden",validate_code(program('  /* omega_validate(w,"grammar") */\n')))

    def valid_omega(self,grammar='  omega_validate(w,"grammar")\n'):
        return (
            '  let w = omega_new(c,"w0")\n'
            '  omega_authority(w,cfg("architecture.effect_authority"))\n'
            '  omega_generation(w,cfg("state.generation"))\n'+grammar+
            '  omega_validate(w,"types")\n'
            '  omega_validate(w,"schema")\n'
            '  omega_validate(w,"authority")\n'
            '  omega_validate(w,"generation")\n'
            '  omega_commit_candidate(c,w)\n'
        )

    def test_valid_omega_commit_requires_real_gate_statements(self):
        self.assertEqual(validate_code(program(self.valid_omega())),[])

    def test_omega_gate_inside_string_does_not_count(self):
        bait='  let bait = "omega_validate(w,\\"grammar\\")"\n'
        self.assertIn("omega_missing_gate:grammar",validate_code(program(self.valid_omega(bait))))

    def test_omega_gate_nested_under_control_flow_does_not_count(self):
        nested='  if false {\n    omega_validate(w,"grammar")\n  }\n'
        self.assertIn("omega_missing_gate:grammar",validate_code(program(self.valid_omega(nested))))

    def test_multiline_or_unclosed_string_fails_closed(self):
        self.assertIn("multiline_or_unclosed_string",validate_code(program('  let bait = "unterminated\n')))

    def test_reject_and_commit_remains_invalid(self):
        omega=self.valid_omega().replace('  omega_commit_candidate(c,w)\n','  omega_reject(w,"bad")\n  omega_commit_candidate(c,w)\n')
        self.assertIn("reject_and_commit",validate_code(program(omega)))

    def test_unknown_intrinsic_fails_closed(self):
        self.assertIn("unknown_intrinsic:mystery_focus",validate_code(program('  mystery_focus(c,"x")\n')))

    def test_wrong_intrinsic_arity_fails_closed(self):
        self.assertIn("arity:focus_set:3!=2",validate_code(program('  focus_set(c,"x","y")\n')))

    def test_literal_punctuation_does_not_change_arity(self):
        self.assertEqual(validate_code(program('  focus_set(c,"literal,(with),commas")\n')),[])

    def test_full_generated_corpus_is_closed(self):
        rows=build(); self.assertEqual(len(rows),1650)
        bad=[]
        for i,row in enumerate(rows):
            errors=validate_code(row["messages"][-1]["content"])
            if errors: bad.append((i,row["family"],errors))
        self.assertEqual(bad,[],bad[:20])

if __name__=='__main__': unittest.main()
