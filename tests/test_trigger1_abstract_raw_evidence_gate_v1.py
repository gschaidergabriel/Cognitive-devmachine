import itertools
import unittest

from tools import trigger1_abstract_raw_evidence_gate_v1 as g


def valid():
    design={}
    for split in g.SPLITS:
        rows=[]
        for f in range(6):
            for si,s in enumerate(g.STATES):
                payload=f'{split}word{f}state{si}'
                rows.append({'case_id':f'{split}-{f}-{s}','family_id':f'{split}-fam-{f}','state_id':s,'scaffold_prefix':'Encode ','semantic_payload':payload,'scaffold_suffix':' silently.','prompt':'Encode '+payload+' silently.'})
        design[split]=rows
    read=[]
    for r in design['holdout']:
        scores={s:0.0 for s in g.STATES}; scores[r['state_id']]=2.0
        read.append({'case_id':r['case_id'],'true_state_id':r['state_id'],'scores':scores})
    causal=[]
    for f in range(6):
        for target in g.STATES:
            for ctrl in g.CONTROLS:
                scores={s:0.0 for s in g.STATES}
                scores[target]=2.0 if ctrl=='TARGET' else (-1.0 if ctrl=='SIGN_FLIP' else 0.0)
                causal.append({'carrier_case_id':f'c{f}','vector_state_id':target,'control':ctrl,'scores':scores})
    opaque=[]
    for f in range(2):
        for mi,perm in enumerate(itertools.permutations(g.CODES)):
            mp=dict(zip(g.STATES,perm))
            for target in g.STATES:
                for ctrl in g.CONTROLS:
                    logits={c:0.0 for c in g.CODES}; logits[mp[target]]=2.0 if ctrl=='TARGET' else (-1.0 if ctrl=='SIGN_FLIP' else 0.0)
                    opaque.append({'carrier_case_id':f'c{f}','vector_state_id':target,'mapping_id':f'm{mi}','control':ctrl,'state_to_code':mp,'code_logits':logits})
    return {'schema':g.ATTESTATION_SCHEMA,'token_scope':'ALL_PROMPT_TOKENS','historical_last_token_used_as_identity_premise':False,'prompt_design':design,'holdout_internal_readout':read,'native_internal_causal_rows':causal,'opaque_code_rows':opaque}


class RawAbstractGateTests(unittest.TestCase):
    def test_valid_raw_envelope(self):
        self.assertTrue(g.adjudicate(valid())['raw_abstract_state_evidence_pass'])

    def test_label_leak_fails(self):
        x=valid(); r=x['prompt_design']['basis'][0]; r['semantic_payload']='affirmative'; r['prompt']='Encode affirmative silently.'
        self.assertFalse(g.adjudicate(x)['raw_abstract_state_evidence_pass'])

    def test_lexical_overlap_fails(self):
        x=valid(); a=x['prompt_design']['basis'][0]; b=x['prompt_design']['holdout'][0]; b['semantic_payload']=a['semantic_payload']; b['prompt']='Encode '+b['semantic_payload']+' silently.'
        self.assertFalse(g.adjudicate(x)['raw_abstract_state_evidence_pass'])

    def test_code_identity_only_effect_fails(self):
        x=valid()
        for r in x['opaque_code_rows']:
            if r['control']=='TARGET': r['code_logits']={'A':2.0,'B':0.0,'C':0.0}
        self.assertFalse(g.adjudicate(x)['raw_abstract_state_evidence_pass'])

    def test_last_token_identity_premise_fails(self):
        x=valid(); x['historical_last_token_used_as_identity_premise']=True
        self.assertFalse(g.adjudicate(x)['raw_abstract_state_evidence_pass'])


if __name__=='__main__':
    unittest.main()
