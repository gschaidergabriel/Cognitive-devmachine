import copy
import json
import unittest
from pathlib import Path

from tools import trigger2_trainingtrace_family_split_linter_v1 as linter

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / 'research_entity/global/j-space/research/trigger2_qwen35_08b_xeno_hcu_synthetic_seed_v1.jsonl'


def load_seed():
    return [json.loads(x) for x in SEED.read_text(encoding='utf-8').splitlines() if x.strip()]


class Trigger2TrainingTraceFamilySplitLinterTests(unittest.TestCase):
    def test_current_seed_passes_candidate_and_dataset_split_gates(self):
        result = linter.adjudicate(load_seed())
        self.assertTrue(result['dataset_split_pass'], result)
        self.assertEqual(result['rows_total'], 16)
        self.assertEqual(result['rows_row_gate_fail'], 0)
        self.assertEqual(result['accepted_dataset_tokens_minted'], 0)
        self.assertFalse(result['canonical_dataset_write_performed'])
        self.assertFalse(result['training_credit_minted'])

    def test_same_family_cannot_cross_split_even_with_new_ancestry(self):
        rows = load_seed()
        x = copy.deepcopy(rows[0])
        x['provenance_ancestry_id'] = 'fresh-ancestry-but-same-family'
        x['split'] = 'VALIDATION'
        rows.append(x)
        result = linter.adjudicate(rows)
        self.assertFalse(result['dataset_split_pass'])
        self.assertIn('XENO_BOOT_JOIN_F01', result['family_split_leaks'])

    def test_same_ancestry_cannot_cross_split_even_with_new_family(self):
        rows = load_seed()
        x = copy.deepcopy(rows[0])
        x['family_id'] = 'FRESH_FAMILY_SAME_ANCESTRY'
        x['split'] = 'HOLDOUT'
        rows.append(x)
        result = linter.adjudicate(rows)
        self.assertFalse(result['dataset_split_pass'])
        self.assertIn('trigger2-v3-synthetic-xeno-boot-join', result['provenance_ancestry_split_leaks'])

    def test_row_gate_failure_is_dataset_failure(self):
        rows = load_seed()
        rows[0]['canonical_truth_allowed'] = True
        result = linter.adjudicate(rows)
        self.assertFalse(result['dataset_split_pass'])
        self.assertEqual(result['rows_row_gate_fail'], 1)
        self.assertIn('TRAINING_ROW_CANNOT_MINT_CANONICAL_TRUTH', result['row_failures'][0]['failures'])

    def test_holdout_selected_row_fails_closed(self):
        rows = load_seed()
        x = copy.deepcopy(rows[0])
        x['family_id'] = 'HOLDOUT_NEW_FAMILY'
        x['provenance_ancestry_id'] = 'holdout-new-ancestry'
        x['split'] = 'HOLDOUT'
        x['selected_using_holdout'] = True
        rows.append(x)
        result = linter.adjudicate(rows)
        self.assertFalse(result['dataset_split_pass'])
        self.assertTrue(any('HOLDOUT_SELECTION_FORBIDDEN' in rf['failures'] for rf in result['row_failures']))


if __name__ == '__main__':
    unittest.main()
