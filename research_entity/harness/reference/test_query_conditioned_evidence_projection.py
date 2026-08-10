from __future__ import annotations
import hashlib,json,unittest
from .query_conditioned_evidence_projection import QueryConditionedEvidenceProjector,QueryEvidenceSpec,StaleEvidenceProjection

def h(v): return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def row(domain,key,value,epistemic='KNOWN',status='CURRENT'):
    return {'domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':status,'domain_epoch':1,'semantic_hash':h([domain,key,value,epistemic,status])}
class Ledger:
    def __init__(self,rows): self._rows=list(rows); self.epoch=1; self.semantic_state_hash=h([(r['domain'],r['key'],r['semantic_hash']) for r in rows])
    def materialized(self): return list(self._rows)

class QCEP03Tests(unittest.TestCase):
    def fixture(self):
        rows=[row('semantic','root',{'text':'anchor'}),row('semantic','needed',{'text':'neutral'}),row('semantic','needed2',{'text':'neutral'}),row('semantic','hub',{'text':'generic'}),row('semantic','conflict',{'text':'uncertain'},'CONFLICT'),row('semantic','launder',{'text':'forbidden'})]
        rows += [
            row('dependency','r-n',{'source':'semantic:root','target':'semantic:needed','strength':.72,'relation_type':'SUPPORTS','cue':'zircon constraint'}),
            row('dependency','n-n2',{'source':'semantic:needed','target':'semantic:needed2','strength':.92,'relation_type':'SUPPORTS','cue':'zircon constraint'}),
            row('dependency','r-h',{'source':'semantic:root','target':'semantic:hub','strength':.99,'relation_type':'RELATED','cue':'generic association'}),
            row('dependency','r-c',{'source':'semantic:root','target':'semantic:conflict','strength':1.0,'relation_type':'SUPPORTS','cue':'zircon constraint'}),
            row('dependency','c-l',{'source':'semantic:conflict','target':'semantic:launder','strength':1.0,'relation_type':'SUPPORTS','cue':'zircon constraint'}),
        ]
        for j in range(20):
            rows.append(row('semantic',f'd{j}',{'text':'generic distractor'}))
            rows.append(row('dependency',f'h-d{j}',{'source':'semantic:hub','target':f'semantic:d{j}','strength':.98,'relation_type':'RELATED','cue':'generic association'}))
        return rows

    def test_exact_topk_output_equals_full_qcep(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        common=dict(projection_id='x',query_text='zircon constraint',seed_refs=('semantic:root',),basis_epoch=1,max_items=3,max_hops=3,frontier_budget=256)
        full=p.project(QueryEvidenceSpec(**common,exact_top_k_stop=False))
        exact=p.project(QueryEvidenceSpec(**common,exact_top_k_stop=True))
        sig=lambda o:[(x['ref'],x['activation_score'],x['hop']) for x in o['selected']]
        self.assertEqual(sig(full),sig(exact))
        self.assertLessEqual(exact['frontier_expansions'],full['frontier_expansions'])
        self.assertIn(exact['frontier_stop_reason'],('EXACT_TOP_K_SCORE_BOUND','FRONTIER_EXHAUSTED'))
        self.assertEqual(exact['top_k_proof'],'ALL_TRANSITION_MULTIPLIERS_LE_1_DESCENDANT_SCORE_LE_FRONTIER_ANCESTOR')

    def test_query_conditioning_beats_generic_hub_and_no_laundering(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        out=p.project(QueryEvidenceSpec('q','zircon constraint',('semantic:root',),1,max_items=4,max_hops=3))
        refs=[x['ref'] for x in out['selected']]
        self.assertLess(refs.index('semantic:needed'),refs.index('semantic:hub'))
        self.assertIn('semantic:conflict',out['blocked_propagation_refs'])
        self.assertNotIn('semantic:launder',refs)
        self.assertEqual(out['truth_authority'],'NONE'); self.assertEqual(out['effect_authority'],'NONE')

    def test_missing_admissible_semantics_falls_back_exact_static_factor(self):
        rows=[row('semantic','root',{}),row('semantic','a',{}),row('semantic','b',{}),row('semantic','conflict',{},'CONFLICT'),row('dependency','ra',{'source':'semantic:root','target':'semantic:a','strength':.7,'relation_type':'SUPPORTS'}),row('dependency','rb',{'source':'semantic:root','target':'semantic:b','strength':.6,'relation_type':'RELATED'}),row('dependency','rc',{'source':'semantic:root','target':'semantic:conflict','strength':1.0,'relation_type':'SUPPORTS','cue':'opaquequery'})]
        p=QueryConditionedEvidenceProjector(Ledger(rows)); out=p.project(QueryEvidenceSpec('ood','opaquequery',('semantic:root',),1,max_items=3,max_hops=1,hop_decay=.88,hub_penalty=9,relevance_floor=.01))
        by={x['ref']:x for x in out['selected']}
        self.assertAlmostEqual(by['semantic:a']['activation_score'],.7*.88,12); self.assertAlmostEqual(by['semantic:b']['activation_score'],.6*.88,12)
        self.assertEqual(by['semantic:a']['edge_hub_factor'],1.0)

    def test_structural_json_field_names_are_not_semantic_evidence(self):
        rows=[
            row('semantic','root',{}),row('semantic','a',{}),row('semantic','b',{}),
            row('dependency','ra',{'source':'semantic:root','target':'semantic:a','strength':.7,'relation_type':'SUPPORTS'}),
            row('dependency','rb',{'source':'semantic:root','target':'semantic:b','strength':.6,'relation_type':'RELATED'}),
        ]
        p=QueryConditionedEvidenceProjector(Ledger(rows))
        out=p.project(QueryEvidenceSpec('schema','target source strength relation_type',('semantic:root',),1,max_items=3,max_hops=1,hop_decay=.88,hub_penalty=9,relevance_floor=.01))
        by={x['ref']:x for x in out['selected']}
        self.assertAlmostEqual(by['semantic:a']['activation_score'],.7*.88,12)
        self.assertAlmostEqual(by['semantic:b']['activation_score'],.6*.88,12)
        self.assertEqual(by['semantic:a']['edge_hub_factor'],1.0)
        self.assertEqual(out['semantic_signal_rule'],'STRUCTURAL_JSON_KEYS_EXCLUDED_ONLY_EXPLICIT_EVIDENCE_FIELDS_COUNT')

    def test_typed_focus_is_not_diluted_by_long_query_or_requirement_id(self):
        rows=[
            row('semantic','root',{'text':'anchor'}),row('semantic','needed',{'text':'neutral'}),row('semantic','hub',{'text':'generic'}),
            row('dependency','rn',{'source':'semantic:root','target':'semantic:needed','strength':.72,'relation_type':'SUPPORTS','query_cue':'target evidence'}),
            row('dependency','rh',{'source':'semantic:root','target':'semantic:hub','strength':.99,'relation_type':'RELATED','query_cue':'generic association'}),
        ]
        for j in range(12):
            rows.append(row('semantic',f'd{j}',{'text':'generic'}))
            rows.append(row('dependency',f'hd{j}',{'source':'semantic:hub','target':f'semantic:d{j}','strength':.98,'relation_type':'RELATED','query_cue':'generic association'}))
        p=QueryConditionedEvidenceProjector(Ledger(rows))
        out=p.project(QueryEvidenceSpec('focus','need target evidence with many unrelated words and target_requirement',('semantic:root',),1,max_items=3,max_hops=1,focus_terms=('target','target_requirement')))
        by={x['ref']:x for x in out['selected']}
        self.assertEqual(by['semantic:needed']['edge_query_relevance'],1.0)
        self.assertGreater(by['semantic:needed']['activation_score'],by['semantic:hub']['activation_score'])
        self.assertEqual(out['relevance_rule'],'TYPED_FOCUS_MATCH_FIRST_ELSE_LOCAL_EVIDENCE_COVERAGE_NOT_QUERY_LENGTH')

    def test_stale_epoch_and_determinism(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        with self.assertRaises(StaleEvidenceProjection): p.project(QueryEvidenceSpec('stale','zircon',('semantic:root',),2))
        s=QueryEvidenceSpec('det','zircon constraint',('semantic:root',),1,max_items=4)
        self.assertEqual(p.project(s)['receipt_hash'],p.project(s)['receipt_hash'])

if __name__=='__main__': unittest.main()
