import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_qwen35_checkpoint_candidates_gate_v1 as g

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'research_entity/global/j-space/research/trigger2_qwen35_08b_checkpoint_candidates_v1.json'
with MANIFEST.open(encoding='utf-8') as fh:
    BASE = json.load(fh)


class Trigger2CheckpointCandidatesGateV1Test(unittest.TestCase):
    def test_source_pins_and_unresolved_selection_pass(self):
        self.assertTrue(g.adjudicate(copy.deepcopy(BASE))['pass'])

    def test_source_pin_cannot_select_winner(self):
        x = copy.deepcopy(BASE)
        x['selected_candidate'] = 'QWEN35_08B_BASE'
        self.assertIn('SOURCE_PIN_CANNOT_SELECT_WINNER', g.adjudicate(x)['failures'])

    def test_bad_weight_sha_fails_closed(self):
        x = copy.deepcopy(BASE)
        x['candidates'][0]['weights_sha256'] = '0' * 64
        self.assertIn('WEIGHTS_SHA_MISMATCH:QWEN35_08B_BASE', g.adjudicate(x)['failures'])

    def test_loader_consumption_claim_fails_closed(self):
        x = copy.deepcopy(BASE)
        x['candidates'][1]['loader_consumption_observed'] = True
        self.assertIn('LOADER_CONSUMPTION_MUST_REMAIN_UNOBSERVED:QWEN35_08B_POSTTRAINED', g.adjudicate(x)['failures'])

    def test_holdout_leak_fails_closed(self):
        x = copy.deepcopy(BASE)
        x['matched_pilot_contract']['holdout_seen_during_selection'] = True
        self.assertIn('HOLDOUT_LEAK_FORBIDDEN', g.adjudicate(x)['failures'])

    def test_provider_preflight_fails_closed(self):
        x = copy.deepcopy(BASE)
        x['execution_boundary']['provider_preflight_performed'] = True
        self.assertIn('EXECUTION_MUST_REMAIN_FALSE:provider_preflight_performed', g.adjudicate(x)['failures'])


if __name__ == '__main__':
    unittest.main()
