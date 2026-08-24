#!/usr/bin/env python3
from __future__ import annotations
import importlib.util, math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'tools/trigger1_intermediate_contrastive_protocol.py'

def load():
    spec=importlib.util.spec_from_file_location('trigger1_intermediate_contrastive_protocol',MOD)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def sha(n:int)->str:
    return f'{n:064x}'


def calibration_rows(m):
    scores={'BASELINE':0.0,'+VECTOR':3.0,'SIGN_FLIP':-3.0,'NULL_VECTOR':0.0,'ORTHOGONAL_SAME_NORM':0.1,'PERMUTED_SAME_NORM':0.2}
    rows=[]
    for case_index,case in enumerate(['c1','c2']):
        for control in m.REQUIRED_CONTROLS:
            rows.append({
                'split':'calibration','layer':8,'gain':2.0,'case_id':case,
                'prompt_sha256':sha(100+case_index),'seed':1701+case_index,
                'positive_label':'A','negative_label':'B',
                'control':control,'target_score':scores[control],
            })
    return rows


def holdout_rows(m, *, include_wrong=True, include_lesion=True, counterbalanced=True, nuisance_sign=1.0):
    scores={
        'BASELINE':0.0,
        '+VECTOR':3.0,
        'SIGN_FLIP':-3.0,
        'NULL_VECTOR':0.0,
        'ORTHOGONAL_SAME_NORM':0.1*nuisance_sign,
        'PERMUTED_SAME_NORM':0.2*nuisance_sign,
    }
    mappings=[('A_POS','A','B'),('B_POS','B','A' if counterbalanced else 'C')]
    rows=[]
    for map_index,(label_map,pos,neg) in enumerate(mappings):
        for case_index,case in enumerate(['h1','h2']):
            prompt_sha=sha(10+map_index*2+case_index)
            seed=(2718,3141)[case_index]
            for control in m.REQUIRED_CONTROLS:
                row={
                    'split':'holdout','layer':8,'gain':2.0,'case_id':case,
                    'label_map_id':label_map,'positive_label':pos,'negative_label':neg,
                    'prompt_sha256':prompt_sha,'seed':seed,
                    'control':control,'target_score':scores[control],
                }
                if control=='+VECTOR' and include_wrong:
                    row.update({
                        'wrong_layer_delta':-0.1,
                        'wrong_layer':12,
                        'wrong_layer_vector_source_layer':8,
                        'wrong_layer_same_selected_vector':True,
                        'wrong_layer_receipt_sha256':'b'*64,
                    })
                if control=='+VECTOR' and include_lesion:
                    row['lesion_delta']=-0.2; row['rescue_delta']=0.5
                rows.append(row)
    return rows


