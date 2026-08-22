#!/usr/bin/env python3
import unittest

from generate_sft_v1 import build
from validate_sft_v1 import validate_code


def minimal(extra=""):
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


class IntrinsicClosureTests(unittest.TestCase):
    def test_generated_corpus_targets_are_intrinsic_closed(self):
        bad=[]
        rows=build()
        self.assertEqual(len(rows),1650)
        for i,row in enumerate(rows):
            errors=validate_code(row["messages"][-1]["content"])
            if errors:
                bad.append((i,row["family"],errors))
        self.assertEqual(bad,[],bad[:20])

    def test_unknown_intrinsic_fails_closed(self):
        errors=validate_code(minimal('  mystery_focus(c,"x")\n'))
        self.assertIn('unknown_intrinsic:mystery_focus',errors)

    def test_wrong_arity_fails_closed(self):
        errors=validate_code(minimal('  focus_set(c,"x","y")\n'))
        self.assertIn('arity:focus_set:3!=2',errors)

    def test_literal_punctuation_does_not_change_arity(self):
        errors=validate_code(minimal('  focus_set(c,"literal,(with),commas")\n'))
        self.assertEqual(errors,[])


if __name__=='__main__':
    unittest.main()
