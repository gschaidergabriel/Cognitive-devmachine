import copy, unittest
from .h1_claygraph import static_architecture_graph, validate_static_graph, dynamic_run_graph, validate_dynamic_graph
from .frank_integrated_spine import FrankIntegratedSpine, MODULES, LINEAGE

VIS={'source_id':'cam0','capture_epoch':1,'features':{'shape':'box'},'sensor_confidence':.9,'candidate_label':'cup','prototype_similarity':.9}
OPTS=[{'name':'answer','salience':.8}]
class GraphTests(unittest.TestCase):
    def test_static_graph_matches_executable_module_set_and_lineage(self):
        g=static_architecture_graph(); v=validate_static_graph(g); self.assertTrue(v['pass'],v); self.assertEqual(v['module_count'],len(MODULES)); self.assertEqual(v['lineage_family_count'],len(LINEAGE))
    def test_static_graph_tamper_detected(self):
        g=static_architecture_graph(); g['nodes']=g['nodes'][1:]; self.assertFalse(validate_static_graph(g)['pass'])
    def test_every_edge_has_intervention_handle_and_known_endpoints(self):
        g=static_architecture_graph(); ids={n['id'] for n in g['nodes']}; self.assertTrue(all(e['source'] in ids and e['target'] in ids and e['intervention_handle'] for e in g['edges']))
    def test_dynamic_run_graph_records_gwt_causal_stages(self):
        r=FrankIntegratedSpine(); c=r.cycle('hello',VIS,OPTS); g=dynamic_run_graph(cycle=c,trace_id='t1'); v=validate_dynamic_graph(g); self.assertTrue(v['pass'],v); s=g['gwt_stages']; self.assertTrue(s['ignition']); self.assertTrue(s['delivery' if 'delivery' in s else 'delivered']); self.assertTrue(s['uptake']); self.assertTrue(s['causal_use']); self.assertTrue(s['reentry']); r.close()
    def test_dynamic_stage_invariant_detects_causal_use_without_uptake(self):
        r=FrankIntegratedSpine(); c=r.cycle('hello',VIS,OPTS); g=dynamic_run_graph(cycle=c,trace_id='t1'); g['gwt_stages']['uptake']=False; from .state_ledger import h; g['run_graph_hash']=h({k:v for k,v in g.items() if k!='run_graph_hash'}); self.assertFalse(validate_dynamic_graph(g)['pass']); r.close()
    def test_intervention_is_recorded(self):
        r=FrankIntegratedSpine(); c=r.cycle('hello',VIS,OPTS); g=dynamic_run_graph(cycle=c,trace_id='t1',interventions=('lesion:hyperposition',)); self.assertIn('lesion:hyperposition',g['interventions']); r.close()
if __name__=='__main__': unittest.main()