class ProtocolTests(unittest.TestCase):
    def setUp(self): self.m=load()

    def test_contrastive_direction_uses_activation_means(self):
        d=self.m.contrastive_direction([[2,0,0],[4,0,0]],[[0,2,0],[0,4,0]])
        self.assertAlmostEqual(math.sqrt(sum(x*x for x in d)),1.0,places=12)
        self.assertGreater(d[0],0); self.assertLess(d[1],0)

    def test_six_controls_sign_null_orthogonal_norm(self):
        c=self.m.control_vectors((1,2,3),2.0)
        self.assertEqual(set(self.m.REQUIRED_CONTROLS),set(c))
        self.assertEqual(tuple(-x for x in c['+VECTOR']),c['SIGN_FLIP'])
        self.assertTrue(all(x==0 for x in c['NULL_VECTOR']))
        self.assertAlmostEqual(sum(a*b for a,b in zip(c['+VECTOR'],c['ORTHOGONAL_SAME_NORM'])),0.0,places=10)
        self.assertAlmostEqual(math.sqrt(sum(x*x for x in c['+VECTOR'])),math.sqrt(sum(x*x for x in c['ORTHOGONAL_SAME_NORM'])),places=10)

    def test_lesion_and_rescue(self):
        d=(1.0,0.0,0.0); h=(3.0,4.0,0.0)
        les=self.m.lesion(h,d); res=self.m.rescue(h,d,2.0)
        self.assertEqual((0.0,4.0,0.0),les)
        self.assertEqual((2.0,4.0,0.0),res)

    def test_calibration_selection_and_strict_holdout(self):
        selected=self.m.select_layer_gain(calibration_rows(self.m))
        self.assertTrue(selected['selected']); self.assertEqual(8,selected['layer'])
        out=self.m.adjudicate_holdout(holdout_rows(self.m),selected_layer=8,selected_gain=2.0)
        self.assertTrue(out['pass']); self.assertTrue(out['counterbalanced_label_mapping'])
        self.assertTrue(out['wrong_layer_evidence_complete']); self.assertTrue(out['wrong_layer_selected_vector_provenance']); self.assertTrue(out['lesion_rescue_evidence_complete'])

    def test_holdout_requires_label_remap(self):
        rows=holdout_rows(self.m)
        for row in rows: row['label_map_id']='one'
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('LABEL_REMAP_HOLDOUT_REQUIRED',out['classification'])

    def test_holdout_requires_actual_counterbalanced_mapping(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,counterbalanced=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('COUNTERBALANCED_LABEL_MAPPING_REQUIRED',out['classification'])

    def test_holdout_requires_wrong_layer_evidence_for_every_case(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,include_wrong=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('WRONG_LAYER_EVIDENCE_REQUIRED',out['classification'])

    def test_holdout_requires_lesion_rescue_evidence_for_every_case(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,include_lesion=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('LESION_RESCUE_EVIDENCE_REQUIRED',out['classification'])

    def test_negative_same_norm_nuisance_is_penalized_by_magnitude(self):
        rows=holdout_rows(self.m,nuisance_sign=-1.0)
        for row in rows:
            if row['control']=='ORTHOGONAL_SAME_NORM': row['target_score']=-4.0
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertLessEqual(out['worst_directional_specificity_margin'],0)

    def test_duplicate_calibration_control_row_fails_closed(self):
        rows=calibration_rows(self.m)
        duplicate=dict(next(row for row in rows if row['case_id']=='c1' and row['control']=='+VECTOR'))
        duplicate['target_score']=-99.0
        rows.append(duplicate)
        with self.assertRaisesRegex(self.m.IntermediateProtocolError,'DUPLICATE_CONTROL_ROW'):
            self.m.select_layer_gain(rows)

    def test_split_calibration_prompt_cannot_form_matched_family(self):
        rows=[dict(row) for row in calibration_rows(self.m) if row['case_id']=='c1']
        next(row for row in rows if row['control']=='+VECTOR')['prompt_sha256']=sha(999)
        selected=self.m.select_layer_gain(rows)
        self.assertFalse(selected['selected'])

    def test_duplicate_holdout_control_row_fails_closed(self):
        rows=holdout_rows(self.m)
        rows.append(dict(next(row for row in rows if row['case_id']=='h1' and row['label_map_id']=='A_POS' and row['control']=='+VECTOR')))
        with self.assertRaisesRegex(self.m.IntermediateProtocolError,'DUPLICATE_CONTROL_ROW'):
            self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)

    def test_split_holdout_prompt_is_not_merged_into_matched_family(self):
        rows=holdout_rows(self.m)
        next(row for row in rows if row['case_id']=='h1' and row['label_map_id']=='A_POS' and row['control']=='SIGN_FLIP')['prompt_sha256']=sha(998)
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('WRONG_LAYER_EVIDENCE_REQUIRED',out['classification'])

    def test_split_holdout_seed_is_not_merged_into_matched_family(self):
        rows=holdout_rows(self.m)
        next(row for row in rows if row['case_id']=='h1' and row['label_map_id']=='A_POS' and row['control']=='SIGN_FLIP')['seed']=9999
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('WRONG_LAYER_EVIDENCE_REQUIRED',out['classification'])

    def test_auxiliary_causal_evidence_must_bind_plus_vector_row(self):
        rows=holdout_rows(self.m)
        plus=next(row for row in rows if row['case_id']=='h1' and row['label_map_id']=='A_POS' and row['control']=='+VECTOR')
        baseline=next(row for row in rows if row['case_id']=='h1' and row['label_map_id']=='A_POS' and row['control']=='BASELINE')
        baseline['wrong_layer_delta']=plus.pop('wrong_layer_delta')
        baseline['wrong_layer']=plus.pop('wrong_layer')
        baseline['wrong_layer_vector_source_layer']=plus.pop('wrong_layer_vector_source_layer')
        baseline['wrong_layer_same_selected_vector']=plus.pop('wrong_layer_same_selected_vector')
        baseline['wrong_layer_receipt_sha256']=plus.pop('wrong_layer_receipt_sha256')
        with self.assertRaisesRegex(self.m.IntermediateProtocolError,'AUXILIARY_CAUSAL_EVIDENCE_MUST_BIND_PLUS_VECTOR_ROW'):
            self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)

if __name__=='__main__': unittest.main()
