#!/usr/bin/env python3
from __future__ import annotations
import hashlib, importlib.util, math
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MOD=ROOT/'tools/trigger1_intermediate_contrastive_protocol.py'

def load():
    spec=importlib.util.spec_from_file_location('trigger1_intermediate_contrastive_protocol',MOD)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def sha(text): return hashlib.sha256(text.encode()).hexdigest()


def semantic_scores(polarity, nuisance_sign=1.0):
    base=1.0 if polarity=='positive' else -1.0
    return {
        'BASELINE':base,
        '+VECTOR':base+3.0,
        'SIGN_FLIP':base-3.0,
        'NULL_VECTOR':base,
        'ORTHOGONAL_SAME_NORM':base+0.1*nuisance_sign,
        'PERMUTED_SAME_NORM':base+0.2*nuisance_sign,
    }


def holdout_rows(m, *, include_wrong=True, include_lesion=True, counterbalanced=True,
                 nuisance_sign=1.0, include_semantic=True, bad_baseline=False,
                 positive_only=False):
    mappings=[('A_POS','A','B'),('B_POS','B','A' if counterbalanced else 'C')]
    cases=[('h1','positive','The panel strongly supports the measure.')]
    if not positive_only:
        cases.append(('h2','negative','The panel strongly opposes the measure.'))
    rows=[]
    for label_map,pos,neg in mappings:
        for case,polarity,stimulus in cases:
            scores=semantic_scores(polarity,nuisance_sign)
            if bad_baseline and polarity=='negative':
                scores={k:v+3.0 for k,v in scores.items()}
            for control in m.REQUIRED_CONTROLS:
                row={
                    'split':'holdout','layer':8,'gain':2.0,'case_id':case,
                    'label_map_id':label_map,'positive_label':pos,'negative_label':neg,
                    'control':control,'target_score':scores[control],
                }
                if include_semantic:
                    row.update({
                        'stimulus_polarity':polarity,
                        'stimulus_family_id':'hold-policy-v1',
                        'stimulus_sha256':sha(stimulus),
                    })
                if include_wrong: row['wrong_layer_delta']=-0.1
                if include_lesion:
                    row['lesion_delta']=-0.2; row['rescue_delta']=0.5
                rows.append(row)
    return rows


def calibration_rows(m, *, include_semantic=True, bad_baseline=False):
    cases=(
        ('c1','positive','The board strongly endorses the proposal.'),
        ('c2','negative','The board strongly rejects the proposal.'),
    )
    rows=[]
    for case,polarity,stimulus in cases:
        scores=semantic_scores(polarity)
        if bad_baseline and polarity=='negative':
            scores={k:v+3.0 for k,v in scores.items()}
        for control in m.REQUIRED_CONTROLS:
            row={'split':'calibration','layer':8,'gain':2.0,'case_id':case,'control':control,'target_score':scores[control]}
            if include_semantic:
                row.update({
                    'stimulus_polarity':polarity,
                    'stimulus_family_id':'cal-policy-v1',
                    'stimulus_sha256':sha(stimulus),
                })
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

    def test_calibration_selection_and_semantic_holdout(self):
        selected=self.m.select_layer_gain(calibration_rows(self.m))
        self.assertTrue(selected['selected']); self.assertEqual(8,selected['layer'])
        self.assertGreater(selected['semantic_baseline_min_signed_margin'],0)
        out=self.m.adjudicate_holdout(holdout_rows(self.m),selected_layer=8,selected_gain=2.0)
        self.assertTrue(out['pass']); self.assertTrue(out['counterbalanced_label_mapping'])
        self.assertEqual(['negative','positive'],out['semantic_polarities'])
        self.assertEqual(out['semantic_baseline_case_count'],out['semantic_baseline_correct_count'])
        self.assertTrue(out['wrong_layer_evidence_complete']); self.assertTrue(out['lesion_rescue_evidence_complete'])

    def test_calibration_rejects_symbol_only_rows(self):
        with self.assertRaisesRegex(self.m.IntermediateProtocolError,'SEMANTIC_STIMULUS_POLARITY_REQUIRED'):
            self.m.select_layer_gain(calibration_rows(self.m,include_semantic=False))

    def test_calibration_requires_baseline_semantic_discrimination(self):
        out=self.m.select_layer_gain(calibration_rows(self.m,bad_baseline=True))
        self.assertFalse(out['selected']); self.assertEqual('SEMANTIC_BASELINE_DISCRIMINATION_REQUIRED',out['reason'])

    def test_holdout_rejects_symbol_only_rows(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,include_semantic=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('SEMANTIC_STIMULUS_POLARITY_REQUIRED',out['classification'])

    def test_holdout_requires_both_semantic_polarities(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,positive_only=True),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('SEMANTIC_POLARITY_COVERAGE_REQUIRED',out['classification'])

    def test_holdout_requires_baseline_semantic_discrimination(self):
        out=self.m.adjudicate_holdout(holdout_rows(self.m,bad_baseline=True),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass']); self.assertEqual('SEMANTIC_BASELINE_DISCRIMINATION_REQUIRED',out['classification'])

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
            if row['control']=='ORTHOGONAL_SAME_NORM':
                polarity=row['stimulus_polarity']; base=1.0 if polarity=='positive' else -1.0
                row['target_score']=base-4.0
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertLessEqual(out['worst_directional_specificity_margin'],0)

if __name__=='__main__': unittest.main()
