from __future__ import annotations
import hashlib, json, unittest

from .query_conditioned_evidence_projection import (
    QueryConditionedEvidenceProjector, QueryEvidenceSpec, StaleEvidenceProjection,
)


def h(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def row(domain,key,value,epistemic='KNOWN',status='CURRENT'):
    return {'domain':domain,'key':key,'value':value,'epistemic':epistemic,'status':status,'domain_epoch':1,'semantic_hash':h([domain,key,value,epistemic,status])}


class Ledger:
    def __init__(self, rows):
        self._rows=list(rows); self.epoch=1; self.semantic_state_hash=h([(r['domain'],r['key'],r['semantic_hash']) for r in rows])
    def materialized(self): return list(self._rows)


class QueryConditionedEvidenceProjectionTests(unittest.TestCase):
    def fixture(self):
        return [
            row('semantic','root',{'text':'anchor'}),
            row('semantic','needed',{'text':'neutral evidence'}),
            row('semantic','hub',{'text':'generic hub'}),
            row('semantic','conflict',{'text':'uncertain'},'CONFLICT'),
            row('semantic','laundered',{'text':'must not relay'}),
            row('dependency','root-needed',{'source':'semantic:root','target':'semantic:needed','strength':0.70,'relation_type':'SUPPORTS','cue':'zircon constraint evidence'}),
            row('dependency','root-hub',{'source':'semantic:root','target':'semantic:hub','strength':0.99,'relation_type':'RELATED','cue':'generic association'}),
            row('dependency','root-conflict',{'source':'semantic:root','target':'semantic:conflict','strength':1.0,'relation_type':'RELATED','cue':'zircon'}),
            row('dependency','conflict-laundered',{'source':'semantic:conflict','target':'semantic:laundered','strength':1.0,'relation_type':'SUPPORTS','cue':'zircon'}),
        ]

    def test_query_conditioning_promotes_supported_route_over_generic_hub(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        out=p.project(QueryEvidenceSpec('q1','zircon constraint evidence',('semantic:root',),1,max_items=3,max_hops=2))
        refs=[x['ref'] for x in out['selected']]
        self.assertEqual(refs[0],'semantic:root')
        self.assertLess(refs.index('semantic:needed'),refs.index('semantic:hub'))
        self.assertEqual(out['truth_authority'],'NONE')
        self.assertEqual(out['effect_authority'],'NONE')
        self.assertFalse(out['persistent_second_store'])

    def test_negative_space_cannot_relay(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        out=p.project(QueryEvidenceSpec('q2','zircon',('semantic:root',),1,max_items=8,max_hops=3))
        self.assertIn('semantic:conflict',out['blocked_propagation_refs'])
        self.assertNotIn('semantic:laundered',[x['ref'] for x in out['selected']])

    def test_missing_admissible_edge_semantics_fall_back_to_static_weight(self):
        rows=[
            row('semantic','root',{'text':'anchor'}),
            row('semantic','needed',{'text':'neutral'}),
            row('semantic','other',{'text':'neutral'}),
            row('semantic','conflict',{'text':'uncertain'},'CONFLICT'),
            row('dependency','root-needed',{'source':'semantic:root','target':'semantic:needed','strength':0.70,'relation_type':'SUPPORTS'}),
            row('dependency','root-other',{'source':'semantic:root','target':'semantic:other','strength':0.60,'relation_type':'RELATED'}),
            row('dependency','root-conflict',{'source':'semantic:root','target':'semantic:conflict','strength':1.0,'relation_type':'SUPPORTS','cue':'opaque-missing-label'}),
        ]
        p=QueryConditionedEvidenceProjector(Ledger(rows))
        out=p.project(QueryEvidenceSpec('q-ood','opaque-missing-label',('semantic:root',),1,max_items=8,max_hops=1,hop_decay=0.88,hub_penalty=9.0,relevance_floor=0.01))
        by_ref={x['ref']:x for x in out['selected']}
        self.assertAlmostEqual(by_ref['semantic:needed']['activation_score'],0.70*0.88,places=12)
        self.assertAlmostEqual(by_ref['semantic:other']['activation_score'],0.60*0.88,places=12)
        self.assertEqual(by_ref['semantic:needed']['edge_hub_factor'],1.0)
        self.assertEqual(out['missing_edge_semantics_rule'],'NO_ADMISSIBLE_LOCAL_QUERY_SIGNAL => EXACT_STATIC_EDGE_FACTOR')

    def test_stale_epoch_fails_closed(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        with self.assertRaises(StaleEvidenceProjection):
            p.project(QueryEvidenceSpec('q3','zircon',('semantic:root',),2))

    def test_deterministic_receipt(self):
        p=QueryConditionedEvidenceProjector(Ledger(self.fixture()))
        spec=QueryEvidenceSpec('q4','zircon constraint evidence',('semantic:root',),1)
        a=p.project(spec); b=p.project(spec)
        self.assertEqual(a['receipt_hash'],b['receipt_hash'])
        self.assertEqual(a['selected'],b['selected'])


if __name__=='__main__': unittest.main()
