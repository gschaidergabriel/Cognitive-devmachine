from __future__ import annotations

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import frankenstein2_agent_hook_identity_v1 as mod


def pre(package: str, tool_use: str, *, session: str = 's1'):
    return mod.parse_agent_pretool({
        'hook_event_name': 'PreToolUse',
        'session_id': session,
        'tool_name': 'Agent',
        'tool_use_id': tool_use,
        'tool_input': {'prompt': f'HANDOFF {package}\nDo the bounded task.'},
    })


def post(tool_use: str, *, session: str = 's1', agent_id='agent-1', event='PostToolUse'):
    response = {} if agent_id is None else {'agentId': agent_id}
    return mod.parse_agent_posttool({
        'hook_event_name': event,
        'session_id': session,
        'tool_name': 'Agent',
        'tool_use_id': tool_use,
        'tool_response': response,
    })


def pkg(package: str, generation: str = 'g1', admissible: bool = True):
    return mod.PackageResolution(package, generation, admissible, 'fixture://package-registry')


class AgentHookIdentityTests(unittest.TestCase):
    def test_exact_handoff_marker_must_be_first_and_unique(self):
        self.assertEqual(mod.parse_handoff_marker('HANDOFF wp-1\nbody'), 'wp-1')
        for prompt in ('body only', 'prefix\nHANDOFF wp-1', 'HANDOFF wp-1\nHANDOFF wp-2'):
            with self.subTest(prompt=prompt):
                with self.assertRaises(mod.AgentHookIdentityError):
                    mod.parse_handoff_marker(prompt)

    def test_same_session_interleave_reverse_completion_stays_separable(self):
        pa = pre('wp-a', 'tool-a')
        pb = pre('wp-b', 'tool-b')
        # Deliberately reverse Post order.
        post_b = post('tool-b', agent_id='agent-b')
        post_a = post('tool-a', agent_id='agent-a')
        jb = mod.join_agent_call(pb, post_b, pkg('wp-b'), expected_work_generation='g1')
        ja = mod.join_agent_call(pa, post_a, pkg('wp-a'), expected_work_generation='g1')
        self.assertEqual((ja.spawn_tool_use_id, ja.native_agent_id), ('tool-a', 'agent-a'))
        self.assertEqual((jb.spawn_tool_use_id, jb.native_agent_id), ('tool-b', 'agent-b'))

    def test_crosswire_posttool_fails_closed_even_in_same_session(self):
        with self.assertRaisesRegex(mod.AgentHookIdentityError, 'TOOL_USE_ID_MISMATCH'):
            mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-b'), pkg('wp-a'), expected_work_generation='g1')

    def test_package_marker_must_match_resolved_package(self):
        with self.assertRaisesRegex(mod.AgentHookIdentityError, 'HANDOFF_PACKAGE_MISMATCH'):
            mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-a'), pkg('wp-b'), expected_work_generation='g1')

    def test_stale_package_generation_fails_closed(self):
        with self.assertRaisesRegex(mod.AgentHookIdentityError, 'STALE_WORK_GENERATION'):
            mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-a'), pkg('wp-a', 'g2'), expected_work_generation='g1')

    def test_resolved_package_must_be_admissible_unresolved(self):
        with self.assertRaisesRegex(mod.AgentHookIdentityError, 'WORKPACKAGE_NOT_ADMISSIBLE_UNRESOLVED'):
            mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-a'), pkg('wp-a', admissible=False), expected_work_generation='g1')

    def test_absent_agent_id_remains_unknown_not_guessed(self):
        j = mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-a', agent_id=None), pkg('wp-a'), expected_work_generation='g1')
        self.assertIsNone(j.native_agent_id)
        self.assertEqual(j.native_agent_id_state, 'UNKNOWN')

    def test_failure_post_can_close_identity_without_claiming_completion(self):
        j = mod.join_agent_call(pre('wp-a', 'tool-a'), post('tool-a', agent_id=None, event='PostToolUseFailure'), pkg('wp-a'), expected_work_generation='g1')
        self.assertEqual(j.spawn_tool_use_id, 'tool-a')
        self.assertEqual(j.native_agent_id_state, 'UNKNOWN')

    def test_non_agent_tool_rejected(self):
        with self.assertRaisesRegex(mod.AgentHookIdentityError, 'UNEXPECTED_TOOL'):
            mod.parse_agent_pretool({
                'hook_event_name': 'PreToolUse', 'session_id': 's1', 'tool_name': 'Bash',
                'tool_use_id': 'x', 'tool_input': {'prompt': 'HANDOFF wp-a'},
            })


if __name__ == '__main__':
    unittest.main()
