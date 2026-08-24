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

    def _scores(self):
        return {'BASELINE':0.0,'+VECTOR':3.0,'SIGN_FLIP':-3.0,'NULL_VECTOR':0.0,'ORTHOGONAL_SAME_NORM':0.1,'PERMUTED_SAME_NORM':0.2}

    def _holdout(self, *, wrong_layer=True, lesion_rescue=True):
        rows=[]; scores=self._scores()
        for label_map, case in [('A_POS','h1'),('B_POS','h2')]:
            for control in self.m.REQUIRED_CONTROLS:
                row={'split':'holdout','layer':8,'gain':2.0,'case_id':case,'label_map_id':label_map,'control':control,'target_score':scores[control]}
                if control=='+VECTOR' and wrong_layer:
                    row['wrong_layer_delta']=-0.1
                if control=='+VECTOR' and lesion_rescue:
                    row['lesion_delta']=-0.2; row['rescue_delta']=0.5
                rows.append(row)
        return rows

    def test_calibration_selection_and_holdout_label_remap(self):
        controls=self.m.REQUIRED_CONTROLS
        cal=[]; scores=self._scores()
        for case in ['c1','c2']:
            for control in controls:
                cal.append({'split':'calibration','layer':8,'gain':2.0,'case_id':case,'control':control,'target_score':scores[control]})
        selected=self.m.select_layer_gain(cal)
        self.assertTrue(selected['selected']); self.assertEqual(8,selected['layer'])
        out=self.m.adjudicate_holdout(self._holdout(),selected_layer=8,selected_gain=2.0)
        self.assertTrue(out['pass']); self.assertEqual(2,out['label_map_count'])

    def test_holdout_requires_label_remap(self):
        scores={'BASELINE':0.0,'+VECTOR':2.0,'SIGN_FLIP':-2.0,'NULL_VECTOR':0.0,'ORTHOGONAL_SAME_NORM':0.0,'PERMUTED_SAME_NORM':0.0}
        rows=[{'split':'holdout','layer':4,'gain':1.0,'case_id':'h1','label_map_id':'one','control':c,'target_score':scores[c]} for c in self.m.REQUIRED_CONTROLS]
        out=self.m.adjudicate_holdout(rows,selected_layer=4,selected_gain=1.0)
        self.assertFalse(out['pass']); self.assertEqual('LABEL_REMAP_HOLDOUT_REQUIRED',out['classification'])

    def test_missing_wrong_layer_evidence_fails_closed(self):
        out=self.m.adjudicate_holdout(self._holdout(wrong_layer=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('WRONG_LAYER_EVIDENCE_REQUIRED_PER_HOLDOUT_CASE',out['classification'])

    def test_missing_lesion_rescue_evidence_fails_closed(self):
        out=self.m.adjudicate_holdout(self._holdout(lesion_rescue=False),selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('LESION_RESCUE_EVIDENCE_REQUIRED_PER_HOLDOUT_CASE',out['classification'])

    def test_partial_lesion_rescue_pair_is_malformed(self):
        rows=self._holdout()
        for row in rows:
            if row['control']=='+VECTOR' and row['case_id']=='h1':
                del row['rescue_delta']; break
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('MALFORMED_LESION_RESCUE_EVIDENCE',out['classification'])

    def test_wrong_layer_positive_effect_rejects_candidate(self):
        rows=self._holdout()
        for row in rows:
            if row['control']=='+VECTOR': row['wrong_layer_delta']=0.25
        out=self.m.adjudicate_holdout(rows,selected_layer=8,selected_gain=2.0)
        self.assertFalse(out['pass'])
        self.assertEqual('INTERMEDIATE_REPRESENTATION_NOT_ESTABLISHED',out['classification'])
        self.assertFalse(out['wrong_layer_ok'])

if __name__=='__main__': unittest.main()
